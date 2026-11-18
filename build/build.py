from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_MARKER_STYLE
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image
import copy

FONT = "Arial"
NAVY, INK, BLUE, DEEP, SKY = "14213D", "2B3A55", "1A73E8", "1A5FD0", "8EC5FF"
AMBER, AMBERD, PALE, MUTED = "FF9F1C", "D97706", "DCEBFF", "5B6B8C"
AMBER_T, BLUE_T = "FFF3E0", "E8F2FF"
IMG = "img/"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
I = Inches


def rgb(h): return RGBColor.from_string(h)


def shape(sl, kind, x, y, w, h, fill=None, alpha=None, line=None, lw=0.75, shadow=False, adj=None):
    s = sl.shapes.add_shape(kind, I(x), I(y), I(w), I(h))
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            clr = s._element.spPr.find(qn('a:solidFill'))[0]
            a = etree.SubElement(clr, qn('a:alpha')); a.set('val', str(int(alpha * 1000)))
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
    else:
        s.line.fill.background()
    eff = etree.SubElement(s._element.spPr, qn('a:effectLst'))
    if shadow:
        sh = etree.SubElement(eff, qn('a:outerShdw'))
        sh.set('blurRad', '300000'); sh.set('dist', '76200'); sh.set('dir', '5400000'); sh.set('algn', 't'); sh.set('rotWithShape', '0')
        c = etree.SubElement(sh, qn('a:srgbClr')); c.set('val', '2A5AA8')
        al = etree.SubElement(c, qn('a:alpha')); al.set('val', '16000')
    if adj is not None and len(s.adjustments):
        s.adjustments[0] = adj
    st = s._element.find(qn('p:style'))
    if st is not None: s._element.remove(st)
    s.text_frame.text = ""
    return s


def card(sl, x, y, w, h, fill="FFFFFF", alpha=78, line="FFFFFF", adj=0.07, shadow=True):
    return shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, alpha, line, 1.5, shadow, adj)


def txt(sl, x, y, w, h, paras, size=14, color=NAVY, bold=False, align='l', anchor='t', italic=False,
        spacing=None, after=0, font=FONT):
    tb = sl.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    if isinstance(paras, str): paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT, 'j': PP_ALIGN.JUSTIFY}[align]
        if spacing: para.line_spacing = spacing
        para.space_after = Pt(after)
        runs = p if isinstance(p, list) else [p]
        for r in runs:
            t, o = (r, {}) if isinstance(r, str) else r
            run = para.add_run(); run.text = t
            f = run.font; f.name = o.get('font', font); f.size = Pt(o.get('size', size))
            f.bold = o.get('bold', bold); f.italic = o.get('italic', italic)
            f.color.rgb = rgb(o.get('color', color))
    return tb


def pic(sl, name, x, y, w, h, halign='c', valign='m'):
    path = IMG + name
    iw, ih = Image.open(path).size
    sc = min(w / iw, h / ih); pw, ph = iw * sc, ih * sc
    px = x + (w - pw) / 2 if halign == 'c' else (x if halign == 'l' else x + w - pw)
    py = y + (h - ph) / 2 if valign == 'm' else (y if valign == 't' else y + h - ph)
    return sl.shapes.add_picture(path, I(px), I(py), I(pw), I(ph))


def bg(sl, kind='content'):
    sl.shapes.add_picture(IMG + f"bg_{kind}.png", 0, 0, prs.slide_width, prs.slide_height)


PAGE = [0]


def base(over, title):
    sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
    bg(sl)
    txt(sl, 0.6, 0.32, 4, 0.4, [[("КАТАРАКТА ", {'bold': True, 'color': "26397A"}), ("2026", {'bold': True, 'color': BLUE})]], size=17)
    txt(sl, 8.2, 0.38, 4.55, 0.3, "2–4 сентября 2026 · Москва", size=11, color=MUTED, align='r')
    txt(sl, 0.6, 0.88, 8, 0.3, over.upper(), size=11, bold=True, color=BLUE)
    txt(sl, 0.6, 1.15, 12.1, 0.6, title, size=28 if len(title) <= 55 else 24, bold=True, color=NAVY)
    txt(sl, 12.1, 7.08, 0.65, 0.25, f"{PAGE[0]:02d}", size=11, bold=True, color="FFFFFF", align='r')
    return sl


def numchip(sl, x, y, n, color=BLUE, size=26):
    txt(sl, x, y, 0.9, 0.5, n, size=size, bold=True, color=color)


def pill(sl, x, y, w, h, text, fill=BLUE, color="FFFFFF", size=13, bold=True, align='c'):
    shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, None, None, adj=0.5)
    txt(sl, x + 0.1, y, w - 0.2, h, text, size=size, bold=bold, color=color, align=align, anchor='m')


def chart_clear(chart):
    cs = chart._chartSpace
    sp = etree.Element(qn('c:spPr'))
    etree.SubElement(sp, qn('a:noFill'))
    ln = etree.SubElement(sp, qn('a:ln')); etree.SubElement(ln, qn('a:noFill'))
    cs.find(qn('c:chart')).addnext(sp)


def style_axes(chart, vmin, vmax, major, size=11):
    va = chart.value_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = vmin, vmax, major
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("D5E2F5"); va.major_gridlines.format.line.width = Pt(0.75)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(size); va.tick_labels.font.color.rgb = rgb(MUTED); va.tick_labels.font.name = FONT
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(size); ca.tick_labels.font.color.rgb = rgb(INK); ca.tick_labels.font.name = FONT
    ca.format.line.color.rgb = rgb("9DB3D6")
    ca.has_major_gridlines = False


def bar_chart(sl, x, y, w, h, cats, series, colors, vmin, vmax, major, fmt='0.00', legend=True, lsize=11, gap=55):
    cd = CategoryChartData(); cd.categories = cats
    for n, v in series: cd.add_series(n, v)
    gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(x), I(y), I(w), I(h), cd)
    ch = gf.chart; chart_clear(ch)
    ch.font.name = FONT
    pl = ch.plots[0]; pl.gap_width = gap; pl.overlap = -8
    for s, c in zip(pl.series, colors):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c); s.invert_if_negative = False
    pl.has_data_labels = True
    dl = pl.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False
    dl.font.size = Pt(lsize); dl.font.bold = True; dl.font.color.rgb = rgb(NAVY); dl.font.name = FONT
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    style_axes(ch, vmin, vmax, major, lsize)
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(lsize); ch.legend.font.color.rgb = rgb(INK); ch.legend.font.name = FONT
    return ch


# ================= 1. TITLE =================
sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
bg(sl, 'title')
txt(sl, 0.6, 0.45, 7, 0.7, [[("КАТАРАКТА ", {'color': "26397A"}), ("2026", {'color': BLUE})]], size=34, bold=True)
txt(sl, 0.6, 1.2, 9.5, 0.7, ["26-й Всероссийский научно-практический конгресс с международным участием",
                              [("Современные технологии катарактальной, рефракционной и роговичной хирургии", {'bold': True})]], size=12, color=INK, spacing=1.15)
txt(sl, 0.6, 1.95, 9, 0.3, [[("2–4 сентября 2026", {'bold': True, 'color': BLUE}), ("  ·  Москва, Конгресс-центр ЦМТ", {})]], size=11, color=MUTED)
txt(sl, 0.6, 2.4, 11.2, 2.2, "Современный подход к хирургической коррекции смешанного астигматизма с применением фемтосекундной лентикулярной технологии",
    size=30, bold=True, color=NAVY, spacing=1.08)
pill(sl, 0.6, 4.85, 3.3, 0.5, "Докладчик: Никитина А.Е.", BLUE, size=13)
txt(sl, 4.1, 4.85, 7, 0.5, "Соавторы: д.м.н. Костенев С.В., к.м.н. Макаров Р.А., Садрутдинов Р.Ш.", size=13, color=INK, anchor='m')
txt(sl, 0.6, 5.55, 8.6, 0.7, ["ФГБОУ ВО «Российский университет медицины» Минздрава России",
                               "ФГАУ «НМИЦ «МНТК «Микрохирургия глаза» им. акад. С.Н. Федорова» Минздрава России"], size=11, color=INK, spacing=1.2)

# ================= 2. АКТУАЛЬНОСТЬ 1 =================
sl = base("Актуальность", "Актуальность")
card(sl, 0.6, 1.85, 12.1, 1.45, "E4EFFF", 85, adj=0.12)
txt(sl, 0.95, 2.0, 11.4, 1.2, [[("•  ", {'color': BLUE, 'bold': True}), "Астигматизм — мультифакторное состояние с выраженным наследственным компонентом."],
                                [("•  ", {'color': BLUE, 'bold': True}), "Полногеномные исследования (Shing E. et al., 2024) выявили свыше 50 полиморфизмов в 10 генах, включая локус PDGFRA, регулирующий кривизну роговицы."]],
    size=14, color=INK, anchor='m', after=6, spacing=1.1)
txt(sl, 0.6, 3.5, 9.3, 0.4, "Хирургическая коррекция смешанного астигматизма", size=18, bold=True, color=NAVY)
card(sl, 0.6, 4.05, 4.7, 1.85, BLUE_T, 90, adj=0.1)
txt(sl, 0.9, 4.2, 4.1, 0.8, "Эксимерлазерная технология (ФемтоЛАЗИК)", size=17, bold=True, color=DEEP)
txt(sl, 0.9, 5.0, 4.1, 0.8, [[("Современный ", {}), ("«золотой»", {'color': AMBERD}), (" стандарт в коррекции смешанного астигматизма", {})]], size=13, color=INK)
card(sl, 5.5, 4.05, 4.4, 1.85, AMBER_T, 90, adj=0.1)
txt(sl, 5.8, 4.2, 3.8, 0.5, "Лентикулярная технология", size=17, bold=True, color=AMBERD)
shape(sl, MSO_SHAPE.OVAL, 7.0, 4.85, 0.85, 0.85, None, None, AMBERD, 2.25)
txt(sl, 7.0, 4.85, 0.85, 0.85, "?", size=30, bold=True, color=AMBERD, align='c', anchor='m')
pic(sl, "p2_22.png", 10.05, 3.5, 2.7, 2.4)
txt(sl, 0.6, 6.05, 12.0, 0.85, [
    "Азара Д.Т., Алио Х.Л., Кортина М.С., Халлака Д.А. Хирургическое лечение астигматизма. Москва: ГЭОТАР-Медиа, 2025. — 272 с. [Azar DT, Alio JL, Cortina MS, Haddock LJ. Surgical Treatment of Astigmatism. Moscow: GEOTAR-Media, 2025. 272. (In Russ.)]. doi: 10.33029/9704-8200-1-STA-2025-1-272;",
    "Shing E., Kam K.W., Zaabaar E., Zhang X.J., Young A.L., Pang C.P., Tham C.C., Yam J.C. Heritability and Genetic Factors of Astigmatism and Corneal Curvature: A Systematic Review and Meta-analysis. American Journal of Ophthalmology. 2025;269:161–171. doi: 10.1016/j.ajo.2024.08.019.",
    "Клокова О.А., Дамашаускас Р.О., Качаров А.И., Пискунов А.В. Гейдерих М.С., Дьяконова Е.И. Ранние клинико-функциональные результаты коррекции смешанного астигматизма в зависимости от его степени с помощью высокочастотного эксимерного лазера Schwind Amaris 1050RS. Офтальмология. 2025;22(2):295–304. https://doi.org/10.18008/1816-5095-2025-2-295-304"],
    size=6.5, italic=True, color=MUTED, spacing=0.95)

# ================= 3. АКТУАЛЬНОСТЬ 2 =================
sl = base("Актуальность", "Актуальность")
card(sl, 0.6, 1.85, 7.5, 1.75, BLUE_T, 90, adj=0.1)
shape(sl, MSO_SHAPE.OVAL, 0.85, 2.1, 0.36, 0.36, BLUE)
txt(sl, 0.85, 2.1, 0.36, 0.36, "i", size=14, bold=True, color="FFFFFF", align='c', anchor='m')
txt(sl, 1.35, 2.0, 6.5, 1.5, [[("Пилотное исследование на платформе ", {}), ("VisuMax", {'bold': True}),
                                (" (Carl Zeiss Meditec AG) показало возможность коррекции смешанного астигматизма методом лентикулярной хирургии (Ganesh S. et al., 2024), однако методика пока не применяется в стандартной практике.", {})]],
    size=13, color=INK, anchor='m', spacing=1.1)
card(sl, 0.6, 3.8, 3.0, 3.0, "FFFFFF", 90, adj=0.08)
pic(sl, "p3_63.png", 0.7, 3.9, 2.8, 2.8)
card(sl, 3.8, 3.8, 4.3, 3.0, AMBER_T, 90, adj=0.1)
txt(sl, 4.1, 3.95, 3.7, 2.7, [[("Экспериментальное исследование ex-vivo (11 свиных глаз) на платформе ", {}), ("Elita", {'bold': True}),
                                (", Johnson and Johnson Surgical Vision, Inc. (США) свидетельствуют о технической возможности коррекции смешанного астигматизма и гиперметропии.", {})]],
    size=13, color=INK, anchor='m', spacing=1.1)
card(sl, 8.4, 1.85, 2.15, 4.2, "FFFFFF", 92, adj=0.05)
pic(sl, "p3_58.png", 8.5, 1.95, 1.95, 4.0, valign='t')
card(sl, 10.65, 1.85, 2.1, 4.2, "FFFFFF", 92, adj=0.05)
pic(sl, "p3_62.png", 10.75, 1.95, 1.9, 4.0, valign='t')
txt(sl, 8.4, 6.2, 2.15, 0.5, "Ganesh S. et al., 2024", size=10, color=MUTED, align='c')
txt(sl, 10.65, 6.2, 2.1, 0.5, "ARVO Annual Meeting, 2025", size=10, color=MUTED, align='c')

# ================= 4. ЦЕЛЬ =================
sl = base("Цель и методы", "Цель")
shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, 2.5, 11.5, 1.8, "FFFFFF", 80, "FFFFFF", 1.5, True, 0.5)
shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, 2.5, 0.16, 1.8, BLUE, None, None, adj=0.5)
txt(sl, 1.5, 2.5, 10.4, 1.8, "Разработать лентикулярную технологию для коррекции смешанного астигматизма", size=28, bold=True, color=NAVY, anchor='m', spacing=1.1)
pic(sl, "p4_74.png", 8.2, 4.35, 4.6, 2.55, halign='r')

# ================= 5. МАТЕРИАЛЫ И МЕТОДЫ =================
sl = base("Цель и методы", "Материалы и методы")
for (x, tint, col, num, label, tech, dev, im1, im2) in [
    (0.6, AMBER_T, AMBERD, "1", "ГРУППА 1", "Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", "p5_87.png", "p5_86.png"),
    (6.85, BLUE_T, DEEP, "2", "ГРУППА 2", "Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", "p5_88.png", "p5_89.png")]:
    card(sl, x, 1.85, 5.85, 3.55, tint, 92, adj=0.07)
    shape(sl, MSO_SHAPE.OVAL, x + 0.25, 2.05, 0.55, 0.55, col)
    txt(sl, x + 0.25, 2.05, 0.55, 0.55, num, size=18, bold=True, color="FFFFFF", align='c', anchor='m')
    txt(sl, x + 0.95, 2.12, 3, 0.4, label, size=12, bold=True, color=col)
    txt(sl, x + 0.3, 2.8, 3.2, 0.9, tech, size=16, bold=True, color=col, spacing=1.05)
    txt(sl, x + 0.3, 3.7, 3.2, 0.9, dev, size=10.5, italic=True, color=INK)
    txt(sl, x + 0.3, 4.5, 1.2, 0.8, "20", size=40, bold=True, color=col, anchor='m')
    txt(sl, x + 1.35, 4.5, 2.2, 0.8, "пациентов (40 глаз)", size=13, bold=True, color=INK, anchor='m')
    pic(sl, im1, x + 3.45, 2.1, 2.3, 1.85)
    pic(sl, im2, x + 3.9, 3.95, 1.45, 1.35)
# timeline diagram
card(sl, 0.6, 5.6, 12.1, 1.2, "FFFFFF", 80, adj=0.2)
txt(sl, 0.9, 5.75, 3.4, 0.9, "Наблюдение проводилось до операции и в стандартные сроки", size=12, bold=True, color=INK, anchor='m')
shape(sl, MSO_SHAPE.RECTANGLE, 5.0, 6.08, 6.9, 0.05, "B6CCF0")
for i, lab in enumerate(["До операции", "1 сутки", "3 месяца", "6 месяцев"]):
    cx = 5.0 + i * 2.3
    shape(sl, MSO_SHAPE.OVAL, cx - 0.13, 5.98, 0.26, 0.26, BLUE if i else AMBER, None, "FFFFFF", 2)
    txt(sl, cx - 0.9, 6.3, 1.8, 0.3, lab, size=11.5, bold=True, color=INK, align='c')

# ================= 6. ДИАПАЗОН РЕФРАКЦИОННЫХ ЗНАЧЕНИЙ =================
sl = base("Цель и методы", "Диапазон рефракционных значений в исследуемых группах")
rows_l = [("Сферический компонент (Sph)", "от +0,25 до +1,75 D", "M ± SD +0,54 ± 0,39"),
          ("Цилиндрический компонент (Cyl)", "от −2,00 до −5,00 D", "M ± SD −3,07 ± 0,93"),
          ("Кератометрия, D", "K1 41,58 · K2 44,44", "K AVE 43,00"),
          ("Пахиметрия, мкм", "от 494 до 615 мкм", "M ± SD 554,1 ± 36,2")]
rows_r = [("Сферический компонент (Sph)", "от +0,25 до +3,00 D", "M ± SD +1,25 ± 0,81"),
          ("Цилиндрический компонент (Cyl)", "от −1,25 до −6,00 D", "M ± SD −3,24 ± 2,03"),
          ("Кератометрия, D", "K1 41,69 · K2 44,76", "K AVE 43,22"),
          ("Пахиметрия, мкм", "от 483 до 596 мкм", "M ± SD 537,1 ± 30,8")]
for x, tint, col, ttl, rows in [(0.6, AMBER_T, AMBERD, "Лентикулярная технология (SMILE)", rows_l), (6.85, BLUE_T, DEEP, "Эксимерлазерная технология (ФемтоЛАЗИК)", rows_r)]:
    card(sl, x, 1.85, 5.85, 3.3, tint, 92, adj=0.07)
    txt(sl, x + 0.3, 1.97, 5.3, 0.4, ttl, size=15, bold=True, color=col)
    for i, (a, b, c) in enumerate(rows):
        yy = 2.5 + i * 0.65
        shape(sl, MSO_SHAPE.RECTANGLE, x + 0.3, yy - 0.04, 5.25, 0.012, "C9D9F0")
        txt(sl, x + 0.3, yy, 2.3, 0.58, a, size=11.5, bold=True, color=INK, anchor='m')
        txt(sl, x + 2.7, yy, 2.85, 0.58, [[(b, {'bold': True, 'color': col, 'size': 13})], [(c, {'size': 10.5, 'color': INK})]], size=12, anchor='m', align='r')
# sex + age
card(sl, 0.6, 5.3, 5.85, 1.5, "FFFFFF", 82, adj=0.1)
txt(sl, 0.9, 5.38, 3, 0.3, "Распределение по полу, n", size=11, bold=True, color=INK)
cd = CategoryChartData(); cd.categories = ["ФемтоЛАЗИК", "SMILE"]
cd.add_series("Мужчины", (7, 11)); cd.add_series("Женщины", (13, 9))
gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, I(0.8), I(5.6), I(5.5), I(1.2), cd)
ch = gf.chart; chart_clear(ch); ch.font.name = FONT
pl = ch.plots[0]; pl.gap_width = 40; pl.overlap = 100
for s, c in zip(pl.series, [DEEP, "F4A28C"]):
    s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c)
pl.has_data_labels = True; pl.data_labels.font.size = Pt(11); pl.data_labels.font.bold = True; pl.data_labels.font.color.rgb = rgb("FFFFFF")
ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
ch.category_axis.tick_labels.font.size = Pt(11); ch.category_axis.format.line.fill.background()
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.RIGHT; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(10)
card(sl, 6.85, 5.3, 5.85, 1.5, "FFFFFF", 82, adj=0.1)
txt(sl, 7.15, 5.38, 3, 0.3, "Средний возраст", size=11, bold=True, color=INK)
txt(sl, 7.15, 5.7, 2.6, 0.8, [[("31,2", {'size': 38, 'bold': True, 'color': AMBERD}), (" года", {'size': 12, 'color': INK})]], anchor='m')
txt(sl, 7.15, 6.42, 2.6, 0.3, "SMILE", size=10.5, color=MUTED)
txt(sl, 9.95, 5.7, 2.6, 0.8, [[("29,2", {'size': 38, 'bold': True, 'color': DEEP}), (" года", {'size': 12, 'color': INK})]], anchor='m')
txt(sl, 9.95, 6.42, 2.6, 0.3, "ФемтоЛАЗИК", size=10.5, color=MUTED)
txt(sl, 0.6, 6.83, 8, 0.2, "* M ± SD — значения представлены как среднее ± стандартное отклонение", size=8.5, italic=True, color=MUTED)

# ================= 7. МЕТОДЫ ДИАГНОСТИКИ =================
sl = base("Цель и методы", "Методы диагностики")
pill(sl, 0.6, 1.85, 5.9, 0.46, "Стандартные методы диагностики", BLUE, size=14)
pill(sl, 6.85, 1.85, 5.85, 0.46, "Специальные методы диагностики", "0A2A6B", size=14)
std = [("Визометрия", "НКОЗ и МКОЗ в естественных условиях и при медикаментозном мидриазе"),
       ("Рефрактометрия, кератометрия", "в естественных условиях и при медикаментозном мидриазе"),
       ("Тонометрия, биометрия, периметрия", ""), ("Биомикроскопия и офтальмоскопия", "")]
for i, (a, b) in enumerate(std):
    yy = 2.45 + i * 0.7
    card(sl, 0.6, yy, 5.9, 0.62, "FFFFFF", 85, adj=0.2, shadow=False, line="D7E6FA")
    txt(sl, 0.8, yy, 0.6, 0.62, f"0{i+1}", size=18, bold=True, color=BLUE, anchor='m')
    txt(sl, 1.45, yy + 0.02, 4.95, 0.6, [[(a, {'bold': True})]] + ([[(b, {'size': 10, 'color': MUTED})]] if b else []), size=12.5, color=NAVY, anchor='m')
spec = [("Кератотопография", "Pentacam AXL (Oculus, Германия)"), ("Анализ биомеханических свойств роговицы", "Corvis ST (Oculus, Германия)"), ("Аберрометрия", "KR-1W (Topcon, Япония)")]
for i, (a, b) in enumerate(spec):
    yy = 2.45 + i * 0.93
    card(sl, 6.85, yy, 5.85, 0.8, "FFFFFF", 85, adj=0.2, shadow=False, line="D7E6FA")
    txt(sl, 7.05, yy, 0.6, 0.8, f"0{i+1}", size=18, bold=True, color=AMBERD, anchor='m')
    txt(sl, 7.7, yy, 4.9, 0.8, [[(a, {'bold': True})], [(b, {'size': 11.5, 'color': MUTED})]], size=13, color=NAVY, anchor='m')
card(sl, 0.6, 5.35, 5.9, 1.5, "FFFFFF", 70, adj=0.1)
pic(sl, "p7_112.png", 0.7, 5.4, 0.95, 1.4); pic(sl, "p7_122.png", 1.7, 5.4, 2.2, 1.4); pic(sl, "p7_121.png", 3.95, 5.4, 2.5, 1.4)
card(sl, 6.85, 5.35, 5.85, 1.5, "FFFFFF", 70, adj=0.1)
pic(sl, "p7_113.png", 6.95, 5.4, 5.65, 1.4)

# ================= 8. ТЕХНОЛОГИЯ =================
sl = base("Технология", "Лентикулярная технология коррекции смешанного астигматизма")
pill(sl, 0.6, 1.8, 8.8, 0.42, "Транспозиция исходной рефракции (sph, cyl, ax) по разработанной технологии", "0A2A6B", size=12.5, align='l')
steps = [("1", "Условия допуска", ["Sph ≤ +1,75 D", "Cyl ≥ −5 D", "SE ≤ −0,75 D"], True),
         ("2", "Транспозиция сферы", ["SPH' = SPH + CYL"], False),
         ("3", "Инверсия цилиндра", ["CYL' = −CYL (знак +)"], False),
         ("4", "Коррекция оси", ["Ax ≤ 90° → +90°;", "AX > 90° → −90°.", "Ручная маркировка роговицы для минимизации циклоторсии (ось астигматизма)"], False)]
for i, (n, ttl, lines, warn) in enumerate(steps):
    x = 0.6 + i * 3.1
    card(sl, x, 2.4, 2.8, 2.2, "FFFFFF", 82, adj=0.09)
    txt(sl, x + 0.22, 2.48, 0.9, 0.6, f"0{n}", size=28, bold=True, color=BLUE if i != 3 else AMBERD)
    txt(sl, x + 0.22, 3.08, 2.4, 0.35, ttl, size=13.5, bold=True, color=NAVY)
    if warn:
        for j, l in enumerate(lines):
            txt(sl, x + 0.22, 3.48 + j * 0.34, 2.3, 0.3, l, size=13, bold=True, color=AMBERD)
    elif i in (1, 2):
        shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x + 0.22, 3.6, 2.35, 0.55, BLUE_T, None, None, adj=0.3)
        txt(sl, x + 0.22, 3.6, 2.35, 0.55, lines[0], size=13, bold=True, color=DEEP, align='c', anchor='m')
    else:
        txt(sl, x + 0.22, 3.45, 2.4, 1.1, [[(lines[0] + " " + lines[1], {'bold': True, 'color': DEEP})], [(lines[2], {'size': 9.5, 'color': MUTED})]], size=11.5, spacing=1.05)
    if i < 3:
        a = shape(sl, MSO_SHAPE.CHEVRON, x + 2.84, 3.35, 0.22, 0.4, AMBER)
card(sl, 0.6, 4.75, 3.4, 1.55, "FFFFFF", 82, adj=0.08)
pic(sl, "p8_153.png", 0.68, 4.8, 3.24, 1.38)
txt(sl, 0.6, 6.33, 3.4, 0.3, "Маркерная разметка роговицы для контроля циклоторсии", size=8.5, italic=True, color=MUTED, align='c')
shape(sl, MSO_SHAPE.CHEVRON, 4.25, 5.45, 0.25, 0.45, AMBER)
card(sl, 4.7, 4.75, 8.0, 1.55, "FFF8EE", 92, "FFC77A", adj=0.09)
txt(sl, 4.95, 4.82, 0.9, 0.6, "05", size=28, bold=True, color=AMBERD)
txt(sl, 5.85, 4.88, 6.6, 0.55, "Ввод полученных рефракционных данных в фемтосекундную лазерную установку", size=14, bold=True, color=NAVY, anchor='m')
txt(sl, 4.95, 5.6, 7.5, 0.65, "Согласно инструкции к VisuMax®, возможна коррекция близорукости от −0,50 до −10,00 дптр и астигматизма до −5,00 дптр", size=11, color=INK)
txt(sl, 0.6, 6.68, 12, 0.4, ["Розенблюм Ю.З. Оптометрия (подбор средств коррекции зрения). СПб.: Гиппократ; 1996.",
                             "Гамидов Г.А., Мушкова И.А., Костенев С.В., Гамидов А.А. Способ контроля циклоторсии глазного яблока при коррекции миопического астигматизма по технологии SMILE. Офтальмология. 2020; 17(3): 351-360."], size=6.5, italic=True, color=MUTED)

# ================= 9. ХОД ОПЕРАЦИИ =================
sl = base("Технология", "Ход операции")
card(sl, 0.6, 1.85, 4.0, 4.95, "FFFFFF", 92, adj=0.04)
pic(sl, "p9_183.png", 0.7, 1.95, 3.8, 4.3)
txt(sl, 0.6, 6.35, 4.0, 0.3, "Протокол ReLEx SMILE · OD", size=10.5, color=MUTED, align='c')
card(sl, 4.85, 1.85, 4.0, 4.95, "FFFFFF", 92, adj=0.04)
pic(sl, "p9_184.png", 4.95, 1.95, 3.8, 4.3)
txt(sl, 4.85, 6.35, 4.0, 0.3, "Протокол ReLEx SMILE · OS", size=10.5, color=MUTED, align='c')
card(sl, 9.1, 1.85, 3.6, 4.95, "FFFFFF", 92, adj=0.04)
pic(sl, "p9_189.png", 9.2, 1.95, 3.4, 4.3)
txt(sl, 9.1, 6.35, 3.6, 0.3, [[("* Оперирующий хирург — ", {}), ("д.м.н. Костенев С.В.", {'bold': True})]], size=10.5, color=MUTED, align='c')

# ================= 10. ПАТЕНТ / КАЛЬКУЛЯТОР =================
sl = base("Технология", "Патент, программа для ЭВМ и калькулятор транспозиции")
card(sl, 0.6, 1.85, 2.95, 4.2, "FFFFFF", 92, adj=0.05)
pic(sl, "p10_196.png", 0.7, 1.95, 2.75, 4.0)
txt(sl, 0.6, 6.15, 2.95, 0.6, [[("Патент РФ № 2862856", {'bold': True})], "Способ коррекции смешанного астигматизма"], size=9.5, color=INK, align='c')
card(sl, 3.75, 1.85, 2.95, 4.2, "FFFFFF", 92, adj=0.05)
pic(sl, "p10_198.png", 3.85, 1.95, 2.75, 4.0)
txt(sl, 3.75, 6.15, 2.95, 0.6, [[("Свидетельство № 2026686768", {'bold': True})], "о регистрации программы для ЭВМ"], size=9.5, color=INK, align='c')
card(sl, 6.9, 1.85, 3.6, 4.2, "FFFFFF", 94, adj=0.05)
txt(sl, 7.15, 2.0, 3.1, 0.8, "Калькулятор транспозиции смешанного астигматизма для лентикулярной технологии", size=11.5, bold=True, color=NAVY, spacing=1.05)
for i, (lab, val) in enumerate([("Sph, дптр", ""), ("Cyl, дптр", "0,00"), ("Ax, градусы", "0")]):
    yy = 2.95 + i * 0.78
    txt(sl, 7.15, yy, 3, 0.25, lab, size=9.5, bold=True, color=MUTED)
    shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 7.15, yy + 0.28, 3.1, 0.38, "F3F7FD", None, "D2E0F5" if i else BLUE, 1, adj=0.25)
    txt(sl, 7.3, yy + 0.28, 2.0, 0.38, val, size=11, color=INK, anchor='m')
shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 7.15, 5.3, 1.45, 0.45, "E5383B", None, None, adj=0.25)
txt(sl, 7.15, 5.3, 1.45, 0.45, "Рассчитать", size=11, bold=True, color="FFFFFF", align='c', anchor='m')
txt(sl, 6.9, 6.15, 3.6, 0.6, [[("Онлайн-калькулятор", {'bold': True})], "расчёт параметров для установки"], size=9.5, color=INK, align='c')
card(sl, 10.7, 1.85, 2.0, 4.2, "FFFFFF", 92, adj=0.05)
pic(sl, "p10_199.png", 10.78, 1.95, 1.84, 4.0)
txt(sl, 10.7, 6.15, 2.0, 0.6, [[("Публикация", {'bold': True})], "первые результаты"], size=9.5, color=INK, align='c')

# ================= 11. КРИТЕРИИ =================
sl = base("Цель и методы", "Критерии включения и исключения")
card(sl, 0.6, 1.85, 5.9, 4.95, "E6F6EE", 94, "BFE5D0", adj=0.06)
shape(sl, MSO_SHAPE.OVAL, 0.9, 2.05, 0.5, 0.5, "2FA36B"); txt(sl, 0.9, 2.05, 0.5, 0.5, "✓", size=18, bold=True, color="FFFFFF", align='c', anchor='m')
txt(sl, 1.55, 2.05, 4.5, 0.5, "Критерии включения", size=18, bold=True, color=NAVY, anchor='m')
inc = ["Возраст 18 лет и старше", "Диагноз «смешанный астигматизм»", "Максимально корригированная острота зрения (МКОЗ) 0,3 и выше", "Толщина роговицы от 470 мкм и более", "Отсутствие признаков кератоконуса по BAD"]
txt(sl, 0.95, 2.8, 5.2, 2.6, [[("—  ", {'color': "2FA36B", 'bold': True}), t] for t in inc], size=13.5, color=INK, after=7, spacing=1.05)
shape(sl, MSO_SHAPE.RECTANGLE, 0.95, 5.35, 5.2, 0.012, "9FD3B8")
txt(sl, 0.95, 5.45, 5.2, 1.3, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'bold': True, 'color': NAVY, 'size': 11})], [("Sph ≤ +1,75 D", {})], [("Cyl ≥ −5 D", {})], [("SE ≤ −0,75 D", {})]],
    size=13, bold=True, color=AMBERD, spacing=1.05)
card(sl, 6.85, 1.85, 5.85, 4.95, "FDEBE9", 94, "F5C6C0", adj=0.06)
shape(sl, MSO_SHAPE.OVAL, 7.15, 2.05, 0.5, 0.5, "E5534B"); txt(sl, 7.15, 2.05, 0.5, 0.5, "✕", size=16, bold=True, color="FFFFFF", align='c', anchor='m')
txt(sl, 7.8, 2.05, 4.5, 0.5, "Критерии исключения", size=18, bold=True, color=NAVY, anchor='m')
exc = ["Возраст младше 18 лет", "Патология роговицы: кератоконус, дистрофии, неоваскуляризация, помутнение, рубцевание, состояние после кератопластики", "МКОЗ менее 0,3; толщина роговицы менее 470 мкм", "Ранее выполненный ЛАЗИК; глаукома (кроме ранней стадии); катаракта (кроме врождённой)", "Воспалительные и системные заболевания в стадии обострения, беременность и лактация"]
txt(sl, 7.2, 2.8, 5.3, 3.2, [[("—  ", {'color': "E5534B", 'bold': True}), t] for t in exc], size=12.5, color=INK, after=6, spacing=1.03)
shape(sl, MSO_SHAPE.RECTANGLE, 7.2, 6.0, 5.3, 0.012, "EDB1AA")
txt(sl, 7.2, 6.07, 5.3, 0.7, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'bold': True, 'color': NAVY, 'size': 11})], [("Несоответствие критериям SE и рефракционным параметрам", {})]], size=11.5, color=INK)

# ================= 12. ПАРАМЕТРЫ SMILE =================
def param_slide(title, sub, rows, accent, tint, imgs):
    sl = base("Технология", title)
    txt(sl, 0.6, 1.72, 12, 0.3, sub, size=12, italic=True, color=MUTED)
    n = len(rows); rh = min(0.55, 4.5 / n)
    card(sl, 0.6, 2.15, 7.6, rh * n + 0.3, "FFFFFF", 80, adj=0.04)
    for i, (a, b) in enumerate(rows):
        yy = 2.3 + i * rh
        if i: shape(sl, MSO_SHAPE.RECTANGLE, 0.9, yy, 7.0, 0.012, "D5E2F5")
        txt(sl, 0.9, yy, 3.3, rh, a, size=13, color=INK, anchor='m')
        txt(sl, 4.3, yy, 3.7, rh, b, size=13.5, bold=True, color=accent, anchor='m')
    return sl


sl = param_slide("Параметры операции: лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)",
                 [("Режим", "«быстрый»"), ("Оптическая зона", "6,7 мм"), ("Переходная зона", "0,10 мм"), ("Диаметр клапана (cap)", "7,8–7,9 мм"),
                  ("Толщина клапана (cap)", "120 мкм"), ("Угол краевого надреза", "90°"), ("Длина входного разреза", "2,0–2,4 мм"),
                  ("Интерфейс", "«S» / «M», в зависимости от диаметра роговицы"), ("Количество разрезов", "1")], AMBERD, AMBER_T, None)
card(sl, 8.5, 2.15, 4.2, 4.65, "FFFFFF", 94, adj=0.05)
pic(sl, "p12_213.png", 8.6, 2.25, 4.0, 4.45)

# ================= 13. ПАРАМЕТРЫ ФЕМТОЛАЗИК =================
sl = param_slide("Параметры операции: ФемтоЛАЗИК", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)",
                 [("Оптическая зона абляции", "6,5 мм"), ("Переходная зона", "1,2 мм"), ("Толщина флэпа", "110 мкм"), ("Общая зона абляции", "8,9 мм"),
                  ("Номограмма", "S 001"), ("Положение и ширина «ножки»", "90°, 0,6 мм"), ("Остальные параметры", "варьировали индивидуально (рефракция, пахиметрия и т.д.)")], DEEP, BLUE_T, None)
card(sl, 8.5, 2.15, 4.2, 2.75, "FFFFFF", 94, adj=0.06)
pic(sl, "p13_226.png", 8.6, 2.25, 4.0, 2.55)
card(sl, 8.5, 5.05, 4.2, 1.75, "FFFFFF", 94, adj=0.06)
pic(sl, "p13_227.png", 8.6, 5.12, 4.0, 1.6)

# ================= 14. МАТ. МОДЕЛИРОВАНИЕ =================
sl = base("Технология", "Математическое моделирование создаваемой лентикулы")
for i, (im, cap) in enumerate([("p14_232.png", "3D-модель: толщина лентикулы"), ("p14_233.png", "Карта толщины (вид сверху)"), ("p14_235.png", "Профиль (вид сбоку)")]):
    x = 0.6 + i * 4.1
    card(sl, x, 1.8, 3.9, 2.75, "FFFFFF", 92, adj=0.06)
    pic(sl, im, x + 0.1, 1.88, 3.7, 2.2)
    txt(sl, x, 4.15, 3.9, 0.3, cap, size=10, color=MUTED, align='c')
txt(sl, 0.6, 4.65, 12.1, 0.35, "На основании математической модели построена геометрическая (схематическая) модель лентикулы при смешанном астигматизме", size=12.5, bold=True, color=INK)
shape(sl, MSO_SHAPE.ROUNDED_RECTANGLE, 0.6, 5.1, 7.4, 1.75, "14284E", None, None, adj=0.1, shadow=True)
txt(sl, 0.9, 5.15, 6.8, 0.3, "Эмпирическая формула расчёта максимальной толщины лентикулы", size=10, color=SKY, bold=True)
txt(sl, 0.9, 5.45, 6.8, 0.5, "T(r,θ) = C + A·(r/R)²·cos(2(θ − ось))", size=21, bold=True, color="FFFFFF", font="Cambria Math")
txt(sl, 0.9, 6.05, 6.9, 0.75, ["C = (Max_theory + T_min) / 2     A = (Max_theory − T_min) / 2     R = S / 2",
                                "Max_theory = (S²/6)·(2|Sph'| + |Cyl'|)     T_min ≈ 20 мкм (константа устройства)"], size=10.5, color="CFE0FF", spacing=1.15)
card(sl, 8.25, 5.1, 4.45, 1.75, "FFFFFF", 92, adj=0.08)
pic(sl, "p14_234.png", 8.35, 5.17, 4.25, 1.6)

# ================= 15. РЕЗУЛЬТАТЫ: ОСТРОТА ЗРЕНИЯ =================
sl = base("Результаты", "Динамика НКОЗ и МКОЗ в исследуемых группах")
cats = ["До операции", "1-е сутки", "3 мес.", "6 мес."]
card(sl, 0.6, 1.85, 5.95, 4.95, "FFFFFF", 82, adj=0.05)
pill(sl, 0.85, 2.0, 3.6, 0.4, "Лентикулярная хирургия (SMILE)", AMBERD, size=11.5)
bar_chart(sl, 0.75, 2.5, 5.65, 4.2, cats, [("НКОЗ", (0.34, 0.73, 0.88, 0.75)), ("МКОЗ", (0.91, 0.87, 0.98, 1.00))], ["C8501F", "F2B8A0"], 0, 1.2, 0.2)
card(sl, 6.75, 1.85, 5.95, 4.95, "FFFFFF", 82, adj=0.05)
pill(sl, 7.0, 2.0, 2.6, 0.4, "ФемтоЛАЗИК", DEEP, size=11.5)
bar_chart(sl, 6.9, 2.5, 5.65, 4.2, cats, [("НКОЗ", (0.32, 0.54, 0.75, 0.72)), ("МКОЗ", (0.87, 0.84, 0.92, 0.95))], ["2F6FBF", "A9C6EA"], 0, 1.2, 0.2)
txt(sl, 4.7, 2.05, 1.7, 0.3, "острота зрения, дес.", size=9, color=MUTED, align='r')

# ================= 16. РЕЗУЛЬТАТЫ: РЕФРАКЦИЯ =================
sl = base("Результаты", "Динамика рефракционного компонента")
card(sl, 0.6, 1.85, 6.6, 4.95, "FFFFFF", 82, adj=0.05)
cd = CategoryChartData(number_format='0.00'); cd.categories = cats
cd.add_series("SMILE — Sph", (0.54, 0.22, 0.37, 0.62)); cd.add_series("SMILE — Cyl", (-3.07, -0.51, -0.44, -0.62))
cd.add_series("ФемтоЛАЗИК — Sph", (1.25, -0.20, 0.02, 0.31)); cd.add_series("ФемтоЛАЗИК — Cyl", (-3.24, -1.13, -1.19, -1.25))
gf = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, I(0.75), I(2.2), I(6.3), I(2.75), cd)
ch = gf.chart; chart_clear(ch); ch.font.name = FONT
style_axes(ch, -4, 2, 1, 11)
for s, (c, dash, pos) in zip(ch.plots[0].series, [(AMBERD, False, XL_LABEL_POSITION.ABOVE), (AMBERD, True, XL_LABEL_POSITION.BELOW), (DEEP, False, XL_LABEL_POSITION.BELOW), (DEEP, True, XL_LABEL_POSITION.BELOW)]):
    s.smooth = False
    s.format.line.color.rgb = rgb(c); s.format.line.width = Pt(2.5)
    if dash: s.format.line.dash_style = MSO_LINE.DASH
    s.marker.style = XL_MARKER_STYLE.CIRCLE; s.marker.size = 8
    s.marker.format.fill.solid(); s.marker.format.fill.fore_color.rgb = rgb("FFFFFF" if dash else c)
    s.marker.format.line.color.rgb = rgb(c)
from pptx.enum.chart import XL_TICK_LABEL_POSITION
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
ch.has_legend = False
# value table under the chart (exact numbers, doubles as legend)
series_tbl = [("SMILE — Sph", AMBERD, False, (0.54, 0.22, 0.37, 0.62)), ("SMILE — Cyl", AMBERD, True, (-3.07, -0.51, -0.44, -0.62)),
              ("ФемтоЛАЗИК — Sph", DEEP, False, (1.25, -0.20, 0.02, 0.31)), ("ФемтоЛАЗИК — Cyl", DEEP, True, (-3.24, -1.13, -1.19, -1.25))]
ty = 5.3
for j, (nm, col, dsh, vals) in enumerate(series_tbl):
    yy = ty + j * 0.33
    shape(sl, MSO_SHAPE.RECTANGLE, 0.85, yy + 0.15, 0.3, 0.035, col)
    if dsh: shape(sl, MSO_SHAPE.RECTANGLE, 0.95, yy + 0.14, 0.07, 0.06, "FFFFFF")
    txt(sl, 1.25, yy, 1.9, 0.3, nm, size=10, bold=True, color=col, anchor='m')
    for k, v in enumerate(vals):
        s_ = ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}".replace(".", ",")
        txt(sl, 3.2 + k * 0.97, yy, 0.9, 0.3, s_, size=10.5, bold=True, color=INK, align='c', anchor='m')
    if j: shape(sl, MSO_SHAPE.RECTANGLE, 0.85, yy - 0.01, 6.2, 0.01, "D5E2F5")
for k, c_ in enumerate(cats):
    txt(sl, 3.2 + k * 0.97, ty - 0.3, 0.9, 0.25, c_, size=8.5, color=MUTED, align='c', anchor='m')
txt(sl, 0.9, 1.98, 2, 0.3, "Диоптрии, D", size=9.5, color=MUTED)
small = [("Пахиметрия, мкм", (554, 537), (501, 501), 440, 600, 40, '0'), ("Кератометрия K1, D", (41.58, 41.69), (40.78, 41.83), 38, 46, 2, '0.00'), ("Кератометрия K2, D", (44.44, 44.76), (41.78, 42.83), 38, 46, 2, '0.00')]
for i, (ttl, a, b, lo, hi, mj, f) in enumerate(small):
    yy = 1.85 + i * 1.7
    card(sl, 7.4, yy, 5.3, 1.6, "FFFFFF", 82, adj=0.08)
    txt(sl, 7.6, yy + 0.08, 4, 0.3, ttl, size=11.5, bold=True, color=NAVY)
    ch = bar_chart(sl, 7.5, yy + 0.3, 5.1, 1.28, ["До операции", "6 мес."], [("SMILE", (a[0], b[0])), ("ФемтоЛАЗИК", (a[1], b[1]))], ["C8501F", "2F6FBF"], lo, hi, mj, fmt=f, legend=(i == 0), lsize=9, gap=70)
    ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
    if i == 0:
        ch.legend.position = XL_LEGEND_POSITION.RIGHT

# ================= 17. ЭФФЕКТИВНОСТЬ И БЕЗОПАСНОСТЬ =================
sl = base("Результаты", "Эффективность и безопасность")
txt(sl, 0.6, 1.62, 10, 0.3, "НКОЗ после операции / МКОЗ до операции", size=12.5, color=MUTED, italic=True)
card(sl, 0.6, 2.05, 9.4, 4.75, "FFFFFF", 94, adj=0.04)
pic(sl, "p17_270.png", 0.7, 2.15, 9.2, 4.55)
for i, (lab, v, col, tint) in enumerate([("Индекс безопасности\nSMILE", "1,03", AMBERD, AMBER_T), ("Индекс безопасности\nФемтоЛАЗИК", "1,02", DEEP, BLUE_T)]):
    yy = 2.05 + i * 2.5
    card(sl, 10.2, yy, 2.5, 2.25, tint, 94, adj=0.1)
    txt(sl, 10.4, yy + 0.2, 2.1, 0.6, lab.split("\n"), size=11.5, bold=True, color=INK)
    txt(sl, 10.4, yy + 0.95, 2.1, 1.1, v, size=48, bold=True, color=col, anchor='m')

# ================= 18. ПРОГНОЗИРУЕМОСТЬ =================
sl = base("Результаты", "Прогнозируемость")
card(sl, 0.6, 1.85, 7.0, 4.95, "FFFFFF", 94, adj=0.04)
pic(sl, "p18_275.png", 0.7, 1.95, 6.8, 4.75)
for i, (v, lab, col) in enumerate([("0,65", "R² — коэффициент детерминации", DEEP), ("74 %", "глаз в пределах ±0,5 D от планируемой коррекции", AMBERD), ("88 %", "глаз в пределах ±1,0 D от планируемой коррекции", DEEP)]):
    yy = 1.85 + i * 1.7
    card(sl, 7.85, yy, 4.85, 1.55, BLUE_T if col == DEEP else AMBER_T, 94, adj=0.1)
    txt(sl, 8.1, yy, 2.0, 1.55, v, size=38, bold=True, color=col, anchor='m')
    txt(sl, 10.1, yy, 2.45, 1.55, lab, size=11.5, color=INK, anchor='m')

# ================= 19. ВЫВОДЫ =================
sl = base("Заключение", "Выводы")
items = [("01", "Геометрическая модель лентикулы", "На основании математического моделирования построена геометрическая модель лентикулы, отражающая её торическую (седловидную) форму, что подтверждает научную обоснованность разработанного и внедрённого в клиническую практику протокола транспозиции.", BLUE),
         ("02", "НКОЗ и МКОЗ", "НКОЗ повысилась в обеих группах (SMILE — с 0,34 до 0,88; ФемтоЛАЗИК — с 0,32 до 0,75): лентикулярная технология обеспечивает более быстрое и полное зрительное восстановление без коррекции. МКОЗ оставалась стабильно высокой (с 0,91 до 1,0 и с 0,87 до 0,95): ни одна из технологий не снижает потенциальную остроту зрения.", AMBER),
         ("03", "Рефракционный компонент", "Сферический компонент приблизился к эмметропии (с +0,54 до +0,37 D в SMILE и с +1,25 до +0,31 D в ФемтоЛАЗИК). Цилиндрический компонент существенно снизился (с −3,07 до −0,62 D и с −3,24 до −1,25 D), остаточный цилиндр в лентикулярной группе вдвое меньше.", AMBER),
         ("04", "Эффективна, безопасна, перспективна", "Разработанная лентикулярная технология эффективна, безопасна и перспективна для внедрения при смешанном астигматизме. Необходимы дальнейшее накопление клинических данных и их статистическая обработка.", BLUE)]
for i, (n, t, body, col) in enumerate(items):
    x = 0.6 + (i % 2) * 6.15; y = 1.85 + (i // 2) * 2.55
    card(sl, x, y, 5.95, 2.4, "FFFFFF", 82, adj=0.08)
    txt(sl, x + 0.3, y + 0.12, 1.2, 0.7, n, size=34, bold=True, color=col if col == BLUE else AMBERD)
    txt(sl, x + 1.5, y + 0.2, 4.2, 0.55, t, size=14.5, bold=True, color=NAVY, anchor='m')
    txt(sl, x + 0.3, y + 0.85, 5.4, 1.5, body, size=12.5, color=INK, spacing=1.05)

# ================= 20. СПАСИБО =================
sl = prs.slides.add_slide(BLANK); PAGE[0] += 1
bg(sl, 'title')
txt(sl, 0.6, 0.45, 7, 0.7, [[("КАТАРАКТА ", {'color': "26397A"}), ("2026", {'color': BLUE})]], size=34, bold=True)
txt(sl, 0.6, 2.4, 7.2, 1.6, "Благодарю за внимание!", size=44, bold=True, color=NAVY, spacing=1.05)
pill(sl, 0.6, 4.3, 5.8, 0.5, "anastasianik2403@gmail.com", BLUE, size=14)
pic(sl, "p20_294.png", 7.6, 1.3, 5.2, 4.1)

prs.save("../Astigmatism_glass_wave.pptx")
print("saved")
