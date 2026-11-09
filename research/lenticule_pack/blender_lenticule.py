"""
blender_lenticule.py — «студийный» рендер 3D-лентикулы в Blender (физически корректное освещение).

Строит ту же модель, что lenticule_model.py (рядом, в одной папке), красит поверхность по толщине,
ставит свет и камеру и крутит лентикулу: сначала оборот по горизонтали, потом оборот по вертикали
(низ проходит быстро) — как в GIF.

Запуск (любой из вариантов):
  A) Blender 4.x/5.x установлен:
       blender -b -P blender_lenticule.py -- --out frames --engine cycles --res 720
  B) только Python:  pip install bpy   (нужен Python той же версии, что у колеса bpy; ~400 МБ)
       python3 blender_lenticule.py --out frames --engine cycles --res 720
  Один кадр для проверки:   ... --only-frame 40
  Сохранить .blend:         ... --save-blend lenticule.blend      (потом открыть и доработать руками)
  Из кадров в GIF / MP4:
       ffmpeg -framerate 16.67 -i frames/f%03d.png -vf "scale=720:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" lenticule.gif
       ffmpeg -framerate 24 -i frames/f%03d.png -c:v libx264 -pix_fmt yuv420p lenticule.mp4

Параметры лентикулы: --sph --cyl --axis --oz --tmin --exag (по умолчанию иллюстративные, не пациент).
Стиль: --style color (цвет по толщине, глянец) | glass (прозрачный, лучше с Cycles).
Подписи толщины на краю: --labels (надписи «80 мкм» шрифтом с кириллицей — DejaVu Sans / Noto Sans, видны только на
  ближней к зрителю стороне); без флага — вариант без цифр. Свой шрифт: --font /путь/к/шрифту.ttf
Видео: --video — после кадров собрать MP4 (H.264) и GIF (нужен ffmpeg).
"""
import sys, os, math, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lenticule_model import Lenticule, lenticule_mesh

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0)
ap.add_argument('--axis', type=float, default=0.0); ap.add_argument('--oz', type=float, default=6.7)
ap.add_argument('--tmin', type=float, default=20.0); ap.add_argument('--exag', type=float, default=8.0)
ap.add_argument('--out', default='frames'); ap.add_argument('--res', type=int, default=720)
ap.add_argument('--n1', type=int, default=110, help='кадров на оборот по горизонтали')
ap.add_argument('--n2', type=int, default=110, help='кадров на оборот по вертикали')
ap.add_argument('--engine', choices=['eevee', 'cycles'], default='cycles')
ap.add_argument('--samples', type=int, default=64); ap.add_argument('--style', choices=['color', 'glass'], default='color')
ap.add_argument('--labels', action='store_true'); ap.add_argument('--only-frame', type=int, default=None)
ap.add_argument('--font', default=None, help='TTF/OTF с кириллицей (по умолчанию ищется DejaVu Sans или Noto Sans)')
ap.add_argument('--unit', default='мкм', help='подпись единиц у толщины')
ap.add_argument('--frame-range', default=None, help='например 111-220: перерендерить только эти кадры (видео собирается из всех кадров в папке)')
ap.add_argument('--video', action='store_true', help='собрать MP4 и GIF из кадров (ffmpeg)'); ap.add_argument('--fps', type=float, default=24.0)
ap.add_argument('--save-blend', default=None); ap.add_argument('--no-render', action='store_true')
A = ap.parse_args(argv)

ELEV_H = 16.0                                   # угол места камеры при горизонтальном обороте (как в GIF)
CMAP = [(205, 226, 251), (158, 197, 244), (109, 167, 236), (57, 135, 229), (37, 106, 191), (28, 92, 171), (24, 79, 149)]
lin = lambda c: (c / 255.0) ** 2.2             # sRGB → линейное (приближённо)


# ---------------------------------------------------------------- сцена ---------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
L = Lenticule(A.sph, A.cyl, A.axis, A.oz, A.tmin)
V, F, thk = lenticule_mesh(L, nth=181, nr=64, exag=A.exag)
V = V - np.array([0, 0, 0.5 * (V[:, 2].max() + V[:, 2].min())])        # центр объёма — в начало координат (иначе при вращении «болтается»)

mesh = bpy.data.meshes.new('lenticule'); mesh.from_pydata(V.tolist(), [], F.tolist()); mesh.update()
mesh.shade_smooth() if hasattr(mesh, 'shade_smooth') else None
att = mesh.attributes.new(name='thk', type='FLOAT', domain='POINT'); att.data.foreach_set('value', thk.astype(np.float32))
obj = bpy.data.objects.new('Lenticule', mesh); scene.collection.objects.link(obj)
obj.rotation_mode = 'XYZ'
try:   # сглаживание по углу, чтобы стенка оставалась чёткой
    mesh.set_sharp_from_angle(angle=math.radians(35))
except Exception:
    pass


def make_material():
    mat = bpy.data.materials.new('LenticuleMat')
    try: mat.use_nodes = True
    except Exception: pass
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (400, 0)
    att_n = nt.nodes.new('ShaderNodeAttribute'); att_n.attribute_type = 'GEOMETRY'; att_n.attribute_name = 'thk'; att_n.location = (-500, 0)
    rng = nt.nodes.new('ShaderNodeMapRange'); rng.location = (-300, 0)
    rng.inputs['From Min'].default_value = 10; rng.inputs['From Max'].default_value = 90
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-100, 0)
    cr = ramp.color_ramp
    while len(cr.elements) > 2: cr.elements.remove(cr.elements[-1])
    for i, c in enumerate(CMAP):
        e = cr.elements[i] if i < len(cr.elements) else cr.elements.new(i / (len(CMAP) - 1))
        e.position = i / (len(CMAP) - 1); e.color = (lin(c[0]), lin(c[1]), lin(c[2]), 1.0)
    nt.links.new(att_n.outputs['Fac'], rng.inputs['Value']); nt.links.new(rng.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    def setin(name, val):
        for n in (name,) if isinstance(name, str) else name:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = val; return
    if A.style == 'color':
        setin('Roughness', 0.32); setin(('Coat Weight', 'Clearcoat'), 0.4); setin(('Coat Roughness', 'Clearcoat Roughness'), 0.05)
    else:   # прозрачная линза, окрашенная по толщине
        setin('Roughness', 0.04); setin(('Transmission Weight', 'Transmission'), 1.0); setin('IOR', 1.376)
    return mat

obj.data.materials.append(make_material())

# мировой фон: белый, даёт мягкое студийное заполняющее освещение
world = bpy.data.worlds.new('World'); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = world.node_tree.nodes.get('Background') or world.node_tree.nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
# для камеры фон чисто белый (сила 1.0), а как источник света — вполовину слабее: иначе всё «выбеливается»
lp = world.node_tree.nodes.new('ShaderNodeLightPath'); mu = world.node_tree.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY_ADD'
mu.inputs[1].default_value = 0.65; mu.inputs[2].default_value = 0.35
world.node_tree.links.new(lp.outputs['Is Camera Ray'], mu.inputs[0]); world.node_tree.links.new(mu.outputs['Value'], bg.inputs['Strength'])

# камера (неподвижна): вращаем сам объект — как турнтейбл, без сингулярности на виде строго сверху
D = 28.0
cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 85; cam_data.sensor_width = 36
cam = bpy.data.objects.new('Camera', cam_data); scene.collection.objects.link(cam); scene.camera = cam
el = math.radians(ELEV_H)
cam.location = (0.0, -D * math.cos(el), D * math.sin(el))
target = bpy.data.objects.new('Target', None); scene.collection.objects.link(target)
tc = cam.constraints.new('TRACK_TO'); tc.target = target; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

def add_area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    lo = bpy.data.objects.new(name, ld); lo.location = loc; scene.collection.objects.link(lo)
    c = lo.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
add_area('Key', (-6, -9, 9), 700, 8)                    # основной: слева-спереди-сверху
add_area('Rim', (7, 8, 6), 600, 6, (0.85, 0.92, 1.0))   # контровой: сзади-справа, подчёркивает край
add_area('Fill', (8, -10, 2), 150, 10)                   # заполняющий

# подписи толщины на краю (кириллица: нужен шрифт с кириллицей; встроенный шрифт Blender её не содержит)
FONT_CANDIDATES = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans.ttf',
                   '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf', '/usr/share/fonts/noto/NotoSans-Regular.ttf',
                   '/Library/Fonts/Arial Unicode.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf',
                   'C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/DejaVuSans.ttf']
labels = []
if A.labels:
    fpath = A.font or next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    font = bpy.data.fonts.load(fpath) if fpath else None
    if font is None:
        print('предупреждение: шрифт с кириллицей не найден, подписи будут латиницей (µm); укажите --font')
    unit = A.unit if font is not None else 'µm'
    for k in range(4):
        th = math.radians(A.axis + 90 * k); flat = (k % 2 == 0)
        t_edge = L.t_flat if flat else L.t_steep
        txt = bpy.data.curves.new(f'lab{k}', 'FONT'); txt.body = f'{t_edge:.0f} {unit}'; txt.align_x = 'CENTER'; txt.align_y = 'CENTER'
        txt.size = 0.62; txt.extrude = 0.0
        if font is not None: txt.font = font
        to = bpy.data.objects.new(f'Label{k}', txt); scene.collection.objects.link(to)
        to['anchor'] = (L.R * math.cos(th), L.R * math.sin(th), float(V[np.argmin(np.abs(np.hypot(V[:, 0], V[:, 1]) - L.R)), 2]))
        cc = to.constraints.new('COPY_ROTATION'); cc.target = cam
        m = bpy.data.materials.new(f'LabMat{k}')
        try: m.use_nodes = True
        except Exception: pass
        nt = m.node_tree; nt.nodes.clear(); em = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
        col = tuple(lin(c) for c in ((42, 120, 214) if flat else (235, 104, 52))) + (1.0,); em.inputs['Color'].default_value = col; em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs['Emission'], o.inputs['Surface']); txt.materials.append(m)
        labels.append(to)


def place_label(label, rot_euler):
    """Подпись ставится у своей точки края (в мировых координатах), сдвинута наружу от края и, на ближней к зрителю
    стороне, ниже кромки — чтобы не ложиться на лентикулу. Возвращает True, если подпись должна быть видна
    (её точка края на ближней стороне и лентикула не перевёрнута)."""
    from mathutils import Euler
    M = Euler(rot_euler, 'XYZ').to_matrix()
    p = M @ Vector(label['anchor'])
    rim = Vector((p.x, p.y, 0.0)); rim = rim.normalized() if rim.length > 1e-6 else Vector((0, -1, 0))
    to_cam = Vector((cam.location.x, cam.location.y, 0.0)).normalized()
    facing = rim.dot(to_cam)                                                   # 1 — край обращён к зрителю, −1 — дальний
    label.location = p + rim * 1.1 - Vector((0, 0, 0.35 + 0.9 * max(facing, 0.0)))
    up = (M @ Vector((0, 0, 1))).z
    # боковые подписи видны при наклоне до ~78°, передняя/задняя — только пока лентикула почти горизонтальна
    return facing > -0.35 and (up > 0.85 or (up > 0.2 and abs(facing) < 0.5))


# ---------------------------------------------------------------- траектория (как в GIF) ------------
def _warp(weight_fn, lo, hi, n=6001):
    xs = np.linspace(lo, hi, n); w = weight_fn(xs)
    cum = np.concatenate([[0.0], np.cumsum((w[:-1] + w[1:]) / 2 * np.diff(xs))]); cum /= cum[-1]
    return lambda u: float(np.interp(u, cum, xs))
ease = lambda u: 0.5 * u + 0.5 * (u * u * (3 - 2 * u))                       # мягкий старт/остановка
# горизонталь: медленнее на видах вдоль меридианов (кратно 90°); вертикаль: быстро через низ
az_of_u = _warp(lambda a: 1.0 / (0.45 + 0.55 * np.sin(np.radians(2 * a)) ** 2), 0.0, 360.0)
pitch_of_u = _warp(lambda p: 1.0 / (0.60 + 1.20 * (0.5 + 0.5 * np.cos(np.radians(p - 270)))), ELEV_H, ELEV_H + 360.0)
N = A.n1 + A.n2
scene.frame_start, scene.frame_end = 1, N
for i in range(N):
    if i < A.n1:
        rz, rx = az_of_u(ease(i / A.n1)), 0.0                                  # оборот вокруг вертикальной оси
    else:
        rz, rx = 0.0, pitch_of_u(ease((i - A.n1) / A.n2)) - ELEV_H             # оборот вокруг горизонтальной оси (через верх)
    obj.rotation_euler = (math.radians(rx), 0.0, math.radians(rz))
    obj.keyframe_insert('rotation_euler', frame=i + 1)
    for lb in labels:                                                          # видимость подписи по кадрам: только ближняя сторона
        lb.hide_render = not place_label(lb, obj.rotation_euler); lb.hide_viewport = lb.hide_render
        lb.keyframe_insert('hide_render', frame=i + 1); lb.keyframe_insert('hide_viewport', frame=i + 1); lb.keyframe_insert('location', frame=i + 1)
ad = obj.animation_data
fcs = ad.action.fcurves if hasattr(ad.action, 'fcurves') else [fc for layer in ad.action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
for fc in fcs:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- рендер ---------------------------
r = scene.render; r.resolution_x = r.resolution_y = A.res; r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'; r.film_transparent = False
if A.engine == 'cycles':
    scene.render.engine = 'CYCLES'
    try:
        scene.cycles.samples = A.samples; scene.cycles.use_denoising = True; scene.cycles.device = 'CPU'
    except Exception as e:
        print('предупреждение: настройки Cycles не применены:', e)
else:
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    try: scene.eevee.taa_render_samples = A.samples
    except Exception: pass
try: scene.view_settings.view_transform = 'Standard'     # без «киношного» AgX: чистый белый фон и честные цвета шкалы
except Exception: pass
os.makedirs(A.out, exist_ok=True)
if A.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(A.save_blend)); print('сохранён', A.save_blend)
if not A.no_render:
    if A.only_frame is not None: frames = [A.only_frame]
    elif A.frame_range: a_, b_ = map(int, A.frame_range.split('-')); frames = range(a_, b_ + 1)
    else: frames = range(1, N + 1)
    for f in frames:
        scene.frame_set(f); r.filepath = os.path.abspath(f'{A.out}/f{f - 1:03d}.png')
        bpy.ops.render.render(write_still=True); print('кадр', f, '/', N, flush=True)
    if A.video and A.only_frame is None:
        import subprocess, shutil
        if shutil.which('ffmpeg') is None:
            print('ffmpeg не найден — MP4/GIF не собраны')
        else:
            base = os.path.abspath(A.out.rstrip('/'))
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(A.fps), '-i', f'{base}/f%03d.png',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{base}.mp4'], check=True)
            gw = min(A.res, 600)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(A.fps * 0.7), '-i', f'{base}/f%03d.png', '-vf',
                            f'scale={gw}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a', f'{base}.gif'], check=True)
            print('видео:', f'{base}.mp4', f'{base}.gif')
