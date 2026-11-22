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


def P():  # bubble chain
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.4, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    cy = 4.1
    oval(2.6, cy, 3.5, f.tint(1)); oval(2.6, cy, 3.5, None, c['s2'], 2.5)
    oval(6.675, cy, 3.9, "FFFFFF", c['hair'], 1.0); oval(6.675, cy, 4.4, None, c['hair'], 1.0, MSO_LINE.DASH)
    oval(10.75, cy, 3.5, f.tint(0)); oval(10.75, cy, 3.5, None, c['s1'], 2.5, MSO_LINE.DASH)
    b.pic("p2_22.png", 5.25, cy - 0.95, 2.85, 1.9)
    pill(1.75, 2.75, 1.7, "золотой стандарт", c['s2'])
    b.txt(1.2, 3.2, 2.8, 1.5, [[(FEMTO_T, {'bold': True, 'size': 12.5, 'color': c['s2t']})], [(FEMTO_D, {'size': 9})]], align='c', anchor='m', spacing=1.05, after=3)
    pill(9.9, 2.75, 1.8, "предстоит изучить", c['s1'])
    b.txt(9.4, 3.2, 2.7, 0.9, "Лентикулярная технология", size=13, bold=True, color=c['s1t'], align='c', anchor='m'); b.txt(9.7, 4.0, 2.1, 1.0, "?", size=54, bold=True, color=c['s1'], align='c', anchor='m')
    rr(0.8, 6.15, 5.7, 0.75, f.tint(2)); b.txt(1.1, 6.15, 5.2, 0.75, "01   " + c4.B1, size=9.5, anchor='m')
    rr(6.85, 6.15, 5.7, 0.75, f.tint(2)); b.txt(7.15, 6.15, 5.2, 0.75, "02   " + c4.B2, size=8.5, anchor='m')


def Q():  # pills
    b.slide("Актуальность"); c = T()
    rr(0.8, 1.4, 11.75, 0.8, f.tint(2)); b.txt(1.2, 1.4, 5.3, 0.8, c4.B1, size=10.5, anchor='m', spacing=1.05); b.hair(6.675, 1.55, 6.675, 2.05, c['hair']); b.txt(6.95, 1.4, 5.3, 0.8, c4.B2, size=9.5, anchor='m', spacing=1.05)
    rr(2.2, 2.55, 8.95, 0.7, c['tcolor'] if c['n'] != 14 else "010233"); b.txt(2.2, 2.55, 8.95, 0.7, HEAD, size=17, bold=True, color="FFFFFF", align='c', anchor='m')
    rr(0.8, 3.65, 7.2, 1.45, f.tint(1), c['s2'], 2.0, 0.5); oval(1.75, 4.375, 1.0, c['s2']); b.txt(1.25, 3.95, 1.0 / b.sx(), 0.85, "✓", size=30, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(2.55, 3.8, 5.2, 0.6, FEMTO_T, size=15, bold=True, color=c['s2t'], anchor='m'); b.txt(2.55, 4.4, 5.2, 0.6, FEMTO_D, size=11)
    pill(6.0, 3.28, 1.8, "золотой стандарт", c['s2'])
    rr(5.35, 5.3, 7.2, 1.45, f.tint(0), c['s1'], 2.0, 0.5, MSO_LINE.DASH); oval(11.5, 6.025, 1.0, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(11.0, 5.6, 1.0 / b.sx(), 0.9, "?", size=32, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(6.05, 5.45, 5.0, 0.7, "Лентикулярная технология", size=15, bold=True, color=c['s1t'], anchor='m'); b.txt(6.05, 6.1, 4.5, 0.5, "предстоит изучить", size=11, color=c['mute'])
    oval(1.9, 6.05, 1.7, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 1.15, 5.65, 1.5, 0.8)


def R():  # arch
    b.slide("Актуальность"); c = T()
    cx, cy = 6.675, 5.25
    for d, col, w in ((5.6, c['hair'], 1.0), (4.4, c['hair'], 1.0)):
        b.rect(cx - d / 2 / b.sx(), cy - d / 2, d / b.sx(), d, None, col, w, MSO_SHAPE.OVAL)
    arc = b.sl.shapes.add_shape(MSO_SHAPE.ARC, b.I(b.gx(cx - 2.5 / b.sx())), b.I(cy - 2.5), b.I(5.0 / b.sx()), b.I(5.0))
    arc.fill.background(); arc.line.color.rgb = b.rgb(c['s2']); arc.line.width = b.Pt(14)
    arc.adjustments[0] = 108; arc.adjustments[1] = 162
    arc2 = b.sl.shapes.add_shape(MSO_SHAPE.ARC, b.I(b.gx(cx - 2.5 / b.sx())), b.I(cy - 2.5), b.I(5.0 / b.sx()), b.I(5.0))
    arc2.fill.background(); arc2.line.color.rgb = b.rgb(c['s1']); arc2.line.width = b.Pt(14); arc2.line.dash_style = MSO_LINE.SQUARE_DOT
    arc2.adjustments[0] = 162; arc2.adjustments[1] = 0
    for a in (arc, arc2):
        st = a._element.find(b.qn('p:style'))
        if st is not None: a._element.remove(st)
    oval(cx, cy, 2.4, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", cx - 1.05, cy - 0.6, 2.1, 1.2)
    b.txt(2.6, 1.4, 8.15, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    rr(0.8, 2.1, 4.1, 1.3, f.tint(2), None, 0, 0.2); b.txt(1.0, 2.1, 3.7, 1.3, c4.B1, size=10.5, anchor='m', spacing=1.06)
    rr(8.45, 2.1, 4.1, 1.3, f.tint(2), None, 0, 0.2); b.txt(8.65, 2.1, 3.7, 1.3, c4.B2, size=9, anchor='m', spacing=1.05)
    pill(1.0, 4.35, 1.7, "золотой стандарт", c['s2']); b.txt(0.8, 4.75, 3.3, 1.4, [[(FEMTO_T, {'bold': True, 'size': 13, 'color': c['s2t']})], [(FEMTO_D, {'size': 10})]], spacing=1.05, after=3)
    pill(10.9, 4.35, 1.65, "предстоит изучить", c['s1']); b.txt(9.2, 4.75, 3.35, 0.9, "Лентикулярная технология", size=13, bold=True, color=c['s1t'], align='r'); b.txt(10.3, 5.3, 2.25, 1.3, "?", size=60, bold=True, color=c['s1'], align='r')


def S():  # concentric
    b.slide("Актуальность"); c = T()
    cx, cy = 4.0, 4.15
    for d, col in ((5.4, f.tint(2)), (4.2, "FFFFFF"), (3.0, f.tint(2)), (1.9, "FFFFFF")):
        oval(cx, cy, d, col, c['hair'], 1.0)
    b.pic("p2_22.png", cx - 0.85, cy - 0.5, 1.7, 1.0)
    b.txt(cx - 1.4, 1.5, 2.8, 0.4, "", size=6)
    b.txt(0.8, 1.35, 6.4, 0.5, HEAD, size=16, bold=True, color=c['tcolor'], anchor='m')
    num_dot(cx, 6.5 - 0.0, "01", c['acc'], 0.0) if False else None
    for y, n, t, sz in ((1.65, "01", c4.B1, 11), (2.85, "02", c4.B2, 9.5)):
        pass
    b.txt(7.7, 1.45, 4.85, 1.0, [[("01  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B1, {})]], size=11, spacing=1.08, anchor='m')
    b.txt(7.7, 2.5, 4.85, 1.2, [[("02  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B2, {'size': 9.5})]], size=9.5, spacing=1.08, anchor='m')
    rr(7.7, 3.95, 4.85, 1.2, "FFFFFF", c['s2'], 2.0, 0.5); oval(8.4, 4.55, 0.75, c['s2']); b.txt(8.0, 4.2, 0.75 / b.sx(), 0.7, "✓", size=22, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(9.0, 4.0, 3.45, 1.1, [[(FEMTO_T, {'bold': True, 'size': 11.5, 'color': c['s2t']})], [(FEMTO_D, {'size': 8.5})]], anchor='m', spacing=1.04)
    pill(10.5, 3.8, 1.9, "золотой стандарт", c['s2'], size=8, h=0.28)
    rr(7.7, 5.4, 4.85, 1.2, "FFFFFF", c['s1'], 2.0, 0.5, MSO_LINE.DASH); oval(8.4, 6.0, 0.75, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(8.0, 5.65, 0.75 / b.sx(), 0.7, "?", size=22, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(9.0, 5.45, 3.45, 1.1, [[("Лентикулярная технология", {'bold': True, 'size': 12.5, 'color': c['s1t']})], [("предстоит изучить", {'size': 9.5, 'color': c['mute']})]], anchor='m', spacing=1.05)


def T_():  # speech bubbles
    b.slide("Актуальность"); c = T()
    oval(2.4, 4.0, 3.6, f.tint(2)); oval(2.4, 4.0, 3.0, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 1.2, 3.35, 2.4, 1.3)
    b.txt(0.8, 5.95, 3.2, 0.9, HEAD, size=14, bold=True, color=c['tcolor'], align='c', anchor='m', spacing=1.05)
    rr(0.8, 1.4, 11.75, 0.75, f.tint(2)); b.txt(1.2, 1.4, 5.3, 0.75, c4.B1, size=10, anchor='m', spacing=1.05); b.hair(6.675, 1.5, 6.675, 2.05, c['hair']); b.txt(6.95, 1.4, 5.3, 0.75, c4.B2, size=9, anchor='m', spacing=1.05)
    for y, col, colt, fill, dash in ((2.5, c['s2'], c['s2t'], f.tint(1), None), (4.6, c['s1'], c['s1t'], f.tint(0), MSO_LINE.DASH)):
        sh = b.rect(5.0, y, 7.55, 1.85, fill, col, 2.0, MSO_SHAPE.OVAL_CALLOUT if False else MSO_SHAPE.ROUNDED_RECTANGULAR_CALLOUT, 0.3, dash=dash)
        sh.adjustments[0] = -0.62; sh.adjustments[1] = 0.1; sh.adjustments[2] = 0.5
    pill(5.4, 2.7, 1.8, "золотой стандарт", c['s2'])
    b.txt(5.4, 3.1, 6.8, 0.6, FEMTO_T, size=15, bold=True, color=c['s2t'], anchor='m'); b.txt(5.4, 3.75, 6.8, 0.5, FEMTO_D, size=11)
    pill(5.4, 4.8, 1.8, "предстоит изучить", c['s1'])
    b.txt(5.4, 5.2, 5.0, 0.7, "Лентикулярная технология", size=15, bold=True, color=c['s1t'], anchor='m'); b.txt(10.6, 4.65, 1.8, 1.8, "?", size=80, bold=True, color=c['s1l'], align='c', anchor='m')


for fn in (P, Q, R, S, T_): fn()
b.prs.save("/tmp/variants5.pptx"); print("ok")
