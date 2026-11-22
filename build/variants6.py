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



def pill(x, y, w, text, fill, color="FFFFFF", size=9, h=0.32):
    b.rect(x, y, w, h, fill, kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5); b.txt(x, y, w, h, text, size=size, bold=True, color=color, align='c', anchor='m')



RR = MSO_SHAPE.ROUNDED_RECTANGLE
def rr(x, y, w, h, fill=None, line=None, lw=1.5, adj=0.5, dash=None, alpha=None):
    return b.rect(x, y, w, h, fill, line, lw, RR, adj, dash=dash, alpha=alpha)
def num_dot(cx, cy, n, col, d=0.7):
    oval(cx, cy, d, col); b.txt(cx - d / 2 / b.sx(), cy - d / 2, d / b.sx(), d, n, size=15, bold=True, color="FFFFFF", align='c', anchor='m')



def U():  # semicircles
    b.slide("Актуальность"); c = T()
    b.txt(2.6, 1.4, 8.15, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    cy = 4.45
    oval(-0.1, cy, 3.4, f.tint(1)); oval(-0.1, cy, 3.4, None, c['s2'], 2.5)
    oval(13.43, cy, 3.4, f.tint(0)); oval(13.43, cy, 3.4, None, c['s1'], 2.5, MSO_LINE.DASH)
    oval(6.675, cy, 3.0, "FFFFFF", c['hair'], 1.0); oval(6.675, cy, 3.6, None, c['hair'], 1.0, MSO_LINE.DASH); b.pic("p2_22.png", 5.4, cy - 0.7, 2.55, 1.4)
    pill(2.0, 3.2, 1.7, "золотой стандарт", c['s2']); b.txt(2.0, 3.6, 3.1, 1.8, [[(FEMTO_T, {'bold': True, 'size': 13, 'color': c['s2t']})], [(FEMTO_D, {'size': 10})]], anchor='m', spacing=1.05, after=3)
    pill(9.7, 3.2, 1.8, "предстоит изучить", c['s1']); b.txt(8.4, 3.6, 3.1, 0.9, "Лентикулярная технология", size=13, bold=True, color=c['s1t'], align='r', anchor='m'); b.txt(9.4, 4.3, 2.1, 1.3, "?", size=64, bold=True, color=c['s1'], align='r', anchor='m')
    rr(0.8, 6.2, 5.7, 0.7, f.tint(2)); b.txt(1.1, 6.2, 5.2, 0.7, "01   " + c4.B1, size=9.5, anchor='m'); rr(6.85, 6.2, 5.7, 0.7, f.tint(2)); b.txt(7.15, 6.2, 5.2, 0.7, "02   " + c4.B2, size=8.5, anchor='m')


def V():  # arch columns
    b.slide("Актуальность"); c = T()
    cols = [(0.8, f.tint(2), c['acc'], "ФАКТЫ"), (4.85, f.tint(1), c['s2'], "ЗОЛОТОЙ СТАНДАРТ"), (8.9, f.tint(0), c['s1'], "ПРЕДСТОИТ ИЗУЧИТЬ")]
    for x, fill, col, lab in cols:
        sh = b.rect(x, 1.55, 3.65, 5.25, fill, col, 2.0, MSO_SHAPE.ROUND_2_SAME_RECTANGLE, 0.5, dash=MSO_LINE.DASH if col == c['s1'] else None)
        oval(x + 1.825 / b.sx() * b.sx() if False else x + 1.825, 2.6, 1.7, "FFFFFF", col, 2.0)
        pill(x + 0.65, 3.65, 2.35, lab, col, size=9)
    # contents
    b.pic("p2_22.png", 1.0, 2.2, 3.25, 0.8) if False else None
    oval(2.625 + 0.0, 2.6, 1.7, "FFFFFF", c['acc'], 2.0); b.pic("p2_22.png", 1.9, 2.15, 1.45, 0.9)
    b.txt(1.05, 4.15, 3.15, 2.55, [[(c4.B1, {'size': 11})], [(c4.B2, {'size': 9, 'color': c['mute']})]], align='c', spacing=1.08, after=6)
    oval(6.675, 2.6, 1.7, c['s2']); b.txt(6.0, 2.15, 1.7 / b.sx(), 0.9, "✓", size=40, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(5.1, 4.15, 3.15, 2.55, [[(FEMTO_T, {'bold': True, 'size': 14, 'color': c['s2t']})], [(FEMTO_D, {'size': 11})]], align='c', spacing=1.08, after=6)
    oval(10.725, 2.6, 1.7, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(10.05, 2.15, 1.7 / b.sx(), 0.9, "?", size=44, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(9.15, 4.15, 3.15, 2.55, [[("Лентикулярная технология", {'bold': True, 'size': 14, 'color': c['s1t']})]], align='c', spacing=1.08)
    b.txt(0.8, 6.95, 11, 0.2, "", size=6)


def W():  # planets
    b.slide("Актуальность"); c = T()
    cx, cy = 6.675, 3.95
    b.rect(cx - 5.2 / b.sx(), cy - 1.9, 10.4 / b.sx(), 3.8, None, c['hair'], 1.0, MSO_SHAPE.OVAL, dash=MSO_LINE.DASH)
    b.rect(cx - 3.6 / b.sx(), cy - 1.3, 7.2 / b.sx(), 2.6, None, c['hair'], 1.0, MSO_SHAPE.OVAL)
    oval(cx, cy, 2.3, f.tint(2)); oval(cx, cy, 1.8, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", cx - 0.82, cy - 0.5, 1.64, 1.0)
    oval(1.5, cy - 0.3, 1.5, c['s2']); b.txt(0.75, cy - 0.7, 1.5 / b.sx(), 0.8, "✓", size=34, bold=True, color="FFFFFF", align='c', anchor='m'); b.txt(0.75, cy - 0.15, 1.5 / b.sx(), 0.4, "Фемто", size=9, bold=True, color="FFFFFF", align='c')
    oval(11.8, cy + 0.3, 1.5, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(11.05, cy - 0.1, 1.5 / b.sx(), 0.8, "?", size=44, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(2.6, 1.35, 8.15, 0.5, HEAD, size=19, bold=True, color=c['tcolor'], align='c', anchor='m')
    pill(0.55, 5.1, 1.7, "золотой стандарт", c['s2']); b.txt(0.55, 5.5, 3.4, 1.4, [[(FEMTO_T, {'bold': True, 'size': 12, 'color': c['s2t']})], [(FEMTO_D, {'size': 9.5})]], spacing=1.05, after=2)
    pill(10.7, 5.1, 1.8, "предстоит изучить", c['s1']); b.txt(9.3, 5.5, 3.25, 0.6, "Лентикулярная технология", size=12.5, bold=True, color=c['s1t'], align='r')
    rr(4.55, 5.45, 4.25, 1.35, f.tint(2), None, 0, 0.25); b.txt(4.7, 5.45, 3.95, 1.35, [[("01  ", {'bold': True, 'color': c['acc'], 'size': 11}), (c4.B1, {'size': 9})], [("02  ", {'bold': True, 'color': c['acc'], 'size': 11}), (c4.B2, {'size': 8})]], anchor='m', spacing=1.05, after=3)


def X():  # donut
    b.slide("Актуальность"); c = T()
    cx, cy, D = 4.2, 4.15, 4.4
    for col, a0, a1, dash in ((c['s2'], 90, 270, None), (c['s1'], 270, 90, MSO_LINE.SQUARE_DOT)):
        arc = b.sl.shapes.add_shape(MSO_SHAPE.ARC, b.I(b.gx(cx - D / 2 / b.sx())), b.I(cy - D / 2), b.I(D / b.sx()), b.I(D))
        arc.fill.background(); arc.line.color.rgb = b.rgb(col); arc.line.width = b.Pt(22)
        if dash: arc.line.dash_style = dash
        arc.adjustments[0] = a0 * 0.6; arc.adjustments[1] = a1 * 0.6
        st = arc._element.find(b.qn('p:style'))
        if st is not None: arc._element.remove(st)
    oval(cx, cy, 3.3, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", cx - 1.45, cy - 0.85, 2.9, 1.7)
    b.txt(0.8, 1.35, 6.4, 0.5, HEAD, size=15, bold=True, color=c['tcolor'], anchor='m')
    b.txt(7.7, 1.45, 4.85, 1.0, [[("01  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B1, {})]], size=11, spacing=1.08, anchor='m')
    b.txt(7.7, 2.45, 4.85, 1.1, [[("02  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B2, {'size': 9.5})]], size=9.5, spacing=1.08, anchor='m')
    oval(8.15, 4.35, 0.5, c['s2']); b.txt(7.9, 4.1, 0.5 / b.sx(), 0.5, "", size=6)
    b.txt(8.7, 3.8, 3.85, 1.4, [[("ФемтоЛАЗИК", {'bold': True, 'size': 15, 'color': c['s2t']})], [(FEMTO_T.replace("Эксимерлазерная технология (ФемтоЛАЗИК)", "Эксимерлазерная технология"), {'size': 10})], [(FEMTO_D, {'size': 10})]], spacing=1.05, after=2); pill(8.7, 3.45, 1.75, "золотой стандарт", c['s2'], size=8.5, h=0.28)
    oval(8.15, 6.05, 0.5, c['s1'])
    b.txt(8.7, 5.55, 3.85, 1.2, [[("Лентикулярная технология", {'bold': True, 'size': 15, 'color': c['s1t']})], [("предстоит изучить  ?", {'size': 10.5, 'color': c['mute']})]], spacing=1.05, after=2)


def Y():  # lanes
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.4, 11.75, 0.5, HEAD, size=19, bold=True, color=c['tcolor'], align='c', anchor='m')
    oval(1.9, 4.0, 2.6, f.tint(2)); oval(1.9, 4.0, 2.1, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 1.0, 3.55, 1.8, 0.9)
    rr(3.6, 2.7, 8.95, 1.35, f.tint(1), c['s2'], 2.0, 0.5); rr(3.6, 4.25, 8.95, 1.35, f.tint(0), c['s1'], 2.0, 0.5, MSO_LINE.DASH)
    b.hair(3.2, 4.0, 3.6, 3.37, c['s2'], 2.5); b.hair(3.2, 4.0, 3.6, 4.92, c['s1'], 2.5, MSO_LINE.DASH)
    oval(4.5, 3.37, 0.85, c['s2']); b.txt(4.05, 2.95, 0.85 / b.sx(), 0.85, "✓", size=26, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(5.3, 2.8, 5.6, 0.6, FEMTO_T, size=15, bold=True, color=c['s2t'], anchor='m'); b.txt(5.3, 3.4, 5.6, 0.55, FEMTO_D, size=11); pill(10.55, 2.5, 1.85, "золотой стандарт", c['s2'])
    oval(4.5, 4.92, 0.85, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(4.05, 4.5, 0.85 / b.sx(), 0.85, "?", size=26, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(5.3, 4.62, 5.6, 0.6, "Лентикулярная технология", size=15, bold=True, color=c['s1t'], anchor='m'); b.txt(5.3, 5.2, 5.6, 0.35, "предстоит изучить", size=11, color=c['mute']); pill(10.55, 4.05, 1.85, "предстоит изучить", c['s1']) if False else None
    rr(0.8, 5.95, 5.7, 0.9, f.tint(2)); b.txt(1.1, 5.95, 5.2, 0.9, "01   " + c4.B1, size=9.5, anchor='m'); rr(6.85, 5.95, 5.7, 0.9, f.tint(2)); b.txt(7.15, 5.95, 5.2, 0.9, "02   " + c4.B2, size=8.5, anchor='m')


for fn in (U, V, W, X, Y): fn()
b.prs.save("/tmp/variants6.pptx"); print("ok")
