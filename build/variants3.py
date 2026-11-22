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



def F():  # bento grid
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 4.6, 5.35, f.tint(2))
    b.txt(1.05, 1.55, 4.1, 1.5, HEAD, size=22, bold=True, color=c['tcolor'], anchor='m', spacing=1.08)
    oval(3.1, 4.75, 3.1, None, c['hair'], 1.0, MSO_LINE.DASH); oval(3.1, 4.75, 2.5, "FFFFFF", c['hair'], 1.0)
    b.pic("p2_22.png", 1.95, 3.95, 2.3, 1.6)
    b.rect(5.6, 1.4, 3.5, 2.5, f.tint(2)); b.txt(5.8, 1.5, 1, 0.7, "01", size=26, bold=True, color=c['acc'], anchor='m'); b.txt(5.8, 2.2, 3.1, 1.6, c4.B1, size=11.5, spacing=1.1)
    b.rect(9.3, 1.4, 3.25, 2.5, f.tint(2)); b.txt(9.5, 1.5, 1, 0.7, "02", size=26, bold=True, color=c['acc'], anchor='m'); b.txt(9.5, 2.2, 2.85, 1.65, c4.B2, size=10, spacing=1.08)
    b.rect(5.6, 4.1, 3.5, 2.65, c['s2'])
    chip(5.85, 4.3, 1.6, "золотой стандарт", "FFFFFF", size=9) if False else (b.rect(5.85, 4.3, 1.6, 0.32, "FFFFFF", kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5), b.txt(5.85, 4.3, 1.6, 0.32, "золотой стандарт", size=9, bold=True, color=c['s2'], align='c', anchor='m'))
    b.txt(5.85, 4.8, 3.0, 0.9, FEMTO_T, size=14, bold=True, color="FFFFFF", spacing=1.05, anchor='m'); b.txt(5.85, 5.75, 3.0, 0.9, FEMTO_D, size=10.5, color="EAF1FB", spacing=1.1)
    b.rect(9.3, 4.1, 3.25, 2.65, c['s1'])
    b.txt(9.3, 4.1, 3.25, 1.7, "?", size=110, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(9.5, 5.75, 2.9, 0.9, "Лентикулярная технология", size=14, bold=True, color="FFFFFF", anchor='m', spacing=1.05)


def G():  # lens + callouts
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.35, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], anchor='m')
    cx, cy = 3.3, 3.9
    oval(cx, cy, 4.0, f.tint(2)); oval(cx, cy, 3.4, "FFFFFF", c['hair'], 1.5); oval(cx, cy, 4.3, None, c['hair'], 1.0, MSO_LINE.DASH)
    b.pic("p2_22.png", cx - 1.7, cy - 1.15, 3.4, 2.3)
    for y, col, colt, ttl, desc, chp in ((2.0, c['s2'], c['s2t'], FEMTO_T, FEMTO_D, "золотой стандарт"), (4.15, c['s1'], c['s1t'], "Лентикулярная технология", "", "предстоит изучить")):
        sh = b.rect(6.7, y, 5.85, 1.8, "FFFFFF", col, 2.0, MSO_SHAPE.ROUNDED_RECTANGULAR_CALLOUT, 0.1)
        sh.adjustments[0] = -0.57; sh.adjustments[1] = 0.0
        chip(7.0, y + 0.18, 1.7, chp, col)
        b.txt(7.0, y + 0.6, 5.3 if desc else 3.8, 0.55, ttl, size=14, bold=True, color=colt, anchor='m', spacing=1.05)
        if desc: b.txt(7.0, y + 1.2, 5.3, 0.55, desc, size=11, spacing=1.08)
        else:
            oval(11.35, y + 1.1, 1.0, "FFFFFF", col, 2.0, MSO_LINE.DASH); b.txt(10.85, y + 0.6, 1.0 / b.sx(), 1.0, "?", size=34, bold=True, color=col, align='c', anchor='m')
    tile(0.8, 6.2, 5.6, 0.7, 1, c4.B1, 9.5); tile(6.7, 6.2, 5.85, 0.7, 2, c4.B2, 9)


def H():  # now / next
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 11.75, 0.95, f.tint(2)); b.txt(1.0, 1.4, 5.5, 0.95, c4.B1, size=10.5, anchor='m', spacing=1.08); b.hair(6.75, 1.55, 6.75, 2.2, c['hair']); b.txt(6.95, 1.4, 5.4, 0.95, c4.B2, size=10, anchor='m', spacing=1.08)
    b.txt(0.8, 2.5, 11.75, 0.5, HEAD, size=20, bold=True, color=c['tcolor'], align='c', anchor='m')
    b.rect(0.8, 3.2, 5.6, 0.5, c['s2']); b.txt(0.8, 3.2, 5.6, 0.5, "ДОСТУПНО СЕЙЧАС", size=12, bold=True, color="FFFFFF", align='c', anchor='m')
    b.rect(6.95, 3.2, 5.6, 0.5, c['s1']); b.txt(6.95, 3.2, 5.6, 0.5, "В СТАДИИ ИССЛЕДОВАНИЯ", size=12, bold=True, color="FFFFFF", align='c', anchor='m')
    b.rect(0.8, 3.7, 5.6, 3.05, f.tint(1)); b.rect(6.95, 3.7, 5.6, 3.05, "FFFFFF", c['s1'], 1.5, dash=MSO_LINE.DASH)
    oval(1.7, 4.6, 0.8, c['s2']); b.txt(1.3, 4.2, 0.8 / b.sx(), 0.8, "✓", size=24, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(2.4, 4.1, 3.8, 1.0, FEMTO_T, size=14, bold=True, color=c['s2t'], anchor='m', spacing=1.05)
    b.txt(1.1, 5.35, 4.8, 1.0, FEMTO_D, size=12, spacing=1.1)
    b.txt(7.4, 4.1, 3.2, 1.0, "Лентикулярная технология", size=15, bold=True, color=c['s1t'], anchor='m', spacing=1.05)
    oval(11.3, 4.6, 1.0, "FFFFFF", c['s1'], 2.5, MSO_LINE.DASH); b.txt(10.8, 4.1, 1.0 / b.sx(), 1.0, "?", size=34, bold=True, color=c['s1'], align='c', anchor='m')
    oval(6.675, 4.2, 1.0, f.tint(2)); b.pic("p2_22.png", 6.1, 3.95, 1.15, 0.5)


def I():  # cascade
    b.slide("Актуальность"); c = T()
    b.rect(0.8, 1.4, 11.75, 0.95, f.tint(2)); b.txt(1.0, 1.4, 5.5, 0.95, c4.B1, size=10.5, anchor='m', spacing=1.08); b.hair(6.75, 1.55, 6.75, 2.2, c['hair']); b.txt(6.95, 1.4, 5.4, 0.95, c4.B2, size=10, anchor='m', spacing=1.08)
    b.rect(0.8, 2.75, 6.9, 3.2, c['s2']); b.rect(5.65, 3.55, 6.9, 3.2, c['s1'])
    b.txt(1.1, 2.9, 5.0, 0.4, "01  ·  золотой стандарт", size=10.5, bold=True, color="EAF1FB")
    b.txt(1.1, 3.35, 4.0, 1.0, FEMTO_T, size=19, bold=True, color="FFFFFF", anchor='m', spacing=1.05)
    b.txt(1.1, 4.45, 4.3, 1.2, FEMTO_D, size=12, color="EAF1FB", spacing=1.1)
    b.txt(8.0, 3.7, 4.2, 0.4, "02  ·  предстоит изучить", size=10.5, bold=True, color="FFF0E8")
    b.txt(8.2, 4.15, 3.0, 1.2, "Лентикулярная технология", size=19, bold=True, color="FFFFFF", anchor='m', spacing=1.05)
    b.txt(10.8, 4.9, 1.6, 1.8, "?", size=90, bold=True, color="FFD7C2", align='c', anchor='m')
    oval(6.675, 4.35, 2.2, "FFFFFF", "FFFFFF", 2.0); b.pic("p2_22.png", 5.65, 3.85, 2.05, 1.0)
    b.txt(5.0, 6.95, 3.4, 0.2, "", size=6)


def J():  # balance
    b.slide("Актуальность"); c = T()
    b.txt(0.8, 1.2, 11.75, 0.4, HEAD, size=19, bold=True, color=c['tcolor'], align='c', anchor='m')
    # balance: tilted beam, pivot, hanging pans; femto side heavier (lower)
    px, py = 6.675, 3.3
    b.hair(2.9, 3.55, 10.45, 3.05, c['ink'], 5.0)
    b.rect(px - 0.08 / b.sx(), py, 0.16 / b.sx(), 1.35, c['ink'])
    b.rect(px - 0.75 / b.sx(), 4.6, 1.5 / b.sx(), 0.14, c['ink'])
    oval(px, py + 0.0, 0.34, c['ink'])
    for x, y, col in ((2.9, 3.55, c['s2']), (10.45, 3.05, c['s1'])):
        b.hair(x, y, x - 1.0, y + 0.9, c['mute'], 1.0); b.hair(x, y, x + 1.0, y + 0.9, c['mute'], 1.0)
    b.rect(1.55, 4.45, 2.7, 0.14, c['s2']); b.rect(9.1, 3.95, 2.7, 0.14, c['s1'])
    b.rect(1.35, 1.95, 3.1, 1.55, c['s2'])
    b.rect(1.55, 2.05, 1.6, 0.28, "FFFFFF", kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5); b.txt(1.55, 2.05, 1.6, 0.28, "золотой стандарт", size=8.5, bold=True, color=c['s2'], align='c', anchor='m')
    b.txt(1.55, 2.4, 2.8, 0.6, FEMTO_T, size=11.5, bold=True, color="FFFFFF", anchor='m', spacing=1.05); b.txt(1.55, 3.0, 2.8, 0.5, FEMTO_D, size=8.5, color="EAF1FB", spacing=1.05)
    b.rect(8.9, 1.55, 3.1, 1.4, "FFFFFF", c['s1'], 2.0, dash=MSO_LINE.DASH)
    b.rect(9.1, 1.65, 1.7, 0.28, c['s1'], kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5); b.txt(9.1, 1.65, 1.7, 0.28, "предстоит изучить", size=8.5, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(9.1, 2.0, 2.0, 0.9, "Лентикулярная технология", size=11.5, bold=True, color=c['s1t'], anchor='m', spacing=1.05); b.txt(11.0, 1.85, 1.0, 1.1, "?", size=44, bold=True, color=c['s1'], align='c', anchor='m')
    oval(px, 2.3, 1.3, "FFFFFF", c['hair'], 1.0); b.pic("p2_22.png", 6.05, 2.0, 1.2, 0.6)
    tile(0.8, 5.55, 5.6, 1.25, 1, c4.B1, 11); tile(6.95, 5.55, 5.6, 1.25, 2, c4.B2, 10.5)


for fn in (F, G, H, I, J): fn()
b.prs.save("/tmp/variants3.pptx"); print("ok")
