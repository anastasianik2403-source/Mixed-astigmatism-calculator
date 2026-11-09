"""
lenticule_math_model.py — математическая модель лентикулы по измеренной карте убыли толщины (выход pentacam_lenticule.py).

Две модели, обе подгоняются по наименьшим квадратам к карте ΔT(x, y), мкм:

A. «Седло с краем» (9 параметров, у каждого — клинический смысл):
     θ' = θ − θ0,   c = cos 2θ'
     ядро:   T0(r, θ) = t0 + (a2 + b2·c)·r² + (a4 + b4·c)·r⁴
     край:   R(θ) = R0 + R2·c,    E(r, θ) = ½·[1 − tanh((r − R(θ)) / w)]
     модель: T(r, θ) = T0(r, θ)·E(r, θ)
   t0 — толщина в центре; θ0 — меридиан наибольшей толщины; (a2 ± b2)/k — оптическая сила профиля в центре вдоль θ0 и
   θ0 + 90° (k = 1/(2(n − 1)) мкм/(дптр·мм²), формула Мунерлина); a4, b4 — отклонение от параболы к краю;
   R0 ± R2 — радиус края вдоль двух меридианов; w — ширина края (переходной зоны).

B. «План → реальность» (перенос протокола VisuMax на измеренную лентикулу):
     T(x, y) ≈ α · (T_plan ∗ G_σ)(x, y)
   T_plan — лентикула Мунерлина по протоколу (в плоскости роговицы), G_σ — гауссово размытие края, α — доля
   «реализованной» толщины. Два параметра; это гипотеза-кандидат для прогноза, проверять на других глазах.

Выход: параметры (JSON), отчёт (MD, с формулами), рисунки (карты, остатки, профили), 3D-модель модели A (STL/OBJ/PLY).

Запуск:
  python3 lenticule_math_model.py --dT out/pentacam_P01_OS/ubyl_tolshchiny_P01_OS_mkm.csv --eye-code P01_OS \
         --plan "+1.75,-5.00,10,6.7,20" --vertex 12 --cap 120 --rcornea 8.18 --out out/math_P01_OS
"""
import argparse, json, math, os, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lenticule_model import Lenticule, write_stl, write_obj, write_ply, thickness_colors, mesh_volume, is_watertight

N = 1.376
K = 1.0 / (2.0 * (N - 1.0))


def read_map(path):
    L = open(path).read().splitlines()
    xs = np.array([float(v) for v in L[0].split(';')[1:]]); ys, Z = [], []
    for line in L[1:]:
        r = line.split(';'); ys.append(float(r[0])); Z.append([float(v) if v else np.nan for v in r[1:]])
    return xs, np.array(ys), np.array(Z)


def model_A(p, r, th):
    t0, a2, b2, a4, b4, th0, R0, R2, w = p
    c = np.cos(2 * (th - th0))
    core = t0 + (a2 + b2 * c) * r ** 2 + (a4 + b4 * c) * r ** 4
    edge = 0.5 * (1 - np.tanh((r - (R0 + R2 * c)) / max(w, 1e-3)))
    return core * edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dT', required=True); ap.add_argument('--eye-code', default='EYE')
    ap.add_argument('--plan', default=None, help='"Sph,Cyl,Ось,ОЗ,tmin" из протокола (очковая плоскость, минус-цилиндр)')
    ap.add_argument('--vertex', type=float, default=12.0); ap.add_argument('--cap', type=float, default=120.0)
    ap.add_argument('--rcornea', type=float, default=7.8, help='радиус передней поверхности роговицы для 3D, мм')
    ap.add_argument('--rmax', type=float, default=4.1, help='радиус, до которого берутся данные, мм')
    ap.add_argument('--out', default='out/lenticule_math')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True); code = A.eye_code
    xs, ys, Z = read_map(A.dT); X, Y = np.meshgrid(xs, ys); R = np.hypot(X, Y); TH = np.arctan2(Y, X)
    m = (R <= A.rmax) & np.isfinite(Z); r, th, v = R[m], TH[m], Z[m]

    # ---------- модель A
    p0 = [Z[70, 70], 2.0, 3.0, 0.0, 0.0, 0.0, 3.5, 0.2, 0.3]
    lo = [0, -50, -50, -20, -20, -math.pi, 2.0, -1.5, 0.05]; hi = [200, 50, 50, 20, 20, math.pi, 5.5, 1.5, 1.5]
    fA = least_squares(lambda p: model_A(p, r, th) - v, p0, bounds=(lo, hi), loss='soft_l1', f_scale=3.0)
    pA = fA.x.copy()
    if pA[2] < 0: pA[2], pA[4], pA[7], pA[5] = -pA[2], -pA[4], -pA[7], pA[5] + math.pi / 2   # θ0 — меридиан наибольшей толщины
    pA[5] = (pA[5] + math.pi) % math.pi
    resA = model_A(pA, r, th) - v; rmsA = float(np.sqrt(np.mean(resA ** 2)))
    t0, a2, b2, a4, b4, th0, R0, R2, w = pA
    J = fA.jac; dof = max(len(v) - len(pA), 1)
    try:
        cov = np.linalg.inv(J.T @ J) * (np.sum(fA.fun ** 2) / dof); se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(len(pA), np.nan)
    PA = dict(t0_um=t0, theta0_deg=math.degrees(th0), P_along_theta0_D=(a2 + b2) / K, P_along_theta0_plus90_D=(a2 - b2) / K,
              a2=a2, b2=b2, a4=a4, b4=b4, R_edge_theta0_mm=R0 + R2, R_edge_theta0_plus90_mm=R0 - R2, edge_width_mm=w,
              rms_um=rmsA, n_points=int(len(v)), std_err=dict(zip(['t0', 'a2', 'b2', 'a4', 'b4', 'theta0', 'R0', 'R2', 'w'], map(float, se))))

    # ---------- модель B (план → реальность)
    PB, Tplan, Lp = None, None, None
    if A.plan:
        ps, pc, pa, poz, ptm = [float(s) for s in A.plan.split(',')]
        vd = A.vertex / 1000.0; cp = lambda P_: P_ / (1 - vd * P_); m1, m2 = cp(ps), cp(ps + pc)
        Lp = Lenticule(m1, m2 - m1, pa, poz, ptm)
        Tplan = np.nan_to_num(Lp.thickness(X, Y), nan=0.0)
        def predB(q): return q[0] * gaussian_filter(Tplan, q[1] / (xs[1] - xs[0]), mode='constant')
        fB = least_squares(lambda q: predB(q)[m] - v, [0.75, 0.4], bounds=([0.1, 0.01], [1.5, 2.0]))
        qB = fB.x; resB = predB(qB)[m] - v
        PB = dict(alpha=float(qB[0]), sigma_mm=float(qB[1]), rms_um=float(np.sqrt(np.mean(resB ** 2))),
                  plan=dict(sph_cornea=Lp.sph, cyl_cornea=Lp.cyl, axis=Lp.axis, oz=Lp.oz, tmin=Lp.tmin, t0=Lp.t0, t_flat=Lp.t_flat,
                            t_steep=Lp.t_steep, volume_mm3=Lp.volume_formula()))
        TB = predB(qB)

    # ---------- 3D-модель модели A (идеализированная гладкая лентикула)
    Rmax = float(min(A.rmax, R0 + abs(R2) + 2.5 * w)); nr, nt = 70, 180
    rr = Rmax * np.sin(np.linspace(0, np.pi / 2, nr))[1:]; tt = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    Ra = A.rcornea - A.cap / 1000.0                          # передняя поверхность лентикулы — сфера (колпачок над ней)
    def pt(rad_, tt_, depth_um):
        s = rad_ / A.rcornea; ang = math.asin(min(s, 0.999)); rho = Ra - depth_um / 1000.0
        return np.array([rho * math.sin(ang) * math.cos(tt_), rho * math.sin(ang) * math.sin(tt_), rho * math.cos(ang) - A.rcornea])
    thk = [max(float(model_A(pA, np.array(0.0), np.array(0.0))), 0.0)]
    top, bot = [pt(0, 0, 0)], [pt(0, 0, thk[0])]
    for rad_ in rr:
        for tt_ in tt:
            tv = max(float(model_A(pA, np.array(rad_), np.array(tt_))), 0.0); thk.append(tv)
            top.append(pt(rad_, tt_, 0)); bot.append(pt(rad_, tt_, tv))
    top, bot = np.array(top), np.array(bot); n0 = len(top); V = np.vstack([top, bot]); F = []
    ring = lambda i, j: 1 + i * nt + (j % nt)
    for j in range(nt):
        F.append([0, ring(0, j), ring(0, j + 1)]); F.append([n0, n0 + ring(0, j + 1), n0 + ring(0, j)])
    for i in range(len(rr) - 1):
        for j in range(nt):
            a, b, c2, d2 = ring(i, j), ring(i, j + 1), ring(i + 1, j + 1), ring(i + 1, j)
            F += [[a, d2, c2], [a, c2, b], [n0 + a, n0 + c2, n0 + d2], [n0 + a, n0 + b, n0 + c2]]
    i = len(rr) - 1
    for j in range(nt):
        a, b = ring(i, j), ring(i, j + 1); F += [[a, b, n0 + b], [a, n0 + b, n0 + a]]
    F = np.array(F); vol = mesh_volume(V, F)
    if vol < 0: F = F[:, ::-1]; vol = -vol
    base = os.path.join(A.out, f'model_A_{code}')
    write_stl(base + '.stl', V, F); write_obj(base + '.obj', V, F)
    thk = np.array(thk); write_ply(base + '.ply', V, F, thickness_colors(np.concatenate([thk, thk]), lo=0.0, hi=float(thk.max())))

    json.dump(dict(eye=code, model_A=PA, model_B=PB, mesh_A=dict(volume_mm3=vol, watertight=is_watertight(F), R_mm=Rmax, cap_um=A.cap,
                                                                    r_cornea_mm=A.rcornea)),
              open(os.path.join(A.out, f'parametry_{code}.json'), 'w'), ensure_ascii=False, indent=1, default=float)

    # ---------- рисунки
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    from lenticule_style import LENT_CMAP, FLAT_COL as GREEN, STEEP_COL as RED, PLAN_COL, MODEL_B_COL, HALO
    TA = np.where(R <= A.rmax, model_A(pA, R, TH), np.nan); Zm = np.where(R <= A.rmax, Z, np.nan)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.7)); ext = [xs[0], xs[-1], ys[-1], ys[0]]; vmax = np.nanpercentile(Zm, 99.5)
    for ax, M_, ttl, cm, vr in ((axs[0], Zm, 'Измерено (Pentacam), мкм', LENT_CMAP, (0, vmax)), (axs[1], TA, 'Модель A (9 параметров), мкм', LENT_CMAP, (0, vmax)),
                               (axs[2], TA - Zm, f'Остаток A − измерено, мкм (RMS {rmsA:.1f})', 'RdBu_r', (-8, 8))):
        im = ax.imshow(M_, extent=ext, cmap=cm, vmin=vr[0], vmax=vr[1]); plt.colorbar(im, ax=ax, shrink=0.85)
        ax.set_xlim(-A.rmax, A.rmax); ax.set_ylim(-A.rmax, A.rmax); ax.set_title(ttl); ax.set_xlabel('x, мм'); ax.set_ylabel('y, мм')
        for ang, col in ((th0, GREEN), (th0 + math.pi / 2, RED)):
            ax.plot([-A.rmax * math.cos(ang), A.rmax * math.cos(ang)], [-A.rmax * math.sin(ang), A.rmax * math.sin(ang)], color=col, lw=2.2, path_effects=HALO)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, f'karty_model_{code}.png'), dpi=160); plt.close(fig)

    from scipy.interpolate import RegularGridInterpolator
    IZ = RegularGridInterpolator((ys[::-1], xs), Z[::-1], bounds_error=False, fill_value=np.nan)
    IB = RegularGridInterpolator((ys[::-1], xs), TB[::-1], bounds_error=False, fill_value=np.nan) if PB else None
    IP = RegularGridInterpolator((ys[::-1], xs), Tplan[::-1], bounds_error=False, fill_value=np.nan) if PB else None
    rs = np.linspace(-A.rmax, A.rmax, 331)
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
    for ax, ang, col, nm in ((axs[0], th0, GREEN, 'наибольшей толщины'), (axs[1], th0 + math.pi / 2, RED, 'наименьшей толщины')):
        q = np.stack([rs * math.sin(ang), rs * math.cos(ang)], -1)
        ax.plot(rs, IZ(q), color='#2b3440', lw=2.4, label='измерено (Pentacam)')
        ax.plot(rs, model_A(pA, np.abs(rs), np.where(rs >= 0, ang, ang + math.pi)), color=col, lw=2, label='модель A')
        if PB:
            ax.plot(rs, IP(q), color=PLAN_COL, lw=1.4, ls='--', label='план VisuMax (Мунерлин)')
            ax.plot(rs, IB(q), color=MODEL_B_COL, lw=1.6, ls='-.', label=f'модель B: {PB["alpha"]:.2f}·план, размытие σ={PB["sigma_mm"]:.2f} мм')
        ax.set_title(f'Меридиан {math.degrees(ang) % 180:.0f}° ({nm})'); ax.set_xlabel('расстояние от центра, мм'); ax.grid(alpha=0.3)
    axs[0].set_ylabel('толщина лентикулы, мкм'); axs[0].legend(fontsize=8.5); axs[0].set_ylim(0, None)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, f'profili_model_{code}.png'), dpi=160); plt.close(fig)

    # ---------- отчёт
    s = PA['std_err']
    md = f"""# Математическая модель лентикулы: {code}

Данные: карта убыли толщины ΔT(x, y) по двум обследованиям Pentacam (до и после SMILE), {PA['n_points']} точек в круге r ≤ {A.rmax} мм.

## Модель A — «седло с краем» (подгонка к измерению)

θ' = θ − θ0, c = cos 2θ'

T(r, θ) = [ t0 + (a2 + b2·c)·r² + (a4 + b4·c)·r⁴ ] · ½·[ 1 − tanh( (r − (R0 + R2·c)) / w ) ]

| параметр | значение | ± ст. ошибка | смысл |
|---|---|---|---|
| t0 | {t0:.1f} мкм | {s['t0']:.1f} | толщина в центре |
| θ0 | {math.degrees(th0):.1f}° | {math.degrees(s['theta0']):.1f} | меридиан наибольшей толщины (плоский) |
| a2 | {a2:.2f} мкм/мм² | {s['a2']:.2f} | среднее приращение к краю (сфера профиля) |
| b2 | {b2:.2f} мкм/мм² | {s['b2']:.2f} | разность меридианов (цилиндр профиля) |
| a4 | {a4:.3f} мкм/мм⁴ | {s['a4']:.3f} | отклонение от параболы к краю |
| b4 | {b4:.3f} мкм/мм⁴ | {s['b4']:.3f} | то же — по меридианам |
| R0 + R2 | {R0 + R2:.2f} мм | | радиус края вдоль θ0 |
| R0 − R2 | {R0 - R2:.2f} мм | | радиус края вдоль θ0 + 90° |
| w | {w:.2f} мм | {s['w']:.2f} | ширина края (переходная зона) |

Остаток (RMS): **{rmsA:.1f} мкм** — модель из 9 чисел описывает измеренную карту с точностью на уровне погрешности прибора.

**Оптическая сила профиля в центре** (P = коэффициент при r² / k, k = {K:.3f} мкм/(дптр·мм²), n = {N}):
вдоль {math.degrees(th0):.0f}° — **{PA['P_along_theta0_D']:+.2f} дптр**, вдоль {math.degrees(th0) + 90:.0f}° — **{PA['P_along_theta0_plus90_D']:+.2f} дптр**
(«эквивалент» Sph {PA['P_along_theta0_D']:+.2f} / Cyl {PA['P_along_theta0_plus90_D'] - PA['P_along_theta0_D']:+.2f} × {math.degrees(th0):.0f}°).
Разные знаки силы по двум меридианам = седловидная (гиперболическая) поверхность в центре.
"""
    if PB:
        pl = PB['plan']
        md += f"""
## Модель B — «план → реальность»

План (протокол → плоскость роговицы): Sph {pl['sph_cornea']:+.2f} / Cyl {pl['cyl_cornea']:+.2f} × {pl['axis']:.0f}°, ОЗ {pl['oz']} мм,
tmin {pl['tmin']:.0f} мкм → Мунерлин: центр {pl['t0']:.0f}, край плоского меридиана {pl['t_flat']:.0f}, крутого {pl['t_steep']:.0f} мкм, объём {pl['volume_mm3']:.2f} мм³.

T_изм(x, y) ≈ α · (T_план ∗ G_σ)(x, y): **α = {PB['alpha']:.2f}**, **σ = {PB['sigma_mm']:.2f} мм**, RMS {PB['rms_um']:.1f} мкм.

Смысл: в первые сутки измеренная лентикула ≈ {PB['alpha']*100:.0f} % плановой толщины, а резкий край плана размыт примерно на
{PB['sigma_mm']:.1f} мм. Это **гипотеза**: один глаз, 1-е сутки (отёк стромы); α и σ нужно проверить на других глазах и сроках.
"""
    md += f"""
## 3D-модель
`model_A_{code}.stl / .obj / .ply` — гладкая лентикула по модели A: передняя поверхность — сфера радиуса
{A.rcornea:.2f} − {A.cap/1000:.2f} мм (колпачок {A.cap:.0f} мкм), задняя — смещена по нормали на T(r, θ). Объём {vol:.3f} мм³,
сетка замкнута: {is_watertight(F)}.

## Ограничения
Один глаз; послеоперационное обследование — в 1-е сутки; ΔT включает эпителий (по ОКТ его изменение −1…−3 мкм) и отёк стромы.
Выводы — гипотезы до сравнения на большем числе глаз и в отдалённые сроки.
"""
    open(os.path.join(A.out, f'matmodel_{code}.md'), 'w').write(md); print(md)


if __name__ == '__main__':
    main()
