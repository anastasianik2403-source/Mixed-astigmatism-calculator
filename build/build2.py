from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

FONT = "Arial"
TITLE, NAVY, MUTED, HAIR = "0D2B2B", "26357A", "6C7AA6", "BAC4E2"
IND, INDL = "2F3E9E", "A9BAF3"       # SMILE
TEAL, TEALL = "1B5E5A", "9CCBC4"     # ФемтоЛАЗИК
IMG = "img/"
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
I = Inches
PAGE = [0]


def rgb(h): return RGBColor.from_string(h)


def _strip(s):
    st = s._element.find(qn('p:style'))
    if st is not None: s._element.remove(st)


def shape(sl, kind, x, y, w, h, fill=None, line=None, lw=0.75, dash=None, alpha=None):
    s = sl.shapes.add_shape(kind, I(x), I(y), I(w), I(h))
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            clr = s._element.spPr.find(qn('a:solidFill'))[0]
            etree.SubElement(clr, qn('a:alpha')).set('val', str(int(alpha * 1000)))
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
        if dash: s.line.dash_style = dash
    else:
        s.line.fill.background()
    etree.SubElement(s._element.spPr, qn('a:effectLst'))
    _strip(s)
    return s


def txt(sl, x, y, w, h, paras, size=12, color=NAVY, bold=False, align='l', anchor='t', italic=False, spacing=None, after=0):
    tb = sl.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    if isinstance(paras, str): paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
        if spacing: para.line_spacing = spacing
        para.space_after = Pt(after)
        for r in (p if isinstance(p, list) else [p]):
            t, o = (r, {}) if isinstance(r, str) else r
            run = para.add_run(); run.text = t
            f = run.font; f.name = FONT; f.size = Pt(o.get('size', size))
            f.bold = o.get('bold', bold); f.italic = o.get('italic', italic); f.color.rgb = rgb(o.get('color', color))
    return tb


def hair(sl, x1, y1, x2, y2, color=HAIR, w=0.75, dash=None):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(w)
    if dash: c.line.dash_style = dash
    _strip(c)
    return c


def dot(sl, x, y, r=0.045, color=NAVY):
    shape(sl, MSO_SHAPE.OVAL, x - r, y - r, 2 * r, 2 * r, color)


def ring(sl, cx, cy, d, color="C9D2EC", w=0.6, dash=None):
    return shape(sl, MSO_SHAPE.OVAL, cx - d / 2, cy - d / 2, d, d, None, color, w, dash)


def orb(sl, cx, cy, d, label=None, size=12, bold=False, color=NAVY, halo=True, strong=False):
    if halo: ring(sl, cx, cy, d * 1.45)
    s = shape(sl, MSO_SHAPE.OVAL, cx - d / 2, cy - d / 2, d, d, "D5DEFA")
    sp = s._element.spPr
    for tag in ('a:solidFill', 'a:noFill'):
        e = sp.find(qn(tag))
        if e is not None: sp.remove(e)
    c0, c1, c2 = ("E6ECFD", "CBD7F9", "A4B6F1") if strong else ("F1F4FE", "DCE4FB", "BCCBF6")
    g = etree.fromstring(
        '<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1"><a:gsLst>'
        f'<a:gs pos="0"><a:srgbClr val="{c0}"/></a:gs><a:gs pos="62000"><a:srgbClr val="{c1}"/></a:gs><a:gs pos="100000"><a:srgbClr val="{c2}"/></a:gs>'
        '</a:gsLst><a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>')
    sp.find(qn('a:prstGeom')).addnext(g)
    if label is not None:
        txt(sl, cx - d / 2 + 0.08, cy - d / 2, d - 0.16, d, label, size=size, bold=bold, color=color, align='c', anchor='m')
    return s


def pic(sl, name, x, y, w, h, halign='c', valign='m', frame=False):
    path = IMG + name
    iw, ih = Image.open(path).size
    sc = min(w / iw, h / ih); pw, ph = iw * sc, ih * sc
    px = x + (w - pw) / 2 if halign == 'c' else (x if halign == 'l' else x + w - pw)
    py = y + (h - ph) / 2 if valign == 'm' else (y if valign == 't' else y + h - ph)
    if frame:
        shape(sl, MSO_SHAPE.RECTANGLE, px - 0.03, py - 0.03, pw + 0.06, ph + 0.06, "FFFFFF", "D7DDEF", 0.6)
    return sl.shapes.add_picture(path, I(px), I(py), I(pw), I(ph))


def slide(title, bgname='plain', sub=None):
    sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
    sl.shapes.add_picture(IMG + f"m_{bgname}.png", 0, 0, prs.slide_width, prs.slide_height)
    txt(sl, 0.8, 0.5, 11.2, 0.5, title, size=24 if len(title) < 48 else 21, bold=True, color=TITLE)
    if sub: txt(sl, 0.8, 1.02, 11.5, 0.3, sub, size=11.5, color=MUTED, italic=True)
    txt(sl, 0.8, 7.12, 5, 0.2, "КАТАРАКТА 2026  ·  Никитина А.Е.", size=8, color=MUTED)
    txt(sl, 11.9, 7.12, 0.65, 0.2, f"{PAGE[0]:02d}", size=8.5, bold=True, color=MUTED, align='r')
    return sl


def chart_clear(chart):
    sp = etree.Element(qn('c:spPr'))
    etree.SubElement(sp, qn('a:noFill'))
    etree.SubElement(etree.SubElement(sp, qn('a:ln')), qn('a:noFill'))
    chart._chartSpace.find(qn('c:chart')).addnext(sp)


def style_axes(chart, vmin, vmax, major, size=10):
    va = chart.value_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = vmin, vmax, major
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("DDE2F0"); va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(size); va.tick_labels.font.color.rgb = rgb(MUTED); va.tick_labels.font.name = FONT
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(size); ca.tick_labels.font.color.rgb = rgb(NAVY); ca.tick_labels.font.name = FONT
    ca.format.line.color.rgb = rgb("AEB9DC"); ca.has_major_gridlines = False


def bar_chart(sl, x, y, w, h, cats, series, colors, vmin, vmax, major, fmt='0.00', legend=True, lsize=10, gap=60):
    cd = CategoryChartData(); cd.categories = cats
    for n, v in series: cd.add_series(n, v)
    ch = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(x), I(y), I(w), I(h), cd).chart
    chart_clear(ch); ch.font.name = FONT
    pl = ch.plots[0]; pl.gap_width = gap; pl.overlap = -6
    for s, c in zip(pl.series, colors):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c); s.invert_if_negative = False
    pl.has_data_labels = True
    dl = pl.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False
    dl.font.size = Pt(lsize); dl.font.bold = True; dl.font.color.rgb = rgb(TITLE); dl.position = XL_LABEL_POSITION.OUTSIDE_END
    style_axes(ch, vmin, vmax, major, lsize)
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(lsize); ch.legend.font.color.rgb = rgb(NAVY)
    return ch


# ============ 1. TITLE ============
sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
sl.shapes.add_picture(IMG + "m_title.png", 0, 0, prs.slide_width, prs.slide_height)
txt(sl, 0.85, 0.85, 9.6, 3.3, [[("Современный подход к хирургической коррекции смешанного астигматизма", {'bold': True, 'size': 36})],
                                [("с применением фемтосекундной лентикулярной технологии", {'size': 28})]], color=TITLE, spacing=1.05, after=6)
hair(sl, 0.85, 4.45, 9.2, 4.45)
txt(sl, 0.85, 4.75, 8.5, 0.3, [[("Докладчик: ", {'color': MUTED}), ("Никитина Анастасия Евгеньевна", {'bold': True})]], size=14)
txt(sl, 0.85, 5.15, 8.8, 0.3, "Соавторы: д.м.н. Костенев С.В., к.м.н. Макаров Р.А., Садрутдинов Р.Ш.", size=12)
txt(sl, 0.85, 5.85, 8.8, 0.5, ["ФГБОУ ВО «Российский университет медицины» Минздрава России",
                                "ФГАУ «НМИЦ «МНТК «Микрохирургия глаза» им. акад. С.Н. Федорова» Минздрава России"], size=9.5, color=MUTED, spacing=1.15)
txt(sl, 0.85, 6.75, 11, 0.3, [[("КАТАРАКТА 2026", {'bold': True}), ("   2–4 сентября 2026   ·   Москва, Конгресс-центр ЦМТ", {})]], size=10.5)

# ============ 2. АКТУАЛЬНОСТЬ 1 ============
sl = slide("Актуальность", 'soft')
hair(sl, 4.7, 0, 4.7, 3.55)
pic(sl, "p2_22.png", 0.8, 1.3, 3.5, 2.3)
txt(sl, 5.1, 1.0, 7.5, 2.4, [[("•  ", {'color': IND, 'bold': True}), "Астигматизм — мультифакторное состояние с выраженным наследственным компонентом."],
                              [("•  ", {'color': IND, 'bold': True}), "Полногеномные исследования (Shing E. et al., 2024) выявили свыше 50 полиморфизмов в 10 генах, включая локус PDGFRA, регулирующий кривизну роговицы."]],
    size=15, color=TITLE, after=12, spacing=1.12)
txt(sl, 0.8, 3.85, 11, 0.3, "Хирургическая коррекция смешанного астигматизма", size=13, bold=True, color=TITLE)
hair(sl, 0.8, 4.2, 12.5, 4.2, "D4DBEE")
hair(sl, 3.5, 4.85, 8.8, 4.85)
orb(sl, 3.5, 4.85, 1.4, "ФемтоЛАЗИК", 12, True)
orb(sl, 8.8, 4.85, 1.4, [[("?", {'size': 30, 'bold': True})]], 12, False, strong=True)
txt(sl, 1.75, 5.75, 3.5, 0.6, [[("Эксимерлазерная технология. Современный ", {}), ("«золотой»", {'bold': True}), (" стандарт в коррекции смешанного астигматизма", {})]], size=10, color=NAVY, align='c')
txt(sl, 7.05, 5.75, 3.5, 0.5, [[("Лентикулярная технология", {'bold': True})]], size=11, color=NAVY, align='c')
txt(sl, 0.8, 6.55, 11.8, 0.55, [
    "Азара Д.Т., Алио Х.Л., Кортина М.С., Халлака Д.А. Хирургическое лечение астигматизма. Москва: ГЭОТАР-Медиа, 2025. — 272 с. doi: 10.33029/9704-8200-1-STA-2025-1-272; Shing E. et al. Heritability and Genetic Factors of Astigmatism and Corneal Curvature. Am J Ophthalmol. 2025;269:161–171. doi: 10.1016/j.ajo.2024.08.019; Клокова О.А. и др. Ранние клинико-функциональные результаты коррекции смешанного астигматизма в зависимости от его степени с помощью высокочастотного эксимерного лазера Schwind Amaris 1050RS. Офтальмология. 2025;22(2):295–304. https://doi.org/10.18008/1816-5095-2025-2-295-304"],
    size=6, italic=True, color=MUTED, spacing=0.95)

# ============ 3. АКТУАЛЬНОСТЬ 2 ============
sl = slide("Актуальность", 'plain')
txt(sl, 0.8, 1.45, 8.2, 1.2, [[("Пилотное исследование на платформе ", {}), ("VisuMax", {'bold': True}), (" (Carl Zeiss Meditec AG) показало возможность коррекции смешанного астигматизма методом лентикулярной хирургии (Ganesh S. et al., 2024), однако методика пока не применяется в стандартной практике.", {})]], size=13, color=TITLE, spacing=1.12)
hair(sl, 0.8, 2.85, 8.9, 2.85); dot(sl, 8.9, 2.85)
txt(sl, 3.9, 3.35, 5.9, 1.3, [[("Экспериментальное исследование ex-vivo (11 свиных глаз) на платформе ", {}), ("Elita", {'bold': True}), (", Johnson and Johnson Surgical Vision, Inc. (США) свидетельствуют о технической возможности коррекции смешанного астигматизма и гиперметропии.", {})]], size=13, color=TITLE, spacing=1.12)
hair(sl, 3.9, 4.85, 9.9, 4.85); dot(sl, 9.9, 4.85)
pic(sl, "p3_63.png", 0.8, 3.35, 2.8, 3.4, frame=False)
pic(sl, "p3_58.png", 10.15, 1.0, 1.25, 2.9, valign='t', frame=True)
pic(sl, "p3_62.png", 11.55, 1.0, 1.25, 2.9, valign='t', frame=True)
txt(sl, 10.0, 2.75, 1.5, 0.3, "Ganesh S. et al., 2024", size=7.5, color=MUTED, align='c')
txt(sl, 11.4, 3.35, 1.5, 0.3, "ARVO, 2025", size=7.5, color=MUTED, align='c')

# ============ 4. ЦЕЛЬ ============
sl = slide("Цель", 'arch')
hair(sl, 4.7, 0, 4.7, 4.6)
txt(sl, 5.1, 2.5, 7.4, 2.0, "Разработать лентикулярную технологию для коррекции смешанного астигматизма", size=28, color=TITLE, spacing=1.1)
pic(sl, "p4_74.png", 1.2, 4.6, 4.6, 2.5)

# ============ 5. МАТЕРИАЛЫ И МЕТОДЫ ============
sl = slide("Материалы и методы", 'plain')
hair(sl, 3.9, 2.85, 9.4, 2.85)
orb(sl, 3.9, 2.85, 2.2, [[("SMILE", {'size': 20, 'bold': True})], [("20 пациентов", {'size': 11})], [("(40 глаз)", {'size': 11})]], 12)
orb(sl, 9.4, 2.85, 2.2, [[("ФемтоЛАЗИК", {'size': 16, 'bold': True})], [("20 пациентов", {'size': 11})], [("(40 глаз)", {'size': 11})]], 12, strong=True)
txt(sl, 2.4, 1.1, 3, 0.25, "ГРУППА 1", size=9, bold=True, color=MUTED, align='c')
txt(sl, 7.9, 1.1, 3, 0.25, "ГРУППА 2", size=9, bold=True, color=MUTED, align='c')
txt(sl, 2.0, 4.55, 3.8, 1.0, [[("Лентикулярная технология (SMILE)", {'bold': True, 'size': 12.5, 'color': TITLE})], [("Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", {'italic': True, 'size': 9.5})]], align='c', spacing=1.1, after=3)
txt(sl, 7.5, 4.55, 3.8, 1.0, [[("Эксимерлазерная технология (ФемтоЛАЗИК)", {'bold': True, 'size': 12.5, 'color': TITLE})], [("Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", {'italic': True, 'size': 9.5})]], align='c', spacing=1.1, after=3)
pic(sl, "p5_87.png", 0.7, 1.7, 1.7, 1.5); pic(sl, "p5_86.png", 0.95, 3.2, 1.2, 1.2)
pic(sl, "p5_88.png", 11.0, 1.7, 1.8, 1.5); pic(sl, "p5_89.png", 11.3, 3.2, 1.2, 1.2)
txt(sl, 0.8, 5.55, 4, 0.3, "Наблюдение проводилось до операции и в стандартные сроки", size=10, bold=True, color=TITLE)
hair(sl, 0.8, 6.4, 12.5, 6.4)
for i, lab in enumerate(["До операции", "1 сутки", "3 месяца", "6 месяцев"]):
    cx = 1.5 + i * 3.45
    dot(sl, cx, 6.4, 0.06); txt(sl, cx - 1, 6.55, 2, 0.3, lab, size=10.5, color=NAVY, align='c')

# ============ 6. ДИАПАЗОН ============
sl = slide("Диапазон рефракционных значений в исследуемых группах", 'plain')
cols = [(0.8, 3.0), (4.0, 3.6), (8.2, 3.9)]
txt(sl, 4.0, 1.25, 3.6, 0.5, [[("Лентикулярная технология", {'bold': True, 'size': 12, 'color': IND})], [("(SMILE)", {'size': 10, 'color': IND})]], spacing=1.0)
txt(sl, 8.2, 1.25, 3.9, 0.5, [[("Эксимерлазерная технология", {'bold': True, 'size': 12, 'color': TEAL})], [("(ФемтоЛАЗИК)", {'size': 10, 'color': TEAL})]], spacing=1.0)
rows = [("Сферический компонент (Sph)", ("от +0,25 до +1,75 D", "M ± SD +0,54 ± 0,39"), ("от +0,25 до +3,00 D", "M ± SD +1,25 ± 0,81")),
        ("Цилиндрический компонент (Cyl)", ("от −2,00 до −5,00 D", "M ± SD −3,07 ± 0,93"), ("от −1,25 до −6,00 D", "M ± SD −3,24 ± 2,03")),
        ("Кератометрия, D", ("K1 41,58 · K2 44,44", "K AVE 43,00"), ("K1 41,69 · K2 44,76", "K AVE 43,22")),
        ("Пахиметрия, мкм", ("от 494 до 615 мкм", "M ± SD 554,1 ± 36,2"), ("от 483 до 596 мкм", "M ± SD 537,1 ± 30,8"))]
for i, (lab, a, b) in enumerate(rows):
    y = 1.95 + i * 0.82
    hair(sl, 0.8, y - 0.08, 12.5, y - 0.08, "D4DBEE")
    txt(sl, 0.8, y, 3.0, 0.7, lab, size=11.5, bold=True, color=TITLE, anchor='m')
    txt(sl, 4.0, y, 3.6, 0.7, [[(a[0], {'bold': True, 'size': 13, 'color': IND})], [(a[1], {'size': 10.5})]], anchor='m')
    txt(sl, 8.2, y, 3.9, 0.7, [[(b[0], {'bold': True, 'size': 13, 'color': TEAL})], [(b[1], {'size': 10.5})]], anchor='m')
hair(sl, 0.8, 5.2, 12.5, 5.2, "D4DBEE")
txt(sl, 0.8, 5.4, 3, 0.25, "Распределение по полу, n", size=10, bold=True, color=TITLE)
cd = CategoryChartData(); cd.categories = ["ФемтоЛАЗИК", "SMILE"]
cd.add_series("Мужчины", (7, 11)); cd.add_series("Женщины", (13, 9))
ch = sl.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, I(0.7), I(5.6), I(5.6), I(1.4), cd).chart
chart_clear(ch); ch.font.name = FONT
pl = ch.plots[0]; pl.gap_width = 45; pl.overlap = 100
for s, c in zip(pl.series, [IND, INDL]): s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c)
pl.has_data_labels = True; pl.data_labels.font.size = Pt(10); pl.data_labels.font.bold = True; pl.data_labels.font.color.rgb = rgb("FFFFFF")
ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
ch.category_axis.tick_labels.font.size = Pt(10); ch.category_axis.format.line.fill.background()
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.RIGHT; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(9)
txt(sl, 7.4, 5.4, 3, 0.25, "Средний возраст", size=10, bold=True, color=TITLE)
orb(sl, 8.4, 6.2, 1.15, [[("31,2", {'size': 17, 'bold': True})], [("года", {'size': 8.5})]], 10)
orb(sl, 11.0, 6.2, 1.15, [[("29,2", {'size': 17, 'bold': True})], [("года", {'size': 8.5})]], 10, strong=True)
txt(sl, 7.6, 6.85, 1.6, 0.2, "SMILE", size=8.5, color=MUTED, align='c'); txt(sl, 10.2, 6.85, 1.6, 0.2, "ФемтоЛАЗИК", size=8.5, color=MUTED, align='c')
txt(sl, 0.8, 6.98, 6, 0.15, "* M ± SD — среднее ± стандартное отклонение", size=7, italic=True, color=MUTED)

# ============ 7. ДИАГНОСТИКА ============
sl = slide("Методы диагностики", 'soft')
hair(sl, 6.65, 1.2, 6.65, 4.9, "D4DBEE")
txt(sl, 0.8, 1.2, 5.5, 0.3, "Стандартные методы диагностики", size=13, bold=True, color=TITLE)
txt(sl, 7.0, 1.2, 5.5, 0.3, "Специальные методы диагностики", size=13, bold=True, color=TITLE)
std = [("Визометрия", "НКОЗ и МКОЗ в естественных условиях и при медикаментозном мидриазе"), ("Рефрактометрия, кератометрия", "в естественных условиях и при медикаментозном мидриазе"),
       ("Тонометрия, биометрия, периметрия", ""), ("Биомикроскопия и офтальмоскопия", "")]
spec = [("Кератотопография", "Pentacam AXL (Oculus, Германия)"), ("Анализ биомеханических свойств роговицы", "Corvis ST (Oculus, Германия)"), ("Аберрометрия", "KR-1W (Topcon, Япония)")]
for col, items, x0 in ((0, std, 0.8), (1, spec, 7.0)):
    for i, (a, b) in enumerate(items):
        y = 1.8 + i * 0.78
        orb(sl, x0 + 0.27, y + 0.3, 0.5, str(i + 1), 10, True, halo=False, strong=bool(col))
        txt(sl, x0 + 0.75, y, 5.0, 0.62, [[(a, {'bold': True, 'size': 12, 'color': TITLE})]] + ([[(b, {'size': 9.5})]] if b else []), anchor='m', spacing=1.05)
hair(sl, 0.8, 5.1, 12.5, 5.1, "D4DBEE")
pic(sl, "p7_112.png", 0.9, 5.25, 0.95, 1.7); pic(sl, "p7_122.png", 2.0, 5.25, 2.3, 1.7); pic(sl, "p7_121.png", 4.4, 5.25, 2.2, 1.7)
pic(sl, "p7_113.png", 7.3, 5.25, 5.0, 1.7)

# ============ 8. ТРАНСПОЗИЦИЯ ============
sl = slide("Лентикулярная технология коррекции смешанного астигматизма", 'plain', "Транспозиция исходной рефракции (sph, cyl, ax) по разработанной технологии")
hair(sl, 0.6, 2.95, 12.3, 2.95)
steps = [("Допуск", "Условия допуска", "Sph ≤ +1,75 D\nCyl ≥ −5 D\nSE ≤ −0,75 D"),
         ("Сфера", "Транспозиция сферы", "SPH' = SPH + CYL"),
         ("Цилиндр", "Инверсия цилиндра", "CYL' = −CYL (знак +)"),
         ("Ось", "Коррекция оси", "Ax ≤ 90° → +90°;\nAX > 90° → −90°.\nРучная маркировка роговицы для минимизации циклоторсии (ось астигматизма)"),
         ("Ввод", "Ввод данных в лазер", "Ввод полученных рефракционных данных в фемтосекундную лазерную установку")]
for i, (inner, ttl, body) in enumerate(steps):
    cx = 1.65 + i * 2.5
    last = i == 4
    orb(sl, cx, 2.95, 1.3, [[(f"0{i+1}", {'size': 9, 'color': MUTED})], [(inner, {'size': 12, 'bold': True})]], 12, strong=last)
    txt(sl, cx - 1.2, 3.95, 2.4, 0.3, ttl, size=11.5, bold=True, color=TITLE, align='c')
    txt(sl, cx - 1.15, 4.3, 2.3, 1.7, body.split("\n"), size=10, color=NAVY, align='c', spacing=1.08, after=2)
pic(sl, "p8_153.png", 0.8, 5.55, 2.2, 1.4, frame=True)
txt(sl, 3.15, 5.7, 3.3, 0.9, "Маркерная разметка роговицы для контроля циклоторсии", size=9, italic=True, color=MUTED)
txt(sl, 7.1, 5.7, 5.4, 0.8, "Согласно инструкции к VisuMax®, возможна коррекция близорукости от −0,50 до −10,00 дптр и астигматизма до −5,00 дптр", size=10, color=NAVY, align='r')
txt(sl, 0.8, 6.98, 12, 0.2, "Розенблюм Ю.З. Оптометрия. СПб.: Гиппократ; 1996.  ·  Гамидов Г.А., Мушкова И.А., Костенев С.В., Гамидов А.А. Способ контроля циклоторсии глазного яблока при коррекции миопического астигматизма по технологии SMILE. Офтальмология. 2020; 17(3): 351-360.", size=5.5, italic=True, color=MUTED)

# ============ 9. ХОД ОПЕРАЦИИ ============
sl = slide("Ход операции", 'plain')
pic(sl, "p9_183.png", 0.8, 1.3, 3.5, 4.9, frame=True)
pic(sl, "p9_184.png", 4.7, 1.3, 3.5, 4.9, frame=True)
pic(sl, "p9_189.png", 8.9, 1.3, 3.6, 4.9, frame=True)
hair(sl, 0.8, 6.45, 12.5, 6.45)
for cx, lab in ((2.55, "Протокол ReLEx SMILE · OD"), (6.45, "Протокол ReLEx SMILE · OS"), (10.7, "* Оперирующий хирург — д.м.н. Костенев С.В.")):
    dot(sl, cx, 6.45, 0.06); txt(sl, cx - 1.9, 6.6, 3.8, 0.3, lab, size=10, color=NAVY, align='c')

# ============ 10. ПАТЕНТ ============
sl = slide("Патент, программа для ЭВМ и калькулятор транспозиции", 'soft')
pic(sl, "p10_196.png", 0.8, 1.3, 2.9, 4.3, frame=True)
pic(sl, "p10_198.png", 3.95, 1.3, 2.9, 4.3, frame=True)
shape(sl, MSO_SHAPE.RECTANGLE, 7.1, 1.3, 3.2, 4.3, "FFFFFF", "D7DDEF", 0.6)
txt(sl, 7.3, 1.45, 2.8, 0.7, "Калькулятор транспозиции смешанного астигматизма для лентикулярной технологии", size=10.5, bold=True, color=TITLE, spacing=1.05)
for i, (lab, val) in enumerate([("Sph, дптр", ""), ("Cyl, дптр", "0,00"), ("Ax, градусы", "0")]):
    yy = 2.4 + i * 0.85
    txt(sl, 7.3, yy, 2.8, 0.22, lab, size=9, bold=True, color=MUTED)
    shape(sl, MSO_SHAPE.RECTANGLE, 7.3, yy + 0.27, 2.8, 0.42, "F7F8FC", IND if i == 0 else "D2D9EE", 0.8)
    txt(sl, 7.42, yy + 0.27, 2.0, 0.42, val, size=10.5, color=NAVY, anchor='m')
shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 7.3, 5.0, 1.4, 0.4, IND); txt(sl, 7.3, 5.0, 1.4, 0.4, "Рассчитать", size=10, bold=True, color="FFFFFF", align='c', anchor='m')
pic(sl, "p10_199.png", 10.55, 1.3, 2.0, 4.3, frame=True)
hair(sl, 0.8, 5.95, 12.5, 5.95)
for cx, a, b in ((2.25, "Патент РФ № 2862856", "Способ коррекции смешанного астигматизма"), (5.4, "Свидетельство № 2026686768", "о регистрации программы для ЭВМ"), (8.7, "Онлайн-калькулятор", "расчёт параметров для установки"), (11.55, "Публикация", "первые результаты")):
    dot(sl, cx, 5.95, 0.06); txt(sl, cx - 1.5, 6.1, 3.0, 0.6, [[(a, {'bold': True})], [(b, {'color': MUTED})]], size=9.5, color=NAVY, align='c')

# ============ 11. КРИТЕРИИ ============
sl = slide("Критерии включения и исключения", 'plain')
hair(sl, 6.65, 1.2, 6.65, 6.8, "D4DBEE")
orb(sl, 1.1, 1.55, 0.6, "✓", 14, True, halo=False)
txt(sl, 1.6, 1.3, 4.5, 0.5, "Критерии включения", size=16, bold=True, color=TITLE, anchor='m')
inc = ["Возраст 18 лет и старше", "Диагноз «смешанный астигматизм»", "Максимально корригированная острота зрения (МКОЗ) 0,3 и выше", "Толщина роговицы от 470 мкм и более", "Отсутствие признаков кератоконуса по BAD"]
for i, t in enumerate(inc):
    y = 2.1 + i * 0.6
    hair(sl, 0.8, y, 6.2, y, "D4DBEE"); txt(sl, 0.8, y + 0.06, 5.4, 0.5, t, size=12, color=NAVY, anchor='m')
txt(sl, 0.8, 5.35, 5.4, 1.4, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'size': 9.5, 'color': MUTED, 'bold': True})], [("Sph ≤ +1,75 D", {})], [("Cyl ≥ −5 D", {})], [("SE ≤ −0,75 D", {})]], size=14, bold=True, color=IND, after=2)
orb(sl, 7.4, 1.55, 0.6, "✕", 13, True, halo=False, strong=True)
txt(sl, 7.9, 1.3, 4.5, 0.5, "Критерии исключения", size=16, bold=True, color=TITLE, anchor='m')
exc = [("Возраст младше 18 лет", 0.5), ("Патология роговицы: кератоконус, дистрофии, неоваскуляризация, помутнение, рубцевание, состояние после кератопластики", 0.95), ("МКОЗ менее 0,3; толщина роговицы менее 470 мкм", 0.5),
       ("Ранее выполненный ЛАЗИК; глаукома (кроме ранней стадии); катаракта (кроме врождённой)", 0.7), ("Воспалительные и системные заболевания в стадии обострения, беременность и лактация", 0.7)]
y = 2.1
for t, h in exc:
    hair(sl, 7.0, y, 12.5, y, "D4DBEE"); txt(sl, 7.0, y + 0.05, 5.5, h, t, size=11.5, color=NAVY, anchor='m'); y += h + 0.1
txt(sl, 7.0, 6.05, 5.5, 0.8, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'size': 9.5, 'color': MUTED, 'bold': True})], [("Несоответствие критериям SE и рефракционным параметрам", {'size': 12, 'bold': True, 'color': TEAL})]], after=2)


# ============ 12–13. ПАРАМЕТРЫ ============
def params(title, sub, rows, accent):
    sl = slide(title, 'right', sub)
    n = len(rows); rh = min(0.6, 5.0 / n)
    for i, (a, b) in enumerate(rows):
        y = 1.6 + i * rh
        hair(sl, 0.8, y, 7.4, y, "D4DBEE")
        txt(sl, 0.8, y, 3.2, rh, a, size=12, color=NAVY, anchor='m')
        txt(sl, 4.1, y, 3.3, rh, b, size=12.5, bold=True, color=accent, anchor='m')
    hair(sl, 0.8, 1.6 + n * rh, 7.4, 1.6 + n * rh, "D4DBEE")
    return sl


sl = params("Параметры операции: лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)",
            [("Режим", "«быстрый»"), ("Оптическая зона", "6,7 мм"), ("Переходная зона", "0,10 мм"), ("Диаметр клапана (cap)", "7,8–7,9 мм"), ("Толщина клапана (cap)", "120 мкм"),
             ("Угол краевого надреза", "90°"), ("Длина входного разреза", "2,0–2,4 мм"), ("Интерфейс", "«S» / «M», в зависимости от диаметра роговицы"), ("Количество разрезов", "1")], IND)
ring(sl, 10.3, 4.0, 4.6, "C9D2EC", 0.6); ring(sl, 10.3, 4.0, 3.9, "C9D2EC", 0.6, MSO_LINE.ROUND_DOT)
pic(sl, "p12_213.png", 8.5, 2.4, 3.6, 3.2)
sl = params("Параметры операции: ФемтоЛАЗИК", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)",
            [("Оптическая зона абляции", "6,5 мм"), ("Переходная зона", "1,2 мм"), ("Толщина флэпа", "110 мкм"), ("Общая зона абляции", "8,9 мм"), ("Номограмма", "S 001"),
             ("Положение и ширина «ножки»", "90°, 0,6 мм"), ("Остальные параметры", "варьировали индивидуально (рефракция, пахиметрия и т.д.)")], TEAL)
ring(sl, 10.3, 3.4, 4.2, "C9D2EC", 0.6); ring(sl, 10.3, 3.4, 3.5, "C9D2EC", 0.6, MSO_LINE.ROUND_DOT)
pic(sl, "p13_226.png", 8.6, 2.2, 3.4, 2.5)
pic(sl, "p13_227.png", 9.3, 5.15, 3.2, 1.7, frame=True)

# ============ 14. МОДЕЛИРОВАНИЕ ============
sl = slide("Математическое моделирование создаваемой лентикулы", 'plain')
for i, (im, cap) in enumerate([("p14_232.png", "3D-модель: толщина лентикулы"), ("p14_233.png", "Карта толщины (вид сверху)"), ("p14_235.png", "Профиль (вид сбоку)")]):
    x = 0.8 + i * 4.05
    pic(sl, im, x, 1.25, 3.7, 2.55); dot(sl, x + 1.85, 3.95, 0.05)
    txt(sl, x, 4.05, 3.7, 0.25, cap, size=9.5, color=NAVY, align='c')
hair(sl, 0.8, 3.95, 12.5, 3.95, "D4DBEE")
txt(sl, 0.8, 4.5, 11.8, 0.3, "На основании математической модели построена геометрическая (схематическая) модель лентикулы при смешанном астигматизме", size=11.5, bold=True, color=TITLE)
shape(sl, MSO_SHAPE.RECTANGLE, 0.8, 5.0, 7.0, 1.9, "FFFFFF", "D7DDEF", 0.6)
txt(sl, 1.05, 5.1, 6.5, 0.25, "Эмпирическая формула расчёта максимальной толщины лентикулы", size=9.5, bold=True, color=MUTED)
txt(sl, 1.05, 5.4, 6.5, 0.5, "T(r,θ) = C + A·(r/R)²·cos(2(θ − ось))", size=20, bold=True, color=TITLE)
txt(sl, 1.05, 6.05, 6.6, 0.8, ["C = (Max_theory + T_min) / 2     A = (Max_theory − T_min) / 2     R = S / 2", "Max_theory = (S²/6)·(2|Sph'| + |Cyl'|)     T_min ≈ 20 мкм (константа устройства)"], size=9.5, color=NAVY, spacing=1.2)
pic(sl, "p14_234.png", 8.2, 4.9, 4.3, 2.0)

# ============ 15. НКОЗ / МКОЗ ============
sl = slide("Динамика НКОЗ и МКОЗ в исследуемых группах", 'plain')
cats = ["До операции", "1-е сутки", "3 мес.", "6 мес."]
hair(sl, 6.65, 1.3, 6.65, 6.8, "D4DBEE")
dot(sl, 0.9, 1.45, 0.06, IND); txt(sl, 1.1, 1.3, 5, 0.3, "Лентикулярная хирургия (SMILE)", size=13, bold=True, color=IND)
bar_chart(sl, 0.7, 1.75, 5.8, 5.1, cats, [("НКОЗ", (0.34, 0.73, 0.88, 0.75)), ("МКОЗ", (0.91, 0.87, 0.98, 1.00))], [IND, INDL], 0, 1.2, 0.2)
dot(sl, 7.0, 1.45, 0.06, TEAL); txt(sl, 7.2, 1.3, 5, 0.3, "ФемтоЛАЗИК", size=13, bold=True, color=TEAL)
bar_chart(sl, 6.85, 1.75, 5.8, 5.1, cats, [("НКОЗ", (0.32, 0.54, 0.75, 0.72)), ("МКОЗ", (0.87, 0.84, 0.92, 0.95))], [TEAL, TEALL], 0, 1.2, 0.2)
txt(sl, 4.6, 1.35, 1.9, 0.25, "острота зрения, дес.", size=8.5, color=MUTED, align='r')

# ============ 16. РЕФРАКЦИЯ ============
sl = slide("Динамика рефракционного компонента", 'plain')
cd = CategoryChartData(number_format='0.00'); cd.categories = cats
S = [("SMILE — Sph", IND, False, (0.54, 0.22, 0.37, 0.62)), ("SMILE — Cyl", IND, True, (-3.07, -0.51, -0.44, -0.62)),
     ("ФемтоЛАЗИК — Sph", TEAL, False, (1.25, -0.20, 0.02, 0.31)), ("ФемтоЛАЗИК — Cyl", TEAL, True, (-3.24, -1.13, -1.19, -1.25))]
for n, c, d, v in S: cd.add_series(n, v)
ch = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, I(0.7), I(1.35), I(6.6), I(3.2), cd).chart
chart_clear(ch); ch.font.name = FONT; style_axes(ch, -4, 2, 1, 10)
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
for s, (n, c, d, v) in zip(ch.plots[0].series, S):
    s.smooth = False; s.format.line.color.rgb = rgb(c); s.format.line.width = Pt(2.25)
    if d: s.format.line.dash_style = MSO_LINE.DASH
    s.marker.style = XL_MARKER_STYLE.CIRCLE; s.marker.size = 7
    s.marker.format.fill.solid(); s.marker.format.fill.fore_color.rgb = rgb("FFFFFF" if d else c); s.marker.format.line.color.rgb = rgb(c)
ch.has_legend = False
txt(sl, 0.85, 1.2, 2, 0.25, "Диоптрии, D", size=8.5, color=MUTED)
for k, c_ in enumerate(cats): txt(sl, 3.6 + k * 0.95, 4.65, 0.9, 0.22, c_, size=8, color=MUTED, align='c')
for j, (nm, col, dsh, vals) in enumerate(S):
    yy = 4.95 + j * 0.45
    hair(sl, 0.8, yy, 7.3, yy, "D4DBEE")
    hair(sl, 0.85, yy + 0.22, 1.2, yy + 0.22, col, 2.25, MSO_LINE.DASH if dsh else None)
    txt(sl, 1.3, yy, 2.3, 0.44, nm, size=10, bold=True, color=col, anchor='m')
    for k, v in enumerate(vals):
        s_ = ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}".replace(".", ",")
        txt(sl, 3.6 + k * 0.95, yy, 0.9, 0.44, s_, size=10.5, bold=True, color=TITLE, align='c', anchor='m')
hair(sl, 0.8, 6.75, 7.3, 6.75, "D4DBEE")
hair(sl, 7.7, 1.3, 7.7, 6.8, "D4DBEE")
small = [("Пахиметрия, мкм", (554, 537), (501, 501), 440, 600, 40, '0'), ("Кератометрия K1, D", (41.58, 41.69), (40.78, 41.83), 38, 46, 2, '0.00'), ("Кератометрия K2, D", (44.44, 44.76), (41.78, 42.83), 38, 46, 2, '0.00')]
for i, (ttl, a, b, lo, hi, mj, f) in enumerate(small):
    yy = 1.3 + i * 1.85
    txt(sl, 8.0, yy, 4, 0.25, ttl, size=11, bold=True, color=TITLE)
    c2 = bar_chart(sl, 7.9, yy + 0.2, 4.7, 1.6, ["До операции", "6 мес."], [("SMILE", (a[0], b[0])), ("ФемтоЛАЗИК", (a[1], b[1]))], [IND, TEAL], lo, hi, mj, fmt=f, legend=(i == 0), lsize=8.5, gap=70)
    c2.value_axis.visible = False; c2.value_axis.has_major_gridlines = False
    if i == 0: c2.legend.position = XL_LEGEND_POSITION.RIGHT

# ============ 17. ЭФФЕКТИВНОСТЬ ============
sl = slide("Эффективность и безопасность", 'soft', "НКОЗ после операции / МКОЗ до операции")
pic(sl, "p17_270.png", 0.8, 1.5, 9.3, 5.3, frame=True)
for i, (lab, v, st) in enumerate([("Индекс безопасности SMILE", "1,03", False), ("Индекс безопасности ФемтоЛАЗИК", "1,02", True)]):
    cy = 2.7 + i * 2.7
    orb(sl, 11.5, cy, 1.7, v, 24, True, strong=st)
    txt(sl, 10.4, cy + 1.2, 2.2, 0.5, lab, size=10, color=NAVY, align='c')

# ============ 18. ПРОГНОЗИРУЕМОСТЬ ============
sl = slide("Прогнозируемость", 'soft')
pic(sl, "p18_275.png", 0.8, 1.3, 7.2, 5.6, frame=True)
for i, (v, lab, st) in enumerate([("0,65", "R² — коэффициент детерминации", False), ("74 %", "глаз в пределах ±0,5 D от планируемой коррекции", False), ("88 %", "глаз в пределах ±1,0 D от планируемой коррекции", True)]):
    cy = 2.1 + i * 2.1
    orb(sl, 9.2, cy, 1.25, v, 17, True, strong=st)
    txt(sl, 10.45, cy - 0.5, 2.2, 1.0, lab, size=10.5, color=NAVY, anchor='m')

# ============ 19. ВЫВОДЫ ============
sl = slide("Выводы", 'soft')
items = [("Геометрическая модель лентикулы", "На основании математического моделирования построена геометрическая модель лентикулы, отражающая её торическую (седловидную) форму, что подтверждает научную обоснованность разработанного и внедрённого в клиническую практику протокола транспозиции."),
         ("НКОЗ и МКОЗ", "НКОЗ повысилась в обеих группах (SMILE — с 0,34 до 0,88; ФемтоЛАЗИК — с 0,32 до 0,75): лентикулярная технология обеспечивает более быстрое и полное зрительное восстановление без коррекции. МКОЗ оставалась стабильно высокой (с 0,91 до 1,0 и с 0,87 до 0,95): ни одна из технологий не снижает потенциальную остроту зрения."),
         ("Рефракционный компонент", "Сферический компонент приблизился к эмметропии (с +0,54 до +0,37 D в SMILE и с +1,25 до +0,31 D в ФемтоЛАЗИК). Цилиндрический компонент существенно снизился (с −3,07 до −0,62 D и с −3,24 до −1,25 D), остаточный цилиндр в лентикулярной группе вдвое меньше."),
         ("Эффективна, безопасна, перспективна", "Разработанная лентикулярная технология эффективна, безопасна и перспективна для внедрения при смешанном астигматизме. Необходимы дальнейшее накопление клинических данных и их статистическая обработка.")]
hair(sl, 6.65, 1.3, 6.65, 6.8, "D4DBEE")
for i, (t, b) in enumerate(items):
    x = 0.8 + (i % 2) * 6.1; y = 1.35 + (i // 2) * 2.85
    orb(sl, x + 0.35, y + 0.35, 0.7, str(i + 1), 14, True, halo=False, strong=i % 3 == 0)
    txt(sl, x + 1.0, y + 0.05, 4.8, 0.6, t, size=14, bold=True, color=TITLE, anchor='m')
    txt(sl, x + 1.0, y + 0.75, 4.8, 1.9, b, size=12.5, color=NAVY, spacing=1.12)

# ============ 20. СПАСИБО ============
sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
sl.shapes.add_picture(IMG + "m_title.png", 0, 0, prs.slide_width, prs.slide_height)
txt(sl, 0.85, 2.1, 7.0, 1.8, "Благодарю за внимание!", size=44, bold=True, color=TITLE, spacing=1.05)
hair(sl, 0.85, 4.1, 7.0, 4.1)
txt(sl, 0.85, 4.4, 7, 0.3, [[("Электронная почта: ", {'color': MUTED}), ("anastasianik2403@gmail.com", {'bold': True})]], size=14)
ring(sl, 10.2, 3.75, 4.9, "9AA8D8", 0.8, MSO_LINE.ROUND_DOT)
pic(sl, "p20_294.png", 8.2, 2.0, 4.0, 3.5)

prs.save("../Astigmatism_minimal.pptx")
print("saved")
