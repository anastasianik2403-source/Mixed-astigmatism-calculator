/* Animated cover: deterministic frame renderer.  Coordinates are in the 829x1280 source space of the cover. */
(function () {
  const SW = 829, SH = 1280;
  const cv = document.getElementById('c');
  const ctx = cv.getContext('2d');
  const KX = cv.width / SW, KY = cv.height / SH;
  const T_END = 17.0;

  // ---------------------------------------------------------------- helpers
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const seg = (t, a, b) => clamp01((t - a) / (b - a));
  const eIO = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const eO3 = (x) => 1 - Math.pow(1 - x, 3);
  const eO2 = (x) => 1 - (1 - x) * (1 - x);
  const eI2 = (x) => x * x;
  const eBack = (x, s = 1.55) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
  const lerp = (a, b, t) => a + (b - a) * t;
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  // ---------------------------------------------------------------- timeline (seconds)
  const TL = {
    eyesIn: [0.45, 1.75],
    dock: [2.0, 3.0],
    p1: [3.0, 5.0],          // posterior lenticule surface  (outer -> centre)
    p2: [5.0, 6.8],          // anterior lenticule surface   (centre -> outer)
    edge: [6.8, 7.4],        // lenticule edge
    tunnels: [7.4, 8.3],     // guiding tunnels
    incision: [8.3, 9.0],    // single ~2 mm incision
    glass: [8.7, 9.5],       // the dissected lenticule becomes visible
    tweezIn: [9.4, 10.2],
    grasp: [10.2, 10.5],
    pull: [10.5, 12.0],
    exit: [12.0, 13.0],
    cones: [12.3, 14.0],
    labels: [14.3, 15.4],
    discGlow: [3.0, 12.6],
    discReveal: [9.6, 12.2],
  };
  const DURATION = 18.2;

  // ---------------------------------------------------------------- assets
  const img = {};
  const loadImg = (k, src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => { img[k] = i; res(); }; i.onerror = rej; i.src = src; });
  let LAYOUT = null;

  // ---------------------------------------------------------------- geometry
  const LE = { cx: 211.6, cy: 907.2, a: 97.3, b: 57.6 };           // optical-zone ellipse, dominant eye
  const RE = { cx: 649.2, cy: 907.3, a: 97.3, b: 57.6 };           // same disc on the other eye
  const PUPIL = { cx: 211.2, cy: 918.7, a: 53.9, b: 29.6 };         // dominant eye pupil
  const IRIS_L = { cx: 212, cy: 940, a: 168, b: 110 };
  const IRIS_R = { cx: 650, cy: 940, a: 168, b: 110 };
  const Ept = (E, u, v) => [E.cx + E.a * u, E.cy + E.b * v];

  // cones (the "arrows")
  const CONE_L = { ax: 220.2, ay: 791, slope: 0.4536, yTop: 432, stops: [
    [432, [240, 236, 225, 0]], [444, [246, 223, 189, 1]], [460, [248, 215, 164, 1]], [480, [253, 208, 143, 1]], [500, [255, 200, 118, 1]],
    [520, [254, 187, 99, 1]], [540, [254, 178, 80, 1]], [560, [255, 170, 65, 1]], [580, [251, 160, 41, 1]], [600, [255, 154, 22, 1]],
    [700, [255, 156, 27, 1]], [760, [253, 154, 25, 1]], [775, [239, 166, 79, 0.9]], [782, [227, 181, 124, 0.6]], [790, [206, 231, 232, 0]]] };
  const CONE_R = { ax: 644.5, ay: 791.3, slope: 0.622, yTop: 580, stops: [
    [580, [165, 226, 247, 0]], [592, [133, 214, 244, 1]], [598, [119, 208, 245, 1]], [604, [103, 202, 244, 1]], [610, [90, 195, 240, 1]],
    [616, [74, 189, 237, 1]], [622, [57, 183, 234, 1]], [628, [26, 177, 232, 1]], [634, [8, 172, 229, 1]], [640, [0, 169, 228, 1]],
    [658, [0, 163, 224, 1]], [700, [0, 151, 216, 1]], [760, [0, 150, 213, 1]], [775, [1, 153, 215, 0.9]], [782, [8, 151, 197, 0.6]], [790, [176, 226, 242, 0]]] };

  // ---------------------------------------------------------------- lenticule outline (ellipse -> pulled teardrop)
  const NPT = 96;
  function catmull(pts, n) { // closed Catmull-Rom, resampled by arc length to n points
    const dense = [];
    const m = pts.length;
    for (let i = 0; i < m; i++) {
      const p0 = pts[(i - 1 + m) % m], p1 = pts[i], p2 = pts[(i + 1) % m], p3 = pts[(i + 2) % m];
      for (let s = 0; s < 24; s++) {
        const t = s / 24, t2 = t * t, t3 = t2 * t;
        dense.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                    0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
      }
    }
    const L = [0]; for (let i = 1; i <= dense.length; i++) { const a = dense[i - 1], b = dense[i % dense.length]; L.push(L[i - 1] + Math.hypot(b[0] - a[0], b[1] - a[1])); }
    const tot = L[L.length - 1], out = []; let j = 0;
    for (let k = 0; k < n; k++) {
      const d = (k / n) * tot; while (L[j + 1] < d) j++;
      const a = dense[j], b = dense[(j + 1) % dense.length], f = (d - L[j]) / (L[j + 1] - L[j] || 1);
      out.push([lerp(a[0], b[0], f), lerp(a[1], b[1], f)]);
    }
    return out;
  }
  // traced from the cover (clockwise on screen, starting at the pointed tip)
  const TEAR_CTRL = [[372, 905], [361, 914], [341, 922], [316, 927], [291, 928], [268, 923], [245, 914], [213, 904], [188, 896], [172, 889], [166, 879],
                     [170, 866], [180, 854], [196, 846], [218, 841], [246, 840], [275, 846], [302, 860], [326, 877], [348, 893], [364, 902]];
  let TEAR = null, ELL = null;
  function buildShapes() {
    TEAR = catmull(TEAR_CTRL, NPT);
    ELL = []; for (let i = 0; i < NPT; i++) { const th = (i / NPT) * 2 * Math.PI; ELL.push([LE.cx + LE.a * Math.cos(th), LE.cy + LE.b * Math.sin(th)]); }
    // align start index of the teardrop to its tip (largest x) so both outlines start on the right
    let k = 0, best = -1; for (let i = 0; i < NPT; i++) if (TEAR[i][0] > best) { best = TEAR[i][0]; k = i; }
    TEAR = TEAR.slice(k).concat(TEAR.slice(0, k));
  }
  function outline(s, dx) {
    const o = [];
    for (let i = 0; i < NPT; i++) o.push([lerp(ELL[i][0], TEAR[i][0], s) + dx, lerp(ELL[i][1], TEAR[i][1], s)]);
    return o;
  }
  function pathClosed(c, pts) { c.beginPath(); const n = pts.length; const m0 = [(pts[n - 1][0] + pts[0][0]) / 2, (pts[n - 1][1] + pts[0][1]) / 2]; c.moveTo(m0[0], m0[1]);
    for (let i = 0; i < n; i++) { const p = pts[i], q = pts[(i + 1) % n]; c.quadraticCurveTo(p[0], p[1], (p[0] + q[0]) / 2, (p[1] + q[1]) / 2); } c.closePath(); }

  // ---------------------------------------------------------------- drawing blocks
  const off = document.createElement('canvas'); off.width = cv.width; off.height = cv.height; const octx = off.getContext('2d');

  function drawLayerImg(c, im, y0, alpha) { c.globalAlpha = alpha; c.drawImage(im, 0, y0, SW, im.height / LAYOUT.scale); c.globalAlpha = 1; }

  function eyesLayer(t) {
    const a = eO3(seg(t, TL.eyesIn[0], TL.eyesIn[1])); if (a <= 0) return;
    const im = img.eyes, y0 = LAYOUT.eyes[0], h = im.height / LAYOUT.scale;
    const sc = lerp(0.9, 1, eO3(seg(t, TL.eyesIn[0], TL.eyesIn[1] + 0.3)));
    for (const [x0, x1, cx, cy] of [[0, 415, 212, 940], [415, SW, 650, 940]]) {
      ctx.save(); ctx.beginPath(); ctx.rect(x0, y0 - 40, x1 - x0, h + 80); ctx.clip();
      ctx.translate(cx, cy); ctx.scale(sc, sc); ctx.translate(-cx, -cy);
      ctx.globalAlpha = a; ctx.drawImage(im, 0, y0, SW, h); ctx.restore();
    }
  }

  function strokeEllipse(c, E, sx, sy, a0, a1) { c.beginPath(); c.ellipse(E.cx, E.cy, E.a * sx, E.b * sy, 0, a0, a1); }

  // spiral scan -------------------------------------------------
  const TURNS = 19, NSEG = 1500;
  function spiralPoint(pass, p) {
    const r = pass === 1 ? 1 - p : p;
    const th = (pass === 1 ? 0 : Math.PI * 0.5) + p * TURNS * 2 * Math.PI * (pass === 1 ? 1 : -1);
    return Ept(LE, r * Math.cos(th), r * Math.sin(th));
  }
  const spark = []; { const R = rng(7); for (let i = 0; i < 520; i++) spark.push({ p: R(), pass: i % 2 === 0 ? 1 : 2, jx: (R() - 0.5) * 3.5, jy: (R() - 0.5) * 3.5, s: 0.5 + R() * 1.0, ph: R() * 6 }); }

  function laser(t) {
    const fadeOutScan = 1 - eO2(seg(t, TL.glass[0], TL.glass[1] + 0.4));
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    // docking / applanation shimmer
    const dk = seg(t, TL.dock[0], TL.dock[1]);
    if (dk > 0 && dk < 1) {
      const al = Math.sin(dk * Math.PI);
      ctx.lineWidth = 1.4; ctx.strokeStyle = `rgba(190,238,255,${0.55 * al})`; ctx.shadowColor = 'rgba(150,225,255,0.9)'; ctx.shadowBlur = 8 * KX;
      strokeEllipse(ctx, IRIS_L, 1.02 + 0.03 * (1 - dk), 1.02 + 0.03 * (1 - dk), 0, Math.PI * 2); ctx.stroke();
      ctx.shadowBlur = 0;
    }
    const sp = [];
    for (const pass of [1, 2]) {
      const [a, b] = pass === 1 ? TL.p1 : TL.p2;
      const q = pass === 1 ? eIO(seg(t, a, b)) * 0.25 + seg(t, a, b) * 0.75 : eIO(seg(t, a, b)) * 0.25 + seg(t, a, b) * 0.75;
      if (q <= 0) continue;
      const n = Math.max(2, Math.floor(q * NSEG));
      const dim = pass === 1 ? (t > TL.p2[0] ? 0.5 : 0.85) : 0.85;
      const col = pass === 1 ? '178,236,255' : '236,248,255';
      // soft body
      ctx.beginPath(); for (let i = 0; i <= n; i++) { const pt = spiralPoint(pass, (i / NSEG)); if (i === 0) ctx.moveTo(pt[0], pt[1]); else ctx.lineTo(pt[0], pt[1]); }
      ctx.lineJoin = 'round';
      ctx.lineWidth = 3.0; ctx.strokeStyle = `rgba(${col},${0.07 * fadeOutScan * dim})`; ctx.stroke();
      ctx.lineWidth = 0.8; ctx.strokeStyle = `rgba(${col},${0.42 * fadeOutScan * dim})`; ctx.stroke();
      if (q < 1) sp.push([spiralPoint(pass, q), pass]);
    }
    // cavitation micro-bubbles along the passed path
    for (const s of spark) {
      const [a, b] = s.pass === 1 ? TL.p1 : TL.p2; const q = eIO(seg(t, a, b)) * 0.25 + seg(t, a, b) * 0.75;
      if (s.p > q) continue;
      // time since the beam passed this point (invert approx: linear in q)
      const age = (q - s.p) * (b - a) * 1.1; const br = Math.exp(-age * 2.6) + 0.18 * (0.5 + 0.5 * Math.sin(t * 6 + s.ph));
      const pt = spiralPoint(s.pass, s.p);
      ctx.fillStyle = `rgba(215,245,255,${Math.min(0.9, br * 0.8) * fadeOutScan})`;
      ctx.beginPath(); ctx.arc(pt[0] + s.jx, pt[1] + s.jy, s.s, 0, 6.283); ctx.fill();
    }
    // beam head
    for (const [pt] of sp) {
      const g = ctx.createRadialGradient(pt[0], pt[1], 0, pt[0], pt[1], 16);
      g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.15, 'rgba(210,245,255,0.85)'); g.addColorStop(0.5, 'rgba(120,215,255,0.25)'); g.addColorStop(1, 'rgba(120,215,255,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(pt[0], pt[1], 16, 0, 6.283); ctx.fill();
    }
    // lenticule edge: bright sweep around the optical zone
    const ed = eIO(seg(t, TL.edge[0], TL.edge[1]));
    if (ed > 0) {
      const fade = 1 - eO2(seg(t, TL.glass[0] + 0.1, TL.glass[1] + 0.5));
      ctx.lineWidth = 1.5; ctx.strokeStyle = `rgba(235,250,255,${0.75 * fade})`; ctx.shadowColor = 'rgba(140,225,255,1)'; ctx.shadowBlur = 9 * KX;
      strokeEllipse(ctx, LE, 1, 1, -0.5 * Math.PI, -0.5 * Math.PI + ed * 2 * Math.PI); ctx.stroke(); ctx.shadowBlur = 0;
      if (ed < 1) { const th = -0.5 * Math.PI + ed * 2 * Math.PI; const pt = Ept(LE, Math.cos(th), Math.sin(th)); const g = ctx.createRadialGradient(pt[0], pt[1], 0, pt[0], pt[1], 15); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(150,230,255,0.4)'); g.addColorStop(1, 'rgba(150,230,255,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(pt[0], pt[1], 15, 0, 6.283); ctx.fill(); }
    }
    // guiding tunnels (anterior / posterior) towards the single incision, then the incision itself
    const I0 = [349, 911];
    const tA = [Ept(LE, Math.cos(-0.16), Math.sin(-0.16)), [I0[0] - 2, I0[1] - 5]];
    const tP = [Ept(LE, Math.cos(0.16), Math.sin(0.16)), [I0[0] - 2, I0[1] + 5]];
    const tu = eIO(seg(t, TL.tunnels[0], TL.tunnels[1]));
    const keep = 1 - eO2(seg(t, TL.pull[0], TL.exit[1] + 1.0));
    if (tu > 0) {
      for (const T of [tA, tP]) {
        const x = lerp(T[0][0], T[1][0], tu), y = lerp(T[0][1], T[1][1], tu);
        ctx.shadowColor = 'rgba(140,225,255,1)'; ctx.shadowBlur = 6 * KX; ctx.lineWidth = 1.5; ctx.strokeStyle = `rgba(225,248,255,${0.9 * keep})`;
        ctx.beginPath(); ctx.moveTo(T[0][0], T[0][1]); ctx.lineTo(x, y); ctx.stroke(); ctx.shadowBlur = 0;
        if (tu < 1) { const g = ctx.createRadialGradient(x, y, 0, x, y, 11); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(150,230,255,0.45)'); g.addColorStop(1, 'rgba(150,230,255,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 11, 0, 6.283); ctx.fill(); }
      }
    }
    const inc = eIO(seg(t, TL.incision[0], TL.incision[1]));
    if (inc > 0) {
      const a0 = -0.52, a1 = -0.02, ee = { cx: 212, cy: 938, a: 141, b: 90 };
      const aEnd = lerp(a0, a1, inc);
      const stay = 0.38 + 0.62 * (1 - eO2(seg(t, TL.pull[0], TL.exit[1] + 0.8)));
      ctx.shadowColor = 'rgba(160,230,255,1)'; ctx.shadowBlur = (inc < 1 ? 8 : 3) * KX; ctx.lineWidth = 1.7; ctx.strokeStyle = `rgba(245,253,255,${inc < 1 ? 1 : stay})`;
      ctx.beginPath(); ctx.ellipse(ee.cx, ee.cy, ee.a, ee.b, 0, a0, aEnd); ctx.stroke(); ctx.shadowBlur = 0;
      if (inc < 1) { const pt = [ee.cx + ee.a * Math.cos(aEnd), ee.cy + ee.b * Math.sin(aEnd)]; const g = ctx.createRadialGradient(pt[0], pt[1], 0, pt[0], pt[1], 13); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(150,230,255,0.45)'); g.addColorStop(1, 'rgba(150,230,255,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(pt[0], pt[1], 13, 0, 6.283); ctx.fill(); }
    }
    ctx.restore();
  }

  // translucent lenticule + tweezers -------------------------------------------------
  function pullState(t) {
    const pull = eIO(seg(t, TL.pull[0], TL.pull[1]));
    const exit = eI2(seg(t, TL.exit[0], TL.exit[1])) * 0.55 + eIO(seg(t, TL.exit[0], TL.exit[1])) * 0.45;
    return { s: pull, dx: 175 * exit, exit };
  }
  function lenticule(t) {
    const vis = eO2(seg(t, TL.glass[0], TL.glass[1]));
    const st = pullState(t);
    const out = 1 - eO2(seg(t, TL.exit[0] + 0.25, TL.exit[1] + 0.35));
    const al = vis * out; if (al <= 0.003) return;
    const pts = outline(st.s, st.dx);
    ctx.save(); ctx.globalAlpha = al;
    // soft contact shadow
    pathClosed(ctx, pts); ctx.shadowColor = 'rgba(20,70,110,0.35)'; ctx.shadowBlur = 5 * KX; ctx.shadowOffsetY = 1.5 * KY; ctx.fillStyle = 'rgba(255,255,255,0.02)'; ctx.fill(); ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    // body veil
    const bb = pts.reduce((m, p) => [Math.min(m[0], p[0]), Math.min(m[1], p[1]), Math.max(m[2], p[0]), Math.max(m[3], p[1])], [1e9, 1e9, -1e9, -1e9]);
    const g = ctx.createLinearGradient(bb[0], bb[1], bb[2], bb[3]);
    g.addColorStop(0, 'rgba(255,255,255,0.50)'); g.addColorStop(0.45, 'rgba(238,249,255,0.34)'); g.addColorStop(1, 'rgba(218,240,252,0.28)');
    pathClosed(ctx, pts); ctx.fillStyle = g; ctx.fill();
    // gray reflection where the veil lies over the (dark) pupil
    ctx.save(); pathClosed(ctx, pts); ctx.clip(); ctx.beginPath(); ctx.ellipse(PUPIL.cx, PUPIL.cy, PUPIL.a + 1, PUPIL.b + 1, 0, 0, 6.283); ctx.clip();
    const g2 = ctx.createLinearGradient(0, PUPIL.cy - PUPIL.b, 0, PUPIL.cy + PUPIL.b); g2.addColorStop(0, 'rgba(176,180,186,0.50)'); g2.addColorStop(1, 'rgba(120,126,134,0.36)');
    ctx.fillStyle = g2; ctx.fillRect(PUPIL.cx - 70, PUPIL.cy - 40, 140, 80); ctx.restore();
    // glass edge: dark under-stroke + bright rim
    pathClosed(ctx, pts); ctx.lineWidth = 2.6; ctx.strokeStyle = 'rgba(70,110,140,0.22)'; ctx.stroke();
    pathClosed(ctx, pts); ctx.lineWidth = 1.25; ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.stroke();
    // inner bevel line (thickness of the lenticule), follows the lower rim
    ctx.save(); pathClosed(ctx, pts); ctx.clip(); ctx.translate(0, 2.4); pathClosed(ctx, pts); ctx.lineWidth = 1.0; ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.stroke(); ctx.restore();
    ctx.restore();
  }

  function rod(c, tip, base, w0, w1, alpha) {
    const dx = base[0] - tip[0], dy = base[1] - tip[1], L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const P = [[tip[0] + nx * w0, tip[1] + ny * w0], [base[0] + nx * w1, base[1] + ny * w1], [base[0] - nx * w1, base[1] - ny * w1], [tip[0] - nx * w0, tip[1] - ny * w0]];
    const mid = [(tip[0] + base[0]) / 2, (tip[1] + base[1]) / 2];
    const g = c.createLinearGradient(mid[0] + nx * w1, mid[1] + ny * w1, mid[0] - nx * w1, mid[1] - ny * w1);
    g.addColorStop(0, 'rgb(120,130,142)'); g.addColorStop(0.35, 'rgb(188,196,204)'); g.addColorStop(0.7, 'rgb(240,244,247)'); g.addColorStop(1, 'rgb(205,213,220)');
    c.beginPath(); c.moveTo(P[0][0], P[0][1]); c.lineTo(P[1][0], P[1][1]); c.lineTo(P[2][0], P[2][1]); c.lineTo(P[3][0], P[3][1]); c.closePath(); c.fillStyle = g; c.fill();
    c.lineWidth = 0.5; c.strokeStyle = 'rgba(90,100,112,0.55)'; c.stroke();
  }
  function tweezers(t) {
    const tin = eO3(seg(t, TL.tweezIn[0], TL.tweezIn[1]));
    const st = pullState(t);
    const out = 1 - eO2(seg(t, TL.exit[0] + 0.45, TL.exit[1] + 0.2));
    const al = Math.min(1, seg(t, TL.tweezIn[0], TL.tweezIn[0] + 0.25)) * out; if (al <= 0.003) return;
    const grip = eIO(seg(t, TL.grasp[0], TL.grasp[1]));
    const tipX = lerp(470, 290, tin) + (336 - 290) * st.s + st.dx;
    const tipY = lerp(902, 909, tin) + 1.5 * st.s;
    const gap = lerp(17, 7.4, grip);
    octx.setTransform(1, 0, 0, 1, 0, 0); octx.clearRect(0, 0, off.width, off.height); octx.setTransform(KX, 0, 0, KY, 0, 0);
    // shadow below
    octx.save(); octx.globalAlpha = 0.18; octx.filter = `blur(${3 * KX}px)`; octx.fillStyle = '#143a5a'; octx.beginPath(); octx.moveTo(tipX, tipY + gap / 2 + 5); octx.lineTo(tipX + 140, tipY + gap / 2 + 14); octx.lineTo(tipX + 140, tipY + gap / 2 + 20); octx.lineTo(tipX, tipY + gap / 2 + 8); octx.fill(); octx.restore();
    rod(octx, [tipX, tipY - gap / 2], [tipX + 150, tipY - gap / 2 - 5 - (15 - gap) * 0.3], 1.9, 3.6);
    rod(octx, [tipX, tipY + gap / 2], [tipX + 150, tipY + gap / 2 + 9 + (15 - gap) * 0.1], 1.9, 3.6);
    // fade towards the centre line like the original artwork
    octx.setTransform(KX, 0, 0, KY, 0, 0); octx.globalCompositeOperation = 'destination-in';
    const mg = octx.createLinearGradient(380, 0, 420, 0); mg.addColorStop(0, 'rgba(0,0,0,1)'); mg.addColorStop(1, 'rgba(0,0,0,0)'); octx.fillStyle = mg; octx.fillRect(0, 0, SW, SH); octx.globalCompositeOperation = 'source-over';
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = al; ctx.drawImage(off, 0, 0); ctx.restore();
  }

  // right eye: lenticule already removed -> echo ring + highlighted disc -----------------
  function rightEye(t) {
    const ga = TL.discGlow;
    // echo of the left scan: ring contracts with pass 1 and expands with pass 2
    const q1 = eIO(seg(t, TL.p1[0], TL.p1[1])) * 0.25 + seg(t, TL.p1[0], TL.p1[1]) * 0.75;
    const q2 = eIO(seg(t, TL.p2[0], TL.p2[1])) * 0.25 + seg(t, TL.p2[0], TL.p2[1]) * 0.75;
    let r = 1, a = 0;
    if (t >= TL.p1[0] && t < TL.p2[0]) { r = 1 - 0.85 * q1; a = 0.42 * Math.min(1, seg(t, TL.p1[0], TL.p1[0] + 0.3)); }
    else if (t >= TL.p2[0]) { r = 0.15 + 0.85 * q2; a = 0.42; }
    const settle = 1 - 0.55 * eO2(seg(t, TL.discReveal[1] - 0.4, TL.discReveal[1] + 1.2));
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    if (a > 0) {
      const ring = a * settle * (r > 0.97 ? 1 : 1);
      ctx.shadowColor = 'rgba(160,230,255,1)'; ctx.shadowBlur = 8 * KX; ctx.lineWidth = 1.5; ctx.strokeStyle = `rgba(215,244,255,${ring})`;
      strokeEllipse(ctx, RE, r, r, 0, 6.283); ctx.stroke(); ctx.shadowBlur = 0;
    }
    // soft inner light that follows the left eye's extraction (peaks while the tweezers pull)
    const pk = Math.sin(Math.PI * seg(t, TL.tweezIn[0] - 0.2, TL.exit[1] + 0.8));
    if (pk > 0) {
      const g = ctx.createRadialGradient(RE.cx, RE.cy + 4, 4, RE.cx, RE.cy + 4, 108);
      g.addColorStop(0, `rgba(210,245,255,${0.30 * pk})`); g.addColorStop(0.7, `rgba(190,238,255,${0.14 * pk})`); g.addColorStop(1, 'rgba(190,238,255,0)');
      ctx.save(); ctx.scale(1, 0.6); ctx.translate(0, RE.cy * (1 / 0.6 - 1)); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(RE.cx, RE.cy + 4, 108, 0, 6.283); ctx.fill(); ctx.restore();
    }
    ctx.restore();
    // the real translucent disc (from the artwork) appears with a radial wipe
    const rv = seg(t, TL.discReveal[0], TL.discReveal[1]);
    if (rv > 0) {
      const op = eIO(rv), wipe = eO2(rv);
      const [x0, y0, x1, y1] = LAYOUT.disc;
      ctx.save(); ctx.beginPath(); ctx.ellipse(RE.cx, RE.cy + 6, (RE.a + 14) * (0.12 + 0.95 * wipe), (RE.b + 16) * (0.12 + 0.95 * wipe), 0, 0, 6.283); ctx.clip();
      ctx.globalAlpha = op; ctx.drawImage(img.disc, x0, y0, x1 - x0, y1 - y0); ctx.restore();
    }
    // a gentle, lasting rim light on the disc once it is revealed
    const rim = eO2(seg(t, TL.discReveal[1] - 1.0, TL.discReveal[1] + 0.8));
    if (rim > 0) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.shadowColor = 'rgba(170,235,255,1)'; ctx.shadowBlur = 7 * KX;
      ctx.lineWidth = 1.1; ctx.strokeStyle = `rgba(220,246,255,${0.30 * rim})`; strokeEllipse(ctx, RE, 1.0, 1.0, 0, 6.283); ctx.stroke(); ctx.restore();
    }
  }

  // cones --------------------------------------------------------------
  function cone(C, e, a) {
    if (e <= 0.001) return;
    const yt = C.ay - e * (C.ay - C.yTop), hw = C.slope * (C.ay - yt) / 2;
    const g = ctx.createLinearGradient(0, yt, 0, C.ay);
    for (const [y, c] of C.stops) { const f = clamp01((y - C.yTop) / (C.ay - C.yTop)); g.addColorStop(f, `rgba(${c[0]},${c[1]},${c[2]},${c[3]})`); }
    // stops were defined for the full cone: map them onto the current length (the beam grows, gradient follows)
    ctx.save(); ctx.globalAlpha = a; ctx.filter = `blur(${1.5 * KX}px)`;
    ctx.beginPath(); ctx.moveTo(C.ax, C.ay); ctx.lineTo(C.ax - hw, yt); ctx.lineTo(C.ax + hw, yt); ctx.closePath(); ctx.fillStyle = g; ctx.fill(); ctx.restore();
  }
  function ripple(C, t0, t) {
    const k = seg(t, t0, t0 + 1.3); if (k <= 0 || k >= 1) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = 1.2; ctx.strokeStyle = `rgba(230,250,255,${0.55 * (1 - k)})`;
    ctx.beginPath(); ctx.ellipse(C.ax, C.ay + 3, 8 + 70 * eO3(k), 3 + 24 * eO3(k), 0, 0, 6.283); ctx.stroke(); ctx.restore();
  }

  // labels ------------------------------------------------------------------
  function labels(t) {
    const defs = [
      { txt: 'ДОМИНАНТНЫЙ', x: 209, y: 1119.5, col: 'rgb(188,102,58)', d: 0.0 },
      { txt: 'ГЛАЗ', x: 209, y: 1157, col: 'rgb(188,102,58)', d: 0.12 },
      { txt: 'НЕДОМИНАНТНЫЙ', x: 646.5, y: 1119.5, col: 'rgb(10,137,186)', d: 0.0 },
      { txt: 'ГЛАЗ', x: 646.5, y: 1157, col: 'rgb(10,137,186)', d: 0.12 },
    ];
    for (const L of defs) {
      const k = seg(t, TL.labels[0] + L.d, TL.labels[1] + L.d); if (k <= 0) continue;
      const a = eO3(seg(k, 0, 0.7)), sc = lerp(0.86, 1, eBack(k)), dy = lerp(16, 0, eO3(k));
      ctx.save(); ctx.globalAlpha = a; ctx.translate(L.x, L.y + dy); ctx.scale(sc, sc);
      ctx.font = '800 28.9px Montserrat'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = L.col; ctx.fillText(L.txt, 0, 0); ctx.restore();
    }
  }

  // ---------------------------------------------------------------- frame
  function drawFrame(t) {
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.setTransform(KX, 0, 0, KY, 0, 0); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(img.base, 0, 0, SW, SH);
    const sa = eIO(seg(t, TL.cones[0] - 0.4, TL.cones[1] + 0.2));
    if (sa > 0) drawLayerImg(ctx, img.scene, LAYOUT.scene[0], sa);
    eyesLayer(t);
    rightEye(t);
    laser(t);
    const ce = eIO(seg(t, TL.cones[0], TL.cones[1]));
    cone(CONE_L, ce, 1); cone(CONE_R, eIO(seg(t, TL.cones[0] + 0.05, TL.cones[1] + 0.05)), 1);
    ripple(CONE_L, TL.cones[1] - 0.3, t); ripple(CONE_R, TL.cones[1] - 0.25, t);
    lenticule(t);
    tweezers(t);
    labels(t);
  }

  // ---------------------------------------------------------------- boot
  window.COVER = { drawFrame, DURATION, ready: null };
  window.COVER.ready = (async () => {
    LAYOUT = await (await fetch('assets/layout.json')).json();
    await Promise.all([loadImg('base', 'assets/base.png'), loadImg('scene', 'assets/scene.png'), loadImg('eyes', 'assets/eyes.png'), loadImg('disc', 'assets/disc.png')]);
    const f = new FontFace('Montserrat', 'url(assets/Montserrat-ExtraBold.ttf)', { weight: '800' }); await f.load(); document.fonts.add(f);
    buildShapes();
    drawFrame(0);
    return true;
  })();
  // live preview in a browser:  index.html?play
  if (new URLSearchParams(location.search).has('play')) {
    window.COVER.ready.then(() => { const t0 = performance.now(); const loop = (n) => { const t = ((n - t0) / 1000) % (DURATION + 1.5); drawFrame(Math.min(t, DURATION)); requestAnimationFrame(loop); }; requestAnimationFrame(loop); });
  }
})();
