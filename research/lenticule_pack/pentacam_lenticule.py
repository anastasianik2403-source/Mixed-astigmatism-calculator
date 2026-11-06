"""
pentacam_lenticule.py — геометрия удалённой лентикулы по двум обследованиям Pentacam (до и после SMILE).

Вход: экспорт Pentacam «ELE» (матрицы высот FRONT [mm] и BACK related to FRONT [mm], сетка 141×141, шаг 0,1 мм)
до и после операции; по желанию — экспорт «ACD» (раздел [GENERAL DATA]: Rh, Rv, ось, пахиметрия).

Что делает:
  1) совмещает обследования по задней поверхности роговицы (после SMILE она меняется мало):
     сдвиг dx, dy, dz и поворот вокруг оси — подбором по наименьшим квадратам в зоне r ≤ 4 мм;
  2) считает толщину роговицы вдоль нормали к передней поверхности (как пахиметрия Pentacam) до и после;
  3) убыль толщины ΔT(x, y) = T_до − T_после → оценка толщины лентикулы;
  4) разбирает ΔT по меридианам (2θ-гармоника: ось наибольшей и наименьшей толщины), профили вдоль
     плоского и крутого меридианов, разложение по полиномам Цернике (OSA), эквивалент Мунерлина в центре;
  5) строит 3D-модель лентикулы: передняя поверхность = передняя поверхность роговицы «до», опущенная на
     толщину колпачка (--cap, по умолчанию 120 мкм) по нормали; задняя = передняя + ΔT; сохраняет STL / OBJ / PLY;
  6) рисует карты, профили и 3D-вид; пишет матрицу ΔT (CSV), коэффициенты Цернике, сводку (JSON) и отчёт (MD).

ФИО и другие данные пациента из файлов не читаются и не выводятся: в именах и подписях — только код глаза (--eye-code).

Запуск:
  python3 pentacam_lenticule.py --pre PRE_ELE.CSV --post POST_ELE.CSV [--pre-acd PRE_ACD.CSV --post-acd POST_ACD.CSV]
                                --eye-code P01_OS --cap 120 --out out/pentacam_P01_OS

ВАЖНО (честно): ΔT — это не «чистая» лентикула. В неё входят перестройка эпителия (Pentacam эпителий не
отделяет), реакция стромы и погрешность измерения (повторяемость пахиметрии Pentacam — порядка нескольких мкм
в центре, хуже на периферии). Выводы — гипотезы до сравнения с протоколом VisuMax и эпителиальными картами (ОКТ).
"""
import argparse, json, math, os, sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lenticule_model import Lenticule, write_stl, write_obj, write_ply, thickness_colors, mesh_volume, is_watertight

N_CORNEA = 1.376
K_MUNN = 1.0 / (2.0 * (N_CORNEA - 1.0))          # мкм на (дптр·мм²)


# ---------------------------------------------------------------- чтение
def _num(s):
    s = s.strip().replace(',', '.')
    return float(s) if s else np.nan


def read_ele(path):
    """Матрицы экспорта Pentacam ELE: {имя: (xs, ys, Z)}; разделы [PATIENT] и т.п. пропускаются."""
    L = open(path, encoding='latin-1').read().splitlines()
    out, i = {}, 0
    while i < len(L):
        row = L[i].split(';')
        if len(row) > 100 and row[0] and not (row[0][0].isdigit() or row[0][0] == '-'):
            xs = np.array([_num(v) for v in row[1:142]])
            ys, Z = [], np.full((141, 141), np.nan)
            for j in range(141):
                r = L[i + 1 + j].split(';'); ys.append(_num(r[0])); Z[j] = [_num(v) for v in r[1:142]]
            out[row[0]] = (xs, np.array(ys), Z); i += 142
        else:
            i += 1
    for k in ('FRONT [mm]', 'BACK related to FRONT [mm]'):
        if k not in out: raise SystemExit(f'{path}: нет матрицы «{k}» — нужен экспорт ELE из Pentacam')
    return out


def read_general(path):
    """Раздел [GENERAL DATA] экспорта ACD: только параметры роговицы (без данных пациента)."""
    if not path: return {}
    keep = ('Cornea Front Rh', 'Cornea Front Rv', 'Cornea Front Axis', 'Cornea Front Astig', 'Cornea Front Exz',
            'Pachy Apex', 'Pachy Min', 'K Max (Front)', 'Pupil Dia')
    g, on = {}, False
    for line in open(path, encoding='latin-1').read().splitlines():
        if line.startswith('['): on = line.startswith('[GENERAL DATA]') or line.startswith('[PUPIL]'); continue
        if on and ';' in line:
            k, v = line.split(';')[:2]
            if k in keep:
                try: g[k] = _num(v)
                except ValueError: pass
    return g


# ---------------------------------------------------------------- геометрия
def interp(xs, ys, Z):
    return RegularGridInterpolator((ys[::-1], xs), Z[::-1], bounds_error=False, fill_value=np.nan)


def warp(I, p, X, Y, with_dz=True):
    dx, dy, dz, th = p; c, s = math.cos(th), math.sin(th)
    xq = c * (X - dx) + s * (Y - dy); yq = -s * (X - dx) + c * (Y - dy)
    return I(np.stack([yq, xq], -1)) + (dz if with_dz else 0.0)


def register(xs, ys, B0, B1, r_max=4.0):
    X, Y = np.meshgrid(xs, ys); m = (np.hypot(X, Y) <= r_max) & np.isfinite(B0); I1 = interp(xs, ys, B1)
    def cost(p):
        d = warp(I1, p, X, Y)[m] - B0[m]; d = d[np.isfinite(d)]; return float(np.mean(d ** 2))
    r0 = math.sqrt(cost(np.zeros(4))) * 1000
    res = minimize(cost, np.zeros(4), method='Nelder-Mead', options=dict(xatol=1e-5, fatol=1e-14, maxiter=6000))
    return res.x, r0, math.sqrt(cost(res.x)) * 1000


def normals(xs, ys, F):
    gy, gx = np.gradient(F, ys[1] - ys[0], xs[1] - xs[0])   # dF/dy, dF/dx (z — вглубь)
    d = np.stack([-gx, -gy, np.ones_like(F)], -1)           # к центру кривизны: для сферы F ≈ r²/2R это (−x/R, −y/R, 1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)    # нормаль к поверхности z=F, направлена вглубь


def normal_thickness(xs, ys, F, B):
    X, Y = np.meshgrid(xs, ys); IB = interp(xs, ys, B); d = normals(xs, ys, F); t = B - F
    for _ in range(8):
        q = np.stack([Y + d[..., 1] * t, X + d[..., 0] * t], -1)
        t = t + (IB(q) - (F + d[..., 2] * t)) / d[..., 2] * 0.9
    return t


# ---------------------------------------------------------------- Цернике (OSA/ANSI, нормировка RMS)
def zernike_list(nmax):
    return [(n, m) for n in range(nmax + 1) for m in range(-n, n + 1, 2)]


def zernike(n, m, rho, th):
    R = np.zeros_like(rho)
    for k in range((n - abs(m)) // 2 + 1):
        R += (-1) ** k * math.factorial(n - k) / (math.factorial(k) * math.factorial((n + abs(m)) // 2 - k)
                                                  * math.factorial((n - abs(m)) // 2 - k)) * rho ** (n - 2 * k)
    norm = math.sqrt(2 * (n + 1)) if m else math.sqrt(n + 1)
    return norm * R * (np.cos(m * th) if m >= 0 else np.sin(-m * th))


def zernike_fit(x, y, v, Rz, nmax):
    rho, th = np.hypot(x, y) / Rz, np.arctan2(y, x)
    terms = zernike_list(nmax)
    A = np.column_stack([zernike(n, m, rho, th) for n, m in terms])
    c, *_ = np.linalg.lstsq(A, v, rcond=None)
    return terms, c, float(np.sqrt(np.mean((A @ c - v) ** 2)))


def zernike_eval(terms, c, Rz, x, y):
    rho, th = np.hypot(x, y) / Rz, np.arctan2(y, x)
    return sum(ci * zernike(n, m, rho, th) for (n, m), ci in zip(terms, c))


# ---------------------------------------------------------------- основной расчёт
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--pre', required=True); ap.add_argument('--post', required=True)
    ap.add_argument('--pre-acd'); ap.add_argument('--post-acd')
    ap.add_argument('--eye-code', default='EYE'); ap.add_argument('--cap', type=float, default=120.0, help='толщина колпачка, мкм')
    ap.add_argument('--r-zern', type=float, default=3.5, help='радиус разложения по Цернике, мм')
    ap.add_argument('--zern-order', type=int, default=8); ap.add_argument('--out', default='out/pentacam_lenticule')
    ap.add_argument('--exag', type=float, default=10.0, help='увеличение толщины на 3D-виде и в профилях-сечениях')
    ap.add_argument('--plan', default=None, help='план из протокола VisuMax в очковой плоскости, минус-цилиндр: "Sph,Cyl,Ось,ОЗ,tmin", напр. "+1.75,-5.00,10,6.7,20"')
    ap.add_argument('--vertex', type=float, default=12.0, help='вертексное расстояние для пересчёта плана в плоскость роговицы, мм')
    ap.add_argument('--days-after', default=None, help='срок послеоперационного обследования (для отчёта), напр. "1 сутки"')
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True); code = A.eye_code
    pre, post = read_ele(A.pre), read_ele(A.post)
    g0, g1 = read_general(A.pre_acd), read_general(A.post_acd)
    xs, ys, F0 = pre['FRONT [mm]']; B0 = pre['BACK related to FRONT [mm]'][2]
    F1, B1 = post['FRONT [mm]'][2], post['BACK related to FRONT [mm]'][2]
    X, Y = np.meshgrid(xs, ys); R = np.hypot(X, Y)

    p, rms0, rms1 = register(xs, ys, B0, B1)
    T0 = normal_thickness(xs, ys, F0, B0)
    T1n = normal_thickness(xs, ys, F1, B1)
    T1 = warp(interp(xs, ys, T1n), p, X, Y, with_dz=False)
    dT = (T0 - T1) * 1000.0                                   # мкм

    # зона надёжных данных: радиус, до которого кольцо покрыто данными ≥ 97 %
    th = np.radians(np.arange(0, 360, 2)); I = interp(xs, ys, dT); r_ok = 0.0
    for r in np.arange(0.5, 6.01, 0.05):
        v = I(np.stack([r * np.sin(th), r * np.cos(th)], -1))
        if np.isfinite(v).mean() < 0.97: break
        r_ok = r
    # меридианы: 2θ-гармоника ΔT
    harm = []
    for r in np.arange(0.5, r_ok + 1e-9, 0.25):
        v = I(np.stack([r * np.sin(th), r * np.cos(th)], -1)); ok = np.isfinite(v)
        M = np.column_stack([np.ones(ok.sum()), np.cos(2 * th[ok]), np.sin(2 * th[ok]), np.cos(th[ok]), np.sin(th[ok])])
        c, *_ = np.linalg.lstsq(M, v[ok], rcond=None)
        amp = math.hypot(c[1], c[2]); ph = math.degrees(0.5 * math.atan2(c[2], c[1])) % 180
        harm.append(dict(r=round(float(r), 2), mean=float(c[0]), axis_max=ph, max=float(c[0] + amp), min=float(c[0] - amp),
                         decentr_um=float(math.hypot(c[3], c[4]))))
    outer = [h for h in harm if h['r'] >= 2.0]
    ax_thick = float(np.degrees(np.angle(np.mean([np.exp(2j * np.radians(h['axis_max'])) * (h['max'] - h['min']) for h in outer])) / 2) % 180)
    ax_flat_k = g0.get('Cornea Front Axis', np.nan)

    # профили вдоль меридиана наибольшей толщины и перпендикулярного
    rs = np.round(np.arange(-r_ok, r_ok + 1e-9, 0.1), 2)
    def prof(ang, Z):
        a = math.radians(ang); return interp(xs, ys, Z)(np.stack([rs * math.sin(a), rs * math.cos(a)], -1))
    m_thick, m_thin = ax_thick, (ax_thick + 90) % 180
    P = {m_thick: prof(m_thick, dT), m_thin: prof(m_thin, dT)}
    PL, plan_rows, Lp = {}, [], None
    if A.plan:                                                # плановая лентикула (Мунерлин) в плоскости роговицы
        ps, pc, pa, poz, ptm = [float(v) for v in A.plan.split(',')]
        vd = A.vertex / 1000.0; cp = lambda P_: P_ / (1 - vd * P_)
        m1, m2 = cp(ps), cp(ps + pc)
        Lp = Lenticule(m1, m2 - m1, pa, poz, ptm)
        for ang in (m_thick, m_thin):
            a = math.radians(ang); PL[ang] = np.nan_to_num(Lp.thickness(rs * math.cos(a), rs * math.sin(a)), nan=0.0)
        for ang, lab in ((pa, 'плоский (ось плана)'), (pa + 90, 'крутой')):
            a = math.radians(ang)
            for rr_ in (0.0, 1.5, 2.5, Lp.R - 0.05):
                x_, y_ = rr_ * math.cos(a), rr_ * math.sin(a)
                plan_v = float(Lp.thickness(x_, y_)); meas = float(I(np.array([[y_, x_]]))[0])
                plan_rows.append((ang % 180, lab, rr_, plan_v, meas))

    # Цернике в зоне r ≤ Rz
    Rz = min(A.r_zern, r_ok); msk = (R <= Rz) & np.isfinite(dT)
    terms, zc, zres = zernike_fit(X[msk], Y[msk], dT[msk], Rz, A.zern_order)
    # эквивалент Мунерлина: квадратичная подгонка в центре (r ≤ 2 мм)
    mc = (R <= 2.0) & np.isfinite(dT); a_ = math.radians(ax_thick)
    u = X[mc] * math.cos(a_) + Y[mc] * math.sin(a_); w = -X[mc] * math.sin(a_) + Y[mc] * math.cos(a_)
    M = np.column_stack([np.ones(mc.sum()), u, w, u * u, w * w, u * w]); qc, *_ = np.linalg.lstsq(M, dT[mc], rcond=None)
    P_thick, P_thin = qc[3] / K_MUNN, qc[4] / K_MUNN          # дптр «вдоль» меридиана наибольшей / наименьшей толщины

    # ---------------- 3D-модель (сглаженная Цернике, полярная сетка)
    IF0 = interp(xs, ys, F0); Dn = normals(xs, ys, F0); IDn = [interp(xs, ys, Dn[..., k]) for k in range(3)]
    nth, nr = 180, 50; tt = np.linspace(0, 2 * np.pi, nth, endpoint=False); rr = Rz * np.sin(np.linspace(0, np.pi / 2, nr))[1:]
    def surf(depth_fn):
        pts = [np.zeros(3)]
        def pt(x, y, extra):
            q = np.array([[y, x]]); z = IF0(q)[0]; d = np.array([IDn[k](q)[0] for k in range(3)])
            return np.array([x, y, z]) + d * (A.cap / 1000.0 + extra / 1000.0)
        pts[0] = pt(0.0, 0.0, depth_fn(0.0, 0.0))
        for r in rr:
            for t in tt:
                x, y = r * math.cos(t), r * math.sin(t); pts.append(pt(x, y, depth_fn(x, y)))
        return np.array(pts)
    tz = lambda x, y: float(max(zernike_eval(terms, zc, Rz, np.array([x]), np.array([y]))[0], 0.0))
    top = surf(lambda x, y: 0.0); bot = surf(tz)
    thk_v = np.concatenate([[tz(0, 0)], [tz(r * math.cos(t), r * math.sin(t)) for r in rr for t in tt]])
    nt = len(top); V = np.vstack([top, bot]); Fc = []
    ring = lambda i, j: 1 + i * nth + (j % nth)
    for j in range(nth):
        Fc.append([0, ring(0, j + 1), ring(0, j)]); Fc.append([nt, nt + ring(0, j), nt + ring(0, j + 1)])
    for i in range(len(rr) - 1):
        for j in range(nth):
            a, b, c2, d2 = ring(i, j), ring(i, j + 1), ring(i + 1, j + 1), ring(i + 1, j)
            Fc += [[a, b, c2], [a, c2, d2], [nt + a, nt + c2, nt + b], [nt + a, nt + d2, nt + c2]]
    i = len(rr) - 1
    for j in range(nth):                                       # боковая стенка лентикулы
        a, b = ring(i, j), ring(i, j + 1); Fc += [[a, b, nt + b], [a, nt + b, nt + a]]
    Fc = np.array(Fc)
    Vz = V.copy(); Vz[:, 2] = -Vz[:, 2]                       # z вверх (глубина в Pentacam — вниз)
    Fz = Fc[:, ::-1]
    base = os.path.join(A.out, f'lentikula_{code}')
    write_stl(base + '.stl', Vz, Fz); write_obj(base + '.obj', Vz, Fz)
    write_ply(base + '.ply', Vz, Fz, thickness_colors(np.concatenate([thk_v, thk_v]), lo=float(np.nanmin(thk_v)), hi=float(np.nanmax(thk_v))))
    vol = mesh_volume(Vz, Fz)

    # ---------------- таблицы
    with open(os.path.join(A.out, f'ubyl_tolshchiny_{code}_mkm.csv'), 'w') as f:
        f.write('y\\x;' + ';'.join(f'{x:.1f}' for x in xs) + '\n')
        for j, y in enumerate(ys):
            f.write(f'{y:.1f};' + ';'.join('' if not np.isfinite(v) else f'{v:.1f}' for v in dT[j]) + '\n')
    with open(os.path.join(A.out, f'cernike_{code}.csv'), 'w') as f:
        f.write(f'# ΔT(ρ,θ) = Σ c·Z(n,m), OSA/ANSI, нормировка RMS, R = {Rz:.2f} мм, мкм; θ от оси x против часовой\nn;m;c_mkm\n')
        for (n, m), ci in zip(terms, zc): f.write(f'{n};{m};{ci:.3f}\n')
    with open(os.path.join(A.out, f'profili_{code}.csv'), 'w') as f:
        f.write(f'r_mm;dT_meridian_{m_thick:.0f}deg_mkm;dT_meridian_{m_thin:.0f}deg_mkm\n')
        for r, a1, a2 in zip(rs, P[m_thick], P[m_thin]): f.write(f'{r:.1f};{a1:.1f};{a2:.1f}\n')

    def K(rmm): return 337.5 / rmm
    kinfo = {}
    if g0 and g1 and all(k in g for g in (g0, g1) for k in ('Cornea Front Rh', 'Cornea Front Rv')):
        kinfo = dict(pre_Rh=g0['Cornea Front Rh'], pre_Rv=g0['Cornea Front Rv'], post_Rh=g1['Cornea Front Rh'], post_Rv=g1['Cornea Front Rv'],
                     dK_h=K(g1['Cornea Front Rh']) - K(g0['Cornea Front Rh']), dK_v=K(g1['Cornea Front Rv']) - K(g0['Cornea Front Rv']),
                     pre_astig=g0.get('Cornea Front Astig'), pre_axis=g0.get('Cornea Front Axis'),
                     post_astig=g1.get('Cornea Front Astig'), post_axis=g1.get('Cornea Front Axis'),
                     pachy_apex_pre=g0.get('Pachy Apex'), pachy_apex_post=g1.get('Pachy Apex'))
    summ = dict(eye=code, registration=dict(dx_um=p[0] * 1000, dy_um=p[1] * 1000, dz_um=p[2] * 1000, rotation_deg=math.degrees(p[3]),
                                             back_rms_before_um=rms0, back_rms_after_um=rms1),
                r_reliable_mm=r_ok, centre_um=float(dT[70, 70]), axis_thickest_deg=ax_thick, front_flat_axis_pre_deg=ax_flat_k,
                harmonics=harm, zernike=dict(R_mm=Rz, order=A.zern_order, residual_rms_um=zres),
                munnerlyn_equiv_centre=dict(P_along_thickest_D=P_thick, P_along_thinnest_D=P_thin,
                                            note='квадратичная подгонка ΔT в r ≤ 2 мм; ΔT = t0 + k·P·r², k = 1/(2(n−1))'),
                mesh=dict(cap_um=A.cap, volume_mm3=vol, watertight=is_watertight(Fz), vertices=len(Vz), faces=len(Fz)), keratometry=kinfo)
    json.dump(summ, open(os.path.join(A.out, f'svodka_{code}.json'), 'w'), ensure_ascii=False, indent=1, default=float)

    # ---------------- рисунки
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    GREEN, RED = '#2e9e5b', '#d64545'
    def mer_lines(ax, r):
        for ang, col in ((m_thick, GREEN), (m_thin, RED)):
            a = math.radians(ang); ax.plot([-r * math.cos(a), r * math.cos(a)], [-r * math.sin(a), r * math.sin(a)], color=col, lw=1.6)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.8)); ext = [xs[0], xs[-1], ys[-1], ys[0]]
    for ax, Z, ttl, cm, vr in ((axs[0], T0 * 1000, 'Толщина роговицы ДО, мкм', 'viridis', None),
                               (axs[1], T1 * 1000, 'Толщина роговицы ПОСЛЕ (совмещено), мкм', 'viridis', None),
                               (axs[2], dT, 'Убыль толщины = лентикула (оценка), мкм', 'magma_r', (0, np.nanpercentile(dT[R <= r_ok], 99)))):
        Zm = np.where(R <= r_ok, Z, np.nan)
        im = ax.imshow(Zm, extent=ext, origin='upper', cmap=cm, vmin=None if vr is None else vr[0], vmax=None if vr is None else vr[1])
        cs = ax.contour(X, Y, Zm, levels=10, colors='k', linewidths=0.4); ax.clabel(cs, fontsize=7, fmt='%.0f')
        mer_lines(ax, r_ok); ax.set_title(ttl); ax.set_xlabel('x, мм'); ax.set_ylabel('y, мм'); ax.set_aspect('equal')
        ax.set_xlim(-r_ok - 0.2, r_ok + 0.2); ax.set_ylim(-r_ok - 0.2, r_ok + 0.2); plt.colorbar(im, ax=ax, shrink=0.85)
    fig.suptitle(f'{code}: зелёная линия — меридиан наибольшей толщины лентикулы ({m_thick:.0f}°), красная — наименьшей ({m_thin:.0f}°)', fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, f'karty_{code}.png'), dpi=160); plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
    ax = axs[0]
    ax.plot(rs, P[m_thick], color=GREEN, lw=2.2, label=f'меридиан {m_thick:.0f}° (плоский до операции: {ax_flat_k:.1f}°)')
    ax.plot(rs, P[m_thin], color=RED, lw=2.2, label=f'меридиан {m_thin:.0f}° (крутой до операции)')
    for ang, colr in ((m_thick, GREEN), (m_thin, RED)):
        if ang in PL: ax.plot(rs, PL[ang], color=colr, lw=1.6, ls='--', label=f'план VisuMax (Мунерлин), {ang:.0f}°')
    ax.axhline(dT[70, 70], color='gray', lw=0.8, ls=':'); ax.set_xlabel('расстояние от центра, мм'); ax.set_ylabel('толщина лентикулы (оценка), мкм')
    ax.set_title('Профили толщины по меридианам'); ax.grid(alpha=0.3); ax.legend(fontsize=8.5); ax.set_ylim(0, None)
    ax = axs[1]                                               # сечения в реальной геометрии: колпачок над лентикулой, кривизна сохранена
    for ang, col, off in ((m_thick, GREEN, 0.0), (m_thin, RED, -1.25)):
        a = math.radians(ang); q = np.stack([rs * math.sin(a), rs * math.cos(a)], -1)
        zf = IF0(q); t = np.nan_to_num(interp(xs, ys, dT)(q), nan=0.0).clip(min=0)
        top_ = -(zf + A.cap / 1000.0) + off; bot_ = top_ - t * A.exag / 1000.0
        ax.plot(rs, -zf + off, color='#7a8794', lw=1.0); ax.fill_between(rs, -zf + off, top_, color='#d9e2ec', lw=0)
        ax.fill_between(rs, top_, bot_, color=col, alpha=0.85, lw=0)
        ax.text(0, off + 0.1, f'меридиан {ang:.0f}°', color=col, fontsize=9, fontweight='bold', ha='center')
    ax.set_title(f'Сечения: колпачок {A.cap:.0f} мкм (серый) и лентикула (толщина ×{A.exag:.0f})', fontsize=10)
    ax.set_xlabel('мм'); ax.set_yticks([]); ax.set_aspect(1.2); ax.set_ylim(-2.35, 0.45)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, f'profili_{code}.png'), dpi=160); plt.close(fig)

    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    fig = plt.figure(figsize=(9, 6.5)); ax = fig.add_subplot(111, projection='3d')
    pr, pt_ = np.meshgrid(np.linspace(0, Rz, 60), np.linspace(0, 2 * np.pi, 181))   # полярная сетка — ровный край
    GX, GY = pr * np.cos(pt_), pr * np.sin(pt_); Tz = np.clip(zernike_eval(terms, zc, Rz, GX, GY), 0, None)
    col = plt.cm.magma_r((Tz - Tz.min()) / (Tz.max() - Tz.min() + 1e-9))
    ax.plot_surface(GX, GY, Tz, facecolors=col, rstride=1, cstride=1, linewidth=0, antialiased=True, shade=True)
    for ang, c3 in ((m_thick, GREEN), (m_thin, RED)):
        a = math.radians(ang); r3 = np.linspace(-Rz, Rz, 141); x3, y3 = r3 * math.cos(a), r3 * math.sin(a)
        ax.plot(x3, y3, np.clip(zernike_eval(terms, zc, Rz, x3, y3), 0, None) + 0.6, color=c3, lw=2.6)
    ax.set_xlabel('x, мм'); ax.set_ylabel('y, мм'); ax.set_zlabel('толщина, мкм'); ax.view_init(28, -58)
    ax.set_box_aspect((1, 1, 0.45))
    ax.set_title(f'{code}: рельеф толщины лентикулы (зелёный — меридиан {m_thick:.0f}°, красный — {m_thin:.0f}°)', fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, f'3d_{code}.png'), dpi=160); plt.close(fig)

    # ---------------- отчёт
    hh = {round(h['r'], 2): h for h in harm}
    rows = '\n'.join(f"| {h['r']:.2f} | {h['mean']:.0f} | {h['axis_max']:.0f}° → {h['max']:.0f} | {(h['axis_max'] + 90) % 180:.0f}° → {h['min']:.0f} |" for h in harm if abs(h['r'] * 4 - round(h['r'] * 4)) < 1e-6)
    kt = ''
    if kinfo:
        kt = (f"\n**Кератометрия передней поверхности (Pentacam, n = 1,3375):** Rh {kinfo['pre_Rh']:.2f} → {kinfo['post_Rh']:.2f} мм "
              f"(ΔK {kinfo['dK_h']:+.2f} дптр), Rv {kinfo['pre_Rv']:.2f} → {kinfo['post_Rv']:.2f} мм (ΔK {kinfo['dK_v']:+.2f} дптр); "
              f"астигматизм {kinfo['pre_astig']} дптр × {kinfo['pre_axis']}° → {kinfo['post_astig']} дптр × {kinfo['post_axis']}°; "
              f"пахиметрия в вершине {kinfo['pachy_apex_pre']:.0f} → {kinfo['pachy_apex_post']:.0f} мкм.\n")
    plan_md = ''
    if Lp is not None:
        trs = '\n'.join(f'| {a_:.0f}° ({l_}) | {r_:.2f} | {pv:.0f} | {mv:.0f} | {mv / pv:.2f} |' for a_, l_, r_, pv, mv in plan_rows if pv > 0)
        plan_md = (f"\n**План (протокол VisuMax → плоскость роговицы, вертекс {A.vertex:.0f} мм):** Sph {Lp.sph:+.2f} / Cyl {Lp.cyl:+.2f} × {Lp.axis:.0f}°, "
                   f"ОЗ {Lp.oz} мм, tmin {Lp.tmin:.0f} мкм → по Мунерлину центр {Lp.t0:.0f}, край плоского меридиана {Lp.t_flat:.0f}, "
                   f"край крутого {Lp.t_steep:.0f} мкм, объём {Lp.volume_formula():.2f} мм³ (измерено {vol:.2f} мм³ в Ø {2*Rz:.1f} мм).\n\n"
                   f"| меридиан | r, мм | план, мкм | измерено ΔT, мкм | измерено / план |\n|---|---|---|---|---|\n{trs}\n")
    md = f"""# Лентикула по данным Pentacam: {code}

Метод: два обследования Pentacam (до и после SMILE) совмещены по задней поверхности роговицы; толщина считается по нормали
к передней поверхности; убыль толщины ΔT = T(до) − T(после) — оценка толщины удалённой лентикулы.

**Совмещение:** сдвиг {p[0]*1000:.0f} / {p[1]*1000:.0f} мкм (x / y), поворот {math.degrees(p[3]):+.2f}°; расхождение задних
поверхностей {rms0:.1f} → {rms1:.1f} мкм (RMS, r ≤ 4 мм). Надёжные данные — до r = {r_ok:.2f} мм (Ø {2*r_ok:.1f} мм).
{kt}
{('**Срок послеоперационного обследования:** ' + A.days_after + '.' + chr(10)) if A.days_after else ''}**ΔT в центре:** {dT[70,70]:.0f} мкм. **Меридиан наибольшей толщины:** {m_thick:.0f}° (плоский меридиан роговицы до операции —
{ax_flat_k}°), наименьшей — {m_thin:.0f}°.

| r, мм | среднее, мкм | максимум (меридиан → мкм) | минимум (меридиан → мкм) |
|---|---|---|---|
{rows}

**Эквивалент Мунерлина в центре (r ≤ 2 мм):** вдоль {m_thick:.0f}° {P_thick:+.2f} дптр, вдоль {m_thin:.0f}° {P_thin:+.2f} дптр
(k = {K_MUNN:.3f} мкм/(дптр·мм²)). Это эффективная «оптическая сила» профиля ΔT, а не план операции.

{plan_md}
**Цернике:** R = {Rz:.2f} мм, порядок {A.zern_order}, остаточная RMS {zres:.1f} мкм — коэффициенты в `cernike_{code}.csv`.

**3D-модель:** `lentikula_{code}.stl / .obj / .ply` — передняя поверхность = передняя поверхность роговицы «до», опущенная
по нормали на колпачок {A.cap:.0f} мкм (допущение — подставьте значение из протокола), задняя = передняя + ΔT (сглажено Цернике);
Ø {2*Rz:.1f} мм, объём {vol:.3f} мм³, сетка замкнута: {is_watertight(Fz)}.

## Что это НЕ доказывает (честно)
* ΔT включает перестройку эпителия (Pentacam эпителий не отделяет), реакцию стромы и погрешность измерения; на периферии
  данные хуже. Это оценка формы лентикулы, а не её точная копия.
* Один глаз; срок после операции — по датам обследований. Выводы — гипотезы до сравнения с протоколом VisuMax
  (Sph, Cyl, ось, ОЗ, переходная зона, колпачок, минимальная толщина) и эпителиальными картами ОКТ.
"""
    open(os.path.join(A.out, f'otchet_{code}.md'), 'w').write(md)
    print(md)


if __name__ == '__main__':
    main()
