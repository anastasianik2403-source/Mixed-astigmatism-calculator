import copy, sys
import build3 as b
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
F = 0.75
b.I = lambda v: Inches(v * F)
b.Pt = lambda v: Pt(v * F)
b.SANS = "Assistant"; b.SERIF = "Assistant"
LAYOUT = {1: 0, 2: 4, 3: 19, 4: 1, 5: 20, 6: 15, 7: 17, 8: 16, 9: 4, 10: 19, 11: 20, 12: 17, 13: 16, 14: 13, 15: 15, 16: 19, 17: 22, 18: 23, 19: 13, 20: 23}


def new(bgname):
    b.PAGE += 1
    lay = b.prs.slide_layouts[LAYOUT[b.PAGE]]
    s = b.prs.slides.add_slide(lay)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    b.sl = s
    return s


b.new = new
theme = next(t for t in b.THEMES if t['n'] == 14)
b.T = theme; b.PAGE = 0
prs = Presentation('sg_template.pptx')
lst = prs.slides._sldIdLst
for sid in list(lst):
    prs.part.drop_rel(sid.rId); lst.remove(sid)
b.prs = prs
b.s_title(); b.s_aktual1(); b.s_aktual2(); b.s_goal(); b.s_methods(); b.s_ranges_tbl(); b.s_diag(); b.s_steps_v(); b.s_operation(); b.s_patent(); b.s_criteria()
b.s_p_smile(); b.s_p_fl(); b.s_model(); b.s_acuity(); b.s_refraction(); b.s_safety(); b.s_predict(); b.s_conclusions(); b.s_end()
import os
os.makedirs("../presentations", exist_ok=True)
prs.save("../presentations/Template14_Slidesgo-Forensic.pptx"); print("saved")
