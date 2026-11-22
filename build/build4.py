"""Template-specific slide arrangements for themes 5 (conference), 7 (purple minimal), 12 (blue corporate)."""
import sys, os
import build3 as b
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE

SANS = b.SANS
B1 = "Астигматизм — мультифакторное состояние с выраженным наследственным компонентом."
B2 = "Полногеномные исследования (Shing E. et al., 2024) выявили свыше 50 полиморфизмов в 10 генах, включая локус PDGFRA, регулирующий кривизну роговицы."
FEMTO = [("Эксимерлазерная технология (ФемтоЛАЗИК)", {'bold': True}), (". Современный «золотой» стандарт в коррекции смешанного астигматизма", {})]
PILOT = "Пилотное исследование на платформе VisuMax (Carl Zeiss Meditec AG) показало возможность коррекции смешанного астигматизма методом лентикулярной хирургии (Ganesh S. et al., 2024), однако методика пока не применяется в стандартной практике."
ELITA = "Экспериментальное исследование ex-vivo (11 свиных глаз) на платформе Elita, Johnson and Johnson Surgical Vision, Inc. (США) свидетельствуют о технической возможности коррекции смешанного астигматизма и гиперметропии."
REFS1 = ("Азара Д.Т., Алио Х.Л., Кортина М.С., Халлака Д.А. Хирургическое лечение астигматизма. Москва: ГЭОТАР-Медиа, 2025. — 272 с. doi: 10.33029/9704-8200-1-STA-2025-1-272; Shing E. et al. Heritability and Genetic Factors of Astigmatism and Corneal Curvature. Am J Ophthalmol. 2025;269:161–171. doi: 10.1016/j.ajo.2024.08.019; "
         "Клокова О.А. и др. Ранние клинико-функциональные результаты коррекции смешанного астигматизма в зависимости от его степени с помощью высокочастотного эксимерного лазера Schwind Amaris 1050RS. Офтальмология. 2025;22(2):295–304. https://doi.org/10.18008/1816-5095-2025-2-295-304")
GOAL = "Разработать лентикулярную технологию для коррекции смешанного астигматизма"
STD = [("Визометрия", "НКОЗ и МКОЗ в естественных условиях и при медикаментозном мидриазе"), ("Рефрактометрия, кератометрия", "в естественных условиях и при медикаментозном мидриазе"), ("Тонометрия, биометрия, периметрия", ""), ("Биомикроскопия и офтальмоскопия", "")]
SPEC = [("Кератотопография", "Pentacam AXL (Oculus, Германия)"), ("Анализ биомеханических свойств роговицы", "Corvis ST (Oculus, Германия)"), ("Аберрометрия", "KR-1W (Topcon, Япония)")]
INC = ["Возраст 18 лет и старше", "Диагноз «смешанный астигматизм»", "Максимально корригированная острота зрения (МКОЗ) 0,3 и выше", "Толщина роговицы от 470 мкм и более", "Отсутствие признаков кератоконуса по BAD"]
EXC = ["Возраст младше 18 лет", "Патология роговицы: кератоконус, дистрофии, неоваскуляризация, помутнение, рубцевание, состояние после кератопластики", "МКОЗ менее 0,3; толщина роговицы менее 470 мкм",
       "Ранее выполненный ЛАЗИК; глаукома (кроме ранней стадии); катаракта (кроме врождённой)", "Воспалительные и системные заболевания в стадии обострения, беременность и лактация"]
LENS_IN = ["Sph ≤ +1,75 D", "Cyl ≥ −5 D", "SE ≤ −0,75 D"]
LENS_EX = "Несоответствие критериям SE и рефракционным параметрам"
CONCL = [("Геометрическая модель лентикулы", "На основании математического моделирования построена геометрическая модель лентикулы, отражающая её торическую (седловидную) форму, что подтверждает научную обоснованность разработанного и внедрённого в клиническую практику протокола транспозиции."),
         ("НКОЗ и МКОЗ", "НКОЗ повысилась в обеих группах (SMILE — с 0,34 до 0,88; ФемтоЛАЗИК — с 0,32 до 0,75): лентикулярная технология обеспечивает более быстрое и полное зрительное восстановление без коррекции. МКОЗ оставалась стабильно высокой (с 0,91 до 1,0 и с 0,87 до 0,95): ни одна из технологий не снижает потенциальную остроту зрения."),
         ("Рефракционный компонент", "Сферический компонент приблизился к эмметропии (с +0,54 до +0,37 D в SMILE и с +1,25 до +0,31 D в ФемтоЛАЗИК). Цилиндрический компонент существенно снизился (с −3,07 до −0,62 D и с −3,24 до −1,25 D), остаточный цилиндр в лентикулярной группе вдвое меньше."),
         ("Эффективна, безопасна, перспективна", "Разработанная лентикулярная технология эффективна, безопасна и перспективна для внедрения при смешанном астигматизме. Необходимы дальнейшее накопление клинических данных и их статистическая обработка.")]
STATS = [("0,65", "R² — коэффициент детерминации"), ("74 %", "глаз в пределах ±0,5 D от планируемой коррекции"), ("88 %", "глаз в пределах ±1,0 D от планируемой коррекции")]
TIMELINE = ["До операции", "1 сутки", "3 месяца", "6 месяцев"]


def T(): return b.T
def txt(*a, **k): return b.txt(*a, **k)
def hair(*a, **k): return b.hair(*a, **k)
def rect(*a, **k): return b.rect(*a, **k)
def pic(*a, **k): return b.pic(*a, **k)


def plus(x, y, d=0.34, color=None):
    c = color or T()['acc']
    rect(x, y, d / b.sx(), d, "FFFFFF", c, 1.0, MSO_SHAPE.OVAL)
    txt(x, y - 0.01, d / b.sx(), d, "+", size=13, color=c, align='c', anchor='m')


def refs(y=6.55):
    txt(0.8, y, 11.8, 0.55, [REFS1], size=6, italic=True, color=T()['mute'], spacing=0.95)


def timeline(y, label_y=None):
    hair(0.8, y, 12.5, y)
    for i, lab in enumerate(TIMELINE):
        cx = 1.5 + i * 3.45; b.dot(cx, y, 0.06); txt(cx - 1, y + 0.15, 2, 0.3, lab, size=10.5, align='c')


# ============================================================ THEME 5 (conference)
def c5_aktual1():
    b.slide("Актуальность")
    pic("p2_22.png", 0.8, 1.55, 4.7, 3.0)
    txt(0.8, 4.85, 4.7, 0.3, "Хирургическая коррекция смешанного астигматизма", size=12, bold=True)
    txt(6.0, 1.5, 6.5, 2.4, [[("•  ", {'color': T()['acc']}), B1], [("•  ", {'color': T()['acc']}), B2]], size=14.5, after=10, spacing=1.1)
    hair(6.0, 3.95, 12.5, 3.95)
    plus(6.0, 4.3); txt(6.6, 4.2, 5.9, 1.0, [FEMTO], size=12.5, spacing=1.1, anchor='m')
    hair(6.0, 5.45, 12.5, 5.45)
    plus(6.0, 5.8); txt(6.6, 5.7, 5.9, 0.6, [[("Лентикулярная технология", {'bold': True})]], size=12.5, anchor='m')
    refs(6.62)


def c5_aktual2():
    b.slide("Актуальность")
    hair(6.675, 1.5, 6.675, 6.8); hair(0.8, 4.15, 12.5, 4.15)
    plus(6.505, 3.98, 0.34)
    txt(0.8, 1.6, 5.5, 2.3, [[(PILOT, {})]], size=12.5, spacing=1.12)
    txt(7.0, 1.6, 5.5, 2.3, [[(ELITA, {})]], size=12.5, spacing=1.12)
    pic("p3_58.png", 0.8, 4.35, 1.6, 2.4, valign='t', frame=True); pic("p3_62.png", 2.6, 4.35, 1.6, 2.4, valign='t', frame=True)
    txt(4.4, 4.5, 2.1, 0.8, "Ganesh S. et al., 2024  ·  ARVO, 2025", size=9, color=T()['mute'])
    pic("p3_63.png", 7.0, 4.35, 3.0, 2.4)


def c5_goal():
    b.slide("Цель")
    txt(0.8, 1.75, 4, 0.3, "+  ЦЕЛЬ ИССЛЕДОВАНИЯ", size=10, bold=True, color=T()['acc'])
    txt(0.8, 2.2, 6.0, 3.2, GOAL, size=30, spacing=1.1)
    hair(0.8, 5.6, 6.6, 5.6)
    pic("p4_74.png", 7.3, 1.6, 5.2, 5.1)


def c5_methods():
    b.slide("Материалы и методы")
    groups = [(0.8, "SMILE", "Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", ("p5_87.png", "p5_86.png")),
              (6.9, "ФемтоЛАЗИК", "Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", ("p5_88.png", "p5_89.png"))]
    for x, nm, ttl, dev, imgs in groups:
        b.node(x + 0.95, 2.7, 1.7, [[(nm, {'size': 13 if len(nm) < 7 else 11, 'bold': True})], [("20 пациентов", {'size': 9})], [("(40 глаз)", {'size': 9})]], 11)
        txt(x + 2.1, 1.7, 3.5, 1.7, [[(ttl, {'bold': True, 'size': 12.5})], [(dev, {'italic': True, 'size': 9.5})]], spacing=1.1, after=4)
        pic(imgs[0], x + 2.1, 3.35, 1.7, 1.15); pic(imgs[1], x + 4.0, 3.3, 1.2, 1.2)
    txt(0.8, 4.95, 6, 0.3, "Наблюдение проводилось до операции и в стандартные сроки", size=10.5, bold=True)
    hair(1.4, 5.85, 12.0, 5.85, T()['acc'], 1.0)
    for i, lab in enumerate(TIMELINE):
        cx = 1.9 + i * 3.1
        rect(cx - 0.4, 5.45, 0.8, 0.8, "FFFFFF", T()['acc'], 1.2, MSO_SHAPE.OVAL); txt(cx - 0.4, 5.45, 0.8, 0.8, f"0{i+1}", size=12, color=T()['acc'], align='c', anchor='m')
        txt(cx - 1.0, 6.35, 2.0, 0.3, lab, size=10.5, align='c')
        if i < 3: rect(cx + 1.4, 5.75, 0.22, 0.22, T()['acc'], kind=MSO_SHAPE.ISOSCELES_TRIANGLE).rotation = 90


def c5_diag():
    b.slide("Методы диагностики")
    hair(6.65, 1.4, 6.65, 4.95)
    txt(0.8, 1.35, 5.5, 0.3, "Стандартные методы диагностики", size=13, bold=True)
    txt(7.0, 1.35, 5.5, 0.3, "Специальные методы диагностики", size=13, bold=True)
    for items, x0 in ((STD, 0.8), (SPEAK := SPEC, 7.0)):
        for i, (a, c) in enumerate(items):
            y = 1.85 + i * 0.78; plus(x0, y + 0.12, 0.3)
            txt(x0 + 0.45, y + 0.12, 0.6, 0.3, f"0{i+1}", size=12, color=T()['acc'], anchor='m')
            txt(x0 + 1.05, y, 4.9, 0.62, [[(a, {'bold': True, 'size': 12})]] + ([[(c, {'size': 9.5, 'color': T()['mute']})]] if c else []), anchor='m', spacing=1.05)
    hair(0.8, 5.1, 12.5, 5.1)
    pic("p7_112.png", 0.9, 5.25, 0.95, 1.7); pic("p7_122.png", 2.0, 5.25, 2.3, 1.7); pic("p7_121.png", 4.4, 5.25, 2.2, 1.7); pic("p7_113.png", 7.3, 5.25, 5.0, 1.7)


def c5_criteria():
    b.slide("Критерии включения и исключения")
    hair(6.675, 1.45, 6.675, 6.85); plus(6.505, 1.3, 0.34)
    for x, ttl, items in ((0.8, "Критерии включения", INC), (7.0, "Критерии исключения", EXC)):
        txt(x, 1.45, 5.4, 0.4, ttl, size=17)
        y = 2.05
        for t in items:
            h = 0.5 if len(t) < 60 else 0.9 if len(t) > 100 else 0.7
            hair(x, y, x + 5.5, y); txt(x, y + 0.04, 5.5, h, t, size=11.5, anchor='m'); y += h + 0.08
    rect(0.8, 5.75, 5.5, 1.05, "FFFFFF", T()['acc'], 1.0)
    txt(1.0, 5.75, 5.2, 1.05, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ:  ", {'size': 9, 'bold': True, 'color': T()['mute']})], [("   ".join(LENS_IN), {'bold': True, 'color': T()['acc'], 'size': 13})]], anchor='m', spacing=1.2)
    rect(7.0, 5.75, 5.5, 1.05, "FFFFFF", T()['acc'], 1.0)
    txt(7.2, 5.75, 5.1, 1.05, [[("ДЛЯ ЛЕНТИКУЛЯРНОЙ ТЕХНОЛОГИИ:  ", {'size': 9, 'bold': True, 'color': T()['mute']})], [(LENS_EX, {'bold': True, 'size': 11.5})]], anchor='m', spacing=1.2)


def c5_concl():
    b.slide("Выводы")
    hair(6.675, 1.5, 6.675, 6.85); hair(0.8, 4.15, 12.5, 4.15)
    for i, (t, body) in enumerate(CONCL):
        x = 0.8 + (i % 2) * 6.2; y = 1.5 + (i // 2) * 2.7
        rect(x, y + 0.1, 0.62, 0.62, "FFFFFF", T()['acc'], 1.2, MSO_SHAPE.OVAL); txt(x, y + 0.1, 0.62, 0.62, f"0{i+1}", size=12, color=T()['acc'], align='c', anchor='m')
        txt(x + 0.85, y + 0.05, 4.7, 0.6, t, size=14, anchor='m')
        txt(x + 0.85, y + 0.75, 4.75, 1.85, body, size=11, spacing=1.12)


def c5_stats():
    b.slide("Прогнозируемость")
    pic("p18_275.png", 0.8, 1.5, 7.0, 5.3, frame=True)
    for i, (v, lab) in enumerate(STATS):
        y = 1.55 + i * 1.8
        rect(8.2, y, 4.35, 1.6, None, T()['hair'], 1.0)
        txt(8.4, y, 1.9, 1.6, v, size=30, color=T()['acc'], anchor='m')
        txt(10.3, y, 2.1, 1.6, lab, size=10.5, anchor='m')


# ============================================================ THEME 7 (purple minimal)
def p7_rows(x, y, rows, gap, w, size=12.5):
    for i, content in enumerate(rows):
        yy = y + i * gap
        if i: hair(x, yy - 0.08, x + w + 0.9, yy - 0.08)
        txt(x, yy, 0.9, 0.4, f"( {i+1:02d} )", size=10.5, color=T()['mute'], font=b.SERIF)
        txt(x + 0.9, yy - 0.02, w, gap - 0.15, [content], size=size, spacing=1.1)


def p7_aktual1():
    b.slide("Актуальность")
    pic("p2_22.png", 0.8, 2.3, 3.3, 2.4)
    p7_rows(4.5, 1.45, [[B1], [B2]], 1.15, 7.0, 13)
    txt(4.5, 3.85, 8, 0.3, "Хирургическая коррекция смешанного астигматизма", size=12, bold=True)
    p7_rows(4.5, 4.4, [[FEMTO[0], FEMTO[1]], [("Лентикулярная технология", {'bold': True}), (": ?", {})]], 0.95, 7.0, 12)
    refs(6.62)


def p7_aktual2():
    b.slide("Актуальность")
    pic("p3_63.png", 0.8, 1.55, 3.0, 4.4)
    p7_rows(4.4, 1.5, [[PILOT], [ELITA]], 1.55, 7.2, 12.5)
    pic("p3_58.png", 4.4, 4.75, 1.4, 2.0, valign='t', frame=True); pic("p3_62.png", 6.0, 4.75, 1.4, 2.0, valign='t', frame=True)
    txt(7.6, 5.0, 4.8, 0.5, "Ganesh S. et al., 2024  ·  ARVO Annual Meeting, 2025", size=9, color=T()['mute'])


def p7_goal():
    b.slide("Цель")
    txt(1.1, 1.9, 9.8, 2.6, GOAL, size=36, spacing=1.08)
    txt(1.1, 4.4, 6, 0.4, "(  цель исследования  )", size=15, color=T()['mute'], font=b.SERIF)
    pic("p4_74.png", 7.3, 4.0, 5.2, 3.0)


def p7_methods():
    b.slide("Материалы и методы")
    for cx, nm, st in ((3.6, "SMILE", False), (5.7, "ФемтоЛАЗИК", True)):
        b.ring(cx, 2.95, 3.0, T()['c1'] if not st else T()['c2'], 2.0)
        txt(cx - 1.0 + (-0.5 if not st else 0.5), 2.35, 2.0, 1.2, [[(nm, {'size': 15 if len(nm) < 7 else 12, 'bold': True})], [("20 пациентов (40 глаз)", {'size': 9.5})]], align='c', anchor='m', spacing=1.2)
    items = [("Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия)", ("p5_87.png", "p5_86.png")),
             ("Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США)", ("p5_88.png", "p5_89.png"))]
    for i, (ttl, dev, imgs) in enumerate(items):
        y = 1.45 + i * 2.0
        txt(8.3, y, 0.9, 0.3, f"( {i+1:02d} )", size=10.5, color=T()['mute'], font=b.SERIF)
        txt(9.2, y - 0.02, 3.3, 1.2, [[(ttl, {'bold': True, 'size': 12})], [(dev, {'italic': True, 'size': 9})]], spacing=1.1, after=3)
        pic(imgs[0], 9.2, y + 1.0, 1.5, 0.9); pic(imgs[1], 10.9, y + 0.95, 0.95, 0.95)
    txt(0.8, 5.0, 6, 0.3, "Наблюдение проводилось до операции и в стандартные сроки", size=10.5, bold=True)
    hair(0.8, 6.1, 12.5, 6.1)
    for i, lab in enumerate(TIMELINE):
        cx = 1.5 + i * 3.45; txt(cx - 1, 5.6, 2, 0.3, f"( Шаг {i+1} )", size=10, color=T()['mute'], font=b.SERIF, align='c'); b.dot(cx, 6.1, 0.07 if i < 3 else 0.14, T()['tcolor']); txt(cx - 1, 6.3, 2, 0.3, lab, size=10.5, align='c')


def p7_concl():
    b.slide("Выводы")
    for i, (t, body) in enumerate(CONCL):
        x = 0.8 + (i % 2) * 6.1; y = 1.5 + (i // 2) * 2.7
        hair(x, y - 0.05, x + 5.7, y - 0.05)
        rect(x, y + 0.15, 0.55, 0.55, "F0EEFB", kind=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.2); txt(x, y + 0.15, 0.55, 0.55, f"{i+1}", size=13, bold=True, color=T()['acc'], align='c', anchor='m')
        txt(x + 0.8, y + 0.12, 4.9, 0.6, t, size=14, bold=True, anchor='m')
        txt(x + 0.8, y + 0.85, 4.9, 1.7, body, size=11.5, spacing=1.12, color=T()['ink'])


def p7_stats():
    b.slide("Прогнозируемость")
    pic("p18_275.png", 0.8, 1.5, 7.0, 5.3, frame=True)
    for i, (v, lab) in enumerate(STATS):
        y = 1.6 + i * 1.8
        if i: hair(8.4, y - 0.1, 12.5, y - 0.1)
        txt(8.4, y, 4.1, 0.9, v, size=36, anchor='m'); txt(8.4, y + 0.9, 4.1, 0.6, lab, size=10.5, color=T()['mute'])


# ============================================================ THEME 12 (blue corporate)
def c12_card(x, y, w, h):
    b.card(x, y, w, h)


def c12_aktual1():
    b.slide("Актуальность")
    heads = ["Наследственность", "Генетика", "Хирургическая коррекция"]
    bodies = [[B1], [B2], [FEMTO, [("Лентикулярная технология", {'bold': True}), (": ?", {})]]]
    for i in range(3):
        x = 0.8 + i * 3.95; c12_card(x, 1.5, 3.8, 4.5)
        b.head(x + 0.2, 1.7, 3.4, heads[i], None, 12)
        txt(x + 0.25, 2.35, 3.3, 3.5, bodies[i], size=12.5, spacing=1.12, after=10)
    refs(6.35)


def c12_aktual2():
    b.slide("Актуальность")
    cards = [("p3_58.png", "VisuMax, 2024", PILOT), ("p3_63.png", "Elita, ex-vivo", ELITA), ("p3_62.png", "ARVO, 2025", "")]
    for i, (im, pill, text) in enumerate(cards):
        x = 0.8 + i * 3.95; c12_card(x, 1.5, 3.8, 5.2)
        pic(im, x + 0.2, 1.65, 3.4, 2.2)
        b.head(x + 0.2, 4.0, 3.4, pill, None, 12)
        if text: txt(x + 0.25, 4.55, 3.3, 2.1, text, size=10.5, spacing=1.1)


def c12_goal():
    b.slide("Цель")
    c12_card(0.8, 1.7, 11.75, 4.6)
    b.head(1.1, 1.95, 2.2, "Цель", None, 12)
    txt(1.1, 2.7, 6.0, 3.3, GOAL, size=28, bold=True, color=T()['tcolor'], spacing=1.1)
    pic("p4_74.png", 7.5, 2.0, 4.8, 4.0)


def c12_methods():
    b.slide("Материалы и методы")
    rows = [("01", "Лентикулярная технология (SMILE)", "Фемтосекундная лазерная установка VisuMax (Carl Zeiss Meditec AG, Германия). 20 пациентов (40 глаз).", ("p5_87.png", "p5_86.png")),
            ("02", "Эксимерлазерная технология (ФемтоЛАЗИК)", "Интегрированная платформа WaveLight Refractive Suite (WaveLight FS200 + WaveLight EX500, Alcon Laboratories Inc., США). 20 пациентов (40 глаз).", ("p5_88.png", "p5_89.png"))]
    for i, (n, ttl, dev, imgs) in enumerate(rows):
        y = 1.5 + i * 1.65; c12_card(0.8, y, 11.75, 1.5)
        txt(1.0, y, 1.1, 1.5, n, size=30, bold=True, color=T()['c1'], anchor='m')
        b.head(2.2, y + 0.15, 5.4, ttl, None, 11.5, 0.36); txt(2.2, y + 0.6, 6.0, 0.85, dev, size=10, spacing=1.1)
        pic(imgs[0], 8.6, y + 0.1, 2.2, 1.3); pic(imgs[1], 10.95, y + 0.1, 1.45, 1.3)
    y = 4.85; c12_card(0.8, y, 11.75, 1.9)
    txt(1.0, y, 1.1, 1.9, "03", size=30, bold=True, color=T()['c1'], anchor='m')
    b.head(2.2, y + 0.15, 5.0, "Наблюдение", None, 11.5, 0.36)
    txt(2.2, y + 0.6, 4.0, 0.9, "Наблюдение проводилось до операции и в стандартные сроки", size=10, spacing=1.1)
    hair(5.4, y + 1.1, 12.1, y + 1.1, T()['c1'], 1.2)
    for i, lab in enumerate(TIMELINE):
        cx = 5.9 + i * 2.0; b.dot(cx, y + 1.1, 0.08, T()['c1']); txt(cx - 0.9, y + 1.3, 1.8, 0.3, lab, size=10, align='c')


def c12_concl():
    b.slide("Выводы")
    for i, (t, body) in enumerate(CONCL):
        y = 1.45 + i * 1.38; c12_card(0.8, y, 11.75, 1.28)
        txt(1.0, y, 1.0, 1.28, f"0{i+1}", size=30, bold=True, color=T()['c1'], anchor='m')
        b.head(2.1, y + 0.1, 4.6, t, None, 11, 0.34)
        txt(2.1, y + 0.5, 10.2, 0.78, body, size=9.5, spacing=1.05)


def c12_stats():
    b.slide("Прогнозируемость")
    pic("p18_275.png", 0.8, 1.5, 7.0, 5.3, frame=True)
    for i, (v, lab) in enumerate(STATS):
        y = 1.5 + i * 1.8; hl = (i == 1)
        b.rect(8.2, y, 4.35, 1.6, T()['c1'] if hl else "FFFFFF", T()['cline'], 0.9, MSO_SHAPE.ROUNDED_RECTANGLE, 0.07)
        txt(8.4, y, 1.9, 1.6, v, size=30, bold=True, color="FFFFFF" if hl else T()['c1'], anchor='m')
        txt(10.3, y, 2.1, 1.6, lab, size=10.5, color="FFFFFF" if hl else T()['ink'], anchor='m')


OVR = {
    5: dict(aktual1=c5_aktual1, aktual2=c5_aktual2, goal=c5_goal, methods=c5_methods, diag=c5_diag, criteria=c5_criteria, concl=c5_concl, predict=c5_stats),
    7: dict(aktual1=p7_aktual1, aktual2=p7_aktual2, goal=p7_goal, methods=p7_methods, concl=p7_concl, predict=p7_stats),
    12: dict(aktual1=c12_aktual1, aktual2=c12_aktual2, goal=c12_goal, methods=c12_methods, concl=c12_concl, predict=c12_stats),
}


def build(n):
    th = next(t for t in b.THEMES if t['n'] == n)
    b.T = th; b.PAGE = 0
    b.prs = Presentation(); b.prs.slide_width, b.prs.slide_height = Inches(13.333), Inches(7.5)
    o = OVR[n]
    tbl = n in (1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14)
    seq = [('title', b.s_title), ('aktual1', b.s_aktual1), ('aktual2', b.s_aktual2), ('goal', b.s_goal), ('methods', b.s_methods),
           ('ranges', b.s_ranges_tbl if tbl else b.s_ranges), ('diag', b.s_diag), ('steps', b.s_steps_v), ('operation', b.s_operation), ('patent', b.s_patent),
           ('criteria', b.s_criteria), ('p_smile', b.s_p_smile), ('p_fl', b.s_p_fl), ('model', b.s_model), ('acuity', b.s_acuity), ('refraction', b.s_refraction),
           ('safety', b.s_safety), ('predict', b.s_predict), ('concl', b.s_conclusions), ('end', b.s_end)]
    for name, fn in seq:
        o.get(name, fn)()
    os.makedirs("../presentations", exist_ok=True)
    out = f"../presentations/{th['name']}.pptx"
    b.prs.save(out); print("saved", out)


if __name__ == "__main__":
    for a in sys.argv[1:] or ['5', '7', '12']:
        build(int(a))
