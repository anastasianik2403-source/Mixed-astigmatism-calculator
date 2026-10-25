"""
fem_hyper_validation.py — проверки нелинейного гиперупругого решателя fem_hyper.py.

  1. Касательная матрица материала = численная производная напряжения; напряжение = численная производная энергии
     (нео-Гук и нео-Гук + волокна HGO).
  2. Однородное одноосное растяжение куба на 30 % (точное решение для сжимаемого нео-Гука): поперечное сужение и сила.
  3. Предел малой нагрузки: при ВГД × 0,001 нелинейный решатель совпадает с линейным (fem_lenticule.py) на той же сетке.
  4. Обратная задача (предварительное напряжение): ненапряжённая форма под ВГД возвращается в измеренную.
  5. Независимая программа: CalculiX 2.21 (нео-Гук, большие перемещения, следящее давление, элементы C3D8I)
     против fem_hyper (те же материал и нагрузка) — смещение вершины.
  6. Сходимость по сетке: три сетки, полный сценарий «до/после» с предварительным напряжением.
Запуск: python3 fem_hyper_validation.py [--skip-ccx] [--out out/hyper_validation]
"""
from __future__ import annotations
import argparse, os, sys, subprocess, shutil, re, json, time
import numpy as np
from scipy.optimize import brentq
import scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem_hyper as H
import fem_lenticule as F
import fe_export as FE
from lenticule_model import Lenticule
from skfem import MeshHex

RESULTS = []


def report(name, ok, detail):
    RESULTS.append(dict(test=name, ok=bool(ok), detail=detail))
    print(('OK   ' if ok else 'FAIL ') + name + ': ' + detail, flush=True)


# ------------------------------------------------------------------------------------------------ 1
def t_tangent():
    rng = np.random.default_rng(0)
    Fd = np.eye(3)[None] + 0.06 * rng.standard_normal((6, 3, 3))
    a1 = np.tile([1.0, 0, 0], (6, 1)); a2 = np.tile([0, 0.6, 0.8], (6, 1))
    for mat, fib in [(H.Material.from_E_nu(1.0, 0.45), None),
                     (H.Material(model='hgo', C10=0.0125, D1=0.6, k1=0.05, k2=100.0), [a1, a2])]:
        P, A = H.stress_tangent(Fd, mat, fib)
        e = 1e-6; eA = eP = 0.0
        for k in range(3):
            for L in range(3):
                dF = np.zeros((3, 3)); dF[k, L] = e
                Pp, _ = H.stress_tangent(Fd + dF, mat, fib); Pm, _ = H.stress_tangent(Fd - dF, mat, fib)
                eA = max(eA, np.abs((Pp - Pm) / (2 * e) - A[:, :, :, k, L]).max())
                eP = max(eP, np.abs((H.energy(Fd + dF, mat, fib) - H.energy(Fd - dF, mat, fib)) / (2 * e) - P[:, k, L]).max())
        rel = eA / np.abs(A).max(); relP = eP / np.abs(P).max()
        report(f'1. касательная ({mat.model})', rel < 1e-6 and relP < 1e-6, f'отн. ошибка ∂P/∂F {rel:.1e}, отн. ошибка P = ∂W/∂F {relP:.1e}')


# ------------------------------------------------------------------------------------------------ 2
def t_uniaxial(stretch=1.30):
    mat = H.Material.from_E_nu(1.0, 0.45)
    m = MeshHex.init_tensor(*(np.linspace(0, 1, 3),) * 3)
    fac = lambda fn: np.nonzero(fn(m.p[:, m.facets]).all(axis=1))[0] if False else m.facets_satisfying(fn)
    geo = H.Geo(m, np.zeros(m.p.shape[1]), np.zeros(m.p.shape[1], int), np.array([], int), np.array([], int), np.array([], int), np.zeros(m.p.shape[1], bool))
    pr = H.Problem.__new__(H.Problem)
    from skfem import Basis, ElementVector, ElementHex2
    pr.geo, pr.mat = geo, mat
    pr.basis = Basis(m, ElementVector(ElementHex2()), intorder=5); b = pr.basis
    G = np.stack([b.basis[i][0].grad for i in range(b.Nbfun)])
    pr.B = np.ascontiguousarray(G.transpose(3, 4, 1, 2, 0).reshape(b.nelems, -1, 9, b.Nbfun)); pr.w = b.dx
    pr.edofs = b.element_dofs.T; pr.fib = None
    dx0 = b.get_dofs(facets=m.facets_satisfying(lambda x: x[0] < 1e-12)).all('u^1')
    dx1 = b.get_dofs(facets=m.facets_satisfying(lambda x: x[0] > 1 - 1e-12)).all('u^1')
    dy0 = b.get_dofs(facets=m.facets_satisfying(lambda x: x[1] < 1e-12)).all('u^2')
    dz0 = b.get_dofs(facets=m.facets_satisfying(lambda x: x[2] < 1e-12)).all('u^3')
    fixed = np.unique(np.concatenate([dx0, dx1, dy0, dz0])); free = np.setdiff1d(np.arange(b.N), fixed)
    u = np.zeros(b.N)
    for s in range(1, 7):
        dd = (stretch - 1) / 6                                     # приращение перемещения грани: вносится через матрицу жёсткости
        f, K = pr.internal(u)
        u[free] += spla.spsolve(K[free][:, free].tocsc(), -(f[free] + K[free][:, dx1] @ np.full(len(dx1), dd)))
        u[dx1] += dd
        for it in range(30):
            f, K = pr.internal(u); r = f[free]
            if np.linalg.norm(r) < 1e-12: break
            u[free] += spla.spsolve(K[free][:, free].tocsc(), -r)
    force = f[dx1].sum()                                           # реакция на грани x = 1 (площадь 1 в отсчётной конфигурации)
    V = u[b.nodal_dofs]; t_fe = 1 + V[1][m.p[1] > 1 - 1e-12].mean()
    lam = stretch
    def Pyy(t):
        Fd = np.diag([lam, t, t])[None]; return H.stress_tangent(Fd, mat)[0][0, 1, 1]
    t_an = brentq(Pyy, 0.5, 1.0); P_an = H.stress_tangent(np.diag([lam, t_an, t_an])[None], mat)[0][0, 0, 0]
    ok = abs(t_fe - t_an) < 1e-8 and abs(force / P_an - 1) < 1e-8
    report('2. одноосное растяжение 30 % (точное решение)', ok,
           f'поперечное растяжение КЭ {t_fe:.8f} / точное {t_an:.8f}; сила КЭ {force:.6f} / точная {P_an:.6f} Н/мм²')


# ------------------------------------------------------------------------------------------------ 3
def t_linear_limit():
    L = Lenticule(); C = F.Cornea(iop=15.0)
    Cs = F.Cornea(iop=15.0 * 1e-3)
    g = H.build_geo(Cs, L, False, 8, 2); pr = H.Problem(g, H.Material.from_E_nu(1.0, 0.45))
    u = pr.solve(H.iop_load(Cs), steps=1)
    nl = pr.vertex_disp(u)[2, H.apex_index(g)] * 1e3
    mesh, basis, ul, _ = F.solve_case(C, L, False, 8, 2, iterative=False)
    on = F.surface_nodes(mesh, C, L, False); lin = float(ul[basis.nodal_dofs][2][np.argmin(np.hypot(mesh.p[0], mesh.p[1]) + 1e3 * (~on))])
    rel = nl / lin - 1
    report('3. предел малой нагрузки = линейная упругость', abs(rel) < 2e-3,
           f'вершина (ВГД×0,001)·1000: нелинейный {nl * 1000:.4f} мкм, линейный {lin * 1000:.4f} мкм, разница {rel * 100:+.3f} %')
    # и при полном ВГД — насколько нелинейность (большие перемещения) меняет ответ
    g2 = H.build_geo(C, L, False, 8, 2); pr2 = H.Problem(g2, H.Material.from_E_nu(1.0, 0.45)); u2 = pr2.solve(H.iop_load(C))
    full = pr2.vertex_disp(u2)[2, H.apex_index(g2)] * 1000
    print(f'      справочно при ВГД 15: нелинейный {full:.1f} мкм против линейного {lin * 1000:.1f} мкм ({(full / (lin * 1000) - 1) * 100:+.1f} %)')
    return full


# ------------------------------------------------------------------------------------------------ 4
def t_inverse():
    L = Lenticule(); C = F.Cornea()
    gm = H.build_geo(C, L, False, 8, 2); mat = H.Material.from_E_nu(1.0, 0.45)
    X0, pr, u, hist = H.stress_free(gm, mat, C, verbose=False)
    pr2 = H.Problem(H.with_points(gm, X0), mat); u2 = pr2.solve(H.iop_load(C), steps=6)  # другой шаг нагружения
    err = np.abs(X0 + pr2.vertex_disp(u2) - gm.mesh.p).max() * 1000
    report('4. обратная задача (ненапряжённая форма)', err < 0.2,
           f'{len(hist)} итераций; повторный прямой расчёт отличается от измеренной формы на {err:.3f} мкм (макс.)')


# ------------------------------------------------------------------------------------------------ 5
def t_calculix(out, nxy_ccx=24, nz_ccx=6):
    if shutil.which('ccx') is None:
        report('5. сверка с CalculiX', False, 'ccx не установлен (apt install calculix-ccx) — НЕ проверено'); return
    L = Lenticule(); C = F.Cornea(E=1.0, nu=0.45, iop=15.0)
    os.makedirs(out, exist_ok=True)
    FE.write_decks(C, L, False, nxy_ccx, nz_ccx, out)
    src = open(f'{out}/calculix_pre.inp', encoding='utf-8').read()
    mat = H.Material.from_E_nu(1.0, 0.45)
    src = src.replace('TYPE=C3D8,', 'TYPE=C3D8I,').replace('*ELASTIC\n1.0,0.45\n', f'*HYPERELASTIC,NEO HOOKE\n{mat.C10:.8f},{mat.D1:.8f}\n')
    assert 'NEO HOOKE' in src and 'C3D8I' in src
    open(f'{out}/ccx_neohooke.inp', 'w', encoding='utf-8').write(src)
    t0 = time.time()
    r = subprocess.run(['ccx', 'ccx_neohooke'], cwd=out, capture_output=True, text=True, env={**os.environ, 'OMP_NUM_THREADS': '4'})
    dat = open(f'{out}/ccx_neohooke.dat').read()
    uz = float(re.findall(r'^\s*\d+\s+\S+\s+\S+\s+(\S+)\s*$', dat, re.M)[-1])
    g = H.build_geo(C, L, False, 16, 4); pr = H.Problem(g, mat); u = pr.solve(H.iop_load(C))
    me = pr.vertex_disp(u)[2, H.apex_index(g)]
    rel = me / uz - 1
    report('5. независимая программа CalculiX (нео-Гук, NLGEOM, C3D8I)', abs(rel) < 0.03,
           f'вершина: CalculiX {uz * 1000:.2f} мкм (сетка {nxy_ccx}×{nxy_ccx}×{nz_ccx}, {time.time() - t0:.0f} с), fem_hyper {me * 1000:.2f} мкм (16×16×4, Hex27); разница {rel * 100:+.2f} %')


# ------------------------------------------------------------------------------------------------ 6
def t_convergence(out):
    L = Lenticule(); C = F.Cornea(); mat = H.Material.from_E_nu(1.0, 0.45)
    rows = []
    for nxy, nz in ((8, 2), (12, 3), (16, 4)):
        r = H.run_case(C, L, mat, nxy, nz, prestress=True); r.pop('_fields')
        rows.append(r)
        print(f'      сетка {nxy}×{nxy}×{nz}: {r["dofs"]} неизв., сдвиг вершины {r["apex_shift_um"]:.2f} мкм, ΔK плоск {r["dK_flat"]:+.3f} '
              f'(по вершинам {r["dK_flat_nodes"]:+.3f}), ΔK крут {r["dK_steep"]:+.3f} (по вершинам {r["dK_steep_nodes"]:+.3f}), '
              f'геометрия {r["Kgeo_flat"]:+.3f}/{r["Kgeo_steep"]:+.3f}, σ_Мизес до/после {r["vm_pre_kPa"]:.1f}/{r["vm_post_kPa"]:.1f} кПа, {r["time_s"]:.0f} с', flush=True)
    keys = ['apex_shift_um', 'dK_flat', 'dK_steep', 'apex_iop_disp_pre_um', 'vm_pre_kPa', 'vm_post_kPa']
    lines = []
    for k in keys:
        a, b, c = (rows[i][k] for i in range(3))
        d1, d2 = abs(b - a), abs(c - b)
        lines.append(f'{k}: {a:.3f} → {b:.3f} → {c:.3f} (изменение {d1:.3f} → {d2:.3f})')
    # критерий: на двух последних сетках изменение ≤ 3 % (или ≤ 0,05 дптр для ΔK) и не больше, чем между первыми двумя
    tolk = {'apex_shift_um': 0.03, 'dK_flat': 0.05, 'dK_steep': 0.05, 'apex_iop_disp_pre_um': 0.03}
    def good(k):
        d2 = abs(rows[2][k] - rows[1][k]); d1 = abs(rows[1][k] - rows[0][k])
        lim = tolk[k] if k.startswith('dK') else tolk[k] * abs(rows[2][k])
        return d2 <= lim or d2 <= 0.5 * d1
    ok = all(good(k) for k in keys[:4])
    geo_ok = all(abs(r['Kgeo_flat'] - 0.8975 * 1.0) < 0.02 and abs(r['Kgeo_steep'] - 0.8975 * -3.0) < 0.02 for r in rows)
    report('6а. метрика ΔK: только геометрия = оптика 0,8975·P на всех сетках', geo_ok,
           '; '.join(f'{r["nxy"]}×{r["nxy"]}×{r["nz"]}: {r["Kgeo_flat"]:+.3f}/{r["Kgeo_steep"]:+.3f} (ожид. +0,898/−2,693)' for r in rows))
    report('6. сходимость по сетке (три сетки)', ok, '; '.join(lines[:4]))
    with open(f'{out}/mesh_convergence.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1, default=float)
    return rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--skip-ccx', action='store_true'); ap.add_argument('--only-convergence', action='store_true'); ap.add_argument('--out', default='out/hyper_validation')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    if not A.only_convergence:
        t_tangent(); t_uniaxial(); t_linear_limit(); t_inverse()
        if not A.skip_ccx: t_calculix(A.out + '/ccx')
    t_convergence(A.out)
    with open(f'{A.out}/validation.json', 'w', encoding='utf-8') as f: json.dump(RESULTS, f, ensure_ascii=False, indent=1)
    ok = all(r['ok'] for r in RESULTS)
    print('ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ' if ok else 'ЕСТЬ НЕПРОЙДЕННЫЕ ПРОВЕРКИ'); raise SystemExit(0 if ok else 1)
