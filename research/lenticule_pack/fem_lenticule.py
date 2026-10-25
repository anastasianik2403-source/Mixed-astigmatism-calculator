"""
fem_lenticule.py — конечно-элементная модель роговицы до и после удаления лентикулы (открытый код, scikit-fem).

ЧТО ЭТО И ЧТО НЕТ (честно):
  * Это учебно-исследовательская модель ПЕРВОГО ПРИБЛИЖЕНИЯ, а не клинический инструмент и не замена ANSYS.
  * Материал — изотропный линейно-упругий (E, ν заданы), геометрия «до» принята ненапряжённой, лимб жёстко закреплён,
    коллаген/анизотропия, эпителий, регресс и переходная зона реальной лентикулы не моделируются.
  * Результаты зависят от E (почти обратно пропорционально) — значения E в литературе сильно разнятся.
    Поэтому смотрите на ОТНОСИТЕЛЬНЫЕ различия «до/после» и делайте анализ чувствительности (--E), а не на абсолютные мкм.
  * Проверка кода: (1) fem_validation.py — решатель сверен с аналитикой (круглая защемлённая пластина: отклонение 2 %;
    защемлённый сферический купол по теории пологих оболочек: апекс 110 мкм против 106–114 мкм); (2) при каждом запуске
    геометрическое изменение кривизны по меридианам сверяется с оптикой (ΔK ≈ 0,8975·сила меридиана).

Что считает:
  1. Сетка 3D (гексаэдры): роговица — сферический купол R=7,8 мм, толщина растёт от центра к лимбу (cct → t_per);
     «после» = передняя поверхность опущена на толщину лентикулы t(x,y) (из lenticule_model.py) со сглаженным краем.
  2. Нагрузка — ВГД на заднюю поверхность, лимб закреплён.
  3. Результаты: смещение вершины, карта разницы смещений «после − до», кривизна по плоскому и крутому меридиану (ΔK, дптр)
     — отдельно «только геометрия» и «геометрия + нагружение ВГД»; максимум напряжений по Мизесу.
  4. Файлы: results.csv, fem_maps.png, pre.vtu / post.vtu (открыть в ParaView).

Запуск:
    pip install scikit-fem meshio matplotlib numpy scipy
    python3 fem_validation.py                         # сначала проверка решателя (≈ 30 с)
    python3 fem_lenticule.py --sph 1.0 --cyl -4.0 --axis 0 --oz 6.7 --tmin 20 --iop 15 --E 1.0 --out fem_out
    python3 fem_lenticule.py --E 0.3 ; --E 1.0 ; --E 3.0      # анализ чувствительности к жёсткости (три запуска)
"""
from __future__ import annotations
import argparse, os, sys, time, csv
from dataclasses import dataclass
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lenticule_model import Lenticule
from skfem import MeshHex, ElementHex2, ElementVector, Basis, FacetBasis, LinearForm, solve, condense
from skfem.helpers import dot

N_KERATOMETRIC = 1.3375
MMHG = 0.133322e-3          # МПа в 1 мм рт. ст.


@dataclass
class Cornea:
    r_ant: float = 7.8      # радиус передней поверхности, мм
    cct: float = 0.54       # центральная толщина, мм
    t_per: float = 0.70     # толщина на границе модели (r_lim), мм
    r_lim: float = 5.5      # радиус модели (≈ лимб), мм; на нём — жёсткое закрепление
    E: float = 1.0          # МПа (эффективный линейный модуль при физиологической нагрузке; в литературе ~0,3–3 МПа)
    nu: float = 0.45        # коэффициент Пуассона (0,49–0,5 в реальности; 0,45 — компромисс против «запирания» элементов)
    iop: float = 15.0       # мм рт. ст.
    trans: float = 0.5      # ширина сглаженного края лентикулы за ОЗ, мм (допущение модели)


def z_ant_pre(C, x, y):
    return np.sqrt(C.r_ant ** 2 - x ** 2 - y ** 2) - C.r_ant


def thickness_pre(C, x, y):
    return C.cct + (C.t_per - C.cct) * (x ** 2 + y ** 2) / C.r_lim ** 2


def lent_depth(C, L, x, y):
    """Глубина удаления (мм) с плавным спадом за границей ОЗ (косинус)."""
    r = np.hypot(x, y)
    t = np.nan_to_num(L.thickness(np.minimum(x, 1e9), np.minimum(y, 1e9)), nan=0.0)
    a = np.radians(L.axis); perp = -x * np.sin(a) + y * np.cos(a)
    t_ext = L.t0 + (L.sph * r ** 2 + L.cyl * perp ** 2) * L.k            # продолжение формулы за ОЗ (для края)
    edge = L.t0 + (L.sph * L.R ** 2 + L.cyl * ((-np.cos(np.arctan2(y, x)) * np.sin(a) + np.sin(np.arctan2(y, x)) * np.cos(a)) * L.R) ** 2) * L.k
    w = np.where(r <= L.R, 1.0, 0.5 * (1 + np.cos(np.pi * np.clip((r - L.R) / C.trans, 0, 1))))
    return np.where(r <= L.R, t_ext, edge * w) / 1000.0


def build_mesh(C, L, post_op, nxy=16, nz=3):
    u = np.linspace(-1, 1, nxy + 1); w = np.linspace(0, 1, nz + 1)
    m0 = MeshHex.init_tensor(u, u, w)
    U, V, W = m0.p
    xd = U * np.sqrt(1 - V ** 2 / 2) * C.r_lim; yd = V * np.sqrt(1 - U ** 2 / 2) * C.r_lim   # квадрат → круг без вырожденных элементов
    za = z_ant_pre(C, xd, yd) - (lent_depth(C, L, xd, yd) if post_op else 0.0)
    zp = z_ant_pre(C, xd, yd) - thickness_pre(C, xd, yd)
    z = zp + W * (za - zp)
    return MeshHex(np.ascontiguousarray(np.vstack([xd, yd, z])), m0.t), (zp, za)



def assemble_stiffness(basis, lam, mu):
    """Матрица жёсткости линейной упругости (векторизованная сборка; штатная сборка scikit-fem для векторных
    квадратичных гексаэдров на порядок медленнее). K_ij = ∫ 2μ ε(φi):ε(φj) + λ div φi div φj dV."""
    import scipy.sparse as sp
    nloc, nel = basis.Nbfun, basis.nelems
    G = np.stack([basis.basis[i][0].grad for i in range(nloc)])           # (nloc, 3, 3, nel, nqp): ∂u_a/∂x_b
    E = 0.5 * (G + np.swapaxes(G, 1, 2)); D = G[:, 0, 0] + G[:, 1, 1] + G[:, 2, 2]
    del G
    w = basis.dx                                                           # (nel, nqp)
    # E: деформация, D: дивергенция; сумма по компонентам и точкам интегрирования — пакетным матричным произведением (экономит память)
    Em = E.reshape(nloc, 9, nel, -1).transpose(2, 0, 1, 3).reshape(nel, nloc, -1)          # (nel, nloc, 9*nqp)
    Wm = np.broadcast_to(w[:, None, :], (nel, 9, w.shape[1])).reshape(nel, 1, -1)          # (nel, 1, 9*nqp)
    Dm = D.transpose(1, 0, 2)                                                              # (nel, nloc, nqp)
    Ke = 2 * mu * np.matmul(Em * Wm, Em.transpose(0, 2, 1)) + lam * np.matmul(Dm * w[:, None, :], Dm.transpose(0, 2, 1))
    ed = basis.element_dofs                                                # (nloc, nel)
    I = np.broadcast_to(ed.T[:, :, None], Ke.shape).ravel(); J = np.broadcast_to(ed.T[:, None, :], Ke.shape).ravel()
    return sp.coo_matrix((Ke.ravel(), (I, J)), shape=(basis.N, basis.N)).tocsr()


def linsolve(K, f, fixed, iterative=False):
    """Прямой решатель (быстрый, но ~17 тыс. неизвестных — предел для 8 ГБ ОЗУ) или сопряжённые градиенты с диагональным
    предобуславливателем (экономит память, медленнее)."""
    A, b, x, I = condense(K, f, D=fixed)
    if not iterative:
        return solve(A, b, x, I)
    import scipy.sparse.linalg as spla
    d = A.diagonal(); M = spla.LinearOperator(A.shape, matvec=lambda v: v / d)
    sol, info = spla.cg(A, b, M=M, rtol=1e-9, atol=0.0, maxiter=20000)
    if info != 0:
        print('предупреждение: CG не сошёлся (info=%s); уменьшите сетку или используйте прямой решатель' % info)
    x[I] = sol
    return x


def solve_case(C, L, post_op, nxy, nz, loaded=True, iterative=False):
    mesh, _ = build_mesh(C, L, post_op, nxy, nz)
    basis = Basis(mesh, ElementVector(ElementHex2()), intorder=5)      # 3×3×3 точки Гаусса: достаточно для трикубической геометрии (по умолчанию scikit-fem берёт 7×7×7)
    lam = C.E * C.nu / ((1 + C.nu) * (1 - 2 * C.nu)); mu = C.E / (2 * (1 + C.nu))

    K = assemble_stiffness(basis, lam, mu)
    zp_fun = lambda x, y: z_ant_pre(C, x, y) - thickness_pre(C, x, y)
    # грани задней поверхности: у которых ВСЕ узлы лежат на ней
    zp_nodes = np.abs(mesh.p[2] - zp_fun(mesh.p[0], mesh.p[1])) < 1e-9
    f2v = mesh.facets
    post_facets = np.nonzero(zp_nodes[f2v].all(axis=0))[0]
    fb = FacetBasis(mesh, basis.elem, facets=post_facets)
    p = C.iop * MMHG if loaded else 0.0

    @LinearForm
    def load(v, w):
        return -p * dot(w.n, v)                      # давление действует на материал против внешней нормали (т.е. вверх)
    f = load.assemble(fb)
    # жёсткое закрепление боковой поверхности (лимб): ВСЕ степени свободы на боковых гранях — вершины, рёбра и грани (у квадратичных элементов их нет только в вершинах)
    on_rim = np.hypot(mesh.p[0], mesh.p[1]) > C.r_lim * (1 - 1e-9)
    fixed = basis.get_dofs(facets=np.nonzero(on_rim[mesh.facets].all(axis=0))[0])
    u = linsolve(K, f, fixed, iterative)
    return mesh, basis, u, (lam, mu)


def surface_nodes(mesh, C, L, post_op):
    za = lambda x, y: z_ant_pre(C, x, y) - (lent_depth(C, L, x, y) if post_op else 0.0)
    return np.abs(mesh.p[2] - za(mesh.p[0], mesh.p[1])) < 1e-9


def meridian_curvature(mesh, uz, onsurf, direction, C, half=2.0):
    """Кривизна передней поверхности вдоль оси x (direction=0) или y (direction=1): параболическая аппроксимация, |s|<half мм."""
    x, y, z = mesh.p
    s, other = (x, y) if direction == 0 else (y, x)
    sel = onsurf & (np.abs(other) < 1e-9) & (np.abs(s) <= half)
    ss = s[sel]; zz = (z + uz)[sel]
    a = np.polyfit(ss, zz, 2)[0]
    R = -1.0 / (2 * a)
    return (N_KERATOMETRIC - 1) * 1000.0 / R     # дптр (мм → м)


def von_mises_zone(basis, mesh, u, lam, mu, r_zone):
    """Максимум напряжения по Мизесу (МПа) в элементах, центр которых лежит в круге радиуса r_zone (зона лентикулы).
    Намеренно не по всей модели: у жёсткого закрепления лимба — сингулярность, там максимум не информативен."""
    eps = basis.interpolate(u).grad                       # (3,3,nel,nqp)
    e = 0.5 * (eps + np.swapaxes(eps, 0, 1)); tr = e[0, 0] + e[1, 1] + e[2, 2]
    s = 2 * mu * e
    for i in range(3): s[i, i] += lam * tr
    vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2) + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))
    cen = mesh.p[:, mesh.t].mean(axis=1)                  # (3, nel)
    return float(vm[np.hypot(cen[0], cen[1]) < r_zone].max())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0)
    ap.add_argument('--axis', type=float, default=0.0); ap.add_argument('--oz', type=float, default=6.7); ap.add_argument('--tmin', type=float, default=20.0)
    ap.add_argument('--iop', type=float, default=15.0); ap.add_argument('--E', type=float, default=1.0); ap.add_argument('--nu', type=float, default=0.45)
    ap.add_argument('--cct', type=float, default=0.54); ap.add_argument('--nxy', type=int, default=16); ap.add_argument('--nz', type=int, default=3)
    ap.add_argument('--direct', action='store_true', help='прямой решатель вместо итерационного (быстрее на малых сетках, но > 17 тыс. неизвестных не помещается в 8 ГБ ОЗУ)')
    ap.add_argument('--out', default='fem_out')
    A = ap.parse_args()
    C = Cornea(cct=A.cct, E=A.E, nu=A.nu, iop=A.iop); L = Lenticule(A.sph, A.cyl, A.axis, A.oz, A.tmin)
    os.makedirs(A.out, exist_ok=True); t0 = time.time()
    print(L.summary())
    res = {}
    for name, post in (('pre', False), ('post', True)):
        mesh, basis, u, (lam, mu) = solve_case(C, L, post, A.nxy, A.nz, iterative=not A.direct)
        res[name] = dict(mesh=mesh, basis=basis, u=u, lam=lam, mu=mu)
        print(f'{name}: {basis.N} степеней свободы, расчёт {time.time() - t0:.0f} с')
    # --- метрики -----------------------------------------------------------------------------------
    rows = []
    onS = {k: surface_nodes(res[k]['mesh'], C, L, k == 'post') for k in res}
    U = {k: res[k]['u'][res[k]['basis'].nodal_dofs] for k in res}                 # (3, nverts)
    # геометрия без нагрузки: ΔK по меридианам (контроль: ≈ 0,8975 · сила меридиана)
    ax = np.radians(L.axis)
    meridians = {'плоский (вдоль оси)': (0 if abs(np.cos(ax)) > 0.7 else 1, L.sph), 'крутой (поперёк оси)': (1 if abs(np.cos(ax)) > 0.7 else 0, L.sph + L.cyl)}
    zero = np.zeros(res['pre']['mesh'].p.shape[1])
    print('\nΔK по меридианам, дптр (после − до):')
    print(f'{"меридиан":24s} {"сила, D":>8s} {"оптика 0,8975·P":>16s} {"геометрия":>10s} {"с нагрузкой ВГД":>16s} {"вклад нагрузки":>15s}')
    for name, (d, P) in meridians.items():
        g_pre = meridian_curvature(res['pre']['mesh'], zero, onS['pre'], d, C); g_post = meridian_curvature(res['post']['mesh'], zero, onS['post'], d, C)
        l_pre = meridian_curvature(res['pre']['mesh'], U['pre'][2], onS['pre'], d, C); l_post = meridian_curvature(res['post']['mesh'], U['post'][2], onS['post'], d, C)
        geo, loaded = g_post - g_pre, l_post - l_pre
        print(f'{name:24s} {P:8.2f} {0.8975 * P:16.2f} {geo:10.2f} {loaded:16.2f} {loaded - geo:15.3f}')
        rows.append(dict(meridian=name, power_D=P, optics_dK=0.8975 * P, geometry_dK=geo, loaded_dK=loaded, load_contribution_dK=loaded - geo))
    apex = lambda k: float(U[k][2][np.argmin(np.hypot(res[k]['mesh'].p[0], res[k]['mesh'].p[1]) + 1e3 * (~onS[k]))]) * 1000
    ap_pre, ap_post = apex('pre'), apex('post')
    vm_pre = von_mises_zone(res['pre']['basis'], res['pre']['mesh'], res['pre']['u'], res['pre']['lam'], res['pre']['mu'], L.R)
    vm_post = von_mises_zone(res['post']['basis'], res['post']['mesh'], res['post']['u'], res['post']['lam'], res['post']['mu'], L.R)
    print(f'\nсмещение вершины под ВГД {A.iop:.0f} мм рт. ст.: до {ap_pre:.1f} мкм, после {ap_post:.1f} мкм (разница {ap_post - ap_pre:+.2f} мкм)')
    print(f'максимум напряжения по Мизесу в зоне лентикулы (r < ОЗ/2): до {vm_pre * 1000:.1f} кПа, после {vm_post * 1000:.1f} кПа ({(vm_post / vm_pre - 1) * 100:+.1f} %)')
    # контроль геометрии
    for r_ in rows:
        assert abs(r_['geometry_dK'] - r_['optics_dK']) < 0.25 * max(abs(r_['optics_dK']), 0.5) + 0.15, f'проверка геометрии не пройдена: {r_}'
    print('проверка геометрии: ΔK по меридианам согласуется с оптикой модели (допуск ±25 % и ±0,15 D)')
    with open(f'{A.out}/results.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ['apex_pre_um', 'apex_post_um', 'vm_pre_kPa', 'vm_post_kPa', 'E_MPa', 'nu', 'iop_mmHg'], delimiter=';')
        w.writeheader()
        for r_ in rows: w.writerow({**r_, 'apex_pre_um': ap_pre, 'apex_post_um': ap_post, 'vm_pre_kPa': vm_pre * 1000, 'vm_post_kPa': vm_post * 1000, 'E_MPa': C.E, 'nu': C.nu, 'iop_mmHg': C.iop})
    # --- VTK и карта -------------------------------------------------------------------------------
    try:
        import meshio
        for k in res:
            m = res[k]['mesh']
            meshio.write(f'{A.out}/{k}.vtu', meshio.Mesh(m.p.T, [('hexahedron', m.t.T)], point_data={'displacement_mm': U[k].T}))
    except Exception as e:
        print('VTK не записан:', e)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    mp, mq = res['pre']['mesh'], res['post']['mesh']
    sel = onS['pre']; dUz = (U['post'][2] - U['pre'][2])[sel] * 1000              # те же узлы (топология одинакова)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    g = np.linspace(-C.r_lim, C.r_lim, 400); GX, GY = np.meshgrid(g, g)
    Tg = np.where(np.hypot(GX, GY) <= C.r_lim, lent_depth(C, L, GX, GY) * 1000, np.nan)          # то, что реально «вырезано» в модели (с плавным краем)
    sc = axs[0].pcolormesh(GX, GY, Tg, cmap='Blues', shading='auto', vmin=0)
    plt.colorbar(sc, ax=axs[0], label='толщина лентикулы, мкм'); axs[0].set_title('Удалённый слой в модели'); axs[0].set_aspect('equal')
    sc = axs[1].tricontourf(mp.p[0][sel], mp.p[1][sel], U['pre'][2][sel] * 1000, 20, cmap='viridis')
    plt.colorbar(sc, ax=axs[1], label='мкм'); axs[1].set_title('Смещение вперёд под ВГД, до операции'); axs[1].set_aspect('equal')
    sc = axs[2].tricontourf(mp.p[0][sel], mp.p[1][sel], dUz, 20, cmap='coolwarm')
    plt.colorbar(sc, ax=axs[2], label='мкм'); axs[2].set_title('Разница смещений: после − до'); axs[2].set_aspect('equal')
    fig.suptitle(f'Линейно-упругая модель: E = {C.E} МПа, ν = {C.nu}, ВГД {C.iop:.0f} мм рт. ст. — гипотеза, не клинический результат', fontsize=10)
    fig.tight_layout(); fig.savefig(f'{A.out}/fem_maps.png', dpi=130)
    print(f'готово за {time.time() - t0:.0f} с; файлы в {A.out}/')


if __name__ == '__main__':
    main()
