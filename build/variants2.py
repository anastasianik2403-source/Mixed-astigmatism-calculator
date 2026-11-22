import sys
import build3 as b
import build4 as c4
import build5 as f
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_LINE

b.T = next(t for t in b.THEMES if t['n'] == int(sys.argv[1] if len(sys.argv) > 1 else 5)); b.PAGE = 0
b.prs = Presentation(); b.prs.slide_width, b.prs.slide_height = Inches(13.333), Inches(7.5)
T = lambda: b.T
FEMTO_T = "Эксимерлазерная технология (ФемтоЛАЗИК)"; FEMTO_D = "Современный «золотой» стандарт в коррекции смешанного астигматизма"
HEAD = "Хирургическая коррекция смешанного астигматизма"


def oval(cx, cy, d, fill=None, line=None, lw=1.5, dash=None, alpha=None):
    return b.rect(cx - d / 2 / b.sx(), cy - d / 2, d / b.sx(), d, fill, line, lw, MSO_SHAPE.OVAL, dash=dash, alpha=alpha)


def tile(x, y, w, h, n, text, size=11.5):
    c = T(); b.rect(x, y, w, h, f.tint(2)); b.txt(x + 0.2, y, 0.7, h, f"0{n}", size=24, bold=True, color=c['acc'], anchor='m'); b.txt(x + 0.9, y, w - 1.1, h, text, size=size, anchor='m', spacing=1.08)


def chip(x, y, w, text, fill, size=9):
    f.chip(x, y, w, 0.32, text, fill, size=size)


def A():  # orbit
    b.slide("Актуальность"); c = T()
    tile(0.8, 1.4, 5.0, 1.0, 1, c4.B1, 11); tile(6.0, 1.4, 6.55, 1.0, 2, c4.B2, 11)
    b.txt(2.6, 2.55, 8.1, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    cx, cy = 6.67, 4.75
    oval(cx, cy, 3.5, None, c['hair'], 1.0, MSO_LINE.DASH); oval(cx, cy, 2.8, "FFFFFF", c['hair'], 1.0)
    b.pic("p2_22.png", cx - 1.35, cy - 1.0, 2.7, 2.0)
    oval(2.35, 4.45, 2.1, c['s2l'], None, alpha=60); oval(2.35, 4.45, 1.7, "FFFFFF", c['s2'], 2.0)
    b.txt(1.5, 4.0, 1.7, 0.9, [[("Фемто-", {'bold': True, 'size': 13, 'color': c['s2t']})], [("ЛАЗИК", {'bold': True, 'size': 13, 'color': c['s2t']})]], align='c', anchor='m')
    oval(10.98, 4.45, 2.1, c['s1l'], None, alpha=60); oval(10.98, 4.45, 1.7, "FFFFFF", c['s1'], 2.0, MSO_LINE.DASH)
    b.txt(10.13, 3.95, 1.7, 1.0, "?", size=48, bold=True, color=c['s1'], align='c', anchor='m')
    b.hair(3.4, 4.45, 4.9, 4.7, c['s2'], 2.0); b.hair(8.45, 4.7, 9.9, 4.45, c['s1'], 2.0, MSO_LINE.DASH)
    chip(1.55, 5.65, 1.6, "золотой стандарт", c['s2'])
    b.txt(0.8, 6.05, 3.1, 0.9, [[(FEMTO_T, {'bold': True, 'size': 11, 'color': c['s2t']})], [(FEMTO_D, {'size': 9.5})]], align='c', spacing=1.05, after=2)
    chip(10.2, 5.65, 1.55, "предстоит изучить", c['s1'])
    b.txt(9.4, 6.05, 3.1, 0.6, [[("Лентикулярная технология", {'bold': True, 'size': 12, 'color': c['s1t']})]], align='c')


def B():  # versus
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.35, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    b.rect(0.8, 2.0, 5.7, 3.7, f.tint(1)); b.rect(0.8, 2.0, 0.14, 3.7, c['s2'])
    chip(1.2, 2.25, 1.7, "золотой стандарт", c['s2'])
    b.txt(1.2, 2.75, 5.0, 1.0, "ФемтоЛАЗИК", size=34, bold=True, color=c['s2t'], anchor='m')
    b.txt(1.2, 3.75, 5.0, 0.7, FEMTO_T, size=13, bold=True, color=c['s2t'], spacing=1.05)
    b.txt(1.2, 4.5, 5.0, 1.0, FEMTO_D, size=12, spacing=1.1)
    b.rect(6.85, 2.0, 5.7, 3.7, f.tint(0)); b.rect(12.41, 2.0, 0.14, 3.7, c['s1'])
    chip(7.2, 2.25, 1.7, "предстоит изучить", c['s1'])
    b.txt(7.2, 2.75, 3.4, 1.0, "Лентикулярная технология", size=18, bold=True, color=c['s1t'], anchor='m', spacing=1.05)
    b.txt(9.3, 2.5, 3.0, 3.0, "?", size=150, bold=True, color=c['s1'], align='c', anchor='m')
    oval(6.675, 3.85, 0.95, "FFFFFF", c['tcolor'], 1.5); b.txt(6.2, 3.4, 0.95 / b.sx(), 0.9, "VS", size=16, bold=True, color=c['tcolor'], align='c', anchor='m')
    tile(0.8, 5.95, 5.7, 0.95, 1, c4.B1, 10); tile(6.85, 5.95, 5.7, 0.95, 2, c4.B2, 10)


def C():  # eye hero left
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 4.3, 5.2, f.tint(2))
    oval(2.95, 3.4, 3.6, None, c['hair'], 1.0, MSO_LINE.DASH); oval(2.95, 3.4, 2.9, "FFFFFF", c['hair'], 1.0)
    b.pic("p2_22.png", 1.55, 2.5, 2.8, 1.8)
    b.txt(1.0, 5.2, 3.9, 1.2, HEAD, size=16, bold=True, color=c['tcolor'], align='c', anchor='m', spacing=1.1)
    tile(5.5, 1.4, 7.05, 1.2, 1, c4.B1, 12); tile(5.5, 2.75, 7.05, 1.3, 2, c4.B2, 12)
    # rows
    b.rect(5.5, 4.35, 7.05, 0.95, "FFFFFF", c['s2'], 1.5); oval(6.05, 4.82, 0.6, c['s2']); b.txt(5.75, 4.52, 0.6 / b.sx(), 0.6, "✓", size=18, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(6.55, 4.35, 4.0, 0.95, [[(FEMTO_T, {'bold': True, 'size': 12.5, 'color': c['s2t']})], [(FEMTO_D, {'size': 9})]], anchor='m', spacing=1.05)
    chip(10.65, 4.67, 1.7, "золотой стандарт", c['s2'])
    b.rect(5.5, 5.5, 7.05, 0.95, "FFFFFF", c['s1'], 1.5, dash=MSO_LINE.DASH); oval(6.05, 5.97, 0.6, "FFFFFF", c['s1'], 2.0); b.txt(5.75, 5.67, 0.6 / b.sx(), 0.6, "?", size=22, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(6.55, 5.5, 4.0, 0.95, [[("Лентикулярная технология", {'bold': True, 'size': 12.5, 'color': c['s1t']})]], anchor='m')
    chip(10.65, 5.82, 1.7, "предстоит изучить", c['s1'])


def D():  # road
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 11.75, 1.0, f.tint(2))
    b.txt(1.0, 1.4, 5.5, 1.0, c4.B1, size=11, anchor='m', spacing=1.08); b.hair(6.75, 1.55, 6.75, 2.25, c['hair']); b.txt(6.95, 1.4, 5.4, 1.0, c4.B2, size=10.5, anchor='m', spacing=1.08)
    b.txt(0.8, 2.65, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    y = 4.55
    b.hair(2.2, y, 6.7, y, c['s2'], 3.0); arrow(6.7, y, 10.2, y, c['s1'], 3.0) if False else b.hair(6.7, y, 10.1, y, c['s1'], 3.0, MSO_LINE.DASH)
    oval(1.5, y, 1.7, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 0.75, y - 0.55, 1.5, 1.1)
    oval(6.7, y, 1.3, c['s2']); b.txt(6.05, y - 0.35, 1.3 / b.sx(), 0.7, "✓", size=34, bold=True, color="FFFFFF", align='c', anchor='m')
    oval(11.0, y, 1.7, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(10.15, y - 0.5, 1.7 / b.sx(), 1.0, "?", size=44, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(0.6, 5.55, 1.8, 0.6, "Смешанный астигматизм", size=10.5, bold=True, align='c')
    chip(5.85, 3.75, 1.7, "золотой стандарт", c['s2'])
    b.txt(5.0, 5.4, 3.4, 1.4, [[(FEMTO_T, {'bold': True, 'size': 12, 'color': c['s2t']})], [(FEMTO_D, {'size': 9.5})]], align='c', spacing=1.05, after=2)
    chip(10.15, 3.75, 1.7, "предстоит изучить", c['s1'])
    b.txt(9.3, 5.55, 3.4, 0.6, [[("Лентикулярная технология", {'bold': True, 'size': 12.5, 'color': c['s1t']})]], align='c')


def E():  # typographic
    b.slide("Актуальность"); c = T()
    b.txt(8.2, 0.9, 4.8, 5.8, "?", size=330, bold=True, color=c['s1l'], align='c', anchor='m')
    b.pic("p2_22.png", 8.8, 4.2, 3.7, 2.5)
    b.txt(0.8, 1.45, 7.2, 1.0, HEAD, size=26, bold=True, color=c['tcolor'], anchor='m', spacing=1.05)
    for i, t in enumerate((c4.B1, c4.B2)):
        y = 2.7 + i * 1.0; b.hair(0.8, y, 7.6, y, c['hair'])
        b.txt(0.8, y + 0.05, 0.8, 0.9, f"0{i+1}", size=22, bold=True, color=c['acc'], anchor='m'); b.txt(1.7, y + 0.05, 5.9, 0.9, t, size=11.5, anchor='m', spacing=1.08)
    b.rect(0.8, 4.9, 0.09, 0.85, c['s2']); b.txt(1.1, 4.9, 6.6, 0.85, [[(FEMTO_T, {'bold': True, 'size': 13, 'color': c['s2t']})], [(FEMTO_D, {'size': 10.5})]], anchor='m', spacing=1.05)
    b.rect(0.8, 5.95, 0.09, 0.85, c['s1']); b.txt(1.1, 5.95, 6.6, 0.85, [[("Лентикулярная технология", {'bold': True, 'size': 13, 'color': c['s1t']})], [("предстоит изучить", {'size': 10.5})]], anchor='m', spacing=1.05)


for fn in (A, B, C, D, E): fn()
b.prs.save("/tmp/variants2.pptx"); print("ok")
