import os, sys, re
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

I = Inches
SANS, SERIF = "Arial", "Georgia"
FORUM = "Офтальмологический форум"
AUTHOR = "Никитина А.Е."
BASE_L, BASE_R = 0.8, 12.55

THEMES = [
    dict(n=1, name="Template1_Blue-Modern", head=SANS, hbold=True, tsize=28, tcase=None, talign='l', tcolor="0A0A0A", ink="1F2D3D", mute="6B7C8F", hair="CFE0EE",
         acc="1E7FC4", c1="1565A8", c1l="9CC7EA", c2="14A0B3", c2l="9EDDE6", card='shadow', cfill="FFFFFF", cline="DCE7F2", node='solid', num='circle', L=0.8, chrome='none', head_fill="1565A8"),
    dict(n=2, name="Template2_Cyan-Serif", head=SERIF, hbold=False, tsize=30, tcase=None, talign='l', tcolor="0B2B3B", ink="15384B", mute="5F7F8C", hair="BCE2EB",
         acc="159DBF", c1="0F8FB0", c1l="A6DFEC", c2="1B4F6B", c2l="A9C1CE", card='flat', cfill="E7F6FA", cline=None, node='soft', num='dot', L=0.8, chrome='top-right', head_fill="159DBF"),
    dict(n=3, name="Template3_Green-Health", head=SANS, hbold=True, tsize=28, tcase=None, talign='l', tcolor="0E9F8A", ink="13302B", mute="5F8079", hair="BFE0DA",
         acc="0E9F8A", c1="0E9F8A", c1l="A8DDD4", c2="0B5D4E", c2l="8DB8AF", card='line', cfill="FFFFFF", cline="BFE0DA", node='ring', num='paren', L=1.15, chrome='health', head_fill="0E9F8A"),
    dict(n=4, name="Template4_Blue-Pitch", head=SANS, hbold=True, tsize=19, tcase='upper', talign='l', tcolor="0A0A0A", ink="1C2A44", mute="66738C", hair="D3DAE8",
         acc="1747C4", c1="0B3FA8", c1l="9DB6EE", c2="1AA0E8", c2l="A9DBF6", card='border', cfill="FFFFFF", cline="C9D3E6", node='solid', num='plain', L=0.8, chrome='pitch', head_fill="0B3FA8"),
    dict(n=5, name="Template5_Orange-Conference", head=SANS, hbold=False, tsize=28, tcase=None, talign='l', tcolor="111111", ink="2A2A2A", mute="7A7A7A", hair="D5D5D5",
         acc="E8531F", c1="E8531F", c1l="F6B9A0", c2="333333", c2l="B8B8B8", card='none', cfill="FFFFFF", cline=None, node='ring', num='orange', L=0.8, chrome='conf', head_fill="E8531F"),
    dict(n=6, name="Template6_Periwinkle-Business", head=SANS, hbold=False, tsize=22, tcase=None, talign='c', tcolor="111111", ink="1F2A44", mute="6F7C99", hair="C7D6F7",
         acc="6F9AF0", c1="4A78E0", c1l="B7CCF7", c2="1F2A44", c2l="A9B3CC", card='border', cfill="FFFFFF", cline="C7D6F7", node='soft', num='circlesoft', L=0.8, chrome='biz', head_fill="86AAF2"),
    dict(n=7, name="Template7_Purple-Minimal", head=SANS, hbold=True, tsize=26, tcase=None, talign='l', tcolor="14141A", ink="2A2A33", mute="8A8A99", hair="D9D9E3",
         acc="6F66D9", c1="5B52C9", c1l="B8B2EE", c2="14141A", c2l="A6A6B3", card='none', cfill="FFFFFF", cline=None, node='orb', num='paren', L=1.1, chrome='min', head_fill="5B52C9"),
]

SECTIONS = {2: "Актуальность", 3: "Актуальность", 4: "Цель", 5: "Цель и методы", 6: "Цель и методы", 7: "Цель и методы", 8: "Технология", 9: "Технология", 10: "Технология",
            11: "Цель и методы", 12: "Технология", 13: "Технология", 14: "Технология", 15: "Результаты", 16: "Результаты", 17: "Результаты", 18: "Результаты", 19: "Заключение"}

# ------------------------------------------------------------------ state
T = None; prs = None; sl = None; PAGE = 0


def rgb(h): return RGBColor.from_string(h)
def sx(): return (BASE_R - T['L']) / (BASE_R - BASE_L)
def gx(x): return T['L'] + (x - BASE_L) * sx()
def gw(w): return w * sx()


def _strip(s):
    st = s._element.find(qn('p:style'))
    if st is not None: s._element.remove(st)


def rect(x, y, w, h, fill=None, line=None, lw=0.75, kind=MSO_SHAPE.RECTANGLE, adj=None, alpha=None, shadow=False, dash=None, raw=False):
    X, W = (x, w) if raw else (gx(x), gw(w))
    s = sl.shapes.add_shape(kind, I(X), I(y), I(W), I(h))
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            etree.SubElement(s._element.spPr.find(qn('a:solidFill'))[0], qn('a:alpha')).set('val', str(int(alpha * 1000)))
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
        if dash: s.line.dash_style = dash
    else:
        s.line.fill.background()
    eff = etree.SubElement(s._element.spPr, qn('a:effectLst'))
    if shadow:
        sh = etree.SubElement(eff, qn('a:outerShdw'))
        for k, v in (('blurRad', '260000'), ('dist', '60000'), ('dir', '5400000'), ('algn', 't'), ('rotWithShape', '0')): sh.set(k, v)
        c = etree.SubElement(sh, qn('a:srgbClr')); c.set('val', '3A5A8C'); etree.SubElement(c, qn('a:alpha')).set('val', '14000')
    if adj is not None and len(s.adjustments): s.adjustments[0] = adj
    _strip(s)
    return s


def txt(x, y, w, h, paras, size=12, color=None, bold=False, align='l', anchor='t', italic=False, spacing=None, after=0, font=None, raw=False):
    X, W = (x, w) if raw else (gx(x), gw(w))
    tb = sl.shapes.add_textbox(I(X), I(y), I(W), I(h))
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
            f = run.font; f.name = o.get('font', font or SANS); f.size = Pt(o.get('size', size))
            f.bold = o.get('bold', bold); f.italic = o.get('italic', italic); f.color.rgb = rgb(o.get('color', color or T['ink']))
    return tb


def hair(x1, y1, x2, y2, color=None, w=0.75, dash=None, raw=False):
    X1, X2 = (x1, x2) if raw else (gx(x1), gx(x2))
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(X1), I(y1), I(X2), I(y2))
    c.line.color.rgb = rgb(color or T['hair']); c.line.width = Pt(w)
    if dash: c.line.dash_style = dash
    _strip(c); return c


def dot(x, y, r=0.05, color=None):
    rect(x - r / sx(), y - r, 2 * r / sx(), 2 * r, color or T['tcolor'] if T['n'] != 3 else T['acc'], kind=MSO_SHAPE.OVAL) if False else \
        sl.shapes.add_shape(MSO_SHAPE.OVAL, I(gx(x) - r), I(y - r), I(2 * r), I(2 * r))
    s = sl.shapes[-1]; s.fill.solid(); s.fill.fore_color.rgb = rgb(color or T['acc']); s.line.fill.background(); _strip(s)


def ring(cx, cy, d, color="C9D2EC", w=0.6, dash=None):
    dd = d * sx()
    s = sl.shapes.add_shape(MSO_SHAPE.OVAL, I(gx(cx) - dd / 2), I(cy - d / 2), I(dd), I(d))
    s.fill.background(); s.line.color.rgb = rgb(color); s.line.width = Pt(w)
    if dash: s.line.dash_style = dash
    _strip(s); return s


def pic(name, x, y, w, h, halign='c', valign='m', frame=False):
    stem = os.path.splitext(name)[0]
    path = next(p for p in (f"imgo/{stem}.png", f"imgo/{stem}.jpg") if os.path.exists(p))
    iw, ih = Image.open(path).size
    W = gw(w); sc = min(W / iw, h / ih); pw, ph = iw * sc, ih * sc
    X = gx(x)
    px = X + (W - pw) / 2 if halign == 'c' else (X if halign == 'l' else X + W - pw)
    py = y + (h - ph) / 2 if valign == 'm' else (y if valign == 't' else y + h - ph)
    if frame:
        rect(px - 0.03, py - 0.03, pw + 0.06, ph + 0.06, "FFFFFF", T['hair'], 0.6, raw=True)
    return sl.shapes.add_picture(path, I(px), I(py), I(pw), I(ph))


# ------------------------------------------------------------------ themed components
def card(x, y, w, h):
    k = T['card']
    if k == 'shadow': rect(x, y, w, h, T['cfill'], T['cline'], 0.75, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05, shadow=True)
    elif k == 'flat': rect(x, y, w, h, T['cfill'])
    elif k == 'line': rect(x, y, w, h, "FFFFFF", T['cline'], 0.9, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03, alpha=70)
    elif k == 'border': rect(x, y, w, h, T['cfill'], T['cline'], 0.9, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    elif k == 'none': hair(x, y, x + w, y); hair(x, y + h, x + w, y + h)


def node(cx, cy, d, label=None, size=12, bold=False, strong=False, color=None):
    st = T['node']; col = T['c2'] if strong else T['c1']
    dd = d * sx()
    if st == 'orb':
        ring(cx, cy, d * 1.45, "CFCBF0")
        s = rect(cx - d / 2, cy - d / 2, d, d, "D8D4F8", kind=MSO_SHAPE.OVAL)
        sp = s._element.spPr
        e = sp.find(qn('a:solidFill')); sp.remove(e)
        c0, c1, c2 = ("EEECFC", "CFCAF6", "9C94EA") if strong else ("F6F5FE", "E1DEFA", "B9B3F0")
        g = etree.fromstring('<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1"><a:gsLst>'
                             f'<a:gs pos="0"><a:srgbClr val="{c0}"/></a:gs><a:gs pos="62000"><a:srgbClr val="{c1}"/></a:gs><a:gs pos="100000"><a:srgbClr val="{c2}"/></a:gs></a:gsLst>'
                             '<a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>')
        sp.find(qn('a:prstGeom')).addnext(g); tc = T['ink']
    elif st == 'solid':
        rect(cx - d / 2, cy - d / 2, d, d, col, kind=MSO_SHAPE.OVAL); tc = "FFFFFF"
    elif st == 'ring':
        rect(cx - d / 2, cy - d / 2, d, d, "FFFFFF", col, 1.5, MSO_SHAPE.OVAL, alpha=80); tc = T['ink']
    else:  # soft
        rect(cx - d / 2, cy - d / 2, d, d, T['c2l'] if strong else T['c1l'], kind=MSO_SHAPE.OVAL, alpha=70); tc = T['ink']
    if label is not None:
        txt(cx - d / 2 + 0.08, cy - d / 2, d - 0.16, d, label, size=size, bold=bold, color=color or tc, align='c', anchor='m')


def numlabel(n, x, y, w=0.7, h=0.4, size=None):
    k = T['num']; s = f"{n:02d}"
    if k == 'circle':
        rect(x, y + (h - 0.4) / 2, 0.4 / sx(), 0.4, T['acc'], kind=MSO_SHAPE.OVAL); txt(x, y, 0.4 / sx(), h, s, size=10, bold=True, color="FFFFFF", align='c', anchor='m')
    elif k == 'circlesoft':
        rect(x, y + (h - 0.4) / 2, 0.4 / sx(), 0.4, T['c1l'], kind=MSO_SHAPE.OVAL); txt(x, y, 0.4 / sx(), h, s, size=10, bold=True, color=T['c1'], align='c', anchor='m')
    elif k == 'dot':
        txt(x, y, w, h, s + ".", size=size or 16, color=T['acc'], font=SERIF, anchor='m')
    elif k == 'paren':
        txt(x, y, w + 0.3, h, f"( {s} )", size=size or 11, color=T['acc'] if T['n'] == 3 else T['mute'], font=SERIF if T['n'] == 7 else SANS, anchor='m')
    elif k == 'orange':
        txt(x, y, w, h, s, size=size or 15, color=T['acc'], anchor='m')
    else:
        txt(x, y, w, h, s, size=size or 12, bold=True, color=T['acc'], anchor='m')


def head(x, y, w, text, color=None, size=13, h=0.38, fill=None):
    if T['n'] == 6:
        rect(x, y, w, h, fill or T['c1l'], kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
        txt(x + 0.1, y, w - 0.2, h, text, size=size - 1, bold=True, color="FFFFFF" if fill else T['c2'], align='c', anchor='m')
    else:
        txt(x, y, w, h, text, size=size, bold=True, color=color or T['tcolor'], anchor='m')


# ------------------------------------------------------------------ slide scaffolding
def titletext(t, key_color=True):
    if T['tcase'] == 'upper': t = t.upper()
    return t


def new(bgname):
    global sl, PAGE
    sl = prs.slides.add_slide(prs.slide_layouts[6]); PAGE += 1
    sl.shapes.add_picture(f"img/th{T['n']}_{bgname}.png", 0, 0, prs.slide_width, prs.slide_height)
    return sl


def slide(title, sub=None):
    new('content')
    sec = SECTIONS.get(PAGE, "")
    plain = title.replace("**", "")
    ch = T['chrome']
    # chrome
    if ch == 'top-right': txt(8.3, 0.32, 4.45, 0.25, FORUM, size=8.5, bold=True, color=T['acc'], align='r', raw=True)
    if ch == 'health':
        txt(1.15, 0.28, 3, 0.25, AUTHOR, size=9, bold=True, color=T['acc'], raw=True); txt(11.0, 0.28, 1.7, 0.25, f"{PAGE:02d}", size=9, color=T['acc'], align='r', raw=True)
    if ch == 'pitch':
        txt(0.8, 0.25, 6, 0.25, sec, size=8.5, color=T['mute'], raw=True)
        txt(0.8, 7.12, 5, 0.22, f"▪ {FORUM}  ·  {AUTHOR}", size=8, bold=True, color=T['c1'], raw=True)
        txt(10.5, 7.12, 2.05, 0.22, f"Страница | {PAGE:02d}", size=8, color=T['mute'], align='r', raw=True)
    if ch == 'conf':
        txt(0.8, 0.28, 5, 0.22, FORUM, size=8, color=T['mute'], raw=True); txt(7.5, 0.28, 5.05, 0.22, AUTHOR, size=8, color=T['mute'], align='r', raw=True)
        txt(7.5, 7.12, 5.05, 0.22, sec, size=8, color=T['mute'], align='r', raw=True); txt(0.8, 7.12, 2, 0.22, f"{PAGE:02d}", size=8, color=T['mute'], raw=True)
    if ch == 'biz':
        txt(0.8, 0.22, 6, 0.22, FORUM.upper(), size=7.5, bold=True, color=T['acc'], raw=True); txt(7.5, 0.22, 5.05, 0.22, sec.upper() + f"  ·  {PAGE:02d}", size=7.5, bold=True, color=T['acc'], align='r', raw=True)
    if ch in ('none', 'min', 'top-right'):
        txt(11.7, 7.12, 0.85, 0.22, f"{PAGE:02d}", size=8.5, bold=True, color=T['mute'], align='r', raw=True)
        txt(0.8 if T['L'] < 1 else T['L'], 7.12, 4, 0.22, AUTHOR, size=8, color=T['mute'], raw=True)
    # title
    parts = re.split(r'(\*\*.+?\*\*)', title)
    runs = []
    for p in parts:
        if not p: continue
        isk = p.startswith("**")
        p = p.strip("*")
        runs.append((titletext(p), {'color': T['acc'] if (isk and T['n'] == 4) else T['tcolor']}))
    ty = 0.5 if ch not in ('pitch', 'biz') else 0.55
    size = T['tsize'] if len(plain) < 46 else T['tsize'] - (6 if T['n'] == 2 else 3 if T['n'] != 4 else 1.5)
    if T['talign'] == 'c':
        txt(0.8, ty, 11.75, 0.5, [runs], size=size, bold=T['hbold'], font=T['head'], align='c', raw=True)
    else:
        txt(0.8, ty, 11.75, 0.5, [runs], size=size, bold=T['hbold'], font=T['head'], raw=True) if T['L'] < 1 else txt(T['L'], ty, 11.4, 0.5, [runs], size=size, bold=T['hbold'], font=T['head'], raw=True)
    if sub:
        txt(0.8 if T['L'] < 1 else T['L'], 1.03, 11.5, 0.3, sub, size=11, color=T['mute'], italic=True, raw=True, align='c' if T['talign'] == 'c' else 'l')
    if ch == 'conf': hair(0.8, 1.2 if not sub else 1.35, 12.55, 1.2 if not sub else 1.35, raw=True)
    return sl


# ------------------------------------------------------------------ charts
def chart_clear(chart):
    sp = etree.Element(qn('c:spPr')); etree.SubElement(sp, qn('a:noFill'))
    etree.SubElement(etree.SubElement(sp, qn('a:ln')), qn('a:noFill'))
    chart._chartSpace.find(qn('c:chart')).addnext(sp)


def style_axes(chart, vmin, vmax, major, size=10):
    va = chart.value_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = vmin, vmax, major
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(T['hair']); va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(size); va.tick_labels.font.color.rgb = rgb(T['mute']); va.tick_labels.font.name = SANS
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(size); ca.tick_labels.font.color.rgb = rgb(T['ink']); ca.tick_labels.font.name = SANS
    ca.format.line.color.rgb = rgb(T['c2l']); ca.has_major_gridlines = False


def bar_chart(x, y, w, h, cats, series, colors, vmin, vmax, major, fmt='0.00', legend=True, lsize=10, gap=60):
    cd = CategoryChartData(); cd.categories = cats
    for n, v in series: cd.add_series(n, v)
    ch = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(gx(x)), I(y), I(gw(w)), I(h), cd).chart
    chart_clear(ch); ch.font.name = SANS
    pl = ch.plots[0]; pl.gap_width = gap; pl.overlap = -6
    for s, c in zip(pl.series, colors):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c); s.invert_if_negative = False
    pl.has_data_labels = True
    dl = pl.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False
    dl.font.size = Pt(lsize); dl.font.bold = True; dl.font.color.rgb = rgb(T['tcolor'] if T['n'] != 3 else T['ink']); dl.position = XL_LABEL_POSITION.OUTSIDE_END
    style_axes(ch, vmin, vmax, major, lsize)
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(lsize); ch.legend.font.color.rgb = rgb(T['ink'])
    return ch


# =========================================================================== SLIDES
MAIN = "Современный подход к хирургической коррекции смешанного астигматизма"
SUBT = "с применением фемтосекундной лентикулярной технологии"
SPEAKER = "Никитина Анастасия Евгеньевна"
COAUTH = "д.м.н. Костенев С.В., к.м.н. Макаров Р.А., Садрутдинов Р.Ш."
AFF = ["ФГБОУ ВО «Российский университет медицины» Минздрава России", "ФГАУ «НМИЦ «МНТК «Микрохирургия глаза» им. акад. С.Н. Федорова» Минздрава России"]


def s_title():
    new('title'); n = T['n']
    if n == 1:
        for i, t in enumerate((AUTHOR, FORUM)):
            rect(0.8 + i * 1.75, 0.45, 1.6 + (0.5 if i else 0), 0.32, "FFFFFF", T['hair'], 0.6, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, raw=True)
            txt(0.8 + i * 1.75, 0.45, 1.6 + (0.5 if i else 0), 0.32, t, size=8, color=T['ink'], align='c', anchor='m', raw=True)
        txt(0.8, 1.7, 9.6, 3.0, MAIN, size=38, bold=True, color=T['tcolor'], spacing=1.0, raw=True)
        txt(0.8, 4.35, 9.6, 0.8, SUBT, size=22, color=T['ink'], raw=True)
        txt(0.8, 5.6, 8.5, 0.6, [[("Докладчик: ", {'color': T['mute']}), (SPEAKER, {'bold': True})], [("Соавторы: " + COAUTH, {'size': 11})]], size=13, spacing=1.2)
        txt(0.8, 6.55, 9, 0.5, AFF, size=9, color=T['mute'], spacing=1.1, raw=True)
    elif n == 2:
        txt(0.8, 3.0, 10.5, 2.4, [[(MAIN, {})], [(SUBT, {'size': 24})]], size=36, color=T['tcolor'], font=SERIF, spacing=1.0, after=4, raw=True)
        txt(0.8, 6.25, 3.8, 0.5, [[(SPEAKER, {'bold': True})], [("Докладчик", {'color': T['mute'], 'size': 8.5})]], size=10, raw=True)
        txt(4.8, 6.25, 4.6, 0.5, [[(COAUTH, {})], [("Соавторы", {'color': T['mute'], 'size': 8.5})]], size=9.5, raw=True)
        txt(9.6, 6.25, 3.0, 0.5, [[(FORUM, {'bold': True})]], size=10, align='r', raw=True)
    elif n == 3:
        txt(1.15, 0.28, 4, 0.25, AUTHOR, size=10, bold=True, color=T['acc'], raw=True)
        txt(1.5, 2.55, 10.4, 2.2, MAIN, size=34, bold=True, color=T['acc'], align='c', spacing=1.0, raw=True)
        txt(1.5, 4.55, 10.4, 0.6, SUBT, size=20, color=T['tcolor'] if False else T['ink'], align='c', raw=True)
        txt(1.15, 6.5, 6, 0.5, [[(SPEAKER, {'bold': True, 'color': T['acc']})], [(COAUTH, {'size': 8.5, 'color': T['mute']})]], size=10, raw=True)
        txt(8.5, 6.5, 4.1, 0.4, FORUM, size=9, color=T['mute'], align='r', raw=True)
    elif n == 4:
        txt(0.8, 0.3, 6, 0.25, FORUM, size=9, color=T['mute'], raw=True)
        txt(0.8, 1.6, 10.8, 3.0, [[("СОВРЕМЕННЫЙ ПОДХОД К ХИРУРГИЧЕСКОЙ КОРРЕКЦИИ ", {}), ("СМЕШАННОГО АСТИГМАТИЗМА", {'color': T['acc']})]], size=34, bold=True, color=T['tcolor'], spacing=1.0, raw=True)
        txt(0.8, 4.3, 10, 0.8, SUBT, size=17, color=T['mute'], raw=True)
        rect(0.8, 5.55, 5.1, 0.7, "FFFFFF", T['cline'], 0.8, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, raw=True)
        txt(1.05, 5.55, 4.7, 0.7, [[(SPEAKER, {'bold': True, 'color': T['c1']})], [(COAUTH, {'size': 7.5, 'color': T['mute']})]], size=10.5, anchor='m', raw=True)
    elif n == 5:
        txt(0.8, 0.28, 5, 0.22, FORUM, size=8, color=T['mute'], raw=True)
        txt(0.8, 1.35, 8.8, 3.4, [[(MAIN, {})], [(SUBT, {'size': 22})]], size=34, color=T['tcolor'], spacing=1.05, after=6, raw=True)
        txt(0.8, 5.65, 8, 0.8, [[(SPEAKER, {'color': T['acc'], 'bold': True}), ("  |  " + COAUTH, {'color': T['acc'], 'size': 9})], [(AFF[0], {'size': 8.5, 'color': T['mute']})], [(AFF[1], {'size': 8.5, 'color': T['mute']})]], size=11, spacing=1.15, raw=True)
    elif n == 6:
        txt(0.8, 1.6, 11, 0.5, "СОВРЕМЕННЫЙ ПОДХОД К ХИРУРГИЧЕСКОЙ КОРРЕКЦИИ", size=24, color=T['acc'], raw=True)
        txt(0.8, 2.2, 11.5, 1.6, "СМЕШАННОГО АСТИГМАТИЗМА", size=36, bold=True, color=T['tcolor'], raw=True)
        txt(0.8, 3.15, 11, 0.5, SUBT, size=20, color=T['tcolor'], raw=True)
        txt(0.8, 5.1, 6, 1.4, [[(FORUM.upper(), {'bold': True, 'color': T['acc'], 'size': 8})], [(SPEAKER, {'bold': True})], [(COAUTH, {'size': 9, 'color': T['mute']})], [(AFF[0], {'size': 8, 'color': T['mute']})], [(AFF[1], {'size': 8, 'color': T['mute']})]], size=11, spacing=1.2, after=2, raw=True)
    elif n == 7:
        txt(1.1, 2.6, 11.2, 2.4, MAIN, size=34, bold=True, color=T['tcolor'], align='c', spacing=1.0, raw=True)
        txt(1.1, 4.6, 11.2, 0.5, f"(  {SUBT}  )", size=18, color=T['ink'], font=SERIF, align='c', raw=True)
        txt(1.1, 6.55, 6, 0.4, f"{SPEAKER}", size=9, bold=True, color=T['tcolor'], raw=True)
        txt(6.0, 6.55, 6.6, 0.4, COAUTH, size=8.5, color=T['mute'], align='r', raw=True)


def s_aktual1():
    slide("Актуальность")
    hair(4.7, 0.5 if False else 1.35, 4.7, 3.55)
    pic("p2_22.png", 0.8, 1.45, 3.5, 2.2)
    txt(5.1, 1.35, 7.4, 2.3, [[("•  ", {'color': T['acc'], 'bold': True}), "Астигматизм — мультифакторное состояние с выраженным наследственным компонентом."],
                               [("•  ", {'color': T['acc'], 'bold': True}), "Полногеномные исследования (Shing E. et al., 2024) выявили свыше 50 полиморфизмов в 10 генах, включая локус PDGFRA, регулирующий кривизну роговицы."]], size=14.5, after=10, spacing=1.1)
    txt(0.8, 3.85, 11, 0.3, "Хирургическая коррекция смешанного астигматизма", size=13, bold=True, color=T['tcolor'] if T['n'] != 3 else T['acc'])
    hair(0.8, 4.2, 12.5, 4.2)
    hair(3.5, 4.85, 8.8, 4.85)
    node(3.5, 4.85, 1.4, [[("ФемтоЛАЗИК", {'size': 11, 'bold': True})]], 11)
    node(8.8, 4.85, 1.4, [[("?", {'size': 28, 'bold': True})]], 12, strong=True)
    txt(1.75, 5.75, 3.5, 0.6, [[("Эксимерлазерная технология. Современный ", {}), ("«золотой»", {'bold': True}), (" стандарт в коррекции смешанного астигматизма", {})]], size=10, align='c')
    txt(7.05, 5.75, 3.5, 0.5, [[("Лентикулярная технология", {'bold': True})]], size=11, align='c')
    txt(0.8, 6.55, 11.8, 0.55, ["Азара Д.Т., Алио Х.Л., Кортина М.С., Халлака Д.А. Хирургическое лечение астигматизма. Москва: ГЭОТАР-Медиа, 2025. — 272 с. doi: 10.33029/9704-8200-1-STA-2025-1-272; Shing E. et al. Heritability and Genetic Factors of Astigmatism and Corneal Curvature. Am J Ophthalmol. 2025;269:161–171. doi: 10.1016/j.ajo.2024.08.019; Клокова О.А. и др. Ранние клинико-функциональные результаты коррекции смешанного астигматизма в зависимости от его степени с помощью высокочастотного эксимерного лазера Schwind Amaris 1050RS. Офтальмология. 2025;22(2):295–304. https://doi.org/10.18008/1816-5095-2025-2-295-304"], size=6, italic=True, color=T['mute'], spacing=0.95)


def s_aktual2():
    slide("Актуальность")
    txt(0.8, 1.5, 8.2, 1.2, [[("Пилотное исследование на платформе ", {}), ("VisuMax", {'bold': True}), (" (Carl Zeiss Meditec AG) показало возможность коррекции смешанного астигматизма методом лентикулярной хирургии (Ganesh S. et al., 2024), однако методика пока не применяется в стандартной практике.", {})]], size=13, spacing=1.1)
    hair(0.8, 2.9, 8.9, 2.9); dot(8.9, 2.9)
    txt(3.9, 3.4, 5.9, 1.3, [[("Экспериментальное исследование ex-vivo (11 свиных глаз) на платформе ", {}), ("Elita", {'bold': True}), (", Johnson and Johnson Surgical Vision, Inc. (США) свидетельствуют о технической возможности коррекции смешанного астигматизма и гиперметропии.", {})]], size=13, spacing=1.1)
    hair(3.9, 4.9, 9.9, 4.9); dot(9.9, 4.9)
    pic("p3_63.png", 0.8, 3.4, 2.8, 3.3)
    pic("p3_58.png", 10.15, 1.45, 1.25, 2.9, valign='t', frame=True)
    pic("p3_62.png", 11.55, 1.45, 1.25, 2.9, valign='t', frame=True)
    txt(10.0, 3.2, 1.5, 0.3, "Ganesh S. et al., 2024", size=7.5, color=T['mute'], align='c')
    txt(11.4, 3.85, 1.5, 0.3, "ARVO, 2025", size=7.5, color=T['mute'], align='c')


def s_goal():
    slide("Цель")
    hair(4.7, 1.35, 4.7, 4.6)
    txt(5.1, 2.5, 7.4, 2.0, "Разработать лентикулярную технологию для коррекции смешанного астигматизма", size=26, color=T['tcolor'] if T['n'] != 3 else T['ink'], spacing=1.1)
    pic("p4_74.png", 1.2, 4.55, 4.6, 2.5)


def s_methods():
    slide("Материалы и методы")
    hair(3.9, 2.85, 9.4, 2.85)
    node(3.9, 2.85, 2.2, [[("SMILE", {'size': 20, 'bold': True})], [("20 пациентов", {'size': 11})], [("(40 глаз)", {'size': 11})]], 12)
    node(9.4, 2.85, 2.2, [[("ФемтоЛАЗИК", {'size': 15, 'bold': True})], [("20 пациентов", {'size': 11})], [("(40 глаз)", {'size': 11})]], 12, strong=True)
    txt(2.4, 1.35, 3, 0.25, "ГРУППА 1", size=9, bold=True, color=T['mute'], align='c'); txt(7.9, 1.35, 3, 0.25, "ГРУППА 2", size=9, bold=True, color=T['mute'], align='c')
    txt(2.0, 4.55, 3.8, 1.0, [[("Лентикулярная технология (SMILE)", {'bold': True, 'size': 12.5, 'color': T['tcolor'] if T['n'] != 3 else T['acc']})], [("Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", {'italic': True, 'size': 9.5})]], align='c', spacing=1.1, after=3)
    txt(7.5, 4.55, 3.8, 1.0, [[("Эксимерлазерная технология (ФемтоЛАЗИК)", {'bold': True, 'size': 12.5, 'color': T['tcolor'] if T['n'] != 3 else T['acc']})], [("Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", {'italic': True, 'size': 9.5})]], align='c', spacing=1.1, after=3)
    pic("p5_87.png", 0.7, 1.7, 1.7, 1.5); pic("p5_86.png", 0.95, 3.2, 1.2, 1.2)
    pic("p5_88.png", 11.0, 1.7, 1.8, 1.5); pic("p5_89.png", 11.3, 3.2, 1.2, 1.2)
    txt(0.8, 5.6, 6, 0.3, "Наблюдение проводилось до операции и в стандартные сроки", size=10, bold=True, color=T['tcolor'] if T['n'] != 3 else T['acc'])
    hair(0.8, 6.4, 12.5, 6.4)
    for i, lab in enumerate(["До операции", "1 сутки", "3 месяца", "6 месяцев"]):
        cx = 1.5 + i * 3.45; dot(cx, 6.4, 0.06); txt(cx - 1, 6.55, 2, 0.3, lab, size=10.5, align='c')


def s_ranges():
    slide("Диапазон **рефракционных значений** в исследуемых группах")
    head(4.0, 1.3, 3.6, "Лентикулярная технология (SMILE)", T['c1'], 12)
    head(8.2, 1.3, 3.9, "Эксимерлазерная технология (ФемтоЛАЗИК)", T['c2'] if T['n'] != 7 else T['mute'], 12)
    rows = [("Сферический компонент (Sph)", ("от +0,25 до +1,75 D", "M ± SD +0,54 ± 0,39"), ("от +0,25 до +3,00 D", "M ± SD +1,25 ± 0,81")),
            ("Цилиндрический компонент (Cyl)", ("от −2,00 до −5,00 D", "M ± SD −3,07 ± 0,93"), ("от −1,25 до −6,00 D", "M ± SD −3,24 ± 2,03")),
            ("Кератометрия, D", ("K1 41,58 · K2 44,44", "K AVE 43,00"), ("K1 41,69 · K2 44,76", "K AVE 43,22")),
            ("Пахиметрия, мкм", ("от 494 до 615 мкм", "M ± SD 554,1 ± 36,2"), ("от 483 до 596 мкм", "M ± SD 537,1 ± 30,8"))]
    c2t = T['c2'] if T['n'] not in (5, 7) else T['ink']
    for i, (lab, a, b) in enumerate(rows):
        y = 1.95 + i * 0.82
        hair(0.8, y - 0.08, 12.5, y - 0.08)
        txt(0.8, y, 3.0, 0.7, lab, size=11.5, bold=True, anchor='m')
        txt(4.0, y, 3.6, 0.7, [[(a[0], {'bold': True, 'size': 13, 'color': T['c1']})], [(a[1], {'size': 10.5})]], anchor='m')
        txt(8.2, y, 3.9, 0.7, [[(b[0], {'bold': True, 'size': 13, 'color': c2t})], [(b[1], {'size': 10.5})]], anchor='m')
    hair(0.8, 5.2, 12.5, 5.2)
    txt(0.8, 5.4, 3, 0.25, "Распределение по полу, n", size=10, bold=True)
    cd = CategoryChartData(); cd.categories = ["ФемтоЛАЗИК", "SMILE"]
    cd.add_series("Мужчины", (7, 11)); cd.add_series("Женщины", (13, 9))
    ch = sl.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, I(gx(0.7)), I(5.6), I(gw(5.6)), I(1.4), cd).chart
    chart_clear(ch); ch.font.name = SANS
    pl = ch.plots[0]; pl.gap_width = 45; pl.overlap = 100
    for s, c in zip(pl.series, [T['c1'], T['c1l']]): s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(c)
    pl.has_data_labels = True; pl.data_labels.font.size = Pt(10); pl.data_labels.font.bold = True; pl.data_labels.font.color.rgb = rgb("FFFFFF")
    ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
    ch.category_axis.tick_labels.font.size = Pt(10); ch.category_axis.format.line.fill.background()
    ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.RIGHT; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(9)
    txt(7.4, 5.4, 3, 0.25, "Средний возраст", size=10, bold=True)
    node(8.4, 6.2, 1.15, [[("31,2", {'size': 16, 'bold': True})], [("года", {'size': 8.5})]], 10)
    node(11.0, 6.2, 1.15, [[("29,2", {'size': 16, 'bold': True})], [("года", {'size': 8.5})]], 10, strong=True)
    txt(7.6, 6.85, 1.6, 0.2, "SMILE", size=8.5, color=T['mute'], align='c'); txt(10.2, 6.85, 1.6, 0.2, "ФемтоЛАЗИК", size=8.5, color=T['mute'], align='c')
    txt(0.8, 7.02, 6, 0.15, "* M ± SD — среднее ± стандартное отклонение", size=6.5, italic=True, color=T['mute'])


def s_diag():
    slide("Методы диагностики")
    hair(6.65, 1.3, 6.65, 4.95)
    head(0.8, 1.3, 5.5, "Стандартные методы диагностики", T['c1'], 13)
    head(7.0, 1.3, 5.5, "Специальные методы диагностики", T['c1'], 13)
    std = [("Визометрия", "НКОЗ и МКОЗ в естественных условиях и при медикаментозном мидриазе"), ("Рефрактометрия, кератометрия", "в естественных условиях и при медикаментозном мидриазе"), ("Тонометрия, биометрия, периметрия", ""), ("Биомикроскопия и офтальмоскопия", "")]
    spec = [("Кератотопография", "Pentacam AXL (Oculus, Германия)"), ("Анализ биомеханических свойств роговицы", "Corvis ST (Oculus, Германия)"), ("Аберрометрия", "KR-1W (Topcon, Япония)")]
    for items, x0 in ((std, 0.8), (spec, 7.0)):
        for i, (a, b) in enumerate(items):
            y = 1.85 + i * 0.78
            numlabel(i + 1, x0, y + 0.1, 0.75, 0.42)
            txt(x0 + 0.85, y, 4.9, 0.62, [[(a, {'bold': True, 'size': 12})]] + ([[(b, {'size': 9.5, 'color': T['mute']})]] if b else []), anchor='m', spacing=1.05)
    hair(0.8, 5.1, 12.5, 5.1)
    pic("p7_112.png", 0.9, 5.25, 0.95, 1.7); pic("p7_122.png", 2.0, 5.25, 2.3, 1.7); pic("p7_121.png", 4.4, 5.25, 2.2, 1.7); pic("p7_113.png", 7.3, 5.25, 5.0, 1.7)


def s_steps():
    slide("Лентикулярная технология коррекции смешанного астигматизма", "Транспозиция исходной рефракции (sph, cyl, ax) по разработанной технологии")
    hair(0.8, 2.95, 12.3, 2.95)
    steps = [("Допуск", "Условия допуска", ["Sph ≤ +1,75 D", "Cyl ≥ −5 D", "SE ≤ −0,75 D"]), ("Сфера", "Транспозиция сферы", ["SPH' = SPH + CYL"]), ("Цилиндр", "Инверсия цилиндра", ["CYL' = −CYL (знак +)"]),
             ("Ось", "Коррекция оси", ["Ax ≤ 90° → +90°;", "AX > 90° → −90°.", "Ручная маркировка роговицы для минимизации циклоторсии (ось астигматизма)"]), ("Ввод", "Ввод данных в лазер", ["Ввод полученных рефракционных данных в фемтосекундную лазерную установку"])]
    for i, (inner, ttl, body) in enumerate(steps):
        cx = 1.75 + i * 2.5
        node(cx, 2.95, 1.3, [[(f"0{i+1}", {'size': 8.5})], [(inner, {'size': 11.5, 'bold': True})]], 11, strong=(i == 4))
        txt(cx - 1.15, 3.95, 2.3, 0.3, ttl, size=11.5, bold=True, align='c', color=T['tcolor'] if T['n'] != 3 else T['acc'])
        txt(cx - 1.1, 4.3, 2.2, 1.7, body, size=10, align='c', spacing=1.08, after=2)
    pic("p8_153.png", 0.8, 5.5, 2.2, 1.4, frame=True)
    txt(3.15, 5.65, 3.3, 0.9, "Маркерная разметка роговицы для контроля циклоторсии", size=9, italic=True, color=T['mute'])
    txt(7.1, 5.65, 5.4, 0.8, "Согласно инструкции к VisuMax®, возможна коррекция близорукости от −0,50 до −10,00 дптр и астигматизма до −5,00 дптр", size=10, align='r')
    txt(0.8, 6.98, 12, 0.2, "Розенблюм Ю.З. Оптометрия. СПб.: Гиппократ; 1996.  ·  Гамидов Г.А., Мушкова И.А., Костенев С.В., Гамидов А.А. Способ контроля циклоторсии глазного яблока при коррекции миопического астигматизма по технологии SMILE. Офтальмология. 2020; 17(3): 351-360.", size=5.5, italic=True, color=T['mute'])


def s_operation():
    slide("Ход операции")
    for im, x, w in (("p9_183.png", 0.8, 3.5), ("p9_184.png", 4.7, 3.5), ("p9_189.png", 8.9, 3.6)):
        card(x - 0.1, 1.3, w + 0.2, 5.0)
        pic(im, x, 1.35, w, 4.9, frame=(T['card'] in ('none', 'flat')))
    hair(0.8, 6.5, 12.5, 6.5)
    for cx, lab in ((2.55, "Протокол ReLEx SMILE · OD"), (6.45, "Протокол ReLEx SMILE · OS"), (10.7, "* Оперирующий хирург — д.м.н. Костенев С.В.")):
        dot(cx, 6.5, 0.06); txt(cx - 1.9, 6.65, 3.8, 0.3, lab, size=10, align='c')


def s_patent():
    slide("Патент, программа для ЭВМ и калькулятор транспозиции")
    pic("p10_196.png", 0.8, 1.3, 2.9, 4.3, frame=True); pic("p10_198.png", 3.95, 1.3, 2.9, 4.3, frame=True)
    rect(7.1, 1.3, 3.2, 4.3, "FFFFFF", T['hair'], 0.8)
    txt(7.3, 1.45, 2.8, 0.7, "Калькулятор транспозиции смешанного астигматизма для лентикулярной технологии", size=10.5, bold=True, spacing=1.05)
    for i, (lab, val) in enumerate([("Sph, дптр", ""), ("Cyl, дптр", "0,00"), ("Ax, градусы", "0")]):
        yy = 2.4 + i * 0.85
        txt(7.3, yy, 2.8, 0.22, lab, size=9, bold=True, color=T['mute'])
        rect(7.3, yy + 0.27, 2.8, 0.42, "F7F8FC", T['acc'] if i == 0 else T['hair'], 0.9)
        txt(7.42, yy + 0.27, 2.0, 0.42, val, size=10.5, anchor='m')
    rect(7.3, 5.0, 1.4, 0.4, T['acc'], kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25); txt(7.3, 5.0, 1.4, 0.4, "Рассчитать", size=10, bold=True, color="FFFFFF", align='c', anchor='m')
    pic("p10_199.png", 10.55, 1.3, 2.0, 4.3, frame=True)
    hair(0.8, 5.95, 12.5, 5.95)
    for cx, a, b in ((2.25, "Патент РФ № 2862856", "Способ коррекции смешанного астигматизма"), (5.4, "Свидетельство № 2026686768", "о регистрации программы для ЭВМ"), (8.7, "Онлайн-калькулятор", "расчёт параметров для установки"), (11.55, "Публикация", "первые результаты")):
        dot(cx, 5.95, 0.06); txt(cx - 1.5, 6.1, 3.0, 0.6, [[(a, {'bold': True})], [(b, {'color': T['mute']})]], size=9.5, align='c')


def s_criteria():
    slide("Критерии включения и исключения")
    hair(6.65, 1.3, 6.65, 6.8)
    node(1.1, 1.65, 0.6, "✓", 14, True)
    txt(1.6, 1.35, 4.5, 0.6, "Критерии включения", size=16, bold=True, anchor='m', color=T['tcolor'] if T['n'] != 3 else T['acc'])
    inc = ["Возраст 18 лет и старше", "Диагноз «смешанный астигматизм»", "Максимально корригированная острота зрения (МКОЗ) 0,3 и выше", "Толщина роговицы от 470 мкм и более", "Отсутствие признаков кератоконуса по BAD"]
    for i, t in enumerate(inc):
        y = 2.2 + i * 0.58; hair(0.8, y, 6.2, y); txt(0.8, y + 0.05, 5.4, 0.5, t, size=12, anchor='m')
    txt(0.8, 5.3, 5.4, 1.4, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'size': 9.5, 'color': T['mute'], 'bold': True})], [("Sph ≤ +1,75 D", {})], [("Cyl ≥ −5 D", {})], [("SE ≤ −0,75 D", {})]], size=14, bold=True, color=T['c1'], after=2)
    node(7.4, 1.65, 0.6, "✕", 13, True, strong=True)
    txt(7.9, 1.35, 4.5, 0.6, "Критерии исключения", size=16, bold=True, anchor='m', color=T['tcolor'] if T['n'] != 3 else T['acc'])
    exc = [("Возраст младше 18 лет", 0.5), ("Патология роговицы: кератоконус, дистрофии, неоваскуляризация, помутнение, рубцевание, состояние после кератопластики", 0.95), ("МКОЗ менее 0,3; толщина роговицы менее 470 мкм", 0.5),
           ("Ранее выполненный ЛАЗИК; глаукома (кроме ранней стадии); катаракта (кроме врождённой)", 0.7), ("Воспалительные и системные заболевания в стадии обострения, беременность и лактация", 0.7)]
    y = 2.2
    for t, h in exc:
        hair(7.0, y, 12.5, y); txt(7.0, y + 0.05, 5.5, h, t, size=11.5, anchor='m'); y += h + 0.1
    txt(7.0, 6.1, 5.5, 0.8, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ", {'size': 9.5, 'color': T['mute'], 'bold': True})], [("Несоответствие критериям SE и рефракционным параметрам", {'size': 12, 'bold': True, 'color': T['c2'] if T['n'] != 7 else T['ink']})]], after=2)


def params(title, sub, rows):
    slide(title, sub)
    n = len(rows); rh = min(0.6, 5.0 / n)
    for i, (a, b) in enumerate(rows):
        y = 1.65 + i * rh
        hair(0.8, y, 7.4, y)
        txt(0.8, y, 3.2, rh, a, size=12, anchor='m'); txt(4.1, y, 3.3, rh, b, size=12.5, bold=True, color=T['c1'], anchor='m')
    hair(0.8, 1.65 + n * rh, 7.4, 1.65 + n * rh)


def s_p_smile():
    params("Параметры операции: лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)",
           [("Режим", "«быстрый»"), ("Оптическая зона", "6,7 мм"), ("Переходная зона", "0,10 мм"), ("Диаметр клапана (cap)", "7,8–7,9 мм"), ("Толщина клапана (cap)", "120 мкм"),
            ("Угол краевого надреза", "90°"), ("Длина входного разреза", "2,0–2,4 мм"), ("Интерфейс", "«S» / «M», в зависимости от диаметра роговицы"), ("Количество разрезов", "1")])
    ring(10.3, 4.1, 4.6, T['hair'], 0.8); card(8.3, 2.3, 4.0, 3.6) if T['card'] in ('shadow', 'border') else None
    pic("p12_213.png", 8.5, 2.4, 3.6, 3.4)


def s_p_fl():
    params("Параметры операции: ФемтоЛАЗИК", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)",
           [("Оптическая зона абляции", "6,5 мм"), ("Переходная зона", "1,2 мм"), ("Толщина флэпа", "110 мкм"), ("Общая зона абляции", "8,9 мм"), ("Номограмма", "S 001"),
            ("Положение и ширина «ножки»", "90°, 0,6 мм"), ("Остальные параметры", "варьировали индивидуально (рефракция, пахиметрия и т.д.)")])
    pic("p13_226.png", 8.5, 1.5, 4.0, 3.3)
    pic("p13_227.png", 9.2, 5.1, 3.3, 1.75, frame=True)


def s_model():
    slide("Математическое моделирование создаваемой лентикулы")
    for i, (im, cap) in enumerate([("p14_232.png", "3D-модель: толщина лентикулы"), ("p14_233.png", "Карта толщины (вид сверху)"), ("p14_235.png", "Профиль (вид сбоку)")]):
        x = 0.8 + i * 4.05
        card(x - 0.05, 1.3, 3.8, 2.85)
        pic(im, x, 1.35, 3.7, 2.45); txt(x, 3.82, 3.7, 0.25, cap, size=9.5, align='c', color=T['mute'])
    txt(0.8, 4.4, 11.8, 0.3, "На основании математической модели построена геометрическая (схематическая) модель лентикулы при смешанном астигматизме", size=11.5, bold=True)
    rect(0.8, 4.9, 7.0, 2.0, T['c2'] if T['n'] in (1, 4, 6, 3) else T['c1'], kind=MSO_SHAPE.ROUNDED_RECTANGLE if T['card'] != 'none' else MSO_SHAPE.RECTANGLE, adj=0.06) if T['n'] in (1, 3, 4, 6) else rect(0.8, 4.9, 7.0, 2.0, "FFFFFF", T['hair'], 0.9)
    dark = T['n'] in (1, 3, 4, 6)
    fc = "FFFFFF" if dark else T['tcolor']; fm = "D5E3F5" if dark else T['mute']
    txt(1.05, 5.0, 6.5, 0.25, "Эмпирическая формула расчёта максимальной толщины лентикулы", size=9.5, bold=True, color=fm)
    txt(1.05, 5.3, 6.5, 0.5, "T(r,θ) = C + A·(r/R)²·cos(2(θ − ось))", size=20, bold=True, color=fc)
    txt(1.05, 5.95, 6.6, 0.85, ["C = (Max_theory + T_min) / 2     A = (Max_theory − T_min) / 2     R = S / 2", "Max_theory = (S²/6)·(2|Sph'| + |Cyl'|)     T_min ≈ 20 мкм (константа устройства)"], size=9.5, color=fm if dark else T['ink'], spacing=1.2)
    pic("p14_234.png", 8.2, 4.85, 4.3, 2.1)


def s_acuity():
    slide("Динамика НКОЗ и МКОЗ в исследуемых группах")
    cats = ["До операции", "1-е сутки", "3 мес.", "6 мес."]
    hair(6.65, 1.3, 6.65, 6.8)
    head(0.8, 1.3, 3.6, "Лентикулярная хирургия (SMILE)", T['c1'], 13, fill=T['c1'] if T['n'] == 6 else None)
    bar_chart(0.7, 1.75, 5.8, 5.1, cats, [("НКОЗ", (0.34, 0.73, 0.88, 0.75)), ("МКОЗ", (0.91, 0.87, 0.98, 1.00))], [T['c1'], T['c1l']], 0, 1.2, 0.2)
    head(6.95, 1.3, 3.0, "ФемтоЛАЗИК", T['c2'] if T['n'] != 7 else T['ink'], 13, fill=T['c2'] if T['n'] == 6 else None)
    bar_chart(6.85, 1.75, 5.8, 5.1, cats, [("НКОЗ", (0.32, 0.54, 0.75, 0.72)), ("МКОЗ", (0.87, 0.84, 0.92, 0.95))], [T['c2'], T['c2l']], 0, 1.2, 0.2)
    txt(4.6, 1.4, 1.9, 0.25, "острота зрения, дес.", size=8.5, color=T['mute'], align='r')


def s_refraction():
    slide("Динамика рефракционного компонента")
    cats = ["До операции", "1-е сутки", "3 мес.", "6 мес."]
    S = [("SMILE — Sph", T['c1'], False, (0.54, 0.22, 0.37, 0.62)), ("SMILE — Cyl", T['c1'], True, (-3.07, -0.51, -0.44, -0.62)),
         ("ФемтоЛАЗИК — Sph", T['c2'], False, (1.25, -0.20, 0.02, 0.31)), ("ФемтоЛАЗИК — Cyl", T['c2'], True, (-3.24, -1.13, -1.19, -1.25))]
    cd = CategoryChartData(number_format='0.00'); cd.categories = cats
    for nm, c, d, v in S: cd.add_series(nm, v)
    ch = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, I(gx(0.7)), I(1.4), I(gw(6.6)), I(3.15), cd).chart
    chart_clear(ch); ch.font.name = SANS; style_axes(ch, -4, 2, 1, 10)
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    for s, (nm, c, d, v) in zip(ch.plots[0].series, S):
        s.smooth = False; s.format.line.color.rgb = rgb(c); s.format.line.width = Pt(2.25)
        if d: s.format.line.dash_style = MSO_LINE.DASH
        s.marker.style = XL_MARKER_STYLE.CIRCLE; s.marker.size = 7
        s.marker.format.fill.solid(); s.marker.format.fill.fore_color.rgb = rgb("FFFFFF" if d else c); s.marker.format.line.color.rgb = rgb(c)
    ch.has_legend = False
    txt(0.85, 1.25, 2, 0.25, "Диоптрии, D", size=8.5, color=T['mute'])
    for k, c_ in enumerate(cats): txt(3.6 + k * 0.95, 4.65, 0.9, 0.22, c_, size=8, color=T['mute'], align='c')
    for j, (nm, col, dsh, vals) in enumerate(S):
        yy = 4.95 + j * 0.45; hair(0.8, yy, 7.3, yy)
        hair(0.85, yy + 0.22, 1.2, yy + 0.22, col, 2.25, MSO_LINE.DASH if dsh else None)
        txt(1.3, yy, 2.3, 0.44, nm, size=10, bold=True, color=col, anchor='m')
        for k, v in enumerate(vals):
            s_ = ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}".replace(".", ",")
            txt(3.6 + k * 0.95, yy, 0.9, 0.44, s_, size=10.5, bold=True, align='c', anchor='m')
    hair(0.8, 6.75, 7.3, 6.75); hair(7.7, 1.3, 7.7, 6.8)
    small = [("Пахиметрия, мкм", (554, 537), (501, 501), 440, 600, 40, '0'), ("Кератометрия K1, D", (41.58, 41.69), (40.78, 41.83), 38, 46, 2, '0.00'), ("Кератометрия K2, D", (44.44, 44.76), (41.78, 42.83), 38, 46, 2, '0.00')]
    for i, (ttl, a, b, lo, hi, mj, f) in enumerate(small):
        yy = 1.3 + i * 1.85
        txt(8.0, yy, 4, 0.25, ttl, size=11, bold=True)
        c2 = bar_chart(7.9, yy + 0.2, 4.7, 1.6, ["До операции", "6 мес."], [("SMILE", (a[0], b[0])), ("ФемтоЛАЗИК", (a[1], b[1]))], [T['c1'], T['c2']], lo, hi, mj, fmt=f, legend=(i == 0), lsize=8.5, gap=70)
        c2.value_axis.visible = False; c2.value_axis.has_major_gridlines = False
        if i == 0: c2.legend.position = XL_LEGEND_POSITION.RIGHT


def s_safety():
    slide("Эффективность и безопасность", "НКОЗ после операции / МКОЗ до операции")
    card(0.7, 1.45, 9.5, 5.45)
    pic("p17_270.png", 0.8, 1.5, 9.3, 5.3, frame=(T['card'] in ('none', 'flat')))
    for i, (lab, v, st) in enumerate([("Индекс безопасности SMILE", "1,03", False), ("Индекс безопасности ФемтоЛАЗИК", "1,02", True)]):
        cy = 2.7 + i * 2.7
        node(11.5, cy, 1.7, v, 24, True, strong=st)
        txt(10.4, cy + 1.2, 2.2, 0.5, lab, size=10, align='c')


def s_predict():
    slide("Прогнозируемость")
    card(0.7, 1.3, 7.4, 5.65)
    pic("p18_275.png", 0.8, 1.35, 7.2, 5.55, frame=(T['card'] in ('none', 'flat')))
    for i, (v, lab, st) in enumerate([("0,65", "R² — коэффициент детерминации", False), ("74 %", "глаз в пределах ±0,5 D от планируемой коррекции", False), ("88 %", "глаз в пределах ±1,0 D от планируемой коррекции", True)]):
        cy = 2.1 + i * 2.1
        node(9.2, cy, 1.25, v, 16, True, strong=st)
        txt(10.45, cy - 0.5, 2.2, 1.0, lab, size=10.5, anchor='m')


def s_conclusions():
    slide("Выводы")
    items = [("Геометрическая модель лентикулы", "На основании математического моделирования построена геометрическая модель лентикулы, отражающая её торическую (седловидную) форму, что подтверждает научную обоснованность разработанного и внедрённого в клиническую практику протокола транспозиции."),
             ("НКОЗ и МКОЗ", "НКОЗ повысилась в обеих группах (SMILE — с 0,34 до 0,88; ФемтоЛАЗИК — с 0,32 до 0,75): лентикулярная технология обеспечивает более быстрое и полное зрительное восстановление без коррекции. МКОЗ оставалась стабильно высокой (с 0,91 до 1,0 и с 0,87 до 0,95): ни одна из технологий не снижает потенциальную остроту зрения."),
             ("Рефракционный компонент", "Сферический компонент приблизился к эмметропии (с +0,54 до +0,37 D в SMILE и с +1,25 до +0,31 D в ФемтоЛАЗИК). Цилиндрический компонент существенно снизился (с −3,07 до −0,62 D и с −3,24 до −1,25 D), остаточный цилиндр в лентикулярной группе вдвое меньше."),
             ("Эффективна, безопасна, перспективна", "Разработанная лентикулярная технология эффективна, безопасна и перспективна для внедрения при смешанном астигматизме. Необходимы дальнейшее накопление клинических данных и их статистическая обработка.")]
    hair(6.65, 1.3, 6.65, 6.8)
    for i, (t, b) in enumerate(items):
        x = 0.8 + (i % 2) * 6.1; y = 1.35 + (i // 2) * 2.85
        numlabel(i + 1, x, y, 0.8, 0.5, 15 if T['num'] in ('dot', 'orange', 'plain') else None)
        txt(x + 0.95, y + 0.02, 4.8, 0.5, t, size=14, bold=True, anchor='m', color=T['tcolor'] if T['n'] != 3 else T['acc'])
        txt(x + 0.95, y + 0.7, 4.8, 1.95, b, size=12, spacing=1.12)


def s_end():
    new('title'); n = T['n']
    if n == 1:
        txt(0.8, 1.9, 7.2, 1.6, "Благодарю за внимание!", size=42, bold=True, color=T['tcolor'], spacing=1.0, raw=True)
        rect(0.8, 4.0, 5.6, 0.5, T['acc'], kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5, raw=True); txt(0.8, 4.0, 5.6, 0.5, "anastasianik2403@gmail.com", size=13, bold=True, color="FFFFFF", align='c', anchor='m', raw=True)
        pic("p20_294.png", 8.1, 1.4, 4.5, 3.8)
    elif n == 2:
        txt(0.8, 3.4, 8, 1.2, "Благодарю за внимание!", size=44, color=T['tcolor'], font=SERIF, raw=True)
        txt(0.8, 5.3, 7, 0.8, [[("✉  ", {'color': T['acc']}), ("anastasianik2403@gmail.com", {})], [("☺  ", {'color': T['acc']}), (SPEAKER + " · " + FORUM, {'size': 10})]], size=12, spacing=1.3, raw=True)
        pic("p20_294.png", 8.3, 2.4, 4.3, 3.6)
    elif n == 3:
        txt(1.5, 2.55, 10.4, 1.2, "Благодарю за внимание!", size=44, bold=True, color=T['acc'], align='c', raw=True)
        txt(1.5, 3.85, 10.4, 0.4, "anastasianik2403@gmail.com", size=15, color=T['ink'], align='c', raw=True)
        pic("p20_294.png", 4.5, 4.45, 4.3, 2.5)
    elif n == 4:
        txt(0.8, 1.6, 7.5, 2.4, [[("БЛАГОДАРЮ ЗА ", {}), ("ВНИМАНИЕ!", {'color': T['acc']})]], size=38, bold=True, color=T['tcolor'], raw=True)
        txt(0.8, 4.3, 7.5, 0.5, [[("Электронная почта: ", {'color': T['mute']}), ("anastasianik2403@gmail.com", {'bold': True, 'color': T['c1']})]], size=13, raw=True)
        pic("p20_294.png", 8.3, 1.6, 4.3, 3.6)
    elif n == 5:
        txt(0.8, 1.5, 8, 1.8, ["Благодарю", "за внимание!"], size=40, color=T['tcolor'], spacing=1.0, raw=True)
        txt(0.8, 4.4, 7, 1.3, [[("Контакты", {'size': 15, 'color': T['tcolor']})], [("+  ", {'color': T['acc']}), ("E-mail  ", {'color': T['mute'], 'size': 9}), ("anastasianik2403@gmail.com", {})], [("+  ", {'color': T['acc']}), ("Докладчик  ", {'color': T['mute'], 'size': 9}), (SPEAKER, {})]], size=12, spacing=1.4, raw=True)
        pic("p20_294.png", 8.4, 2.5, 4.0, 3.4)
    elif n == 6:
        txt(0.8, 2.3, 11.7, 1.2, "Благодарю за внимание!", size=40, bold=True, color=T['tcolor'], align='c', raw=True)
        txt(0.8, 3.6, 11.7, 0.5, "anastasianik2403@gmail.com", size=15, color=T['acc'], align='c', raw=True)
        pic("p20_294.png", 4.7, 4.3, 3.9, 2.6)
    elif n == 7:
        txt(1.1, 2.9, 11.2, 1.2, "Благодарю за внимание!", size=44, bold=True, color=T['tcolor'], align='c', raw=True)
        txt(1.1, 4.1, 11.2, 0.5, f"(  anastasianik2403@gmail.com  )", size=16, font=SERIF, align='c', raw=True)
        pic("p20_294.png", 5.0, 4.8, 3.3, 2.2)


def build(theme):
    global T, prs, PAGE
    T = theme; PAGE = 0
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s_title(); s_aktual1(); s_aktual2(); s_goal(); s_methods(); s_ranges(); s_diag(); s_steps(); s_operation(); s_patent(); s_criteria()
    s_p_smile(); s_p_fl(); s_model(); s_acuity(); s_refraction(); s_safety(); s_predict(); s_conclusions(); s_end()
    os.makedirs("../presentations", exist_ok=True)
    out = f"../presentations/{theme['name']}.pptx"
    prs.save(out); print("saved", out)


if __name__ == "__main__":
    ids = [int(a) for a in sys.argv[1:]] or [t['n'] for t in THEMES]
    for t in THEMES:
        if t['n'] in ids: build(t)
