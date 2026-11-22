"""Finalists: 5 (orange conference), 7 (purple minimal), 14 (Slidesgo forensic).
Slides are arranged after the author's original deck and revealed step by step (fade entrance on click)."""
import os, sys
import build3 as b
import build4 as c4
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
STYLE = {5: 'sq', 7: 'round', 14: 'line'}
TINT = {5: ("FCEFE6", "E6EEF8", "FFF7F1"), 7: ("FDEEE4", "E7EFFC", "F2F0FC"), 14: ("FDEEE4", "E6EDF9", "E9ECF6")}  # smile, femto, band


def T(): return b.T
def stl(): return STYLE[T()['n']]
def tint(i): return TINT[T()['n']][i]


# ------------------------------------------------------------------ animation
def grab(fn):
    before = len(list(b.sl.shapes)); fn(); return list(b.sl.shapes)[before:]


def add_anim(slide, groups):
    groups = [g for g in groups if g]
    n = [2]

    def nid():
        n[0] += 1; return n[0]
    clicks = ""
    for g in groups:
        inner = ""
        for k, sh in enumerate(g):
            sid = sh.shape_id
            node = "clickEffect" if k == 0 else "withEffect"
            inner += (f'<p:par><p:cTn id="{nid()}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                      f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
                      f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="500"/><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>')
        clicks += (f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    xml = (f'<p:timing xmlns:p="{P_NS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
           f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{clicks}</p:childTnLst></p:cTn>'
           '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    el = etree.fromstring(xml)
    sld = slide._element
    old = sld.find(f'{{{P_NS}}}timing')
    if old is not None: sld.remove(old)
    ext = sld.find(f'{{{P_NS}}}extLst')
    if ext is not None: ext.addprevious(el)
    else: sld.append(el)


# ------------------------------------------------------------------ small helpers
def panel(x, y, w, h, accent, tin):
    s = stl()
    if s == 'sq': b.rect(x, y, w, h, tin)
    elif s == 'round': b.rect(x, y, w, h, tin, kind=b.MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.07)
    else: b.rect(x, y, w, h, None, accent, 1.0)


def arrow(x1, y1, x2, y2, color, w=2.0):
    c = b.hair(x1, y1, x2, y2, color, w)
    ln = c.line._get_or_add_ln()
    te = etree.SubElement(ln, '{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd'); te.set('type', 'triangle'); te.set('w', 'med'); te.set('len', 'med')
    return c


def badge(x, y, n, color, d=0.46):
    b.rect(x, y, d / b.sx(), d, color, kind=b.MSO_SHAPE.OVAL)
    b.txt(x, y, d / b.sx(), d, str(n), size=13, bold=True, color="FFFFFF", align='c', anchor='m')


def tri(x, y, color, s=0.26):
    sh = b.rect(x, y, s / b.sx(), s, color, kind=MSO_SHAPE.ISOSCELES_TRIANGLE); sh.rotation = 90; return sh


# ------------------------------------------------------------------ slides after the original
def o_aktual1():
    b.slide("Актуальность")
    c = T()
    b.rect(0.8, 1.45, 11.75, 1.25, tint(2))
    b.txt(1.0, 1.45, 11.35, 1.25, [[("•  ", {'color': c['acc']}), c4.B1], [("•  ", {'color': c['acc']}), c4.B2]], size=13, anchor='m', after=4, spacing=1.08)
    b.txt(0.8, 3.0, 6.6, 0.9, "Хирургическая коррекция смешанного астигматизма", size=18, bold=True, color=c['tcolor'], align='c', anchor='m', spacing=1.05)
    b.pic("p2_22.png", 8.3, 2.85, 4.2, 2.8)
    arrow(3.9, 3.95, 2.7, 4.6, c['s2']); arrow(3.9, 3.95, 5.4, 4.6, c['s1'])
    b.txt(0.8, 4.7, 3.7, 1.5, [[("Эксимерлазерная технология (ФемтоЛАЗИК)", {'bold': True, 'color': c['s2t'], 'size': 13})],
                                [("Современный «золотой» стандарт в коррекции смешанного астигматизма", {'size': 11.5})]], align='c', spacing=1.1, after=6)
    b.txt(4.6, 4.7, 3.4, 0.6, [[("Лентикулярная технология", {'bold': True, 'color': c['s1t'], 'size': 13})]], align='c')
    b.rect(5.55, 5.35, 0.95 / b.sx(), 0.95, None, c['s1'], 2.0, MSO_SHAPE.OVAL)
    b.txt(5.55, 5.35, 0.95 / b.sx(), 0.95, "?", size=30, bold=True, color=c['s1'], align='c', anchor='m')
    c4.refs(6.62)


def o_aktual2():
    b.slide("Актуальность")
    c = T()
    b.rect(0.8, 1.55, 0.36 / b.sx(), 0.36, c['acc'], kind=MSO_SHAPE.OVAL); b.txt(0.8, 1.55, 0.36 / b.sx(), 0.36, "i", size=13, bold=True, color="FFFFFF", align='c', anchor='m')
    b.txt(1.35, 1.45, 8.6, 1.8, [[("Пилотное исследование на платформе ", {}), ("VisuMax", {'bold': True}),
                                  (" (Carl Zeiss Meditec AG) показало возможность коррекции смешанного астигматизма методом лентикулярной хирургии (Ganesh S. et al., 2024), однако методика пока не применяется в стандартной практике.", {})]], size=14, spacing=1.12)
    b.pic("p3_58.png", 10.4, 1.3, 2.1, 3.0, valign='t', frame=True)
    b.hair(0.8, 4.4, 12.5, 4.4)
    b.pic("p3_63.png", 0.8, 4.6, 2.6, 2.3)
    b.txt(3.7, 4.7, 6.0, 2.0, [[("Экспериментальное исследование ex-vivo (11 свиных глаз) на платформе ", {}), ("Elita", {'bold': True}),
                                 (", Johnson and Johnson Surgical Vision, Inc. (США) свидетельствуют о технической возможности коррекции смешанного астигматизма и гиперметропии.", {})]], size=14, spacing=1.12)
    b.pic("p3_62.png", 10.4, 4.55, 2.1, 2.3, valign='t', frame=True)
    b.txt(10.0, 4.4, 2.5, 0.2, "", size=6)
    b.txt(7.6, 4.15, 2.6, 0.22, "Ganesh S. et al., 2024  ·  ARVO, 2025", size=7.5, color=c['mute'], align='r')


def o_goal():
    b.slide("Цель")
    c = T()
    panel(1.0, 1.9, 11.3, 1.7, c['acc'], tint(2))
    b.txt(1.3, 1.9, 10.7, 1.7, "Разработать лентикулярную технологию для коррекции смешанного астигматизма", size=26, color=c['tcolor'], align='c', anchor='m', spacing=1.1)
    b.pic("p4_74.png", 7.4, 4.0, 5.3, 3.0)


def o_methods():
    b.slide("Материалы и методы")
    c = T(); sl = b.sl
    groups = []
    data = [(0.8, 5.8, "1", "ГРУППА 1", "Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", c['s1'], c['s1t'], tint(0), ("p5_87.png", "p5_86.png"), ((0.8, 4.35, 3.3, 2.5), (4.25, 4.45, 2.3, 2.3))),
            (6.8, 5.75, "2", "ГРУППА 2", "Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", c['s2'], c['s2t'], tint(1), ("p5_88.png", "p5_89.png"), ((6.8, 4.35, 3.4, 2.5), (10.3, 4.45, 2.2, 2.3)))]
    obs = None
    for x, w, num, lab, ttl, dev, col, colt, tin, imgs, pos in data:
        def card():
            panel(x, 1.45, w, 2.4, col, tin)
            badge(x + 0.15, 1.6, num, col)
            b.txt(x + 0.8, 1.62, 3, 0.3, lab, size=9.5, bold=True, color=colt, anchor='m')
            b.txt(x + 0.3, 2.1, w - 0.6, 0.7, ttl, size=14, bold=True, color=colt, align='c', anchor='m', spacing=1.05)
            b.txt(x + 0.3, 2.8, w - 0.6, 0.6, dev, size=9.5, italic=True, align='c', spacing=1.05)
            b.txt(x + 0.3, 3.45, w - 0.6, 0.3, "20 пациентов (40 глаз)", size=11.5, bold=True, align='c')
        groups.append(grab(card))
        groups.append(grab(lambda: [b.pic(imgs[0], *pos[0]), b.pic(imgs[1], *pos[1])]))
    groups.append(grab(lambda: b.txt(0.8, 3.95, 11.75, 0.3, "Наблюдение проводилось до операции и в стандартные сроки – 1 сутки, 3 и 6 месяцев", size=11, bold=True, align='c')))
    # reorder: g1 card, g1 imgs, g2 card, g2 imgs, obs -> obs after both cards (kept last)
    add_anim(sl, groups)


def o_diag():
    b.slide("Методы диагностики")
    c = T(); sl = b.sl; groups = []
    left_fill, right_fill = c['acc'], c['c2'] if c['n'] != 14 else c['s2']

    def head(x, w, text, fill):
        b.rect(x, 1.4, w, 0.5, fill); b.txt(x + 0.1, 1.4, w - 0.2, 0.5, text, size=13, bold=True, color="FFFFFF", align='c', anchor='m')
    groups.append(grab(lambda: head(0.8, 5.9, "Стандартные методы диагностики", left_fill)))
    for i, (a, t) in enumerate(c4.STD):
        def item(i=i, a=a, t=t):
            y = 2.05 + i * 0.78; b.rect(0.8, y, 5.9, 0.7, "FFFFFF", c['hair'], 0.9)
            b.txt(1.0, y, 5.5, 0.7, [[(a, {'bold': True, 'size': 12})]] + ([[(t, {'size': 9.5, 'color': c['mute']})]] if t else []), anchor='m', spacing=1.05)
        groups.append(grab(item))
    groups.append(grab(lambda: head(7.0, 5.55, "Специальные методы диагностики", right_fill)))
    for i, (a, t) in enumerate(c4.SPEC):
        def item(i=i, a=a, t=t):
            y = 2.05 + i * 0.78; b.rect(7.0, y, 5.55, 0.7, "FFFFFF", c['hair'], 0.9)
            b.txt(7.2, y, 5.2, 0.7, [[(a, {'bold': True, 'size': 12})], [(t, {'size': 9.5, 'color': c['mute']})]], anchor='m', spacing=1.05)
        groups.append(grab(item))
    groups.append(grab(lambda: [b.pic("p7_112.png", 0.9, 5.3, 0.95, 1.65), b.pic("p7_122.png", 2.0, 5.3, 2.3, 1.65), b.pic("p7_121.png", 4.4, 5.3, 2.2, 1.65), b.pic("p7_113.png", 7.3, 5.3, 5.0, 1.65)]))
    add_anim(sl, groups)


def o_steps():
    b.slide("Лентикулярная технология коррекции смешанного астигматизма")
    c = T(); sl = b.sl; groups = []
    b.rect(0.8, 1.4, 8.4, 0.46, None, c['acc'], 1.0)
    b.txt(0.95, 1.4, 8.2, 0.46, "Транспозиция исходной рефракции (sph, cyl, ax) по разработанной технологии:", size=11.5, bold=True, anchor='m')
    steps = [("Шаг 1", "Условия допуска:", ["Sph ≤ +1,75D", "Cyl ≥ −5D", "SE ≤ −0,75D"]), ("Шаг 2", "Транспозиция сферы", ["SPH' = SPH + CYL"]), ("Шаг 3", "Инверсия цилиндра", ["CYL' = −CYL (знак +)"]),
             ("Шаг 4", "Коррекция оси", ["Ax ≤ 90° → +90°;", "AX > 90° → −90°.", "Ручная маркировка роговицы для минимизации циклоторсии (ось астигматизма)"])]
    for i, (h, ttl, body) in enumerate(steps):
        x = 0.8 + i * 2.95
        def box(i=i, h=h, ttl=ttl, body=body, x=x):
            if i: tri(x - 0.27, 3.15, c['acc'])
            b.rect(x, 2.15, 2.7, 2.55, "FFFFFF", c['acc'], 1.2)
            b.txt(x + 0.15, 2.22, 2.4, 0.4, h, size=14, bold=True, color=c['acc'], align='c', anchor='m')
            b.txt(x + 0.15, 2.65, 2.4, 0.4, ttl, size=11.5, bold=True, align='c', anchor='m')
            lines = body if i != 3 else body[:2] + [("", {})] if False else body
            b.txt(x + 0.15, 3.1, 2.4, 1.55, [[(l, {'size': 10 if len(l) > 28 else 11.5, 'bold': len(l) < 28})] for l in body], align='c', spacing=1.08, after=2)
        groups.append(grab(box))
    groups.append(grab(lambda: [b.pic("p8_153.png", 0.8, 4.95, 3.0, 1.75, frame=True), b.txt(0.8, 6.68, 3.0, 0.25, "Маркерная разметка роговицы для контроля циклоторсии", size=7.5, italic=True, color=c['mute'], align='c')]))

    def step5():
        tri(4.0, 5.55, c['acc'])
        b.rect(4.55, 4.95, 8.0, 1.75, "FFFFFF", c['acc'], 1.2)
        b.txt(4.55, 5.0, 8.0, 0.45, "Шаг 5", size=14, bold=True, color=c['acc'], align='c', anchor='m')
        b.txt(4.75, 5.45, 7.6, 0.55, "Ввод полученных рефракционных данных в фемтосекундную лазерную установку", size=12, bold=True, align='c', anchor='m')
        b.txt(4.75, 6.05, 7.6, 0.6, "(Согласно инструкции к VisuMax®, возможна коррекция близорукости от −0,50 дптр до −10,00 дптр и астигматизма до −5,00 дптр)", size=9, align='c', color=c['mute'], anchor='m')
    groups.append(grab(step5))
    b.txt(0.8, 6.98, 12, 0.2, c4.__dict__.get('REFS_STEPS', "Розенблюм Ю.З. Оптометрия. СПб.: Гиппократ; 1996.  ·  Гамидов Г.А. и др. Способ контроля циклоторсии глазного яблока при коррекции миопического астигматизма по технологии SMILE. Офтальмология. 2020; 17(3): 351-360."), size=5.5, italic=True, color=c['mute'])
    add_anim(sl, groups)


from pptx.enum.dml import MSO_LINE


def chip(x, y, w, h, text, fill, color="FFFFFF", size=9):
    b.rect(x, y, w, h, fill, kind=b.MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
    b.txt(x, y, w, h, text, size=size, bold=True, color=color, align='c', anchor='m')


def o_aktual1():
    b.slide("Актуальность")
    c = T()
    # two statements as numbered tiles
    for i, (x, w, text) in enumerate(((0.8, 4.4, c4.B1), (5.4, 7.15, c4.B2))):
        panel(x, 1.4, w, 1.2, c['acc'], tint(2))
        b.txt(x + 0.2, 1.4, 0.7, 1.2, f"0{i+1}", size=26, bold=True, color=c['acc'], anchor='m')
        b.txt(x + 0.95, 1.4, w - 1.15, 1.2, text, size=11.5 if i else 12, anchor='m', spacing=1.1)
    # heading + eye with halo rings
    b.txt(0.8, 2.85, 8.0, 0.55, "Хирургическая коррекция смешанного астигматизма", size=20, bold=True, color=c['tcolor'], anchor='m')
    b.ring(11.0, 4.4, 3.4, c['hair'], 1.0, MSO_LINE.DASH); b.ring(11.0, 4.4, 2.7, c['hair'], 1.0)
    b.pic("p2_22.png", 9.4, 3.15, 3.2, 2.5)
    # fork connector
    hx = 4.75
    b.hair(hx, 3.45, hx, 3.78, c['mute'], 1.5); b.hair(2.75, 3.78, 6.75, 3.78, c['mute'], 1.5)
    arrow(2.75, 3.78, 2.75, 4.2, c['s2'], 2.0); arrow(6.75, 3.78, 6.75, 4.2, c['s1'], 2.0)
    # left card: FemtoLASIK (known, gold standard)
    b.rect(0.8, 4.25, 3.9, 2.25, "FFFFFF", c['s2'], 1.5)
    b.rect(0.8, 4.25, 3.9, 0.09, c['s2'])
    chip(2.55, 4.0, 1.6, 0.34, "золотой стандарт", c['s2'], size=9)
    b.txt(1.0, 4.5, 3.5, 0.75, "Эксимерлазерная технология (ФемтоЛАЗИК)", size=14, bold=True, color=c['s2t'], anchor='m', spacing=1.05)
    b.txt(1.0, 5.3, 3.5, 1.1, "Современный «золотой» стандарт в коррекции смешанного астигматизма", size=11.5, spacing=1.1)
    # right card: lenticular (open question)
    b.rect(4.9, 4.25, 3.9, 2.25, "FFFFFF", c['s1'], 1.5, dash=MSO_LINE.DASH)
    b.rect(4.9, 4.25, 3.9, 0.09, c['s1'])
    chip(6.7, 4.0, 1.6, 0.34, "предстоит изучить", c['s1'], size=9)
    b.txt(5.1, 4.5, 2.3, 1.2, "Лентикулярная технология", size=14, bold=True, color=c['s1t'], anchor='m', spacing=1.05)
    b.ring(7.85, 5.4, 1.7, c['s1l'], 1.0)
    b.rect(7.4, 4.95, 0.9 / b.sx(), 0.9, "FFFFFF", c['s1'], 2.0, MSO_SHAPE.OVAL)
    b.txt(7.4, 4.95, 0.9 / b.sx(), 0.9, "?", size=32, bold=True, color=c['s1'], align='c', anchor='m')
    c4.refs(6.62)


def o_methods():
    b.slide("Материалы и методы")
    c = T(); sl = b.sl; groups = []
    cards = [(0.8, "1", "ГРУППА 1", "SMILE", "Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", c['s1'], c['s1t'], tint(0), ("p5_87.png", "p5_86.png")),
             (6.85, "2", "ГРУППА 2", "ФемтоЛАЗИК", "Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", c['s2'], c['s2t'], tint(1), ("p5_88.png", "p5_89.png"))]
    for x, num, lab, short, ttl, dev, col, colt, tin, imgs in cards:
        def card(x=x, num=num, lab=lab, short=short, ttl=ttl, dev=dev, col=col, colt=colt, tin=tin, imgs=imgs):
            w = 5.7
            panel(x, 1.4, w, 4.65, col, tin)
            kind = b.MSO_SHAPE.ROUNDED_RECTANGLE if stl() == 'round' else b.MSO_SHAPE.RECTANGLE
            b.rect(x + 0.2, 1.6, w - 0.4, 0.5, col, kind=kind, adj=0.5 if kind != b.MSO_SHAPE.RECTANGLE else None)
            b.txt(x + 0.4, 1.6, 3, 0.5, f"{lab}", size=10.5, bold=True, color="FFFFFF", anchor='m')
            b.txt(x + 2.6, 1.6, w - 3.0, 0.5, short, size=12, bold=True, color="FFFFFF", align='r', anchor='m')
            b.txt(x + 0.35, 2.2, w - 0.7, 0.55, ttl, size=15, bold=True, color=colt, anchor='m', spacing=1.05)
            b.txt(x + 0.35, 2.78, w - 0.7, 0.6, dev, size=9.5, italic=True, spacing=1.05, color=c['mute'])
            b.txt(x + 0.3, 3.35, 1.7, 1.0, "20", size=60, bold=True, color=col, anchor='m')
            b.txt(x + 1.85, 3.5, 1.6, 0.75, [[("пациентов", {'bold': True})], [("(40 глаз)", {})]], size=12, anchor='m', spacing=1.1)
            b.pic(imgs[0], x + 0.3, 4.4, 3.0, 1.5); b.pic(imgs[1], x + 3.6, 4.35, 1.8, 1.6)
        groups.append(grab(card))
    def lab():
        b.txt(0.8, 6.2, 3.4, 0.7, "Наблюдение проводилось до операции и в стандартные сроки", size=10.5, bold=True, anchor='m', spacing=1.1)
        b.hair(4.4, 6.55, 12.5, 6.55, c['acc'], 1.5)
    groups.append(grab(lab))
    for i, t in enumerate(c4.TIMELINE):
        def ms(i=i, t=t):
            cx = 5.2 + i * 2.35
            b.rect(cx - 0.13, 6.42, 0.26 / b.sx(), 0.26, c['acc'] if i else "FFFFFF", c['acc'], 1.5, MSO_SHAPE.OVAL)
            b.txt(cx - 1.0, 6.72, 2.0, 0.25, t, size=10.5, align='c')
        groups.append(grab(ms))
    add_anim(sl, groups)


def o_steps():
    b.slide("Лентикулярная технология коррекции смешанного астигматизма")
    c = T(); sl = b.sl; groups = []
    b.rect(0.8, 1.35, 8.4, 0.44, None, c['acc'], 1.0)
    b.txt(0.95, 1.35, 8.2, 0.44, "Транспозиция исходной рефракции (sph, cyl, ax) по разработанной технологии:", size=11.5, bold=True, anchor='m')
    steps = [("1", "Условия допуска:", ["Sph ≤ +1,75D", "Cyl ≥ −5D", "SE ≤ −0,75D"]), ("2", "Транспозиция сферы", ["SPH' = SPH + CYL"]), ("3", "Инверсия цилиндра", ["CYL' = −CYL (знак +)"]),
             ("4", "Коррекция оси", ["Ax ≤ 90° → +90°;", "AX > 90° → −90°.", "Ручная маркировка роговицы для минимизации циклоторсии (ось астигматизма)"]),
             ("5", "Ввод данных в лазер", ["Ввод полученных рефракционных данных в фемтосекундную лазерную установку", "(Согласно инструкции к VisuMax®, возможна коррекция близорукости от −0,50 дптр до −10,00 дптр и астигматизма до −5,00 дптр)"])]
    hs = [2.25, 2.7, 3.15, 3.7, 4.3]; bottom = 6.7
    for i, (n, ttl, body) in enumerate(steps):
        x = 0.8 + i * 2.37; h = hs[i]; y = bottom - h; last = i == 4
        def box(i=i, n=n, ttl=ttl, body=body, x=x, h=h, y=y, last=last):
            fill = c['acc'] if last else "FFFFFF"
            b.rect(x, y, 2.27, h, fill, c['acc'], 1.2)
            if not last: b.rect(x, y, 2.27, 0.09, c['acc'])
            fg = "FFFFFF" if last else c['ink']
            b.txt(x + 0.18, y + 0.15, 1.2, 0.7, f"0{n}", size=30, bold=True, color="FFFFFF" if last else c['acc'], anchor='m')
            b.txt(x + 0.18, y + 0.88, 1.95, 0.5, ttl, size=12, bold=True, color=fg, anchor='m', spacing=1.05)
            if i == 4:
                b.txt(x + 0.18, y + 1.45, 1.95, 1.35, body[0], size=10.5, color=fg, spacing=1.1)
                b.txt(x + 0.18, y + 2.85, 1.95, 1.4, body[1], size=8.5, color="E4E8F6", spacing=1.08)
            else:
                b.txt(x + 0.18, y + 1.42, 1.95, h - 1.5, [[(l, {'size': 10 if len(l) > 28 else 12, 'bold': len(l) < 28})] for l in body], color=fg, spacing=1.08, after=2)
        groups.append(grab(box))
        if i == 3:
            groups.append(grab(lambda: [b.pic("p8_153.png", 0.8, 2.0, 2.3, 1.55, frame=True), b.txt(0.8, 3.6, 2.3, 0.36, "Маркерная разметка роговицы для контроля циклоторсии", size=7.5, italic=True, color=c['mute'], align='c')]))
    b.txt(0.8, 6.98, 12, 0.2, "Розенблюм Ю.З. Оптометрия. СПб.: Гиппократ; 1996.  ·  Гамидов Г.А. и др. Способ контроля циклоторсии глазного яблока при коррекции миопического астигматизма по технологии SMILE. Офтальмология. 2020; 17(3): 351-360.", size=5.5, italic=True, color=c['mute'])
    add_anim(sl, groups)


OVR = {
    5: dict(aktual1=o_aktual1, aktual2=o_aktual2, methods=o_methods, diag=o_diag, steps=o_steps),
    7: dict(aktual1=o_aktual1, aktual2=o_aktual2, methods=o_methods, diag=o_diag, steps=o_steps),
    14: dict(aktual1=o_aktual1, goal=o_goal, methods=o_methods, diag=o_diag, steps=o_steps),
}


def sequence(n):
    tbl = n in (1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14)
    base = dict(title=b.s_title, aktual1=b.s_aktual1, aktual2=b.s_aktual2, goal=b.s_goal, methods=b.s_methods, ranges=b.s_ranges_tbl if tbl else b.s_ranges, diag=b.s_diag, steps=b.s_steps_v,
                operation=b.s_operation, patent=b.s_patent, criteria=b.s_criteria, p_smile=b.s_p_smile, p_fl=b.s_p_fl, model=b.s_model, acuity=b.s_acuity, refraction=b.s_refraction,
                safety=b.s_safety, predict=b.s_predict, concl=b.s_conclusions, end=b.s_end)
    ov = dict(c4.OVR.get(n, {})); ov.update(OVR.get(n, {}))
    order = ['title', 'aktual1', 'aktual2', 'goal', 'methods', 'ranges', 'diag', 'steps', 'operation', 'patent', 'criteria', 'p_smile', 'p_fl', 'model', 'acuity', 'refraction', 'safety', 'predict', 'concl', 'end']
    return [ov.get(k, base[k]) for k in order]


def build(n):
    th = next(t for t in b.THEMES if t['n'] == n)
    b.T = th; b.PAGE = 0
    if n == 14:
        F = 0.75
        b.I = lambda v: Inches(v * F); b.Pt = lambda v: Pt(v * F)
        b.SANS = "Assistant"; b.SERIF = "Assistant"
        import build_sg_helpers as sg
        sg.setup()
    else:
        b.prs = Presentation(); b.prs.slide_width, b.prs.slide_height = Inches(13.333), Inches(7.5)
    for fn in sequence(n): fn()
    os.makedirs("../presentations", exist_ok=True)
    out = f"../presentations/{th['name']}.pptx"
    b.prs.save(out); print("saved", out)


if __name__ == "__main__":
    build(int(sys.argv[1]))
