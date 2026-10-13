// Render deck.json into an editable PowerPoint file (native text, shapes and charts).
// Usage: node build_pptx.js   (needs pptxgenjs: npm i pptxgenjs@3.12.0)
const path = require("path");
const pptxgen = require("pptxgenjs");
const S = require("./deck.json");

const ROOT = path.resolve(__dirname, "..");
const A = (f) => path.join(ROOT, "assets", f);
const IN = (px) => px / 144;            // 1920 px canvas -> 13.333 in
const PT = (px) => Math.round(px * 0.5 * 10) / 10;
const FONT = "Manrope";
const COL = { text: "0B1A6B", muted: "5B6795", accent: "1736D9", white: "FFFFFF", grid: "D9E1F5" };

// *word* -> accent run; keeps \n as line breaks
function runs(t, c, opts) {
  const acc = c === "white" ? "BFD0FF" : COL.accent;
  const out = [];
  t.replace(/\{\*\}/g, "\u0001").split("\n").forEach((line, li, arr) => {
    const parts = line.split(/(\*[^*]+\*)/).filter(Boolean);
    if (!parts.length) parts.push(" ");
    parts.forEach((p, pi) => {
      const isAcc = p.startsWith("*") && p.endsWith("*");
      const o = Object.assign({}, opts, { color: isAcc ? acc : COL[c] });
      if (pi === parts.length - 1 && li < arr.length - 1) o.breakLine = true;
      out.push({ text: (isAcc ? p.slice(1, -1) : p).replace(/\u0001/g, "*"), options: o });
    });
  });
  return out;
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Современный подход к хирургической коррекции смешанного астигматизма";
pres.author = "Никитина А.Е.";

for (const sd of S) {
  const sl = pres.addSlide();
  sl.background = { path: A("bg-page.jpg") };
  for (const e of sd.els) {
    const box = { x: IN(e.x || 0), y: IN(e.y || 0), w: IN(e.w || 0), h: IN(e.h || 0) };
    switch (e.k) {
      case "card": {
        const fill = e.v === "solid" ? { color: "1E3FE0" } : e.v === "ice" ? { color: "EEF2FD" } : { color: "FFFFFF", transparency: 8 };
        sl.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({}, box, {
          fill, rectRadius: IN(34), line: { color: e.v === "solid" ? "1E3FE0" : "FFFFFF", width: 1 },
          shadow: { type: "outer", color: "1736D9", opacity: e.v === "solid" ? 0.28 : 0.1, blur: 24, offset: 8, angle: 90 },
        }));
        break;
      }
      case "text": {
        sl.addText(runs(e.t, e.c, { fontFace: FONT, fontSize: PT(e.s), bold: e.wt >= 600 }), Object.assign({}, box, {
          margin: 0, valign: { t: "top", m: "middle", b: "bottom" }[e.va], align: { l: "left", c: "center", r: "right" }[e.al],
          lineSpacingMultiple: e.lh, fit: "none",
        }));
        break;
      }
      case "pill": {
        const on = e.v === "onsolid";
        sl.addText(e.t, { x: box.x, y: box.y, w: IN(e.w) * 1.12, h: IN(e.h), shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: IN(22),
          fill: on ? { color: "FFFFFF", transparency: 84 } : { color: "EEF2FD" }, line: { type: "none" },
          fontFace: FONT, fontSize: PT(21), bold: true, color: on ? "FFFFFF" : COL.muted, margin: [0, IN(22), 0, IN(22)], valign: "middle" });
        break;
      }
      case "pager":
        sl.addText(e.t, Object.assign({}, box, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: IN(20), fill: { color: "FFFFFF", transparency: 100 },
          line: { color: "CDD7F1", width: 1 }, fontFace: FONT, fontSize: PT(19), color: COL.muted, align: "center", valign: "middle", margin: 0 }));
        break;
      case "img":
        sl.addImage({ path: A(e.src), x: box.x, y: box.y, w: box.w, h: box.h, sizing: { type: e.fit === "cover" ? "cover" : "contain", w: box.w, h: box.h } });
        break;
      case "dot":
        sl.addShape(pres.shapes.OVAL, { x: IN(e.x), y: IN(e.y), w: IN(e.d), h: IN(e.d), fill: { color: COL.accent }, line: { color: "D3DCFA", width: 4 } });
        break;
      case "line":
        sl.addShape(pres.shapes.LINE, { x: IN(e.x1), y: IN(e.y1), w: IN(e.x2 - e.x1), h: IN(e.y2 - e.y1), line: { color: COL[e.c], width: e.wd * 0.75, dashType: e.dash ? "dash" : "solid" } });
        break;
      case "table": {
        const rh = IN(e.h / e.rows.length);
        const rows = e.rows.map((r, ri) => r.map((cell, ci) => ({
          text: runs(cell, ci === 0 ? "muted" : "text", { fontFace: FONT, fontSize: PT(e.s), bold: ci > 0 }), options: {
            fontFace: FONT, fontSize: PT(e.s), bold: ri === 0 && r[0] === "" ? true : ci > 0,
            color: ri === 0 && r[0] === "" ? COL.accent : ci === 0 ? COL.muted : COL.text, valign: "middle",
            border: [{ type: "none" }, { type: "none" }, ri === e.rows.length - 1 ? { type: "none" } : { type: "solid", color: "E1E7F6", pt: 1 }, { type: "none" }],
            margin: [0, IN(16), 0, 0],
          },
        })));
        sl.addTable(rows, { x: box.x, y: box.y, w: box.w, colW: e.cols.map(IN), rowH: rh });
        break;
      }
      case "chart": {
        const data = e.series.map((s) => ({ name: s.n, labels: e.cats, values: s.v }));
        if (e.type === "doughnut") {
          sl.addChart(pres.charts.DOUGHNUT, [{ name: e.series[0].n, labels: e.cats, values: e.series[0].v }], Object.assign({}, box, {
            holeSize: 72, chartColors: [e.series[0].c, "E3E9F8"], showLegend: false, showValue: false, showPercent: false, showLabel: false,
            dataBorder: { pt: 0, color: "FFFFFF" },
          }));
          break;
        }
        const common = {
          chartColors: e.series.map((s) => s.c), showLegend: e.legend, legendPos: "t", legendFontFace: FONT, legendFontSize: 11, legendColor: COL.muted,
          valAxisMinVal: e.ymin, valAxisMaxVal: e.ymax, valAxisLabelColor: COL.muted, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 10,
          catAxisLabelColor: COL.muted, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11, catAxisLineShow: false, valAxisLineShow: false,
          valGridLine: { color: "E1E7F6", size: 0.75, style: "dash" }, catGridLine: { style: "none" },
          showValue: e.labels, dataLabelFontFace: FONT, dataLabelFontSize: 11, dataLabelFontBold: true, dataLabelColor: COL.text,
          dataLabelFormatCode: e.fmt === "0" ? "0" : "0.00", valAxisLabelFormatCode: e.fmt === "0" ? "0" : "0.0",
        };
        if (e.type === "bar") {
          sl.addChart(pres.charts.BAR, data, Object.assign({}, box, common, { barDir: "col", barGapWidthPct: 60, barOverlapPct: -10, dataLabelPosition: "outEnd" }));
        } else {
          sl.addChart(pres.charts.LINE, data, Object.assign({}, box, common, {
            lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9, dataLabelPosition: "t",
            lineDash: e.series.map((s) => (s.dash ? "dash" : "solid")),
          }));
        }
        break;
      }
      default:
        throw new Error("unknown element " + e.k);
    }
  }
  if (sd.notes) sl.addNotes(sd.notes);
}

pres.writeFile({ fileName: path.join(ROOT, "Коррекция_смешанного_астигматизма_новый_дизайн.pptx") }).then((f) => console.log("written", f));
