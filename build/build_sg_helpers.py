import build3 as b
from pptx import Presentation
LAYOUT = {1: 0, 2: 4, 3: 19, 4: 1, 5: 20, 6: 15, 7: 17, 8: 16, 9: 4, 10: 19, 11: 20, 12: 17, 13: 16, 14: 13, 15: 15, 16: 19, 17: 22, 18: 23, 19: 13, 20: 23}


def _new(bgname):
    b.PAGE += 1
    s = b.prs.slides.add_slide(b.prs.slide_layouts[LAYOUT[b.PAGE]])
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    b.sl = s
    return s


def setup():
    b.new = _new
    prs = Presentation('sg_template.pptx')
    lst = prs.slides._sldIdLst
    for sid in list(lst):
        prs.part.drop_rel(sid.rId); lst.remove(sid)
    b.prs = prs
