"""Render deck.json into a single self-contained HTML presentation (fixed 1920x1080 stage)."""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SLIDES = json.load(open(os.path.join(HERE, "deck.json")))
BASE_CSS = open(os.path.join(ROOT, "..", ".claude", "skills", "frontend-slides", "viewport-base.css")).read()

COL = dict(text="#0B1A6B", muted="#5B6795", accent="#1736D9", white="#FFFFFF", grid="#D9E1F5")

def rich(t, color):
    """*word* -> accent span; newline -> <br>."""
    acc = "#BFD0FF" if color == "white" else COL["accent"]
    out = html.escape(t)
    out = re.sub(r"\*(.+?)\*", lambda m: f'<span style="color:{acc}">{m.group(1)}</span>', out)
    return out.replace("\n", "<br>")

def fmt(v, f):
    s = f"{v:.0f}" if f == "0" else f"{v:.2f}"
    return s.replace("-", "−").replace(".", ",")

def nice_ticks(lo, hi):
    """Round tick values (step 0.2/0.25/0.5/1/2/5/10/20…) between lo and hi."""
    span = hi - lo
    for st in [0.1, 0.2, 0.25, 0.5, 1, 2, 5, 10, 20, 25, 50, 100]:
        if span / st <= 6: break
    import math
    t = math.ceil(lo / st - 1e-9) * st; out = []
    while t <= hi + 1e-9: out.append(round(t, 4)); t += st
    dec = 0 if st >= 1 else (1 if st in (0.2, 0.5) else 2)
    return out, dec

def svg_chart(e):
    w, h = e["w"], e["h"]
    cats, ser = e["cats"], e["series"]
    if e["type"] == "doughnut":
        v = ser[0]["v"]; frac = v[0] / sum(v)
        r, cx, cy, sw = min(w, h) / 2 - 30, w / 2, h / 2, 46
        c = 2 * 3.14159 * r
        return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#E3E9F8" stroke-width="{sw}"/>'
                f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{ser[0]["c"]}" stroke-width="{sw}" stroke-linecap="round" '
                f'stroke-dasharray="{c*frac:.1f} {c:.1f}" transform="rotate(-90 {cx} {cy})"/></svg>')
    L, R, T, B = 110, 30, 70 if e["legend"] else 30, 64
    lo, hi = e["ymin"], e["ymax"]
    y = lambda v: T + (hi - v) / (hi - lo) * (h - T - B)
    n = len(cats); slot = (w - L - R) / n
    p = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Manrope">']
    ticks, dec = nice_ticks(lo, hi)
    for v in ticks:
        p.append(f'<line x1="{L}" x2="{w-R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{COL["grid"]}" stroke-width="1.5" stroke-dasharray="4 8"/>')
        p.append(f'<text x="{L-14}" y="{y(v)+7:.1f}" text-anchor="end" font-size="20" fill="{COL["muted"]}">{f"{v:.{dec}f}".replace("-", "−").replace(".", ",")}</text>')
    for i, c in enumerate(cats):
        p.append(f'<text x="{L+slot*(i+.5):.1f}" y="{h-18}" text-anchor="middle" font-size="22" fill="{COL["muted"]}">{c}</text>')
    if e["legend"]:
        lx = L
        for s in ser:
            p.append(f'<rect x="{lx}" y="14" width="30" height="8" rx="4" fill="#{s["c"]}"/><text x="{lx+42}" y="26" font-size="22" fill="{COL["muted"]}">{s["n"]}</text>')
            lx += 60 + len(s["n"]) * 13
    if e["type"] == "bar":
        k = len(ser); bw = slot * 0.62 / k
        for si, s in enumerate(ser):
            for i, v in enumerate(s["v"]):
                x = L + slot * i + slot * 0.19 + si * bw
                base = y(max(lo, 0) if lo <= 0 <= hi else lo)
                top = y(v)
                p.append(f'<rect class="bar" x="{x+4:.1f}" y="{min(top,base):.1f}" width="{bw-8:.1f}" height="{abs(base-top):.1f}" rx="10" fill="#{s["c"]}"/>')
                p.append(f'<text x="{x+bw/2:.1f}" y="{top-12:.1f}" text-anchor="middle" font-size="22" font-weight="700" fill="{COL["text"]}">{fmt(v, e["fmt"])}</text>')
    else:
        xs = [L + slot * (i + .5) for i in range(n)]
        main = ser[0]
        pts = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, main["v"]))
        p.append(f'<defs><linearGradient id="ar{id(e)}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#{main["c"]}" stop-opacity=".22"/><stop offset="1" stop-color="#{main["c"]}" stop-opacity="0"/></linearGradient></defs>')
        base = y(lo) if main["v"][0] >= lo else y(hi)
        p.append(f'<polygon points="{xs[0]:.1f},{y(lo):.1f} {pts} {xs[-1]:.1f},{y(lo):.1f}" fill="url(#ar{id(e)})"/>')
        for si, s in reversed(list(enumerate(ser))):
            ps = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, s["v"]))
            p.append(f'<polyline points="{ps}" fill="none" stroke="#{s["c"]}" stroke-width="{6 if si==0 else 4}" stroke-linejoin="round" {"stroke-dasharray=\"12 10\"" if s["dash"] else ""}/>')
        for si, s in enumerate(ser):
            for i, (x, v) in enumerate(zip(xs, s["v"])):
                other = ser[1 - si]["v"][i] if len(ser) > 1 else v - 1
                above = v >= other
                p.append(f'<circle cx="{x:.1f}" cy="{y(v):.1f}" r="{10 if si==0 else 7}" fill="#{s["c"]}" stroke="#fff" stroke-width="3"/>')
                dy = -20 if above else 38
                lx, anc = (x - 20, "end") if i == 0 else (x, "middle")
                if i == 0: dy = 8 if si == 0 else 34
                p.append(f'<text x="{lx:.1f}" y="{y(v)+dy:.1f}" text-anchor="{anc}" font-size="{24 if si==0 else 20}" font-weight="{700 if si==0 else 500}" fill="{COL["text"] if si==0 else COL["muted"]}">{fmt(v, e["fmt"])}</text>')
    p.append("</svg>")
    return "".join(p)

def el(e):
    st = f'left:{e.get("x",0)}px;top:{e.get("y",0)}px;width:{e.get("w",0)}px;height:{e.get("h",0)}px;'
    k = e["k"]
    if k == "card":
        return f'<div class="card {e["v"]}" style="{st}"></div>'
    if k == "text":
        va = {"t": "flex-start", "m": "center", "b": "flex-end"}[e["va"]]
        al = {"l": "left", "c": "center", "r": "right"}[e["al"]]
        fam = "var(--display)" if e["ff"] == "display" else "var(--body)"
        ls = "-.035em" if e["s"] >= 48 else ("-.01em" if e["s"] >= 30 else "0")
        return (f'<div class="tx" style="{st}justify-content:{va};text-align:{al};font-family:{fam};font-size:{e["s"]}px;'
                f'font-weight:{e["wt"]};line-height:{e["lh"]};color:{COL[e["c"]]};letter-spacing:{ls}"><div>{rich(e["t"], e["c"])}</div></div>')
    if k == "pill":
        return f'<div class="pill {e["v"]}" style="left:{e["x"]}px;top:{e["y"]}px;height:{e["h"]}px">{html.escape(e["t"])}</div>'
    if k == "pager":
        return f'<div class="pager" style="{st}">{e["t"]}</div>'
    if k == "img":
        r = f'border-radius:{e["r"]}px;' if e["r"] else ""
        return f'<img class="im" src="assets/{e["src"]}" style="{st}object-fit:{e["fit"]};{r}" alt="">'
    if k == "chart":
        return f'<div class="chart" style="{st}">{svg_chart(e)}</div>'
    if k == "table":
        rows = e["rows"]; rh = e["h"] / len(rows)
        out = [f'<div class="tbl" style="{st}">']
        for ri, row in enumerate(rows):
            out.append(f'<div class="tr{" th" if ri==0 and row[0]=="" else ""}" style="height:{rh:.0f}px;grid-template-columns:{" ".join(str(c)+"px" for c in e["cols"])};font-size:{e["s"]}px">')
            for ci, cell in enumerate(row):
                out.append(f'<div class="td{" c0" if ci==0 else ""}">{rich(cell, "text")}</div>')
            out.append("</div>")
        return "".join(out) + "</div>"
    if k == "dot":
        return f'<div class="dot" style="left:{e["x"]}px;top:{e["y"]}px;width:{e["d"]}px;height:{e["d"]}px"></div>'
    if k == "line":
        return (f'<svg class="ln" style="left:0;top:0;width:1920px;height:1080px" viewBox="0 0 1920 1080"><line x1="{e["x1"]}" y1="{e["y1"]}" x2="{e["x2"]}" y2="{e["y2"]}" '
                f'stroke="{COL[e["c"]]}" stroke-width="{e["wd"]}" stroke-linecap="round" {"stroke-dasharray=\"8 10\"" if e["dash"] else ""}/></svg>')
    raise ValueError(k)

CSS = """
/* === TOKENS: style D «Глянец на свету» — colours from reference 1, block layout from reference 2 === */
:root{--text:#0B1A6B;--muted:#5B6795;--accent:#1736D9;--display:'Manrope',sans-serif;--body:'Manrope',sans-serif;
  --stage-bg:#0b1030;--slide-bg:#e9eefb;
  --page:radial-gradient(55% 60% at 75% 40%,#fff 0%,rgba(255,255,255,0) 70%),radial-gradient(60% 70% at 10% 100%,#bccbf3 0%,rgba(188,203,243,0) 70%),linear-gradient(150deg,#e9eefb,#cdd9f4)}
body{font-family:var(--body);color:var(--text)}
.slide{background:var(--page)}
/* === BUILDING BLOCKS === */
.card{position:absolute;border-radius:34px}
.card.white{background:rgba(255,255,255,.88);border:1.5px solid #fff;box-shadow:0 24px 60px rgba(23,54,217,.10)}
.card.solid{background:linear-gradient(150deg,#2a4cf5,#0A1E9E);box-shadow:0 24px 60px rgba(23,54,217,.28)}
.card.ice{background:#EEF2FD}
.tx{position:absolute;display:flex;flex-direction:column}
.pill{position:absolute;display:flex;align-items:center;padding:0 22px;border-radius:30px;font-size:21px;font-weight:600;white-space:nowrap}
.pill.ice{background:#EEF2FD;color:var(--muted)}
.pill.onsolid{background:rgba(255,255,255,.16);color:#fff}
.pager{position:absolute;display:flex;align-items:center;justify-content:center;border:1.5px solid #cdd7f1;border-radius:30px;font-size:19px;color:var(--muted)}
.im{position:absolute}
.chart{position:absolute}
.dot{position:absolute;border-radius:50%;background:var(--accent);box-shadow:0 0 0 8px rgba(23,54,217,.15)}
.ln{position:absolute;pointer-events:none}
.tbl{position:absolute;display:flex;flex-direction:column}
.tr{display:grid;align-items:center;border-bottom:1.5px solid #E1E7F6}
.tr:last-child{border-bottom:0}
.tr.th{color:var(--muted);font-weight:700}
.td{padding-right:20px;line-height:1.3;font-weight:600}
.td.c0{color:var(--muted);font-weight:500}
.tr.th .td{color:var(--accent);font-weight:800}
/* === MOTION: staggered reveal on the active slide === */
.slide>*{opacity:0;transform:translateY(18px);transition:opacity .7s cubic-bezier(.2,.7,.2,1),transform .7s cubic-bezier(.2,.7,.2,1)}
.slide.active>*{opacity:1;transform:none}
.slide.active .im[src*="3d-"]{animation:float 7s ease-in-out infinite alternate}
@keyframes float{to{transform:translateY(-14px) rotate(-.6deg)}}
.slide.active .bar{animation:grow .9s cubic-bezier(.2,.7,.2,1) both;transform-origin:bottom;transform-box:fill-box}
@keyframes grow{from{transform:scaleY(0)}}
@media (prefers-reduced-motion:reduce){.slide>*{transition:none;opacity:1;transform:none}.slide.active .im,.slide.active .bar{animation:none}}
/* === CONTROLS === */
.deck-controls{display:flex;gap:10px;align-items:center;background:rgba(11,26,107,.75);padding:8px 14px;border-radius:30px;color:#fff;font:600 14px var(--body);opacity:0;transition:opacity .3s}
body:hover .deck-controls{opacity:1}
.deck-controls button{background:none;border:0;color:#fff;font-size:18px;cursor:pointer;width:32px;height:32px;border-radius:50%}
.deck-controls button:hover{background:rgba(255,255,255,.15)}
.progress{position:fixed;left:0;top:0;height:3px;background:#1736D9;z-index:1001;transition:width .4s}
@media print{.slide>*{opacity:1!important;transform:none!important}.progress{display:none}}
"""

JS = """
/* === NAVIGATION + STAGE SCALING === */
const stage=document.querySelector('.deck-stage'), slides=[...document.querySelectorAll('.slide')];
const counter=document.getElementById('counter'), bar=document.querySelector('.progress');
let cur=0;
function fit(){const s=Math.min(innerWidth/1920,innerHeight/1080);
  stage.style.transform=`translate(${(innerWidth-1920*s)/2}px,${(innerHeight-1080*s)/2}px) scale(${s})`;}
function go(i){cur=Math.max(0,Math.min(slides.length-1,i));
  slides.forEach((s,k)=>s.classList.toggle('active',k===cur));
  [...slides[cur].children].forEach((c,k)=>c.style.transitionDelay=(k*45)+'ms');
  counter.textContent=(cur+1)+' / '+slides.length; bar.style.width=((cur+1)/slides.length*100)+'%';
  history.replaceState(null,'','#'+(cur+1));}
addEventListener('resize',fit);
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){e.preventDefault();go(cur+1)}
  if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){e.preventDefault();go(cur-1)}
  if(e.key==='Home')go(0); if(e.key==='End')go(slides.length-1);
  if(e.key==='f')document.documentElement.requestFullscreen?.();});
let tx=null;addEventListener('touchstart',e=>tx=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(tx===null)return;const d=e.changedTouches[0].clientX-tx;if(Math.abs(d)>40)go(cur+(d<0?1:-1));tx=null});
document.getElementById('prev').onclick=()=>go(cur-1);document.getElementById('next').onclick=()=>go(cur+1);
fit();go((parseInt(location.hash.slice(1))||1)-1);
"""

def build():
    body = []
    for i, s in enumerate(SLIDES):
        body.append(f'<section class="slide" data-n="{i+1}"><!-- {html.escape(s.get("notes",""))} -->' + "".join(el(e) for e in s["els"]) + "</section>")
    doc = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Лентикулярная коррекция смешанного астигматизма</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{BASE_CSS}
{CSS}
</style></head>
<body>
<div class="progress"></div>
<div class="deck-viewport"><div class="deck-stage">
{chr(10).join(body)}
</div></div>
<div class="deck-controls"><button id="prev" aria-label="Назад">‹</button><span id="counter"></span><button id="next" aria-label="Вперёд">›</button></div>
<script>{JS}</script>
</body></html>"""
    open(os.path.join(ROOT, "index.html"), "w").write(doc)
    print("ok", len(SLIDES))

if __name__ == "__main__":
    build()
