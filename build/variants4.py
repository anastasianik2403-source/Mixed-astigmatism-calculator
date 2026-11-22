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


def K():  # venn
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.4, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    oval(5.2, 4.4, 3.2, c['s2l'], None, alpha=55); oval(8.15, 4.4, 3.2, c['s1l'], None, alpha=55)
    oval(5.2, 4.4, 3.2, None, c['s2'], 2.0); oval(8.15, 4.4, 3.2, None, c['s1'], 2.0, MSO_LINE.DASH)
    oval(6.675, 4.4, 1.4, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 5.98, 4.1, 1.3, 0.62)
    b.txt(3.9, 3.9, 2.0, 1.0, [[("ФемтоЛАЗИК", {'bold': True, 'size': 15, 'color': c['s2t']})]], align='c', anchor='m')
    b.txt(8.75, 3.85, 2.2, 1.1, "?", size=60, bold=True, color=c['s1'], align='c', anchor='m')
    pill(1.2, 6.05, 1.7, "золотой стандарт", c['s2']); b.txt(0.8, 6.4, 3.8, 0.6, FEMTO_D, size=9.5, align='c', spacing=1.05)
    pill(9.65, 6.05, 1.8, "предстоит изучить", c['s1']); b.txt(8.9, 6.4, 3.5, 0.5, "Лентикулярная технология", size=12, bold=True, color=c['s1t'], align='c')
    b.rect(0.8, 1.95, 4.3, 1.0, f.tint(2)); b.txt(0.95, 1.95, 4.0, 1.0, c4.B1, size=10.5, anchor='m', spacing=1.08)
    b.rect(8.25, 1.95, 4.3, 1.0, f.tint(2)); b.txt(8.4, 1.95, 4.0, 1.0, c4.B2, size=9, anchor='m', spacing=1.05)


def L():  # vertical path
    b.slide("Актуальность"); c = T()
    x = 1.25
    b.hair(x, 1.7, x, 6.4, c['hair'], 3.0)
    steps = [(1.55, "01", c['acc'], None), (3.35, "02", c['s2'], None), (5.1, "03", c['s1'], None)]
    for y, n, col, _ in steps:
        oval(x, y + 0.45, 0.85, col); b.txt(x - 0.42 / b.sx(), y, 0.85 / b.sx(), 0.9, n, size=18, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(2.1, 1.45, 6.2, 1.2, [[(c4.B1, {'size': 12})], [(c4.B2, {'size': 10.5, 'color': c['mute']})]], anchor='m', spacing=1.1, after=3)
    b.txt(2.1, 3.1, 6.2, 0.4, HEAD, size=11, bold=True, color=c['mute'])
    b.txt(2.1, 3.45, 6.2, 0.85, [[(FEMTO_T, {'bold': True, 'size': 16, 'color': c['s2t']})], [(FEMTO_D, {'size': 11.5})]], spacing=1.08, after=3)
    pill(2.1, 4.35, 1.75, "золотой стандарт", c['s2'], size=8.5, h=0.28)
    b.txt(2.1, 5.0, 6.2, 0.6, [[("Лентикулярная технология", {'bold': True, 'size': 16, 'color': c['s1t']})]], anchor='m'); pill(2.1, 5.65, 1.8, "предстоит изучить", c['s1'], size=8.5, h=0.28)
    b.rect(8.6, 1.5, 3.95, 5.3, f.tint(2)); oval(10.575, 3.6, 3.2, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 9.1, 2.9, 2.95, 1.45)
    b.txt(8.8, 5.3, 3.55, 1.2, HEAD, size=15, bold=True, color=c['tcolor'], align='c', anchor='m', spacing=1.08)


def M():  # dark spotlight
    b.slide("Актуальность"); c = T()
    b.rect(0, 1.35, 13.333, 3.0, c['tcolor'] if c['n'] != 14 else "010233", raw=True)
    b.txt(0.8, 1.5, 3.0, 0.5, HEAD.upper(), size=10, bold=True, color="F3B79C")
    b.txt(0.8, 1.9, 5.3, 2.3, [[(c4.B1, {'size': 13})], [("", {'size': 6})], [(c4.B2, {'size': 10.5, 'color': "C9CFE0"})]], color="FFFFFF", spacing=1.1, after=4)
    oval(9.2, 3.0, 2.4, "FFFFFF", None); b.pic("p2_22.png", 8.1, 2.45, 2.2, 1.1)
    oval(9.2, 3.0, 2.9, None, "FFFFFF", 1.0, MSO_LINE.DASH)
    b.rect(0.8, 4.65, 5.7, 2.1, "FFFFFF", c['s2'], 2.5); b.rect(0.8, 4.65, 0.16, 2.1, c['s2'])
    pill(1.2, 4.85, 1.7, "золотой стандарт", c['s2']); b.txt(1.2, 5.25, 5.1, 0.6, FEMTO_T, size=15, bold=True, color=c['s2t'], anchor='m'); b.txt(1.2, 5.9, 5.1, 0.7, FEMTO_D, size=11.5)
    b.rect(6.85, 4.65, 5.7, 2.1, "FFFFFF", c['s1'], 2.5, dash=MSO_LINE.DASH); b.rect(6.85, 4.65, 0.16, 2.1, c['s1'])
    pill(7.25, 4.85, 1.8, "предстоит изучить", c['s1']); b.txt(7.25, 5.25, 3.5, 0.9, "Лентикулярная технология", size=15, bold=True, color=c['s1t'], anchor='m'); b.txt(10.5, 4.7, 1.9, 2.0, "?", size=84, bold=True, color=c['s1l'], align='c', anchor='m')


def N():  # org tree
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 5.7, 0.95, f.tint(2)); b.txt(1.0, 1.4, 5.3, 0.95, c4.B1, size=10.5, anchor='m', spacing=1.08)
    b.rect(6.85, 1.4, 5.7, 0.95, f.tint(2)); b.txt(7.05, 1.4, 5.3, 0.95, c4.B2, size=10, anchor='m', spacing=1.06)
    b.hair(3.65, 2.35, 3.65, 2.65, c['hair'], 1.5); b.hair(9.7, 2.35, 9.7, 2.65, c['hair'], 1.5); b.hair(3.65, 2.65, 9.7, 2.65, c['hair'], 1.5); b.hair(6.675, 2.65, 6.675, 2.9, c['hair'], 1.5)
    b.rect(3.7, 2.9, 5.95, 0.7, c['tcolor'] if c['n'] != 14 else "010233"); b.txt(3.7, 2.9, 5.95, 0.7, HEAD, size=15, bold=True, color="FFFFFF", align='c', anchor='m')
    b.hair(6.675, 3.6, 6.675, 3.95, c['mute'], 1.5); b.hair(3.1, 3.95, 10.25, 3.95, c['mute'], 1.5); b.hair(3.1, 3.95, 3.1, 4.3, c['s2'], 2.5); b.hair(10.25, 3.95, 10.25, 4.3, c['s1'], 2.5, MSO_LINE.DASH)
    oval(6.675, 3.95, 0.4, "FFFFFF", c['mute'], 1.5)
    b.rect(0.8, 4.3, 4.6, 2.45, "FFFFFF", c['s2'], 2.0); b.rect(0.8, 4.3, 4.6, 0.1, c['s2']); pill(1.05, 4.55, 1.7, "золотой стандарт", c['s2'])
    b.txt(1.05, 4.95, 4.1, 0.85, FEMTO_T, size=14, bold=True, color=c['s2t'], anchor='m', spacing=1.05); b.txt(1.05, 5.8, 4.1, 0.9, FEMTO_D, size=11.5, spacing=1.08)
    b.rect(7.95, 4.3, 4.6, 2.45, "FFFFFF", c['s1'], 2.0, dash=MSO_LINE.DASH); b.rect(7.95, 4.3, 4.6, 0.1, c['s1']); pill(8.2, 4.55, 1.8, "предстоит изучить", c['s1'])
    b.txt(8.2, 4.95, 2.9, 0.85, "Лентикулярная технология", size=14, bold=True, color=c['s1t'], anchor='m', spacing=1.05); b.txt(10.8, 4.6, 1.6, 2.0, "?", size=80, bold=True, color=c['s1'], align='c', anchor='m')
    oval(6.675, 5.5, 2.0, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 5.7, 5.05, 1.95, 0.9)


def O():  # full-bleed eye
    b.slide("Актуальность"); c = T()
    b.pic("p2_22.png", 8.4, 1.6, 4.5, 3.2, halign='r')
    b.txt(1.1, 1.55, 7.2, 0.9, HEAD, size=24, bold=True, color=c['tcolor'], anchor='m', spacing=1.05)
    b.txt(1.1, 2.5, 7.0, 1.35, [[("01  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B1, {})], [("02  ", {'bold': True, 'color': c['acc'], 'size': 14}), (c4.B2, {'size': 10.5})]], size=11.5, spacing=1.1, after=5)
    b.hair(1.1, 4.0, 7.9, 4.0, c['hair'])
    oval(1.5, 4.8, 0.75, c['s2']); b.txt(1.12, 4.43, 0.75 / b.sx(), 0.75, "✓", size=20, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(2.15, 4.45, 5.7, 0.7, FEMTO_T, size=13.5, bold=True, color=c['s2t'], anchor='m'); b.txt(2.15, 5.1, 5.7, 0.5, FEMTO_D, size=10.5)
    oval(1.5, 6.1, 0.75, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(1.12, 5.73, 0.75 / b.sx(), 0.75, "?", size=22, bold=True, color=c['s1'], align='c', anchor='m')
    b.txt(2.15, 5.75, 5.7, 0.7, [[("Лентикулярная технология", {'bold': True, 'size': 13.5, 'color': c['s1t']})], [("предстоит изучить", {'size': 10.5, 'color': c['mute']})]], anchor='m')


for fn in (K, L, M, N, O): fn()
b.prs.save("/tmp/variants4.pptx"); print("ok")
