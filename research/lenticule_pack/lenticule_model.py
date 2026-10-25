"""
lenticule_model.py — геометрия лентикулы SMILE (торическое приближение Мунерлина).

Что делает:
  * считает толщину лентикулы t(x, y) в оптической зоне по Sph / Cyl / оси / ОЗ / tmin;
  * строит ЗАМКНУТУЮ (водонепроницаемую) треугольную сетку: передняя поверхность — часть сферы
    радиусом DOME_R (как у роговицы), задняя = передняя минус толщина (с множителем exag для наглядности);
  * сохраняет STL / OBJ / PLY (с цветом по толщине) и CSV-матрицу толщины (мкм) — всё это открывается
    в Blender, MeshLab, ANSYS SpaceClaim, 3D-принтерных программах;
  * самопроверка: формула объёма = численный интеграл = объём сетки.

Запуск:
    python3 lenticule_model.py --sph 1.0 --cyl -4.0 --axis 0 --oz 6.7 --tmin 20 --exag 8 --out out
    python3 lenticule_model.py --selftest

Только numpy. Физика модели (честно): параболическое приближение, переходная зона и «регресс» не учитываются.
Основа: Munnerlyn C.R., Koons S.J., Marshall J. J Cataract Refract Surg 1988;14(1):46-52. Торическое
обобщение и перенос на лентикулу SMILE — стандартное приближение, но в самой статье его нет.
"""
from __future__ import annotations
import argparse, os, struct
from dataclasses import dataclass
import numpy as np

N_CORNEA = 1.376


@dataclass
class Lenticule:
    sph: float = 1.0        # сфера, дптр
    cyl: float = -4.0       # цилиндр, дптр (минусовая запись)
    axis: float = 0.0       # ось цилиндра, градусы
    oz: float = 6.7         # оптическая зона (диаметр), мм
    tmin: float = 20.0      # минимальная толщина на краю, мкм
    n: float = N_CORNEA     # показатель преломления роговицы
    dome_r: float = 7.8     # радиус передней поверхности для 3D, мм (типичное значение)

    # --- производные величины ---------------------------------------------------------------
    @property
    def R(self) -> float:                       # радиус ОЗ, мм
        return self.oz / 2

    @property
    def k(self) -> float:                       # мкм на (дптр·мм²)
        return 1.0 / (2.0 * (self.n - 1.0))

    @property
    def kR2(self) -> float:                     # мкм на 1 дптр на краю ОЗ (≈14,9 при ОЗ 6,7)
        return self.k * self.R ** 2

    @property
    def p_min(self) -> float:
        return min(self.sph, self.sph + self.cyl)

    @property
    def t0(self) -> float:                      # толщина в центре, мкм
        return self.tmin + max(-self.p_min, 0.0) * self.kR2

    @property
    def t_flat(self) -> float:                  # край по плоскому меридиану (вдоль оси), мкм
        return self.t0 + self.sph * self.kR2

    @property
    def t_steep(self) -> float:                 # край по крутому меридиану (поперёк оси), мкм
        return self.t0 + (self.sph + self.cyl) * self.kR2

    def thickness(self, x, y):
        """Толщина, мкм, в точке (x, y) мм от центра. Вне ОЗ — NaN."""
        a = np.radians(self.axis)
        perp = -np.asarray(x) * np.sin(a) + np.asarray(y) * np.cos(a)
        t = self.t0 + (self.sph * (np.asarray(x) ** 2 + np.asarray(y) ** 2) + self.cyl * perp ** 2) * self.k
        return np.where(np.asarray(x) ** 2 + np.asarray(y) ** 2 <= self.R ** 2 * (1 + 1e-12), t, np.nan)

    def volume_formula(self) -> float:          # мм³
        return np.pi * self.R ** 2 * (self.t0 + self.kR2 * (self.sph / 2 + self.cyl / 4)) / 1000.0

    def volume_numeric(self, n: int = 1601) -> float:
        g = np.linspace(-self.R, self.R, n)
        X, Y = np.meshgrid(g, g)
        return float(np.nansum(self.thickness(X, Y)) * (g[1] - g[0]) ** 2 / 1000.0)

    def summary(self) -> str:
        return (f"Sph {self.sph:+.2f}  Cyl {self.cyl:+.2f}  ось {self.axis:.0f}°  ОЗ {self.oz} мм  tmin {self.tmin:.0f} мкм\n"
                f"  центр {self.t0:.1f} мкм | край (плоский меридиан) {self.t_flat:.1f} | край (крутой меридиан) {self.t_steep:.1f}\n"
                f"  объём {self.volume_formula():.3f} мм³ (формула), {self.volume_numeric():.3f} мм³ (численно)")


# ====================================================================================================
def dome_z(L: Lenticule, r):
    """Передняя поверхность: сфера радиуса dome_r, z=0 в центре, вниз — в глубину."""
    return np.sqrt(L.dome_r ** 2 - np.asarray(r) ** 2) - L.dome_r


def _ring(x, y, z):
    return np.column_stack([x, y, np.broadcast_to(z, np.shape(x))])


def lenticule_mesh(L: Lenticule, nth: int = 181, nr: int = 64, nwall: int = 4, exag: float = 1.0):
    """Замкнутая сетка без дублирующихся вершин.
    Возвращает V (N,3) мм, F (M,3) int (нормали наружу), thk (N,) мкм — толщина в вершине (для цвета)."""
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    # радиальные кольца: плотнее к краю, где важна форма стенки
    rr = L.R * np.sin(np.linspace(0, np.pi / 2, nr)) ** 1.0
    rr = rr[1:]                                                  # без центра: центр — отдельная вершина
    rr[-1] = L.R
    verts, thk = [], []
    # верх: центр + кольца
    verts.append([0.0, 0.0, float(dome_z(L, 0.0))]); thk.append(float(L.thickness(0.0, 0.0)))
    for r in rr:
        x, y = r * np.cos(th), r * np.sin(th)
        verts += list(_ring(x, y, dome_z(L, r))); thk += list(L.thickness(x, y))
    n_top = len(verts)
    idx_top_ring = lambda i, j: 1 + i * nth + (j % nth)          # i=0..len(rr)-1
    # стенка: промежуточные кольца между верхним и нижним краем
    xe, ye = L.R * np.cos(th), L.R * np.sin(th)
    ze_top = float(dome_z(L, L.R)); te = L.thickness(xe, ye)
    wall_first = len(verts)
    for w in range(1, nwall + 1):
        f = w / (nwall + 1)
        verts += list(_ring(xe, ye, ze_top - exag * te * f / 1000.0)); thk += list(te)
    wall_idx = lambda w, j: wall_first + (w - 1) * nth + (j % nth)
    # низ: кольца от края к центру + центр
    bot_first = len(verts)
    for i in range(len(rr) - 1, -1, -1):
        r = rr[i]
        x, y = r * np.cos(th), r * np.sin(th); t = L.thickness(x, y)
        verts += list(_ring(x, y, dome_z(L, r) - exag * t / 1000.0)); thk += list(t)
    bot_ring = lambda i, j: bot_first + (len(rr) - 1 - i) * nth + (j % nth)
    bot_center = len(verts)
    verts.append([0.0, 0.0, float(dome_z(L, 0.0)) - exag * float(L.thickness(0.0, 0.0)) / 1000.0]); thk.append(float(L.thickness(0.0, 0.0)))
    F = []
    # верх (нормаль вверх): веер от центра + полосы
    for j in range(nth):
        F.append([0, idx_top_ring(0, j), idx_top_ring(0, j + 1)])
    for i in range(len(rr) - 1):
        for j in range(nth):
            a, b, c, d = idx_top_ring(i, j), idx_top_ring(i, j + 1), idx_top_ring(i + 1, j + 1), idx_top_ring(i + 1, j)
            F += [[a, d, c], [a, c, b]]
    # цепочка колец края: верх (i=len(rr)-1) → стенка → низ (i=len(rr)-1)
    chain = [lambda j: idx_top_ring(len(rr) - 1, j)] + [(lambda w: (lambda j: wall_idx(w, j)))(w) for w in range(1, nwall + 1)] + [lambda j: bot_ring(len(rr) - 1, j)]
    for c0, c1 in zip(chain[:-1], chain[1:]):
        for j in range(nth):
            a, b, c, d = c0(j), c0(j + 1), c1(j + 1), c1(j)
            F += [[a, c, b], [a, d, c]]
    # низ (нормаль вниз)
    for i in range(len(rr) - 1, 0, -1):
        for j in range(nth):
            a, b, c, d = bot_ring(i, j), bot_ring(i, j + 1), bot_ring(i - 1, j + 1), bot_ring(i - 1, j)
            F += [[a, c, b], [a, d, c]]
    for j in range(nth):
        F.append([bot_center, bot_ring(0, j + 1), bot_ring(0, j)])
    V = np.asarray(verts, float); F = np.asarray(F, int); thk = np.asarray(thk, float)
    return V, F, thk


def mesh_volume(V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return float(np.sum(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6.0)


def is_watertight(F):
    e = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return bool(np.all(cnt == 2))


# ---------------------------------------------------------------------------- экспорт ---------------
def write_stl(path, V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-30)
    with open(path, 'wb') as f:
        f.write(b'lenticule (mm)'.ljust(80, b' ')); f.write(struct.pack('<I', len(F)))
        for tri, nn in zip(F, n):
            f.write(struct.pack('<12fH', *nn, *V[tri[0]], *V[tri[1]], *V[tri[2]], 0))


def write_obj(path, V, F):
    with open(path, 'w') as f:
        f.write('# lenticule, mm\n')
        for v in V: f.write(f'v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
        for t in F + 1: f.write(f'f {t[0]} {t[1]} {t[2]}\n')


def thickness_colors(thk, lo=10.0, hi=90.0):
    """Цветовая шкала как на рисунках (светло-голубой → тёмно-синий). Возвращает uint8 (N,3)."""
    stops = np.array([[205, 226, 251], [158, 197, 244], [109, 167, 236], [57, 135, 229], [37, 106, 191], [28, 92, 171], [24, 79, 149]], float)
    u = np.clip((thk - lo) / (hi - lo), 0, 1) * (len(stops) - 1)
    i = np.minimum(u.astype(int), len(stops) - 2); f = (u - i)[:, None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).round().astype(np.uint8)


def write_ply(path, V, F, rgb):
    with open(path, 'w') as f:
        f.write(f'ply\nformat ascii 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\n'
                f'property uchar red\nproperty uchar green\nproperty uchar blue\nelement face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n')
        for v, c in zip(V, rgb): f.write(f'{v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {c[0]} {c[1]} {c[2]}\n')
        for t in F: f.write(f'3 {t[0]} {t[1]} {t[2]}\n')


def write_thickness_csv(path, L: Lenticule, step=0.1):
    g = np.arange(-L.R, L.R + 1e-9, step)
    X, Y = np.meshgrid(g, g); T = L.thickness(X, Y)
    with open(path, 'w') as f:
        f.write('# толщина лентикулы, мкм; строки — y (мм) сверху вниз от +R к -R; столбцы — x (мм); пусто вне оптической зоны\n')
        f.write('y\\x;' + ';'.join(f'{x:.2f}' for x in g) + '\n')
        for j in range(len(g) - 1, -1, -1):
            f.write(f'{g[j]:.2f};' + ';'.join('' if np.isnan(v) else f'{v:.1f}' for v in T[j]) + '\n')


# ---------------------------------------------------------------------------- самопроверка -----------
def selftest():
    cases = [Lenticule(1.0, -4.0, 0.0), Lenticule(0.25, -3.0, 5.0), Lenticule(1.75, -5.0, 10.0), Lenticule(-3.0, -2.0, 90.0)]
    ok = True
    for L in cases:
        V, F, thk = lenticule_mesh(L, exag=1.0)
        vf, vn, vm = L.volume_formula(), L.volume_numeric(), mesh_volume(V, F)
        wt = is_watertight(F)
        good = wt and abs(vf - vn) < 0.01 and abs(vf - vm) / vf < 0.02
        ok &= good
        print(('OK ' if good else 'FAIL'), f'Sph {L.sph:+.2f} Cyl {L.cyl:+.2f} ось {L.axis:.0f}: V формула {vf:.3f} | числ. {vn:.3f} | сетка {vm:.3f} мм³ | герметична: {wt} | min t {np.nanmin(thk):.1f} мкм')
    # проверка толщины по краю: минимум на краю = tmin (если Sph+Cyl<0)
    L = cases[0]; th = np.linspace(0, 2 * np.pi, 3601)
    edge = L.thickness(L.R * np.cos(th) * 0.999999, L.R * np.sin(th) * 0.999999)
    print('край: min %.2f (ожидается tmin %.0f), max %.2f (ожидается %.2f)' % (np.nanmin(edge), L.tmin, np.nanmax(edge), L.t_flat))
    assert abs(np.nanmin(edge) - L.tmin) < 0.05 and abs(np.nanmax(edge) - L.t_flat) < 0.05
    print('ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ' if ok else 'ЕСТЬ ОШИБКИ'); return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0)
    ap.add_argument('--axis', type=float, default=0.0); ap.add_argument('--oz', type=float, default=6.7)
    ap.add_argument('--tmin', type=float, default=20.0); ap.add_argument('--dome-r', type=float, default=7.8)
    ap.add_argument('--exag', type=float, default=1.0, help='увеличение толщины для наглядности (1 = истинный масштаб)')
    ap.add_argument('--out', default='out'); ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(0 if selftest() else 1)
    L = Lenticule(a.sph, a.cyl, a.axis, a.oz, a.tmin, dome_r=a.dome_r)
    os.makedirs(a.out, exist_ok=True)
    V, F, thk = lenticule_mesh(L, exag=a.exag)
    write_stl(f'{a.out}/lenticule.stl', V, F); write_obj(f'{a.out}/lenticule.obj', V, F)
    write_ply(f'{a.out}/lenticule_colored.ply', V, F, thickness_colors(thk)); write_thickness_csv(f'{a.out}/thickness_um.csv', L)
    print(L.summary()); print(f'сетка: {len(V)} вершин, {len(F)} треугольников, герметична: {is_watertight(F)}; файлы в {a.out}/')
