"""
blender_smile_procedure.py — 3D-схема операции SMILE (фемтосекундная лентикулярная экстракция) в Blender.

Сюжет одного ролика (≈45 с при 24 к/с):
  1) анатомия глаза в горизонтальном разрезе (роговица, передняя камера, радужка, хрусталик, цилиарное тело,
     склера, сосудистая оболочка, сетчатка, стекловидное тело, зрительный нерв);
  2) роговица крупно: эпителий, боуменова мембрана, строма, десцеметова мембрана с эндотелием;
  3) фиксация изогнутой контактной линзой (вакуум);
  4) фемтосекундный лазер по шагам VisuMax: задняя поверхность лентикулы (спираль от периферии к центру) →
     боковой рез лентикулы → граница колпачка на глубине 120 мкм (спираль от центра к периферии) → разрез доступа;
  5) лентикула той же торической формы, что в lenticule_model.py (по умолчанию Sph +1,0 / Cyl −4,0 × 0°, ОЗ 6,7 мм);
  6) разделение слоёв шпателем (сначала передняя, затем задняя поверхность);
  7) извлечение лентикулы пинцетом через разрез, лентикула сжимается и выходит; затем её показывают целиком.

Это СХЕМА, а не клинический протокол: толщина лентикулы по умолчанию увеличена ×2, шаг спирали лазера увеличен
(реально — микрометры), ИК-излучение (~1040 нм) показано условным цветом, деформация лентикулы при извлечении —
наглядная, не механическая модель. Размеры глаза — типичные (длина оси ≈24,7 мм, роговица 550 мкм в центре).

Запуск (bpy 4.2+/5.x, Eevee или Cycles; кадры рендерятся по одному, анимация задаётся в Python, а не ключами):
  python3 blender_smile_procedure.py --out out/smile --engine eevee --video
  blender -b -P blender_smile_procedure.py -- --out out/smile --video
  Пробный кадр:        ... --only-frame 300
  Каждый 6-й кадр:     ... --step 6            (быстрый просмотр)
  Короче/длиннее:      ... --speed 0.7         (множитель длительности всех этапов)
  Параметры лентикулы: --sph --cyl --axis --oz --tmin, колпачок --cap (мкм), разрез --inc-angle --inc-width (мм)
Выход: <out>/lab/*.png (с подписями), <out>/clean/*.png (без подписей), <out>.mp4, <out>_bez_podpisej.mp4, <out>.gif
"""
import sys, os, math, argparse, time, subprocess, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from lenticule_model import Lenticule

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0)
ap.add_argument('--axis', type=float, default=0.0); ap.add_argument('--oz', type=float, default=6.7)
ap.add_argument('--tmin', type=float, default=20.0)
ap.add_argument('--exag', type=float, default=3.0, help='увеличение толщины лентикулы для наглядности')
ap.add_argument('--cap', type=float, default=120.0, help='толщина колпачка, мкм'); ap.add_argument('--cap-d', type=float, default=7.5, help='диаметр колпачка, мм')
ap.add_argument('--inc-angle', type=float, default=120.0, help='положение разреза доступа, градусы (TABO)')
ap.add_argument('--inc-width', type=float, default=2.5, help='длина разреза доступа (хорда), мм')
ap.add_argument('--width', type=int, default=1280); ap.add_argument('--height', type=int, default=720)
ap.add_argument('--fps', type=float, default=24.0); ap.add_argument('--speed', type=float, default=1.0)
ap.add_argument('--engine', choices=['eevee', 'cycles'], default='cycles'); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--out', default='out/smile'); ap.add_argument('--only-frame', type=int, default=None)
ap.add_argument('--frames', default=None, help='диапазон 1-200 или список 10,250,600'); ap.add_argument('--step', type=int, default=1)
ap.add_argument('--font', default=None); ap.add_argument('--video', action='store_true')
ap.add_argument('--text', action='store_true', help='наложить заголовки этапов и подписи (по умолчанию — без текста)')
ap.add_argument('--save-blend', default=None)
ap.add_argument('--no-pointers', action='store_true', help='без подписей-выносок (структуры глаза, инструменты); заголовки этапов остаются')
ap.add_argument('--overlay-only', action='store_true', help='не рендерить: заново наложить подписи на готовые кадры <out>/raw')
A = ap.parse_args(argv)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ================================================================ анатомия (мм; ось глаза — +Z, вершина роговицы в 0)
R_ANT = 7.8                       # радиус передней поверхности роговицы
CCT = 0.55                        # толщина роговицы в центре
R_LIMB = 5.8                      # полудиаметр роговицы (лимб)
PSI_L = math.asin(R_LIMB / R_ANT)
EPI, BOW, DE = 0.050, 0.012, 0.020          # эпителий, боуменова, десцемет+эндотелий
C = np.array([0.0, 0.0, -R_ANT])            # центр передней сферы роговицы
RS, TS = 11.8, 0.7                          # склера: наружный радиус, толщина
Z_A = -R_ANT + R_ANT * math.cos(PSI_L)
ZS = Z_A - math.sqrt(RS ** 2 - R_LIMB ** 2)  # центр склеральной сферы
RSI = RS - TS
TH_C = math.radians(A.axis + 45.0)           # вырезанный сектор между плоским (ось) и крутым (ось+90°) меридианами

L = Lenticule(A.sph, A.cyl, A.axis, A.oz, A.tmin)
CAP = A.cap / 1000.0
R_LT = R_ANT - CAP - 0.002                   # радиус сферы передней поверхности лентикулы
R_CAPD = A.cap_d / 2
TH_INC = math.radians(A.inc_angle)
D_INC = np.array([math.cos(TH_INC), math.sin(TH_INC), 0.0])
N_INC = np.array([-math.sin(TH_INC), math.cos(TH_INC), 0.0])
EZ = np.array([0.0, 0.0, 1.0])
S_INC = R_LT * math.asin(R_CAPD / R_LT)      # дуга от центра до разреза
S_LEAD = R_LT * math.asin(L.R / R_LT)        # дуга до края лентикулы
HALF_INC = math.asin(A.inc_width / 2 / R_CAPD)


def T_cornea(psi):
    return CCT + 0.17 * (np.asarray(psi) / PSI_L) ** 2


def cornea_pt(psi, d):
    R = R_ANT - d
    return np.column_stack([R * np.sin(psi), -R_ANT + R * np.cos(psi)])


def layer_profile(d0, d1, n=90):
    ps = np.linspace(0, PSI_L, n)
    return np.vstack([cornea_pt(ps, d0(ps)), cornea_pt(ps[::-1], d1(ps[::-1]))])


def sph(rad, ang, n):  # дуга склеральной сферы: ang — угол от +Z (вперёд), мм
    a = np.linspace(ang[0], ang[1], n)
    return np.column_stack([rad * np.sin(a), ZS + rad * np.cos(a)])


def ang_at_z(rad, z):
    return math.acos((z - ZS) / rad)


def sclera_profile():
    psA = ang_at_z(RS, Z_A)
    B = cornea_pt(np.array([PSI_L]), T_cornea(PSI_L))[0]
    psB = math.asin(min(B[0] / RSI, 1.0))
    return np.vstack([sph(RS, (psA, math.pi), 120), sph(RSI, (math.pi, psB), 120)[1:], B[None]])


Z_ORA = -7.6
CHOR = (RSI, RSI - 0.22); RET = (RSI - 0.22, RSI - 0.45)


def shell_profile(r0, r1, z_front):
    a0, a1 = ang_at_z(r0, z_front), ang_at_z(r1, z_front)
    return np.vstack([sph(r0, (a0, math.pi), 100), sph(r1, (math.pi, a1), 100)[1:]])


def ciliary_profile():
    a0, a1 = ang_at_z(RSI, -3.30), ang_at_z(RSI, Z_ORA)
    outer = sph(RSI, (a0, a1), 30)
    inner = [(math.sqrt((RSI - 0.22) ** 2 - (Z_ORA - ZS) ** 2), Z_ORA), (math.sqrt((RSI - 0.35) ** 2 - (-5.8 - ZS) ** 2), -5.8),
             (4.95, -4.55), (5.0, -4.1), (5.3, -3.62)]
    return np.vstack([outer, np.array(inner)])


IRIS = np.array([(1.75, -3.56), (2.2, -3.46), (2.7, -3.40), (3.5, -3.36), (4.5, -3.33), (5.2, -3.38), (5.45, -3.50),
                 (5.45, -3.72), (4.5, -3.73), (3.5, -3.75), (2.5, -3.77), (1.75, -3.73)])
LZ_A, LZ_P, LRA, LRP = -3.80, -7.80, 10.0, 6.0


def lens_profile(n=70):
    za = lambda r: LZ_A - (LRA - np.sqrt(LRA ** 2 - r ** 2))
    zp = lambda r: LZ_P + (LRP - np.sqrt(LRP ** 2 - r ** 2))
    lo, hi = 0.0, 5.99
    for _ in range(60):
        m = 0.5 * (lo + hi); lo, hi = (m, hi) if za(m) > zp(m) else (lo, m)
    req = lo
    r1 = req * np.sin(np.linspace(0, np.pi / 2, n))
    return np.vstack([np.column_stack([r1, za(r1)]), np.column_stack([r1[::-1], zp(r1[::-1])])[1:-1]])


# ================================================================ сетки
def revolve(prof, th0, th1, nth=180, closed=True, caps=True):
    """Тело (closed) или поверхность (open) вращения профиля (r, z) в секторе [th0, th1].
    prof — массив (M,2) или функция th -> (M,2). Возвращает V, (quads, tris, ngons), mats, ii, tt."""
    full = (th1 - th0) >= 2 * np.pi - 1e-6
    if full:
        nt = nth; ths = th0 + np.arange(nt) * (2 * np.pi / nth)
    else:
        nt = max(2, int(math.ceil(nth * (th1 - th0) / (2 * np.pi))) + 1); ths = np.linspace(th0, th1, nt)
    P = np.stack([np.asarray(prof(t) if callable(prof) else prof, float) for t in ths])
    if closed:
        p0 = P[0]; area = 0.5 * np.sum(p0[:, 0] * np.roll(p0[:, 1], -1) - np.roll(p0[:, 0], -1) * p0[:, 1])
        if area < 0: P = P[:, ::-1].copy()
    M = P.shape[1]
    V = np.empty((nt, M, 3)); V[..., 0] = P[..., 0] * np.cos(ths)[:, None]; V[..., 1] = P[..., 0] * np.sin(ths)[:, None]; V[..., 2] = P[..., 1]
    idx = np.arange(nt * M).reshape(nt, M)
    jn = np.arange(nt) if full else np.arange(nt - 1)
    j1 = (jn + 1) % nt
    im = np.arange(M) if closed else np.arange(M - 1)
    i1 = (im + 1) % M
    A_ = idx[jn][:, im]; B_ = idx[j1][:, im]; C_ = idx[j1][:, i1]; D_ = idx[jn][:, i1]
    onax = P[0, :, 0] < 1e-9
    a_ax = np.broadcast_to(onax[im], A_.shape); d_ax = np.broadcast_to(onax[i1], A_.shape)
    q = ~a_ax & ~d_ax; ta = a_ax & ~d_ax; td = ~a_ax & d_ax
    quads = np.stack([A_[q], B_[q], C_[q], D_[q]], 1)
    tris = np.vstack([np.stack([A_[ta], C_[ta], D_[ta]], 1), np.stack([A_[td], B_[td], C_[td]], 1)])
    ngons = []
    if closed and caps and not full:
        ngons = [idx[0].copy(), idx[-1][::-1].copy()]
    mats = np.concatenate([np.zeros(len(quads) + len(tris), int), np.ones(len(ngons), int)])
    ii = np.broadcast_to(np.arange(M), (nt, M)).ravel(); tt = np.repeat(ths, M)
    return V.reshape(-1, 3), (quads, tris, ngons), mats, ii, tt


def set_mesh(obj, V, polys, mats, attrs=None, smooth=True, sharp=35):
    quads, tris, ngons = polys
    me = obj.data; me.clear_geometry()
    me.vertices.add(len(V)); me.vertices.foreach_set('co', np.ascontiguousarray(V, np.float32).ravel())
    parts = [quads.ravel(), tris.ravel()] + [np.asarray(g) for g in ngons]
    loops = np.concatenate(parts).astype(np.int32)
    sizes = np.concatenate([np.full(len(quads), 4), np.full(len(tris), 3), np.array([len(g) for g in ngons], int)]).astype(np.int32)
    if len(sizes) == 0:
        me.update(); return
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)
    me.loops.add(len(loops)); me.loops.foreach_set('vertex_index', loops)
    me.polygons.add(len(sizes)); me.polygons.foreach_set('loop_start', starts)
    me.polygons.foreach_set('material_index', mats.astype(np.int32))
    me.update(calc_edges=True)
    me.polygons.foreach_set('use_smooth', np.full(len(sizes), smooth))
    if smooth and sharp:
        try: me.set_sharp_from_angle(angle=math.radians(sharp))
        except Exception: pass
    for name, arr in (attrs or {}).items():
        at = me.attributes.new(name=name, type='FLOAT', domain='POINT'); at.data.foreach_set('value', np.asarray(arr, np.float32))
    me.update()


def new_obj(name, mats=()):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    return ob


def tube(points, radius, nseg=14, cap_tip=True):
    """Трубка вдоль ломаной (параллельный перенос рамки). radius — число или массив по точкам."""
    P = np.asarray(points, float); n = len(P); r = np.broadcast_to(np.asarray(radius, float), (n,))
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    ref = np.array([0, 0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0, 0])
    U = np.zeros_like(P); u = np.cross(T[0], ref); u /= np.linalg.norm(u)
    for k in range(n):
        u = u - T[k] * np.dot(u, T[k]); u /= np.linalg.norm(u); U[k] = u
    W = np.cross(T, U); a = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    V = (P[:, None, :] + r[:, None, None] * (np.cos(a)[None, :, None] * U[:, None, :] + np.sin(a)[None, :, None] * W[:, None, :])).reshape(-1, 3)
    idx = np.arange(n * nseg).reshape(n, nseg); j1 = (np.arange(nseg) + 1) % nseg
    quads = np.stack([idx[:-1][:, np.arange(nseg)], idx[:-1][:, j1], idx[1:][:, j1], idx[1:][:, np.arange(nseg)]], -1).reshape(-1, 4)
    V = np.vstack([V, P[0], P[-1] + T[-1] * r[-1] * (0.6 if cap_tip else 0)])
    c0, c1 = len(V) - 2, len(V) - 1
    tris = np.vstack([np.stack([np.full(nseg, c0), idx[0][j1], idx[0]], 1), np.stack([np.full(nseg, c1), idx[-1], idx[-1][j1]], 1)])
    return V, (quads, tris, []), np.zeros(len(quads) + len(tris), int)


def tapered_bar(xs, w, t, zsign):
    """Пластина вдоль +x (бранша пинцета): ширина w(x), толщина t(x); zsign=+1 — над плоскостью z=0, −1 — под ней."""
    xs = np.asarray(xs, float); w = np.asarray(w, float); t = np.asarray(t, float); n = len(xs)
    z0 = np.zeros(n); z1 = zsign * t
    ring = lambda k: [(xs[k], -w[k] / 2, z0[k]), (xs[k], w[k] / 2, z0[k]), (xs[k], w[k] / 2, z1[k]), (xs[k], -w[k] / 2, z1[k])]
    V = np.array([p for k in range(n) for p in ring(k)])
    quads = []
    for k in range(n - 1):
        for e in range(4):
            a, b = 4 * k + e, 4 * k + (e + 1) % 4
            quads.append([a, b, b + 4, a + 4] if zsign > 0 else [a, a + 4, b + 4, b])
    quads += [[0, 3, 2, 1] if zsign > 0 else [0, 1, 2, 3], [4 * (n - 1) + i for i in ((0, 1, 2, 3) if zsign > 0 else (0, 3, 2, 1))]]
    return V, (np.array(quads), np.zeros((0, 3), int), []), np.zeros(len(quads), int)


# ================================================================ материалы
def lin(c): return tuple((x / 255.0) ** 2.2 for x in c)


def mat_basic(name, color, alpha=1.0, rough=0.5, metal=0.0, coat=0.0, emit=0.0, sss=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = m.node_tree.nodes.get('Principled BSDF')
    def s(k, v):
        for kk in ((k,) if isinstance(k, str) else k):
            if kk in b.inputs: b.inputs[kk].default_value = v; return
    s('Base Color', (*color, 1)); s('Roughness', rough); s('Metallic', metal); s('Alpha', alpha)
    s(('Coat Weight', 'Clearcoat'), coat); s(('Specular IOR Level', 'Specular'), spec)
    if emit: s(('Emission Color', 'Emission'), (*color, 1)); s('Emission Strength', emit)
    if sss: s(('Subsurface Weight', 'Subsurface'), sss)
    if alpha < 1:
        for k, v in (('surface_render_method', 'DITHERED'), ('blend_method', 'HASHED')):
            try: setattr(m, k, v)
            except Exception: pass
    m['bsdf'] = b.name
    return m


def mat_attr_alpha(name, color, attr_expr, base_alpha=0.9, emit=0.25, noise_scale=0.0):
    """Материал «слоя пузырьков» (OBL): прозрачность = base·cut·(1−clear)·пятнистость."""
    m = mat_basic(name, color, 1.0, rough=0.6, emit=emit)
    nt = m.node_tree; b = nt.nodes[m['bsdf']]
    cut = nt.nodes.new('ShaderNodeAttribute'); cut.attribute_type = 'GEOMETRY'; cut.attribute_name = 'cut'
    clr = nt.nodes.new('ShaderNodeAttribute'); clr.attribute_type = 'GEOMETRY'; clr.attribute_name = 'clear'
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(clr.outputs['Fac'], inv.inputs[1])
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(cut.outputs['Fac'], m1.inputs[0]); nt.links.new(inv.outputs['Value'], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = base_alpha; nt.links.new(m1.outputs['Value'], m2.inputs[0])
    last = m2
    if noise_scale:
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = noise_scale
        cr = nt.nodes.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.35; cr.inputs['From Max'].default_value = 0.65
        cr.inputs['To Min'].default_value = 0.45; cr.inputs['To Max'].default_value = 1.0
        nt.links.new(nz.outputs['Fac'], cr.inputs['Value'])
        m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs['Value'], m3.inputs[0]); nt.links.new(cr.outputs['Result'], m3.inputs[1]); last = m3
    nt.links.new(last.outputs['Value'], b.inputs['Alpha'])
    for k, v in (('surface_render_method', 'DITHERED'), ('blend_method', 'HASHED')):
        try: setattr(m, k, v)
        except Exception: pass
    return m


CMAP = [(205, 226, 251), (158, 197, 244), (109, 167, 236), (57, 135, 229), (37, 106, 191), (28, 92, 171), (24, 79, 149)]


def mat_lenticule():
    m = mat_basic('Lenticule', (0.3, 0.5, 0.9), 1.0, rough=0.28, coat=0.5)
    nt = m.node_tree; b = nt.nodes[m['bsdf']]
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'thk'
    rg = nt.nodes.new('ShaderNodeMapRange'); rg.inputs['From Min'].default_value = 10; rg.inputs['From Max'].default_value = 90
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    for i, c in enumerate(CMAP):
        e = cr.elements[i] if i < len(cr.elements) else cr.elements.new(i / (len(CMAP) - 1))
        e.position = i / (len(CMAP) - 1); e.color = (*lin(c), 1.0)
    nt.links.new(at.outputs['Fac'], rg.inputs['Value']); nt.links.new(rg.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    for k in ('Emission Color', 'Emission'):
        if k in b.inputs: nt.links.new(ramp.outputs['Color'], b.inputs[k]); break
    b.inputs['Emission Strength'].default_value = 0.12
    for k, v in (('surface_render_method', 'DITHERED'), ('blend_method', 'HASHED')):
        try: setattr(m, k, v)
        except Exception: pass
    return m


def mat_beam():
    m = bpy.data.materials.new('Beam')
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader'); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    em.inputs['Color'].default_value = (1.0, 0.16, 0.30, 1); em.inputs['Strength'].default_value = 1.6
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'MULTIPLY_ADD'; inv.inputs[1].default_value = 0.30; inv.inputs[2].default_value = 0.10
    nt.links.new(lw.outputs['Facing'], inv.inputs[0])
    nt.links.new(inv.outputs['Value'], mix.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mix.inputs[1]); nt.links.new(em.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m['strength_node'] = em.name; m['fac_node'] = inv.name
    for k, v in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
        try: setattr(m, k, v)
        except Exception: pass
    return m


M = {
    'cornea': mat_basic('Cornea', lin((215, 235, 252)), 0.07, rough=0.08, coat=0.5, spec=0.5),
    'epi_cut': mat_basic('EpitheliumCut', lin((236, 170, 160)), 1.0, rough=0.6),
    'bow_cut': mat_basic('BowmanCut', lin((250, 245, 220)), 1.0, rough=0.6, emit=0.15),
    'str_cut': mat_basic('StromaCut', lin((150, 188, 225)), 1.0, rough=0.7),
    'end_cut': mat_basic('EndotheliumCut', lin((70, 105, 190)), 1.0, rough=0.6),
    'scl': mat_basic('Sclera', lin((238, 232, 222)), 1.0, rough=0.55, sss=0.05),
    'scl_cut': mat_basic('ScleraCut', lin((225, 214, 198)), 1.0, rough=0.8),
    'cho': mat_basic('Choroid', lin((120, 40, 34)), 1.0, rough=0.6),
    'ret': mat_basic('Retina', lin((236, 140, 105)), 1.0, rough=0.5),
    'cil': mat_basic('Ciliary', lin((138, 62, 48)), 1.0, rough=0.6),
    'iris': mat_basic('Iris', lin((110, 72, 44)), 1.0, rough=0.55),
    'iris_cut': mat_basic('IrisCut', lin((60, 36, 24)), 1.0, rough=0.7),
    'lens': mat_basic('Lens', lin((246, 236, 200)), 0.30, rough=0.15, coat=0.6),
    'lens_cut': mat_basic('LensCut', lin((236, 226, 190)), 1.0, rough=0.6),
    'nerve': mat_basic('Nerve', lin((240, 226, 190)), 1.0, rough=0.6),
    'nerve_cut': mat_basic('NerveCut', lin((228, 205, 160)), 1.0, rough=0.8),
    'glass': mat_basic('ContactGlass', lin((215, 238, 252)), 0.05, rough=0.03, coat=0.2, spec=0.3),
    'house': mat_basic('Housing', lin((95, 102, 115)), 1.0, rough=0.35, metal=0.8),
    'steel': mat_basic('Steel', lin((205, 208, 214)), 1.0, rough=0.22, metal=1.0),
    'steel_dark': mat_basic('SteelDark', lin((120, 124, 132)), 1.0, rough=0.35, metal=1.0),
    'spot': mat_basic('Spot', (1.0, 0.75, 0.85), 1.0, emit=40.0),
    'obl': mat_attr_alpha('OBL', lin((236, 242, 250)), 'cut', base_alpha=0.2, emit=0.10, noise_scale=45.0),
    'flat': mat_basic('MeridianFlat', lin((46, 204, 113)), 1.0, rough=0.4, emit=1.2),
    'steep': mat_basic('MeridianSteep', lin((239, 68, 68)), 1.0, rough=0.4, emit=1.2),
    'lent': mat_lenticule(),
    'beam': mat_beam(),
}
# прозрачность лентикулы меняется по кадрам
LENT_BSDF = M['lent'].node_tree.nodes[M['lent']['bsdf']]



# ================================================================ объекты
def wedge_range(W):
    """Оставляемый сектор при вырезе W (градусы), вырез обращён к камере (TH_C)."""
    w = math.radians(W)
    return (TH_C + w / 2, TH_C + 2 * np.pi - w / 2) if W > 0.01 else (0.0, 2 * np.pi)


def lent_profile(th, rt=R_LT, nr=34, nwall=3, out=0.0):
    """Профиль лентикулы в меридиане th: передняя поверхность (сфера rt) → стенка → задняя поверхность."""
    rs = L.R * np.sin(np.linspace(0, np.pi / 2, nr))
    t = L.thickness(rs * np.cos(th), rs * np.sin(th)) * A.exag / 1000.0
    zt = -R_ANT + np.sqrt(rt ** 2 - rs ** 2)
    k = (rt - t) / rt
    top = np.column_stack([rs, zt]); bot = np.column_stack([rs * k, -R_ANT + (zt + R_ANT) * k])
    wall = [top[-1] + (bot[-1] - top[-1]) * f for f in np.linspace(0, 1, nwall + 2)[1:-1]]
    return np.vstack([top, wall, bot[::-1]])


def lent_bottom(th, rs, off=0.004):
    t = L.thickness(rs * np.cos(th), rs * np.sin(th)) * A.exag / 1000.0 + off
    zt = -R_ANT + np.sqrt(R_LT ** 2 - rs ** 2); k = (R_LT - t) / R_LT
    return np.column_stack([rs * k, -R_ANT + (zt + R_ANT) * k])


def sphere_pts(rad, rs):
    rs = np.asarray(rs, float); return np.column_stack([rs, -R_ANT + np.sqrt(rad ** 2 - rs ** 2)])


def to3(r, z, th):
    return np.array([r * math.cos(th), r * math.sin(th), z])


CORNEA_LAYERS = [  # слои роговицы видны только на плоскости среза
    ('Epithelium', layer_profile(lambda p: 0 * p, lambda p: EPI + 0 * p), 'epi_cut'),
    ('Bowman', layer_profile(lambda p: EPI + 0 * p, lambda p: EPI + BOW + 0 * p), 'bow_cut'),
    ('Stroma', layer_profile(lambda p: EPI + BOW + 0 * p, lambda p: T_cornea(p) - DE), 'str_cut'),
    ('Endothelium', layer_profile(lambda p: T_cornea(p) - DE, lambda p: T_cornea(p)), 'end_cut'),
]
CORNEA_PROF = layer_profile(lambda p: 0 * p, lambda p: T_cornea(p))
ANAT = [  # имя, профиль, материалы (поверхность, срез)
    ('Sclera', sclera_profile(), ('scl', 'scl_cut')),
    ('Choroid', shell_profile(CHOR[0], CHOR[1], Z_ORA), ('cho', 'cho')),
    ('Retina', shell_profile(RET[0], RET[1], Z_ORA + 0.2), ('ret', 'ret')),
    ('Ciliary', ciliary_profile(), ('cil', 'cil')),
    ('Iris', IRIS, ('iris', 'iris_cut')),
    ('Lens', lens_profile(), ('lens', 'lens_cut')),
]
anat_objs = [(new_obj(n, [M[a], M[b]]), prof) for n, prof, (a, b) in ANAT]
cornea_obj = new_obj('Cornea', [M['cornea']])
layer_objs = [(new_obj('Cut_' + n, [M[m]]), prof) for n, prof, m in CORNEA_LAYERS]

zin = lambda r: -R_ANT + math.sqrt(R_ANT ** 2 - r ** 2)
GL_R = 4.9
glass_prof = np.vstack([sphere_pts(R_ANT, np.linspace(0, GL_R, 50)), sphere_pts(R_ANT + 0.9, np.linspace(GL_R, 0, 50))])
house_prof = np.array([(GL_R, zin(GL_R) + 0.05), (GL_R + 0.35, zin(GL_R) + 0.05), (GL_R + 0.35, zin(GL_R) + 0.75), (GL_R, zin(GL_R) + 0.75)])
glass_obj = new_obj('ContactGlass', [M['glass'], M['glass']]); house_obj = new_obj('Housing', [M['house'], M['house']])
lent_obj = new_obj('Lenticule', [M['lent'], M['lent']])
obl = {k: new_obj('OBL_' + k, [M['obl']]) for k in ('post', 'side', 'cap', 'inc')}

# зрительный нерв: полуцилиндр в плоскости разреза, на 15° в сторону носа
a_n = np.array([math.sin(math.radians(15)) * math.cos(TH_C + np.pi / 2), math.sin(math.radians(15)) * math.sin(TH_C + np.pi / 2), -math.cos(math.radians(15))])
e_s = np.array([math.cos(TH_C + np.pi / 2), math.sin(TH_C + np.pi / 2), 0.0]); e1 = e_s - a_n * np.dot(e_s, a_n); e1 /= np.linalg.norm(e1); e2 = np.cross(a_n, e1)
hc = np.array([math.cos(TH_C), math.sin(TH_C), 0.0])
NERVE0 = np.array([0, 0, ZS]) + (RS - 0.9) * a_n
Vn, Pn, Mn, _, _ = revolve(np.array([(0, 0), (1.55, 0), (1.55, 3.0), (1.45, 9.0), (0, 9.0)]), *((np.pi, 2 * np.pi) if np.dot(e2, hc) > 0 else (0, np.pi)), nth=64)
Vn = NERVE0 + Vn[:, :1] * e1 + Vn[:, 1:2] * e2 + Vn[:, 2:3] * a_n
nerve_obj = new_obj('OpticNerve', [M['nerve'], M['nerve_cut']]); set_mesh(nerve_obj, Vn, Pn, Mn)

# луч лазера (конус, вершина в фокусе) и пятно
beam_obj = new_obj('Beam', [M['beam']])
Vb, Pb, Mb, _, _ = revolve(np.array([(0, 0), (0.28, 2.5), (0.7, 7.0)]), 0, 2 * np.pi, 48, closed=False)
set_mesh(beam_obj, Vb, Pb, Mb)
spot_obj = new_obj('Spot', [M['spot']])
Vs, Ps, Ms, _, _ = revolve(np.column_stack([0.035 * np.sin(np.linspace(0, np.pi, 12)), -0.035 * np.cos(np.linspace(0, np.pi, 12))]), 0, 2 * np.pi, 16, closed=False)
set_mesh(spot_obj, Vs, Ps, Ms)
halo_obj = new_obj('Halo', [M['beam']])
set_mesh(halo_obj, Vs * 2.2, Ps, Ms)

spat_obj = new_obj('Spatula', [M['steel']])
forceps = bpy.data.objects.new('Forceps', None); scene.collection.objects.link(forceps)
FXS = [0, 0.8, 3, 8, 14, 30, 72]; FW = [0.16, 0.24, 0.42, 0.8, 1.2, 1.9, 1.9]; FT = [0.045, 0.07, 0.12, 0.2, 0.3, 0.45, 0.45]
jaws = []
for zs_ in (+1, -1):
    ob = new_obj('ForcepsArm%+d' % zs_, [M['steel']]); Vj, Pj, Mj = tapered_bar(FXS, FW, FT, zs_)
    set_mesh(ob, Vj, Pj, Mj, sharp=25); ob.parent = forceps; jaws.append((ob, zs_))


# пузырьки лазера: вершины сетки -> сферы (узел «Mesh to Points»), радиус и свечение — атрибуты вершин
def mat_bubble():
    m = mat_basic('Bubble', lin((236, 244, 255)), 0.92, rough=0.15, coat=0.6, emit=0.0)
    nt = m.node_tree; b = nt.nodes[m['bsdf']]
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'glow'
    ma = nt.nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = 7.0; ma.inputs[2].default_value = 0.18
    nt.links.new(at.outputs['Fac'], ma.inputs[0])
    for k in ('Emission Color', 'Emission'):
        if k in b.inputs: b.inputs[k].default_value = (0.80, 0.90, 1.0, 1); break
    nt.links.new(ma.outputs['Value'], b.inputs['Emission Strength'])
    return m


M['bubble'] = mat_bubble()
bub_obj = new_obj('Bubbles', [M['bubble']])
gn = bpy.data.node_groups.new('BubblePoints', 'GeometryNodeTree')
gn.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
gn.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = gn.nodes.new('NodeGroupInput'); go = gn.nodes.new('NodeGroupOutput')
m2p = gn.nodes.new('GeometryNodeMeshToPoints'); na = gn.nodes.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'
na.inputs['Name'].default_value = 'rad'
sm = gn.nodes.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = M['bubble']
gn.links.new(gi.outputs[0], m2p.inputs['Mesh']); gn.links.new(na.outputs['Attribute'], m2p.inputs['Radius'])
gn.links.new(m2p.outputs['Points'], sm.inputs['Geometry']); gn.links.new(sm.outputs['Geometry'], go.inputs[0])
bub_obj.modifiers.new('pts', 'NODES').node_group = gn

mer_obj = new_obj('Meridians', [M['flat'], M['steep']])


# ================================================================ таймлайн
SEGS = [('intro', 96), ('zoom', 72), ('layers', 48), ('dock', 40), ('post', 168), ('side', 48), ('cap', 144), ('inc', 60),
        ('undock', 36), ('form', 132), ('close', 54), ('spat_in', 20), ('spat_ant', 56), ('spat_post', 56), ('spat_out', 20),
        ('forc_in', 36), ('pull', 110), ('show', 144)]
SEGS = [(n, max(6, int(round(k * A.speed)))) for n, k in SEGS]
START = {}; acc = 1
for n, k in SEGS: START[n] = acc; acc += k
NF = acc - 1
LEN = dict(SEGS)


def seg_of(f):
    for n, k in SEGS:
        if f < START[n] + k: return n, (f - START[n]) / k
    return SEGS[-1][0], 1.0


def prog(n, f): return float(np.clip((f - START[n]) / LEN[n], 0, 1))
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x) if np.ndim(x) else float(x * x * (3 - 2 * x))
def after(n, f): return f >= START[n] + LEN[n]
def during(n, f): return START[n] <= f < START[n] + LEN[n]


def W_of(f):
    if f < START['zoom']: return 180.0
    if f < START['layers']: return 180.0 - 90.0 * ss(prog('zoom', f))
    if f < START['close']: return 90.0
    if f < START['spat_in']: return 90.0 * (1 - ss(prog('close', f)))
    return 0.0


def dock_of(f):  # подъём контактной линзы над глазом, мм (0 — пристыкована)
    if f < START['dock']: return 14.0
    if f < START['post']: return 14.0 * (1 - ss(prog('dock', f)))
    if f < START['undock']: return 0.0
    return 14.0 * ss(prog('undock', f))


# ---------------------------------------------------------------- путь извлечения
RB, GMAX = 0.6, math.radians(60)


def path(s):
    s = np.atleast_1d(np.asarray(s, float))
    a = np.minimum(s, S_INC)[:, None] / R_LT
    P = C + R_LT * (np.sin(a) * D_INC + np.cos(a) * EZ); T = np.cos(a) * D_INC - np.sin(a) * EZ; B = np.sin(a) * D_INC + np.cos(a) * EZ
    a0 = S_INC / R_LT
    P0 = C + R_LT * (math.sin(a0) * D_INC + math.cos(a0) * EZ); T0 = math.cos(a0) * D_INC - math.sin(a0) * EZ; B0 = math.sin(a0) * D_INC + math.cos(a0) * EZ
    e = np.maximum(s - S_INC, 0)[:, None]; g = np.minimum(e / RB, GMAX)
    Pe = P0 + RB * (np.sin(g) * T0 + (1 - np.cos(g)) * B0); Te = np.cos(g) * T0 + np.sin(g) * B0; Be = -np.sin(g) * T0 + np.cos(g) * B0
    Pe = Pe + np.maximum(e - RB * GMAX, 0) * Te
    out = (s > S_INC)[:, None]
    return np.where(out, Pe, P), np.where(out, Te, T), np.where(out, Be, B)


def lent_deform(V, pull, comp=1.0):
    q = V - C; rad = np.linalg.norm(q, axis=1); u = q / rad[:, None]
    beta = np.arcsin(np.clip(u @ N_INC, -1, 1)); alpha = np.arctan2(u @ D_INC, u @ EZ)
    s = R_LT * alpha + pull; v = R_LT * beta; h = rad - R_LT
    c = comp * ss((s - (S_INC - 1.4)) / 1.35)
    Xf = (R_LT + h) * np.sin(beta); Yf = (R_LT + h) * np.cos(beta) - R_LT
    sig = (A.inc_width * 0.46) / L.R
    Xc = sig * v; Yc = h + 0.13 * np.sin(2 * np.pi * v / 0.85 + 1.7 * s) * (0.4 + 0.6 * np.abs(v) / L.R)
    X = (1 - c) * Xf + c * Xc; Y = (1 - c) * Yf + c * Yc
    P, T, B = path(s)
    return P + N_INC[None] * X[:, None] + B * Y[:, None]


T_EDGE_INC = float(L.thickness(L.R * 0.999 * math.cos(TH_INC), L.R * 0.999 * math.sin(TH_INC)))
H_MID = -A.exag * T_EDGE_INC / 2000.0
P_TOTAL = S_INC + S_LEAD + 2.2
S_GRIP = S_LEAD - 0.35
GAP_CLOSED = A.exag * T_EDGE_INC / 1000.0 + 0.012     # бранши смыкаются на краю лентикулы


def forceps_state(f):
    """(s кончика, раскрытие кончиков мм, видимость, отвод мм)"""
    if during('forc_in', f):
        u = prog('forc_in', f)
        s = S_GRIP + (S_INC + 5.0 - S_GRIP) * (1 - ss(u / 0.7)); gap = 0.75 if u < 0.72 else 0.75 - (0.75 - GAP_CLOSED) * ss((u - 0.72) / 0.25)
        return s, gap, True, 0.0
    if during('pull', f):
        return S_GRIP + P_TOTAL * ss(prog('pull', f)), GAP_CLOSED, True, 0.0
    if during('show', f) or f > NF - 1:
        return S_GRIP + P_TOTAL, GAP_CLOSED, True, 0.0
    return 0, 0, False, 0


def forceps_frame(s):
    P, T, B = path(np.array([s, s + 1.0]))
    x = P[1] - P[0]; x /= np.linalg.norm(x); z = B[0] - x * np.dot(B[0], x); z /= np.linalg.norm(z); y = np.cross(z, x)
    return P[0] + B[0] * H_MID, x, y, z


def spat_state(f):
    """(плоскость 'ant'/'post', длина внутри мм, угол рад, видимость)"""
    AM = math.radians(68)
    if during('spat_in', f): return 'ant', -4.0 + 5.6 * ss(prog('spat_in', f)), 0.0, True
    for pl in ('ant', 'post'):
        n = 'spat_' + pl
        if during(n, f):
            u = prog(n, f); reach = 1.6 + 5.8 * ss(min(1, u / 0.55)); amp = AM * ss(min(1, u / 0.45))
            if u > 0.85: reach = 1.6 + (reach - 1.6) * (1 - ss((u - 0.85) / 0.15))
            return pl, reach, amp * math.sin(2 * np.pi * 2.2 * u), True
    if during('spat_out', f): return 'post', 1.6 - 6.0 * ss(prog('spat_out', f)), 0.0, True
    return 'ant', 0, 0, False


def spat_cleared(pl, f, X, Y):
    """Доля «разделённого» слоя пузырьков в точках (X, Y) (горизонтальные координаты)."""
    n = 'spat_' + pl
    if f < START[n]: return np.zeros_like(X)
    u = 1.0 if after(n, f) else prog(n, f)
    reach = 1.6 + 5.8 * ss(min(1, u / 0.55)); amp = math.radians(68) * ss(min(1, u / 0.45))
    px, py = R_CAPD * math.cos(TH_INC), R_CAPD * math.sin(TH_INC)
    dx, dy = X - px, Y - py; dist = np.hypot(dx, dy)
    ang = np.arctan2(-D_INC[0] * dy + D_INC[1] * dx, -(D_INC[0] * dx + D_INC[1] * dy))
    return np.clip((reach - dist) / 0.4, 0, 1) * np.clip((amp + 0.12 - np.abs(ang)) / 0.15, 0, 1)


def spat_geometry(pl, Lin, psi):
    rr = R_LT + 0.006 if pl == 'ant' else R_LT - A.exag * L.t0 / 1000.0 - 0.03
    h = R_CAPD * rr / R_LT
    Q0 = C + rr * np.array([h * math.cos(TH_INC) / rr, h * math.sin(TH_INC) / rr, math.sqrt(1 - (h / rr) ** 2)])
    u0 = (Q0 - C) / rr
    g = np.array([-D_INC[0] * math.cos(psi) + D_INC[1] * math.sin(psi), -D_INC[1] * math.cos(psi) - D_INC[0] * math.sin(psi), 0.0])
    w = g - u0 * np.dot(g, u0); w /= np.linalg.norm(w)
    o = -w * 0.84 + u0 * 0.55; o /= np.linalg.norm(o)
    pts, rad = [], []
    if Lin > 0:
        for t in np.linspace(Lin, 0, max(3, int(Lin / 0.15))):
            pts.append(C + rr * (math.cos(t / rr) * u0 + math.sin(t / rr) * w)); rad.append(0.07 if Lin - t > 0.25 else 0.05)
        start_out = 0.0
    else:
        start_out = -Lin
    for t in np.concatenate([np.linspace(start_out, 3.0, 10)[1 if Lin > 0 else 0:], np.linspace(3.0, 40.0, 16)[1:]]):
        pts.append(Q0 + t * o); rad.append(0.07 if t < 1.5 else (0.07 + 0.13 * (t - 1.5) / 1.5 if t < 3 else (0.2 if t < 10 else 0.55)))
    return np.array(pts), np.array(rad), Q0, o


# ---------------------------------------------------------------- лазер: пузырьки по одному
BUB_PITCH, BUB_STEP, BUB_R = 0.17, 0.065, 0.021   # шаг спирали, шаг импульсов, радиус пузырька, мм (схема: реально — микрометры)
TH_AX = math.radians(A.axis)                       # спирали начинаются на плоском меридиане (плоскость среза)


def bottom_xyz(r, th, off=0.0):
    r = np.asarray(r, float); th = np.broadcast_to(np.asarray(th, float), r.shape)
    t = L.thickness(np.minimum(r, L.R * 0.9999) * np.cos(th), np.minimum(r, L.R * 0.9999) * np.sin(th)) * A.exag / 1000.0 + off
    zt = -R_ANT + np.sqrt(R_LT ** 2 - r ** 2); k = (R_LT - t) / R_LT
    return np.column_stack([r * k * np.cos(th), r * k * np.sin(th), -R_ANT + (zt + R_ANT) * k])


def cap_xyz(r, th, rad=R_ANT - CAP):
    r = np.asarray(r, float); th = np.broadcast_to(np.asarray(th, float), r.shape)
    return np.column_stack([r * np.cos(th), r * np.sin(th), -R_ANT + np.sqrt(rad ** 2 - r ** 2)])


def spiral(r0, r1):
    """Спираль от радиуса r0 к r1 (угол убывает от плоского меридиана); точки через BUB_STEP по дуге."""
    turns = abs(r1 - r0) / BUB_PITCH; phi = np.linspace(0, 2 * np.pi * turns, int(turns * 4000) + 2)
    r = r0 + (r1 - r0) * phi / phi[-1]
    ds = np.hypot(np.diff(r), r[:-1] * np.diff(phi)); sarc = np.concatenate([[0], np.cumsum(ds)])
    k = np.searchsorted(sarc, np.arange(0, sarc[-1], BUB_STEP))
    return r[k], TH_AX - phi[k], phi[k] / (2 * np.pi)


def build_bubbles():
    B = {}
    r, th, q = spiral(L.R * 0.995, 0.0); B['post'] = dict(P=bottom_xyz(r, th, 0.006), r=r, th=th, q=q, k=7.5)
    rows = []
    for fr in np.linspace(0.12, 0.88, 5):
        n = int(2 * np.pi * L.R / BUB_STEP); th = TH_AX - np.arange(n) * 2 * np.pi / n
        bt = bottom_xyz(np.full(n, L.R), th); tp = cap_xyz(np.full(n, L.R), th, R_LT)
        rows.append((bt + (tp - bt) * fr, th))
    B['side'] = dict(P=np.vstack([p for p, _ in rows]), r=np.full(sum(len(t) for _, t in rows), L.R), th=np.concatenate([t for _, t in rows]), k=2.0)
    r, th, q = spiral(0.0, R_CAPD); B['cap'] = dict(P=cap_xyz(r, th, R_ANT - CAP + 0.006), r=r, th=th, q=q, k=7.0)
    psi = math.asin(R_CAPD / R_ANT); n = int(2 * HALF_INC * R_CAPD / BUB_STEP) + 1; P, T = [], []
    for row, fr in enumerate(np.linspace(0.85, 0.15, 4)):
        th = TH_INC - HALF_INC + 2 * HALF_INC * np.linspace(0, 1, n)[:: 1 if row % 2 == 0 else -1]; d = CAP * fr
        P.append(C + (R_ANT - d) * np.column_stack([np.sin(psi) * np.cos(th), np.sin(psi) * np.sin(th), np.full(n, np.cos(psi))])); T.append(th)
    B['inc'] = dict(P=np.vstack(P), r=np.full(4 * n, R_CAPD), th=np.concatenate(T), k=1.5)
    for k_, b in B.items():
        N = len(b['P']); kk = b['k']; i = np.arange(N)
        b['u'] = np.log1p(i / N * np.expm1(kk)) / kk        # момент импульса i в долях этапа: сначала медленно, потом быстрее
    return B


BUB = build_bubbles()


def fired(k_, f):
    """Сколько пузырьков этапа уже поставлено и «возраст» каждого в кадрах."""
    b = BUB[k_]
    if f < START[k_]: return 0, None
    u = prog(k_, f); n = len(b['P']) if after(k_, f) else int(np.searchsorted(b['u'], u, side='right'))
    age = f - (START[k_] + b['u'][:n] * LEN[k_])
    return n, age


def laser_state(f):
    """Положение фокуса (последний импульс) или None, и прогресс резов."""
    pr = {k: prog(k, f) for k in ('post', 'side', 'cap', 'inc')}
    spot = None
    for k_ in ('post', 'side', 'cap', 'inc'):
        if during(k_, f):
            n, _ = fired(k_, f); spot = BUB[k_]['P'][max(n - 1, 0)]
            if 'q' in BUB[k_]: pr[k_ + '_q'] = BUB[k_]['q'][max(n - 1, 0)]
    return spot, pr


# ================================================================ построение кадра
_cache = {'W': None}


def build_static(W):
    th0, th1 = wedge_range(W)
    e0, e1 = wedge_range(max(W - 0.8, 0.0)) if W > 0.01 else (th0, th1)
    for ob, prof in anat_objs:
        V, P, Mt, _, _ = revolve(prof, th0, th1, 180)
        set_mesh(ob, V, P, Mt, sharp=40)
    V, P, Mt, _, _ = revolve(CORNEA_PROF, th0, th1, 180, caps=False); set_mesh(cornea_obj, V, P, Mt, sharp=40)
    for ob, prof in layer_objs:
        V, P, Mt, _, _ = revolve(prof, th0, th1, 2)
        ng = P[2]; ob.hide_render = not ng
        set_mesh(ob, V, (np.zeros((0, 4), int), np.zeros((0, 3), int), ng), np.zeros(len(ng), int), smooth=False)
    for ob, prof in ((glass_obj, glass_prof), (house_obj, house_prof)):
        V, P, Mt, _, _ = revolve(prof, th0, th1, 120); set_mesh(ob, V, P, Mt, sharp=40)
    # слои пузырьков (OBL): геометрия + координаты для масок
    rr = np.linspace(0, L.R, 72)
    V, P, Mt, ii, tt = revolve(lambda th: lent_bottom(th, rr), e0, e1, 180, closed=False)
    _cache['post'] = (V, P, Mt, rr[ii], tt)
    lv = np.linspace(0, 1, 6)
    def side_prof(th):
        bt = lent_bottom(th, np.array([L.R]), 0)[0]; tp = sphere_pts(R_LT, [L.R])[0]
        return np.array([bt + (tp - bt) * k for k in lv]) + np.array([0.004, 0])
    V, P, Mt, ii, tt = revolve(side_prof, e0, e1, 180, closed=False)
    _cache['side'] = (V, P, Mt, lv[ii], tt)
    rc = np.linspace(0, R_CAPD, 84)
    V, P, Mt, ii, tt = revolve(sphere_pts(R_ANT - CAP + 0.004, rc), e0, e1, 180, closed=False)
    _cache['cap'] = (V, P, Mt, rc[ii], tt)
    psi = math.asin(R_CAPD / R_ANT); dd = np.linspace(CAP, 0.0, 6)
    prof = np.column_stack([(R_ANT - dd) * math.sin(psi), -R_ANT + (R_ANT - dd) * math.cos(psi)])
    V, P, Mt, ii, tt = revolve(prof, TH_INC - HALF_INC, TH_INC + HALF_INC, 360, closed=False)
    _cache['inc'] = (V, P, Mt, ii / (len(dd) - 1), tt)
    V, P, Mt, _, _ = revolve(lent_profile, e0, e1, 180)
    Vl = V; thk = lent_thk(Vl)
    _cache['lent'] = (Vl, P, Mt, thk)
    _cache['W'] = W


def lent_thk(V):
    rh = np.hypot(V[:, 0], V[:, 1]); k = np.minimum(1.0, L.R * 0.9999 / np.maximum(rh, 1e-9))
    return np.nan_to_num(L.thickness(V[:, 0] * k, V[:, 1] * k), nan=L.tmin)


V_FULL, P_FULL, M_FULL, _, _ = revolve(lent_profile, 0, 2 * np.pi, 180)
THK_FULL = lent_thk(V_FULL)


def spiral_time(r, th, pitch, th_start, inward, R0):
    fr = ((th_start - th) / (2 * np.pi)) % 1.0
    base = (R0 - r) / pitch if inward else r / pitch
    return fr + np.round(base - fr)


def update_masks(f, pr):
    for k in ('post', 'side', 'cap', 'inc'):
        V, P, Mt, a, tt = _cache[k]
        if k == 'post':
            qv = spiral_time(a, tt, BUB_PITCH, TH_AX, True, L.R); cut = np.clip((pr.get('post_q', 0 if pr['post'] <= 0 else 1e9) - qv) / 0.3 + 0.5, 0, 1)
            if pr['post'] >= 1: cut[:] = 1
            clear = spat_cleared('post', f, a * np.cos(tt), a * np.sin(tt))
        elif k == 'side':
            cut = np.clip((pr['side'] * 1.05 - a) / 0.05 + 0.5, 0, 1); clear = np.full(len(a), 1.0 if after('spat_post', f) else (0.6 * prog('spat_post', f)))
        elif k == 'cap':
            qv = spiral_time(a, tt, BUB_PITCH, TH_AX, False, R_CAPD); cut = np.clip((pr.get('cap_q', 0 if pr['cap'] <= 0 else 1e9) - qv) / 0.3 + 0.5, 0, 1)
            if pr['cap'] >= 1: cut[:] = 1
            clear = spat_cleared('ant', f, a * np.cos(tt), a * np.sin(tt))
        else:
            fr = (tt - (TH_INC - HALF_INC)) / (2 * HALF_INC)
            cut = np.clip((pr['inc'] * 1.05 - (1 - a) * 0.75 - fr * 0.25) / 0.06 + 0.5, 0, 1) if pr['inc'] < 1 else np.ones(len(a))
            clear = np.zeros(len(a))
        if f >= START['close']:   # пузырьки (OBL) со временем рассасываются — лентикула видна лучше
            cut = cut * (1 - 0.55 * ss(prog('close', f)))
        set_mesh(obl[k], V, P, Mt, attrs={'cut': cut, 'clear': clear}, smooth=False)
        obl[k].hide_render = bool(cut.max() <= 0.01)


# цветные меридианы на лентикуле: плоский (ось, ось+180°) — зелёный, крутой (ось±90°) — красный
def build_meridians():
    Vs_, Q, T, Mi = [], [], [], []; off = 0
    for j in range(4):
        th = TH_AX + j * np.pi / 2
        pr_ = lent_profile(th)
        pts = np.array([to3(r_, z_, th) for r_, z_ in pr_])
        V_, (q_, t_, _), _ = tube(pts, 0.011, 8, cap_tip=False)
        Vs_.append(V_); Q.append(q_ + off); T.append(t_ + off); off += len(V_)
    mats = np.concatenate([np.full(len(q), j % 2) for j, q in enumerate(Q)] + [np.full(len(t), j % 2) for j, t in enumerate(T)])
    return np.vstack(Vs_), (np.vstack(Q), np.vstack(T), []), mats


MER_V, MER_P, MER_M = build_meridians()


def update_bubbles(f, W):
    if f < START['post'] or f >= START['forc_in']:
        bub_obj.hide_render = True; return
    th0, th1 = wedge_range(max(W - 1.2, 0.0)) if W > 0.01 else (0.0, 2 * np.pi)
    Ps, rads, glows = [], [], []
    fade = 1 - 0.45 * ss(prog('close', f))
    for k_ in ('post', 'side', 'cap', 'inc'):
        n, age = fired(k_, f)
        if n == 0: continue
        b = BUB[k_]; P = b['P'][:n]; th = b['th'][:n]
        keep = (((th - th0) % (2 * np.pi)) <= (th1 - th0) + 1e-9) if W > 0.01 else np.ones(n, bool)
        rad = BUB_R * (0.45 + 0.55 * np.clip(age / 2.0, 0, 1)) * fade
        if k_ in ('post', 'cap'):
            clr = spat_cleared('post' if k_ == 'post' else 'ant', f, P[:, 0], P[:, 1]); rad = rad * (1 - clr)
        elif k_ == 'side':
            rad = rad * (1 - ss(prog('spat_post', f)))
        keep &= rad > 0.002
        Ps.append(P[keep]); rads.append(rad[keep]); glows.append(np.exp(-np.maximum(age[keep], 0) / 2.5))
    if not Ps or sum(len(p) for p in Ps) == 0:
        bub_obj.hide_render = True; return
    V = np.vstack(Ps); me = bub_obj.data; me.clear_geometry()
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.update()
    for name, arr in (('rad', np.concatenate(rads)), ('glow', np.concatenate(glows))):
        at = me.attributes.new(name=name, type='FLOAT', domain='POINT'); at.data.foreach_set('value', arr.astype(np.float32))
    me.update(); bub_obj.hide_render = False


def place(obj, origin, x, y, z):
    obj.matrix_world = Matrix(((x[0], y[0], z[0], origin[0]), (x[1], y[1], z[1], origin[1]), (x[2], y[2], z[2], origin[2]), (0, 0, 0, 1)))


DISPLAY_LIFT = 3.4
DISP_C0 = np.array([0, 0, -0.1])
G_REST = to3(*lent_profile(TH_INC)[33], TH_INC) * 0.5 + to3(*lent_profile(TH_INC)[37], TH_INC) * 0.5   # край у разреза, середина толщины


EXAG_SHOW = 8.0   # в конце толщина лентикулы плавно увеличивается ×3 → ×8, чтобы седловидная форма читалась при облёте


def thick_scale(V, k):
    q = np.asarray(V) - C; rad = np.linalg.norm(q, axis=1, keepdims=True)
    return C + q / rad * (R_LT + (rad - R_LT) * k)


def display_pose(V, f=None):
    """Извлечённая лентикула в пинцете: над глазом, горизонтально (камера облетает её вокруг)."""
    if f is not None and f >= START['show']:
        V = thick_scale(V, 1 + (EXAG_SHOW / A.exag - 1) * ss((prog('show', f) - 0.45) / 0.2))
    return (np.asarray(V) - DISP_C0) + np.array([0, 0, DISPLAY_LIFT])


def forceps_display():
    tip = display_pose(G_REST[None])[0]
    x = D_INC * math.cos(math.radians(12)) + EZ * math.sin(math.radians(12)); z = EZ - x * np.dot(EZ, x); z /= np.linalg.norm(z)
    return tip, x, np.cross(z, x), z


def frame_state(f):
    W = W_of(f)
    if _cache['W'] != W:
        build_static(W); _cache['W'] = W
    spot, pr = laser_state(f)
    update_masks(f, pr)
    # контактная линза
    dz = dock_of(f)
    show_glass = during('dock', f) or during('undock', f) or (during('post', f) and f < START['post'] + 10)
    glass_obj.location = (0, 0, dz); glass_obj.hide_render = bool(dz > 13.5 or not show_glass)   # на крупных планах лазера не мешает
    house_obj.hide_render = True
    # лазер
    on = spot is not None
    for ob in (beam_obj, spot_obj, halo_obj):
        ob.hide_render = not on
        if on: ob.location = tuple(spot)
    # пузырьки и меридианы
    update_bubbles(f, W)
    # лентикула
    a_l = ss(prog('form', f) / 0.15)
    lent_obj.hide_render = bool(a_l <= 0.001)
    LENT_BSDF.inputs['Alpha'].default_value = float(a_l)
    if f >= START['forc_in']:
        if f < START['show']:
            fs = forceps_state(f); pull = (fs[0] - S_GRIP) if during('pull', f) else 0.0
            V = lent_deform(V_FULL, pull) if pull > 0 else V_FULL
        else:
            k = ss((prog('show', f) - 0.05) / 0.4)
            V = lent_deform(V_FULL, P_TOTAL) * (1 - k) + display_pose(V_FULL, f) * k
        set_mesh(lent_obj, V, P_FULL, M_FULL, attrs={'thk': THK_FULL}, sharp=35)
    else:
        Vl, P, Mt, thk = _cache['lent']; set_mesh(lent_obj, Vl, P, Mt, attrs={'thk': thk}, sharp=35)
    mer_obj.hide_render = f < START['post']
    if not mer_obj.hide_render:
        if f < START['forc_in'] or not (during('pull', f) or f >= START['show']): Vm = MER_V
        elif during('pull', f): Vm = lent_deform(MER_V, forceps_state(f)[0] - S_GRIP)
        else:
            k = ss((prog('show', f) - 0.05) / 0.4); Vm = lent_deform(MER_V, P_TOTAL) * (1 - k) + display_pose(MER_V, f) * k
        set_mesh(mer_obj, Vm, MER_P, MER_M, sharp=0)
    # шпатель
    pl, Lin, psi, vis = spat_state(f)
    spat_obj.hide_render = not vis
    if vis:
        pts, rad, _, _ = spat_geometry(pl, Lin, psi)
        Vt, Pt, Mt = tube(pts, rad, 12); set_mesh(spat_obj, Vt, Pt, Mt, sharp=60)
    # пинцет
    s, gap, vis, away = forceps_state(f)
    for ob, _ in jaws: ob.hide_render = not vis
    if vis:
        o, x, y, z = forceps_frame(s)
        if f >= START['show']:   # пинцет держит лентикулу и переносит её в положение показа
            k = ss((prog('show', f) - 0.05) / 0.4); o2, x2, y2, z2 = forceps_display()
            o = o * (1 - k) + o2 * k; x = x * (1 - k) + x2 * k; x /= np.linalg.norm(x); z = z * (1 - k) + z2 * k
            z = z - x * np.dot(z, x); z /= np.linalg.norm(z); y = np.cross(z, x)
        place(forceps, o + x * away, x, y, z)
        a = math.atan(gap / 2 / FXS[-1])
        for ob, zs_ in jaws:
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = Matrix.Translation((FXS[-1], 0, 0)) @ Matrix.Rotation(zs_ * a, 4, 'Y') @ Matrix.Translation((-FXS[-1], 0, 0))
    return dict(W=W, spot=spot, pr=pr)


# ================================================================ камера и свет
LAYER_T = to3(1.75, -0.32, TH_C - math.radians(45))
AXD = A.axis
z_mid = lambda r, th: float(bottom_xyz(np.array([r]), th)[0, 2] * 0.5 + cap_xyz(np.array([r]), th, R_LT)[0, 2] * 0.5)
P_START = to3(L.R * 0.93, z_mid(L.R * 0.93, TH_AX - 0.08), TH_AX - 0.08)
FLAT_T = to3(1.75, z_mid(1.75, TH_AX), TH_AX); STEEP_T = to3(1.75, z_mid(1.75, TH_AX + np.pi / 2), TH_AX + np.pi / 2)
INC_T = tuple(np.array([R_CAPD * 0.8 * math.cos(TH_INC), R_CAPD * 0.8 * math.sin(TH_INC), -0.6]))
CTR = (0, 0, -0.45)
CAM = [  # (этап, доля этапа), азимут, высота, расстояние, цель, up: 0 — ось глаза горизонтально, 1 — вверх
    (('intro', 0), dict(az=AXD + 63, el=8, d=92, t=(0, 0, -14.5), up=0)), (('zoom', 0), dict(az=AXD + 33, el=6, d=90, t=(0, 0, -14.5), up=0)),
    (('layers', 0), dict(az=AXD + 85, el=14, d=7.0, t=tuple(LAYER_T), up=1)), (('dock', 0), dict(az=AXD + 82, el=15, d=7.6, t=tuple(LAYER_T), up=1)),
    # крупно: первые импульсы по одному у края лентикулы
    (('post', 0), dict(az=AXD - 4, el=34, d=3.0, t=tuple(P_START), up=1)), (('post', 0.42), dict(az=AXD - 8, el=36, d=3.4, t=tuple(P_START), up=1)),
    (('post', 0.78), dict(az=AXD + 40, el=12, d=8.6, t=CTR, up=1)),
    (('side', 0), dict(az=AXD + 45, el=8, d=8.0, t=CTR, up=1)), (('cap', 0), dict(az=AXD + 45, el=10, d=6.8, t=(0, 0, -0.3), up=1)),
    (('cap', 0.7), dict(az=AXD + 40, el=13, d=8.6, t=CTR, up=1)),
    (('inc', 0), dict(az=A.inc_angle - 10, el=26, d=7.5, t=INC_T, up=1)), (('undock', 0), dict(az=A.inc_angle - 15, el=24, d=8.5, t=INC_T, up=1)),
    # форма: профиль по каждому меридиану сбоку, с увеличением
    (('form', 0), dict(az=AXD + 45, el=10, d=8.8, t=CTR, up=1)),
    (('form', 0.18), dict(az=AXD + 89, el=2, d=4.4, t=tuple(FLAT_T), up=1)), (('form', 0.44), dict(az=AXD + 87, el=3, d=4.6, t=tuple(FLAT_T), up=1)),
    (('form', 0.6), dict(az=AXD + 1, el=2, d=4.4, t=tuple(STEEP_T), up=1)), (('form', 0.86), dict(az=AXD + 3, el=3, d=4.6, t=tuple(STEEP_T), up=1)),
    (('close', 0), dict(az=AXD + 30, el=12, d=9.5, t=CTR, up=1)),
    (('spat_in', 0), dict(az=210, el=50, d=16, t=(-0.5, 0.8, -0.4), up=1)), (('spat_ant', 0), dict(az=212, el=50, d=16, t=(-0.5, 0.8, -0.4), up=1)),
    (('spat_post', 0), dict(az=214, el=50, d=16, t=(-0.5, 0.8, -0.4), up=1)), (('spat_out', 0), dict(az=215, el=50, d=16, t=(-0.5, 0.8, -0.4), up=1)),
    (('forc_in', 0), dict(az=215, el=46, d=14.5, t=(-1.0, 1.7, -0.3), up=1)), (('pull', 0), dict(az=215, el=44, d=14.5, t=(-1.0, 1.7, -0.3), up=1)),
    (('show', 0), dict(az=220, el=32, d=22, t=(-2.9, 4.6, 1.8), up=1)),
    # лентикула в пинцете: облёт сбоку — видна седловидная форма и цветные меридианы
    (('show', 0.42), dict(az=215, el=4, d=10.5, t=(0, 0, DISPLAY_LIFT - 0.15), up=1)),
    (None, dict(az=215 + 180, el=-3, d=10.5, t=(0, 0, DISPLAY_LIFT - 0.15), up=1))]


def cam_pose(f):
    keys = [((START[n[0]] + n[1] * LEN[n[0]]) if n else NF + 1, p) for n, p in CAM]
    for (f0, p0), (f1, p1) in zip(keys[:-1], keys[1:]):
        if f < f1 or f1 == NF + 1:
            k = float(ss((f - f0) / max(1, f1 - f0))); break
    lerp = lambda a, b: a + (b - a) * k
    az, el = math.radians(lerp(p0['az'], p1['az'])), math.radians(lerp(p0['el'], p1['el']))
    d = math.exp(lerp(math.log(p0['d']), math.log(p1['d'])))
    kt = float(ss(min(1.0, k * 1.5))) if p1['d'] < 0.3 * p0['d'] else k
    t = np.array(p0['t']) + (np.array(p1['t']) - np.array(p0['t'])) * kt
    upb = lerp(p0['up'], p1['up'])
    h = np.array([math.cos(az), math.sin(az), 0.0])
    up = np.array([h[1], -h[0], 0.0]) * (1 - upb) + EZ * upb
    pos = t + d * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    zc = pos - t; zc /= np.linalg.norm(zc); xc = np.cross(up, zc); xc /= np.linalg.norm(xc); yc = np.cross(zc, xc)
    return pos, xc, yc, zc, d, t


cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 50; cam_data.sensor_width = 36; cam_data.clip_start = 0.05; cam_data.clip_end = 2000
cam = bpy.data.objects.new('Camera', cam_data); scene.collection.objects.link(cam); scene.camera = cam
LIGHTS = []
for name, off, en, size, col in (('Key', (-0.55, 0.65, 0.55), 2.6, 0.5, (1, 0.97, 0.93)), ('Rim', (0.6, 0.55, -0.6), 2.2, 0.4, (0.8, 0.9, 1.0)),
                                 ('Fill', (0.8, -0.25, 0.55), 0.8, 0.8, (1, 1, 1))):
    ld = bpy.data.lights.new(name, 'AREA'); ld.color = col
    lo = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo)
    try: lo.visible_glossy = False; lo.visible_camera = False   # без огромных бликов-«зеркал» на роговице
    except Exception: pass
    LIGHTS.append((lo, np.array(off) / np.linalg.norm(off), en, size))


def set_camera(f):
    pos, xc, yc, zc, d, t = cam_pose(f)
    place(cam, pos, xc, yc, zc)
    for lo, off, en, size in LIGHTS:
        p = t + d * (off[0] * xc + off[1] * yc + off[2] * zc)
        zz = p - t; zz /= np.linalg.norm(zz); xx = np.cross(EZ if abs(zz[2]) < 0.95 else np.array([1.0, 0, 0]), zz); xx /= np.linalg.norm(xx)
        place(lo, p, xx, np.cross(zz, xx), zz)
        lo.data.energy = en * d * d * 9.0; lo.data.size = size * d
    return d


world = bpy.data.worlds.new('World'); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = world.node_tree.nodes.get('Background') or world.node_tree.nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.20, 0.22, 0.26, 1.0); bg.inputs['Strength'].default_value = 1.0

# ================================================================ рендер
r = scene.render; r.resolution_x, r.resolution_y = A.width, A.height; r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.film_transparent = True
if A.engine == 'cycles':
    scene.render.engine = 'CYCLES'
    cy = scene.cycles; cy.samples = A.samples; cy.use_denoising = True; cy.device = 'CPU'
    cy.transparent_max_bounces = 32; cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 2
    cy.caustics_reflective = False; cy.caustics_refractive = False; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03
    scene.render.use_persistent_data = True
else:
    eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in eng else 'BLENDER_EEVEE_NEXT'
    try: scene.eevee.taa_render_samples = A.samples
    except Exception: pass
try: scene.view_settings.view_transform = 'Standard'
except Exception: pass
scene.frame_start, scene.frame_end = 1, NF
scene.render.fps = int(round(A.fps))

# ================================================================ подписи (накладываются после рендера, PIL)
from PIL import Image, ImageDraw, ImageFont
FONT_R = A.font or next((p for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans.ttf',
                                     '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf', 'C:/Windows/Fonts/arial.ttf') if os.path.exists(p)), None)
FONT_B = (FONT_R.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf') if FONT_R and os.path.exists(FONT_R.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')) else FONT_R)
SC = A.height / 720.0
fnt = lambda p, s: ImageFont.truetype(p, int(round(s * SC))) if p else ImageFont.load_default()
F_TITLE, F_SUB, F_LAB, F_NOTE = fnt(FONT_B, 32), fnt(FONT_R, 21), fnt(FONT_R, 19), fnt(FONT_R, 15)
ACC = (79, 195, 247)


def fmt(x, nd=1): return f'{x:.{nd}f}'.replace('.', ',').replace('-', '−')


def sp(r, z, up=True):  # точка на плоскости горизонтального разреза (вступление)
    th = TH_C - np.pi / 2 if up else TH_C + np.pi / 2
    return to3(r, z, th) + hc * 0.05


def on_layer(rh, d):
    th = TH_C - math.radians(45); psi = math.asin(rh / R_ANT)
    p = cornea_pt(np.array([psi]), np.array([d]))[0]; return to3(p[0], p[1], th) + np.array([math.cos(th + np.pi / 2), math.sin(th + np.pi / 2), 0]) * 0.01


psi24 = math.asin(2.4 / R_ANT); cm = cornea_pt(np.array([psi24]), T_cornea(psi24) / 2)[0]
z_ch = -17.0; r_ch = math.sqrt(((CHOR[0] + CHOR[1]) / 2) ** 2 - (z_ch - ZS) ** 2)
z_rt = -19.5; r_rt = math.sqrt(((RET[0] + RET[1]) / 2) ** 2 - (z_rt - ZS) ** 2)
z_sc = -11.0; r_sc = math.sqrt((RS - TS / 2) ** 2 - (z_sc - ZS) ** 2)
psi_l = math.asin(1.6 / R_ANT); T16 = float(T_cornea(psi_l))
ANAT_SEG = ('intro', 'zoom', 0.15)
LABELS = [
    # текст, (сегмент начала, сегмент конца, доля конца), якорь (3D или функция кадра), подпись: 3D-точка или смещение в пикселях
    ('Роговица', ANAT_SEG, sp(cm[0], cm[1]), sp(5.6, 6.6)),
    ('Передняя камера', ANAT_SEG, sp(2.0, -2.0), sp(9.6, 3.6)),
    ('Радужка', ANAT_SEG, sp(4.0, -3.55), sp(12.6, 0.2)),
    ('Цилиарное тело', ANAT_SEG, sp(5.15, -4.6), sp(14.4, -7.4)),
    ('Сосудистая оболочка', ANAT_SEG, sp(r_ch, z_ch), sp(15.2, -20.0)),
    ('Зрачок', ANAT_SEG, sp(0.0, -3.62, False), sp(7.2, 3.2, False)),
    ('Хрусталик', ANAT_SEG, sp(2.2, -5.8, False), sp(13.4, -4.2, False)),
    ('Склера', ANAT_SEG, sp(r_sc, z_sc, False), sp(15.4, -11.5, False)),
    ('Сетчатка', ANAT_SEG, sp(r_rt, z_rt, False), sp(15.2, -18.5, False)),
    ('Стекловидное тело', ANAT_SEG, sp(4.0, -15.5, False), sp(12.0, -25.5, False)),
    ('Зрительный нерв', ANAT_SEG, NERVE0 + a_n * 6.5, (0, 95)),
    ('Эпителий, ≈50 мкм', ('layers', 'dock', 0.35), on_layer(1.6, EPI / 2), (-330, -105)),
    ('Боуменова мембрана', ('layers', 'dock', 0.35), on_layer(1.6, EPI + BOW / 2), (-330, -45)),
    ('Строма', ('layers', 'dock', 0.35), on_layer(1.6, 0.30), (-330, 20)),
    ('Десцеметова мембрана и эндотелий', ('layers', 'dock', 0.35), on_layer(1.6, T16 - DE / 2), (-330, 95)),
    ('Контактная линза (вакуум)', ('dock', 'post', 0.5), lambda f: to3(*sphere_pts(R_ANT + 0.9, [3.6])[0], TH_C + np.pi / 2) + np.array([0, 0, dock_of(f)]), (190, -70)),
    ('Фокус лазера', ('post', 'inc', 1.0), lambda f: laser_state(f)[0], (170, -120)),
    ('Задняя поверхность лентикулы', ('post', 'side', 1.0), lambda f: to3(*lent_bottom(TH_C - math.radians(45), np.array([1.6]))[0], TH_C - math.radians(45)), (-300, 110)),
    ('Граница колпачка, ' + fmt(A.cap, 0) + ' мкм', ('cap', 'inc', 1.0), to3(*sphere_pts(R_ANT - CAP, [2.6])[0], TH_C - math.radians(45)), (-300, -95)),
    ('Разрез доступа ' + fmt(A.inc_width) + ' мм', ('inc', 'spat_out', 1.0), C + R_ANT * np.array([R_CAPD / R_ANT * math.cos(TH_INC), R_CAPD / R_ANT * math.sin(TH_INC), math.sqrt(1 - (R_CAPD / R_ANT) ** 2)]), (-210, -90)),
    ('центр ' + fmt(L.t0, 0) + ' мкм', ('close', 'spat_in', 1.0), to3(0, -R_ANT + R_LT - A.exag * L.t0 / 2000, 0), (40, -150)),
    ('край ' + fmt(L.t_steep, 0) + ' мкм — крутой меридиан', ('close', 'spat_in', 1.0), to3(*lent_profile(math.radians(A.axis + 90) + np.pi)[33], math.radians(A.axis + 90) + np.pi), (200, 60)),
    ('край ' + fmt(L.t_flat, 0) + ' мкм — плоский меридиан', ('close', 'spat_in', 1.0), to3(*lent_profile(math.radians(A.axis) + np.pi)[33], math.radians(A.axis) + np.pi), (-200, 90)),
    ('Шпатель', ('spat_in', 'spat_out', 1.0), lambda f: spat_geometry(*spat_state(f)[:3])[2] + spat_geometry(*spat_state(f)[:3])[3] * 3.5, (120, -90)),
    ('Пинцет', ('forc_in', 'show', 0.3), lambda f: (lambda o, x, y, z: o + x * (3.5 + forceps_state(f)[3]))(*forceps_frame(forceps_state(f)[0])), (110, -90)),
    ('Лентикула', ('pull', 'pull', 1.0), lambda f: lent_deform(np.array([to3(*lent_profile(TH_INC)[15], TH_INC + np.pi)]), (forceps_state(f)[0] - S_GRIP))[0], (-160, 90)),
    ('Лентикула извлечена целиком', ('show', 'show', 1.0), lambda f: display_pose(np.array([[0, 0, -R_ANT + R_LT]]), f)[0], (-250, -150)),
    ('край ' + fmt(L.t_flat, 0) + ' мкм', ('show', 'show', 1.0), lambda f: display_pose(np.array([to3(*lent_profile(math.radians(A.axis))[33], math.radians(A.axis))]), f)[0] if prog('show', f) > 0.55 else None, (170, -40)),
    ('край ' + fmt(L.t_steep, 0) + ' мкм', ('show', 'show', 1.0), lambda f: display_pose(np.array([to3(*lent_profile(math.radians(A.axis + 90))[33], math.radians(A.axis + 90))]), f)[0] if prog('show', f) > 0.55 else None, (-150, 90)),
]
TITLES = {
    'intro': ('Анатомия глаза', 'горизонтальный разрез'), 'zoom': ('Анатомия глаза', 'горизонтальный разрез'),
    'layers': ('Роговица', 'слои роговицы в разрезе'), 'dock': ('Шаг 1. Фиксация глаза', 'изогнутая контактная линза, вакуум'),
    'post': ('Шаг 2. Задняя поверхность лентикулы', 'фемтосекундный лазер: спираль от периферии к центру'),
    'side': ('Шаг 3. Боковой рез лентикулы', 'по краю оптической зоны ' + fmt(L.oz) + ' мм'),
    'cap': ('Шаг 4. Передняя поверхность — граница колпачка', 'глубина ' + fmt(A.cap, 0) + ' мкм, спираль от центра к периферии, Ø ' + fmt(A.cap_d) + ' мм'),
    'inc': ('Шаг 5. Разрез доступа', fmt(A.inc_width) + ' мм, на ' + fmt(A.inc_angle, 0) + '°'),
    'undock': ('Лентикула сформирована', 'вакуум снят, контактная линза отведена'),
    'form': ('Профиль лентикулы', 'зелёный — плоский меридиан, красный — крутой: седловидная форма'),
    'close': ('Форма лентикулы', 'торическая: Sph ' + ('+' if L.sph >= 0 else '') + fmt(L.sph, 2) + ' / Cyl ' + fmt(L.cyl, 2) + ' × ' + fmt(L.axis, 0) + '°'),
    'spat_in': ('Шаг 6. Разделение слоёв шпателем', 'сначала передняя поверхность'), 'spat_ant': ('Шаг 6. Разделение слоёв шпателем', 'сначала передняя поверхность'),
    'spat_post': ('Шаг 6. Разделение слоёв шпателем', 'затем задняя поверхность'), 'spat_out': ('Шаг 6. Разделение слоёв шпателем', 'затем задняя поверхность'),
    'forc_in': ('Шаг 7. Извлечение лентикулы', 'пинцет захватывает край лентикулы'),
    'pull': ('Шаг 7. Извлечение лентикулы', 'лентикула выходит через разрез ' + fmt(A.inc_width) + ' мм'),
    'show': ('Лентикула извлечена', 'проверка целостности краёв'),
}
INFO = ('Лентикула: Sph ' + ('+' if L.sph >= 0 else '') + fmt(L.sph, 2) + ' / Cyl ' + fmt(L.cyl, 2) + ' × ' + fmt(L.axis, 0) + '°, ОЗ ' + fmt(L.oz) + ' мм',
        'центр ' + fmt(L.t0, 0) + ' мкм, край ' + fmt(L.t_flat, 0) + ' / ' + fmt(L.t_steep, 0) + ' мкм; колпачок ' + fmt(A.cap, 0) + ' мкм')
NOTE = 'Схема: толщина лентикулы ×' + fmt(A.exag, 0 if A.exag == int(A.exag) else 1) + ', шаг спирали увеличен, ИК-луч показан условно'


def label_alpha(spec, f, fade=10):
    s0, s1, k1 = spec
    a, b = START[s0], START[s1] + LEN[s1] * k1
    return float(np.clip(min(f - a, b - f) / fade, 0, 1))


def proj(p):
    co = world_to_camera_view(scene, cam, Vector(tuple(map(float, p))))
    return np.array([co.x * A.width, (1 - co.y) * A.height]), co.z > 0


def collect_labels(f):
    out = []
    if A.no_pointers: return out
    for text, spec, anc, tp in LABELS:
        al = label_alpha(spec, f)
        if al <= 0: continue
        p3 = anc(f) if callable(anc) else anc
        if p3 is None: continue
        a2, ok = proj(p3)
        if not ok: continue
        t2 = (a2 + np.array(tp) * SC) if (isinstance(tp, tuple) and len(tp) == 2) else proj(tp)[0]
        out.append((text, a2, t2, al))
    return out


_BG = {}


def background():
    if 'img' not in _BG:
        yy, xx = np.mgrid[0:A.height, 0:A.width]
        d = np.hypot((xx - A.width * 0.5) / A.width, (yy - A.height * 0.46) / A.height * 0.75) * 1.6
        c0, c1 = np.array([28, 40, 60]), np.array([7, 10, 17])
        g = np.clip(d, 0, 1)[..., None]
        _BG['img'] = Image.fromarray((c0 * (1 - g) + c1 * g).astype(np.uint8), 'RGB').convert('RGBA')
    return _BG['img'].copy()


def text_box(dr, xy, text, font, al, anchor='mm', pad=(9, 5)):
    x0, y0, x1, y1 = dr.textbbox(xy, text, font=font, anchor=anchor)
    box = (x0 - pad[0] * SC, y0 - pad[1] * SC, x1 + pad[0] * SC, y1 + pad[1] * SC)
    dr.rounded_rectangle(box, radius=6 * SC, fill=(9, 15, 25, int(200 * al)), outline=(*ACC, int(150 * al)), width=1)
    dr.text(xy, text, font=font, fill=(255, 255, 255, int(255 * al)), anchor=anchor)
    return box


def compose(raw_path, f, labels):
    im = Image.open(raw_path).convert('RGBA'); base = background(); base.alpha_composite(im)
    clean = base.convert('RGB')
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for text, a2, t2, al in labels:
        x0, y0, x1, y1 = dr.textbbox(tuple(t2), text, font=F_LAB, anchor='mm')
        m = 14 * SC; dxm = max(0, m - x0) - max(0, x1 - (A.width - m)); dym = max(0, 120 * SC - y0) - max(0, y1 - (A.height - 90 * SC))
        t2 = (t2[0] + dxm, t2[1] + dym); x0, x1, y0, y1 = x0 + dxm, x1 + dxm, y0 + dym, y1 + dym
        pad = 9 * SC; bx = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
        cx = min(max(a2[0], bx[0]), bx[2]); cy = min(max(a2[1], bx[1]), bx[3])
        dr.line([tuple(a2), (cx, cy)], fill=(255, 255, 255, int(190 * al)), width=max(1, int(2 * SC)))
        rr_ = 4.5 * SC; dr.ellipse([a2[0] - rr_, a2[1] - rr_, a2[0] + rr_, a2[1] + rr_], fill=(*ACC, int(255 * al)), outline=(255, 255, 255, int(220 * al)))
        text_box(dr, tuple(t2), text, F_LAB, al)
    n, u = seg_of(f)
    ttl, sub = TITLES[n]
    # плавная смена заголовка: гаснет только если следующий/предыдущий этап с другим заголовком
    idx = [s for s, _ in SEGS].index(n); k = LEN[n]; pos = f - START[n]
    al = 1.0
    if idx > 0 and TITLES[SEGS[idx - 1][0]][0] != ttl: al = min(al, (pos + 1) / 8)
    if idx < len(SEGS) - 1 and TITLES[SEGS[idx + 1][0]][0] != ttl: al = min(al, (k - pos) / 8)
    al = float(np.clip(al, 0, 1))
    x, y = 40 * SC, 30 * SC
    for dx, dy, col in ((2, 2, (0, 0, 0, int(160 * al))), (0, 0, (255, 255, 255, int(255 * al)))):
        dr.text((x + dx * SC, y + dy * SC), ttl, font=F_TITLE, fill=col)
    dr.text((x, y + 46 * SC), sub, font=F_SUB, fill=(190, 214, 235, int(255 * al)))
    dr.line([(x, y + 40 * SC), (x + 70 * SC, y + 40 * SC)], fill=(*ACC, int(255 * al)), width=max(2, int(3 * SC)))
    if f >= START['post']:
        a_i = float(np.clip((f - START['post']) / 12, 0, 1))
        y0 = A.height - 74 * SC
        for i, line in enumerate(INFO):
            dr.text((40 * SC, y0 + i * 25 * SC), line, font=F_SUB if i == 0 else F_LAB, fill=(225, 236, 248, int(235 * a_i)))
        dr.text((A.width - 40 * SC, A.height - 26 * SC), NOTE, font=F_NOTE, fill=(160, 180, 200, int(220 * a_i)), anchor='rs')
    base.alpha_composite(ov)
    return clean, base.convert('RGB')


# ================================================================ основной цикл
OUT = os.path.abspath(A.out.rstrip('/'))
for sub_ in ('raw', 'clean', 'lab'): os.makedirs(os.path.join(OUT, sub_), exist_ok=True)
if A.only_frame is not None: frames = [A.only_frame]
elif A.frames and ',' in A.frames: frames = [int(x) for x in A.frames.split(',')]
elif A.frames: a_, b_ = map(int, A.frames.split('-')); frames = range(a_, b_ + 1, A.step)
else: frames = range(1, NF + 1, A.step)
print(f'кадров в ролике: {NF} ({NF / A.fps:.1f} с при {A.fps:g} к/с); рендер: {len(list(frames))}', flush=True)
if A.save_blend:
    frame_state(START['cap'] + LEN['cap'] // 2); set_camera(START['cap'] + LEN['cap'] // 2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(A.save_blend))
t_all = time.time()
for f in frames:
    t0 = time.time()
    scene.frame_set(f)
    frame_state(f); set_camera(f)
    bpy.context.view_layer.update()
    labels = collect_labels(f); t1 = time.time()
    raw = os.path.join(OUT, 'raw', f'f{f:04d}.png'); r.filepath = raw
    if not A.overlay_only:
        bpy.ops.render.render(write_still=True)
    elif not os.path.exists(raw):
        continue
    clean, lab = compose(raw, f, labels)
    clean.save(os.path.join(OUT, 'clean', f'f{f:04d}.png'))
    if A.text: lab.save(os.path.join(OUT, 'lab', f'f{f:04d}.png'))
    print(f'кадр {f}/{NF} [{seg_of(f)[0]}] {time.time() - t0:.1f} с (сцена {t1 - t0:.1f} с)', flush=True)
print(f'готово за {(time.time() - t_all) / 60:.1f} мин', flush=True)

if A.video and A.only_frame is None and shutil.which('ffmpeg'):
    fr = A.fps / A.step
    def mk(src, dst):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', f'{fr:g}', '-pattern_type', 'glob', '-i', f'{OUT}/{src}/f*.png',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], check=True)
    mk('clean', OUT + '.mp4')
    if A.text: mk('lab', OUT + '_s_podpisyami.mp4')
    gw = min(A.width, 640)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', OUT + '.mp4', '-vf',
                    f'fps=12,scale={gw}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a', OUT + '.gif'], check=True)
    print('видео:', OUT + '.mp4', OUT + '.gif')
