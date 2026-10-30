"""Shared PDF toolkit for the Massive PSXL manual and video scripts (reportlab).

Brand: deep indigo + cyan / magenta / amber accents (the plug-in's own palette).
Only the standard PDF fonts are used so the generators run unchanged on any OS.
"""
import math
import os

from reportlab.graphics.shapes import (Circle, Drawing, Group, Line, PolyLine, Polygon, Rect, String)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "Resources", "art")

# ------------------------------------------------------------------ palette
HC = colors.HexColor
INDIGO = HC("#1E1B5E")
INDIGO2 = HC("#2D2A7B")
CYAN = HC("#27C4EE")
CYAN_D = HC("#0A7E9E")
MAGENTA = HC("#C63BF0")
MAG_D = HC("#9A1FC4")
AMBER = HC("#FFB43A")
AMBER_D = HC("#A8620A")
GREEN = HC("#4BE08A")
GREEN_D = HC("#12A35A")
INK = HC("#1B1D2E")
DIM = HC("#5A6079")
ZEBRA = HC("#F1F3FB")
GRID = HC("#D5D9EC")
TINT_CYAN = HC("#E6F8FD")
TINT_MAG = HC("#F7E9FD")
TINT_AMB = HC("#FFF4DE")
TINT_IND = HC("#E9E8FA")
# the plug-in's dark UI colours (used by the diagrams)
UI_BG = HC("#0B0D14")
UI_PANEL = HC("#151925")
UI_HI = HC("#1E2333")
UI_LINE = HC("#2C3350")
UI_TEXT = HC("#E9EDF9")
UI_DIM = HC("#8A93B0")

TITLE = "Massive PSXL"
FOOT = "Massive PSXL - Phil S Audio"
VERSION = "1.0.0"

# frame width (points); updated by make_doc()
FW = 504.0


def _ps(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13.6, textColor=INK, spaceAfter=5, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "body": _ps("body"),
    "small": _ps("small", fontSize=8.2, leading=11, textColor=DIM),
    "h2": _ps("h2", fontName="Helvetica-Bold", fontSize=14.5, leading=18, textColor=MAG_D, spaceBefore=12, spaceAfter=5, keepWithNext=1),
    "h3": _ps("h3", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=CYAN_D, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "h4": _ps("h4", fontName="Helvetica-Bold", fontSize=9.5, leading=12.5, textColor=INDIGO2, spaceBefore=5, spaceAfter=2, keepWithNext=1),
    "bullet": _ps("bullet", leftIndent=14, bulletIndent=3, spaceAfter=2.5),
    "num": _ps("num", leftIndent=18, bulletIndent=0, spaceAfter=3),
    "cell": _ps("cell", fontSize=8.2, leading=10.6, spaceAfter=0),
    "cellb": _ps("cellb", fontName="Helvetica-Bold", fontSize=8.2, leading=10.6, spaceAfter=0),
    "cellh": _ps("cellh", fontName="Helvetica-Bold", fontSize=8.2, leading=10.6, textColor=colors.white, spaceAfter=0),
    "cell7": _ps("cell7", fontSize=7.6, leading=9.8, spaceAfter=0),
    "cellc": _ps("cellc", fontSize=8.2, leading=10.6, spaceAfter=0, alignment=TA_CENTER),
    "toc0": _ps("toc0", fontName="Helvetica-Bold", fontSize=10.5, leading=15, textColor=INDIGO, spaceBefore=5, spaceAfter=1),
    "toc1": _ps("toc1", fontSize=9, leading=12, leftIndent=16, textColor=INK, spaceAfter=0),
    "cap": _ps("cap", fontSize=8, leading=10.5, textColor=DIM, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8),
    "tag": _ps("tag", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=AMBER_D, spaceAfter=3),
    "goal": _ps("goal", fontName="Helvetica-Oblique", fontSize=10, leading=14, textColor=INDIGO2, spaceAfter=5),
}


# ------------------------------------------------------------------ flowables
class Banner(Flowable):
    """Chapter banner (registers itself in the table of contents)."""

    def __init__(self, num, title, kicker="", level=0):
        super().__init__()
        self.num, self.title, self.kicker = num, title, kicker
        self.toc_level = level
        self.toc_text = (f"{num}  " if num else "") + title
        self.hAvail = 56

    def wrap(self, aw, ah):
        self.w = aw
        return aw, self.hAvail + 10

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(INDIGO)
        c.roundRect(0, 6, self.w, self.hAvail, 7, stroke=0, fill=1)
        c.setFillColor(CYAN)
        c.rect(0, 6, 7, self.hAvail, stroke=0, fill=1)
        c.setFillColor(MAGENTA)
        c.rect(7, 6, 3, self.hAvail, stroke=0, fill=1)
        x = 24
        if self.num:
            c.setFillColor(CYAN)
            c.setFont("Helvetica-Bold", 30)
            c.drawString(x, 6 + 17, str(self.num))
            x += 24 + 18 * len(str(self.num))
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 21)
        c.drawString(x, 6 + 24, self.title)
        if self.kicker:
            c.setFillColor(HC("#B9BFF0"))
            c.setFont("Helvetica", 9)
            c.drawString(x, 6 + 9, self.kicker)
        c.restoreState()


class Heading(Paragraph):
    """H2/H3 paragraph that also feeds the table of contents."""

    def __init__(self, text, style, level, plain=None):
        super().__init__(text, style)
        self.toc_level = level
        self.toc_text = plain or text


class HRule(Flowable):
    def __init__(self, color=GRID, thick=0.8, space=4):
        super().__init__()
        self.color, self.thick, self.space = color, thick, space

    def wrap(self, aw, ah):
        self.w = aw
        return aw, self.space * 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.space, self.w, self.space)


# ------------------------------------------------------------------ document
class PSDoc(BaseDocTemplate):
    def __init__(self, filename, doc_title, pagesize=letter, cover=None, part_bg=None, **kw):
        global FW
        super().__init__(filename, pagesize=pagesize, title=doc_title, author="Phil S Audio",
                         subject="Massive PSXL", **kw)
        self.doc_title = doc_title
        self.cover_cb = cover
        self.part_cb = part_bg
        w, h = pagesize
        lm = rm = 54 if w < 700 else 40
        tm, bm = 60, 48
        FW = w - lm - rm
        self.lm, self.pw, self.ph = lm, w, h
        self.chapter = ""
        body = Frame(lm, bm, w - lm - rm, h - tm - bm, id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        full = Frame(0, 0, w, h, id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        part = Frame(lm + 20, h * 0.30, w - 2 * lm - 40, h * 0.40, id="part", leftPadding=0, rightPadding=0)
        self.addPageTemplates([
            PageTemplate("cover", frames=[full], onPage=self._cover),
            PageTemplate("body", frames=[body], onPageEnd=self._page),
            PageTemplate("part", frames=[part], onPage=self._part),
        ])

    def _cover(self, c, doc):
        if self.cover_cb:
            c.saveState()
            self.cover_cb(c, self)
            c.restoreState()

    def _part(self, c, doc):
        c.saveState()
        c.setFillColor(UI_BG)
        c.rect(0, 0, self.pw, self.ph, stroke=0, fill=1)
        c.setFillColor(INDIGO)
        c.rect(0, self.ph * 0.62, self.pw, self.ph * 0.38, stroke=0, fill=1)
        c.setFillColor(CYAN); c.rect(0, self.ph * 0.62 - 6, self.pw / 3, 6, stroke=0, fill=1)
        c.setFillColor(MAGENTA); c.rect(self.pw / 3, self.ph * 0.62 - 6, self.pw / 3, 6, stroke=0, fill=1)
        c.setFillColor(AMBER); c.rect(2 * self.pw / 3, self.ph * 0.62 - 6, self.pw / 3, 6, stroke=0, fill=1)
        c.restoreState()

    def _page(self, c, doc):
        c.saveState()
        w, h = self.pw, self.ph
        c.setStrokeColor(CYAN)
        c.setLineWidth(1.2)
        c.line(self.lm, h - 40, w - self.lm, h - 40)
        c.setFont("Helvetica-Bold", 8.2)
        c.setFillColor(INDIGO2)
        c.drawString(self.lm, h - 35, FOOT)
        c.setFont("Helvetica", 8.2)
        c.setFillColor(DIM)
        c.drawRightString(w - self.lm, h - 35, self.chapter or self.doc_title)
        c.setStrokeColor(GRID)
        c.setLineWidth(0.6)
        c.line(self.lm, 38, w - self.lm, 38)
        c.setFont("Helvetica", 8)
        c.setFillColor(DIM)
        c.drawString(self.lm, 26, f"{self.doc_title}  |  Version {VERSION}")
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(INDIGO2)
        c.drawRightString(w - self.lm, 26, f"Page {doc.page}")
        c.restoreState()

    def afterFlowable(self, f):
        lvl = getattr(f, "toc_level", None)
        if lvl is None:
            return
        key = "h%d" % id(f)
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(f.toc_text.replace("<b>", "").replace("</b>", ""), key, level=lvl, closed=(lvl > 0))
        if lvl == 0:
            self.chapter = f.toc_text
        self.notify("TOCEntry", (lvl, f.toc_text, self.page, key))


def make_toc(max_level=1):
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"]][: max_level + 1]
    toc.dotsMinLevel = 0
    toc.rightColumnWidth = 30
    return toc


# ------------------------------------------------------------------ content helpers
def P(text, style="body"):
    return Paragraph(text, S[style] if isinstance(style, str) else style)


def H2(text):
    return Heading(text, S["h2"], 1)


def H3(text):
    return Paragraph(text, S["h3"])


def H4(text):
    return Paragraph(text, S["h4"])


def bullets(items, style="bullet"):
    return [Paragraph(t, S[style], bulletText="•") for t in items]


def numbered(items, start=1):
    return [Paragraph(t, S["num"], bulletText=f"{i}.") for i, t in enumerate(items, start)]


def cap(text):
    return Paragraph(text, S["cap"])


def callout(kind, text, width=None):
    spec = {
        "tip": ("TIP", CYAN, TINT_CYAN, CYAN_D),
        "note": ("NOTE", INDIGO2, TINT_IND, INDIGO2),
        "warn": ("IMPORTANT", MAGENTA, TINT_MAG, MAG_D),
        "start": ("STARTING POINT", AMBER, TINT_AMB, AMBER_D),
    }[kind]
    label, bar, bg, txt = spec
    st = ParagraphStyle("callout", parent=S["body"], fontSize=9, leading=12.5, spaceAfter=0)
    body = Paragraph(f'<font name="Helvetica-Bold" color="{txt.hexval().replace("0x", "#")}">{label}.</font> {text}', st)
    t = Table([[body]], colWidths=[(width or FW) - 6])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 4, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    wrapper = Table([[t]], colWidths=[width or FW])
    wrapper.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return wrapper


def tbl(rows, widths, header=True, font="cell", zebra=True, repeat=True, first_bold=False, head_color=INDIGO2, align_center=()):
    """Table with word-wrapped Paragraph cells. widths = relative weights."""
    tot = float(sum(widths))
    cw = [FW * w / tot for w in widths]
    data = []
    for ri, r in enumerate(rows):
        row = []
        for ci, cell in enumerate(r):
            if isinstance(cell, (Flowable, Table)) or (isinstance(cell, list)):
                row.append(cell)
                continue
            if header and ri == 0:
                st = S["cellh"]
            elif first_bold and ci == 0:
                st = S["cellb"]
            elif ci in align_center:
                st = S["cellc"]
            else:
                st = S[font]
            row.append(Paragraph(str(cell), st))
        data.append(row)
    t = Table(data, colWidths=cw, repeatRows=1 if (header and repeat) else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, GRID),
        ("BOX", (0, 0), (-1, -1), 0.6, GRID),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), head_color), ("LINEBELOW", (0, 0), (-1, 0), 1.2, CYAN)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if (i % 2) == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(cmds))
    return t


def section_header_row(title, ncols, color=INDIGO2):
    return (title,) + ("",) * (ncols - 1)


def kv_table(rows, widths=(1.2, 3), head=("Parameter", "Value")):
    return tbl([list(head)] + [list(r) for r in rows], list(widths), first_bold=True)


def spacer(h=6):
    return Spacer(1, h)


# ------------------------------------------------------------------ drawing helpers
def _s(d, x, y, text, size=8, color=UI_TEXT, anchor="start", bold=False):
    d.add(String(x, y, text, fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size, fillColor=color, textAnchor=anchor))


def _rr(d, x, y, w, h, fill=None, stroke=None, sw=0.8, r=3):
    d.add(Rect(x, y, w, h, rx=r, ry=r, fillColor=fill, strokeColor=stroke, strokeWidth=sw if stroke else 0))


def _bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts += [x, y]
    return pts


NODE_NAMES = ["Osc 1", "Osc 2", "Noise", "Filter 1", "Filter 2", "Insert", "Out"]
NODE_COLS = [CYAN, CYAN, GREEN, MAGENTA, MAGENTA, AMBER, UI_TEXT]
NODE_SUB = ["wavetable", "wavetable", "noise", "filter", "filter", "waveshaper", "stereo amp"]


def node_diagram(width, height, wires, title=None, compact=False, subs=True, active=None):
    """Draws the routing node editor schematic. wires = list of (src_idx, dst_idx_node)."""
    d = Drawing(width, height)
    _rr(d, 0, 0, width, height, fill=UI_PANEL, stroke=UI_LINE, r=6)
    cx = [0.10, 0.10, 0.10, 0.32, 0.54, 0.74, 0.91]
    cy = [0.22, 0.50, 0.78, 0.34, 0.66, 0.50, 0.50]
    nw = max(34.0, min(width * 0.13, 70.0))
    nh = 16.0 if compact else 30.0
    centres = []
    for i in range(7):
        centres.append((cx[i] * width, height - cy[i] * height * 0.86 - (14 if title else 0) * 0 - 4))
    # wires first
    for (s, dn) in wires:
        a = (centres[s][0] + nw / 2, centres[s][1])
        b = (centres[dn][0] - nw / 2, centres[dn][1])
        dx = max(14.0, abs(b[0] - a[0]) * 0.5)
        pts = _bezier(a, (a[0] + dx, a[1]), (b[0] - dx, b[1]), b)
        col = NODE_COLS[s] if s != 6 else CYAN
        d.add(PolyLine(pts, strokeColor=col, strokeWidth=1.8 if not compact else 1.2, strokeOpacity=0.9))
    for i, (x, y) in enumerate(centres):
        _rr(d, x - nw / 2, y - nh / 2, nw, nh, fill=UI_HI, stroke=NODE_COLS[i], sw=1.1, r=4)
        _s(d, x - nw / 2 + 4, y + (1 if compact else 3), NODE_NAMES[i], size=6 if compact else 7.6, bold=True)
        if subs and not compact:
            _s(d, x - nw / 2 + 4, y - 9, NODE_SUB[i], size=5.8, color=UI_DIM)
        if i != 6:
            d.add(Circle(x + nw / 2, y, 2.6 if compact else 3.2, fillColor=UI_PANEL, strokeColor=NODE_COLS[i], strokeWidth=1))
        if i >= 3:
            d.add(Circle(x - nw / 2, y, 2.6 if compact else 3.2, fillColor=UI_PANEL, strokeColor=NODE_COLS[i], strokeWidth=1))
    if title:
        _s(d, 6, height - 10, title, size=6.6 if compact else 8, color=UI_DIM, bold=True)
    return d


def envelope_diagram(width=480, height=150):
    d = Drawing(width, height)
    _rr(d, 0, 0, width, height, fill=UI_PANEL, stroke=UI_LINE, r=6)
    x0, y0, w, h = 24, 34, width - 48, height - 62
    # time slots
    seg = [("Delay", 0.08), ("Attack", 0.10), ("Hold", 0.09), ("Decay", 0.22), ("Sustain", 0.21), ("Release", 0.30)]
    xs = [x0]
    for _, f in seg:
        xs.append(xs[-1] + f * w)
    sus = 0.55
    pts = [xs[0], y0, xs[1], y0, xs[2], y0 + h, xs[3], y0 + h]
    for i in range(1, 25):
        u = i / 24
        pts += [xs[3] + (xs[4] - xs[3]) * u, y0 + h * (sus + (1 - sus) * math.exp(-5 * u))]
    pts += [xs[5], y0 + h * sus]
    for i in range(1, 25):
        u = i / 24
        pts += [xs[5] + (xs[6] - xs[5]) * u, y0 + h * sus * math.exp(-5 * u)]
    for i in range(7):
        d.add(Line(xs[i], y0 - 4, xs[i], y0 + h + 6, strokeColor=UI_LINE, strokeWidth=0.6, strokeDashArray=[2, 2]))
    d.add(Polygon(pts + [xs[6], y0, xs[0], y0], fillColor=HC("#27C4EE"), fillOpacity=0.14, strokeColor=None))
    d.add(PolyLine(pts, strokeColor=CYAN, strokeWidth=2))
    for i, (name, _) in enumerate(seg):
        _s(d, (xs[i] + xs[i + 1]) / 2, 14, name, size=7.5, color=UI_TEXT, anchor="middle", bold=True)
    _s(d, xs[0], height - 14, "Key down", size=7, color=GREEN, bold=True)
    d.add(Line(xs[0], y0 - 4, xs[0], height - 20, strokeColor=GREEN, strokeWidth=1.2))
    d.add(Line(xs[5], y0 - 4, xs[5], height - 20, strokeColor=MAGENTA, strokeWidth=1.2))
    _s(d, xs[5], height - 14, "Key up", size=7, color=MAGENTA, bold=True)
    d.add(Line(x0 + w * 0.0, y0 + h * sus, xs[4] - 2, y0 + h * sus, strokeColor=AMBER, strokeWidth=0.6, strokeDashArray=[3, 2]))
    _s(d, xs[4] + 6, y0 + h * sus + 5, "Sustain level", size=6.5, color=AMBER)
    _s(d, xs[2] + 4, y0 + h + 4, "peak = Env Level", size=6.5, color=UI_DIM)
    return d


def lfo_shapes_diagram(width=500, height=88):
    names = ["Sine", "Triangle", "Saw Up", "Saw Down", "Square", "Sample & Hold", "Smooth Random"]
    d = Drawing(width, height)
    n = len(names)
    cw = width / n
    rnd = [0.35, -0.6, 0.8, -0.2, 0.55, -0.85]
    srnd = [0.3, 0.8, -0.5, 0.6, -0.8, 0.2, 0.5]
    for i, nm in enumerate(names):
        x0 = i * cw + 4
        w = cw - 8
        _rr(d, x0, 18, w, height - 20, fill=UI_PANEL, stroke=UI_LINE, r=4)
        pts = []
        N = 60
        for k in range(N + 1):
            t = k / N
            ph = (t * 2) % 1.0
            cyc = int(t * 2) if t < 1 else 1
            if i == 0: v = math.sin(2 * math.pi * ph)
            elif i == 1: v = 1 - 4 * abs(ph - 0.5)
            elif i == 2: v = 2 * ph - 1
            elif i == 3: v = 1 - 2 * ph
            elif i == 4: v = 1 if ph < 0.5 else -1
            elif i == 5: v = rnd[min(5, int(t * 6))]
            else:
                x = t * 6; j = int(min(5, x)); f = x - j; s = f * f * (3 - 2 * f)
                v = srnd[j] * (1 - s) + srnd[j + 1] * s
            pts += [x0 + 4 + (w - 8) * t, 18 + (height - 20) / 2 + v * (height - 20) * 0.38]
        d.add(PolyLine(pts, strokeColor=CYAN, strokeWidth=1.5))
        _s(d, x0 + w / 2, 6, nm, size=6.4, color=INK, anchor="middle", bold=True)
    return d


def performer_diagram(width=480, height=130, steps=8, vals=None):
    d = Drawing(width, height)
    _rr(d, 0, 0, width, height, fill=UI_PANEL, stroke=UI_LINE, r=6)
    vals = vals or [0.0, 0.25, 0.58, 1.0, 0.58, 0.25, 0.9, 0.4] + [0.5] * 8
    bx, by, bw, bh = 12, 24, width - 24, height - 44
    cw = bw / 16
    for i in range(16):
        act = i < steps
        _rr(d, bx + i * cw + 2, by, cw - 4, bh, fill=HC("#30385A") if act else HC("#222840"), r=2)
        hh = bh * vals[i]
        _rr(d, bx + i * cw + 2, by, cw - 4, max(hh, 0.1), fill=AMBER if act else HC("#7a5a1c"), r=2)
        _s(d, bx + i * cw + cw / 2, by - 11, str(i + 1), size=6.5, color=UI_DIM, anchor="middle")
    # playhead
    px = bx + 3 * cw
    d.add(Rect(px + 2, by, cw - 4, bh, fillColor=None, strokeColor=UI_TEXT, strokeWidth=1.4, rx=2, ry=2))
    _s(d, px + cw / 2, by + bh + 6, "playing step", size=6.5, color=UI_TEXT, anchor="middle")
    d.add(Line(bx + steps * cw, by - 4, bx + steps * cw, by + bh + 4, strokeColor=MAGENTA, strokeWidth=1.3, strokeDashArray=[3, 2]))
    _s(d, bx + steps * cw + 4, by + bh - 4, f"Steps = {steps}: the loop ends here", size=6.8, color=MAGENTA, bold=True)
    _s(d, width - 12, height - 12, "bar height = modulation value 0..1", size=6.8, color=UI_DIM, anchor="end")
    return d


def fx_chain_diagram(width=504, height=110):
    d = Drawing(width, height)
    _rr(d, 0, 0, width, height, fill=UI_PANEL, stroke=UI_LINE, r=6)
    _s(d, 8, height - 11, "PER VOICE (up to 16 voices)", size=6.8, color=UI_DIM, bold=True)
    voice = [("Osc 1 / 2\nNoise", CYAN), ("Filter 1", MAGENTA), ("Filter 2", MAGENTA), ("Insert", AMBER), ("Amp\npan + env", UI_TEXT)]
    bw, bh = 56, 26
    gap = (width - 16 - 5 * bw) / 4
    for i, (nm, col) in enumerate(voice):
        x = 8 + i * (bw + gap)
        _rr(d, x, height - 48, bw, bh, fill=UI_HI, stroke=col, sw=1.1, r=4)
        for k, ln in enumerate(nm.split("\n")):
            _s(d, x + bw / 2, height - 31 + (3 if "\n" in nm else 0) - 8 * k, ln, size=6.8, anchor="middle", bold=True)
        if i < 4:
            d.add(Line(x + bw, height - 35, x + bw + gap, height - 35, strokeColor=UI_DIM, strokeWidth=1))
            d.add(Polygon([x + bw + gap, height - 35, x + bw + gap - 4, height - 33, x + bw + gap - 4, height - 37], fillColor=UI_DIM, strokeColor=None))
    _s(d, 8, 38, "MASTER (stereo, after all voices are summed)", size=6.8, color=UI_DIM, bold=True)
    fx = [("EQ", CYAN), ("Distortion", CYAN), ("Chorus", CYAN), ("Delay", CYAN), ("Reverb", CYAN), ("Volume", UI_TEXT)]
    bw2 = 62
    gap2 = (width - 16 - 6 * bw2) / 5
    for i, (nm, col) in enumerate(fx):
        x = 8 + i * (bw2 + gap2)
        _rr(d, x, 6, bw2, 22, fill=UI_HI, stroke=col, sw=1.1, r=4)
        _s(d, x + bw2 / 2, 14, nm, size=7.2, anchor="middle", bold=True)
        if i < 5:
            d.add(Line(x + bw2, 17, x + bw2 + gap2, 17, strokeColor=UI_DIM, strokeWidth=1))
            d.add(Polygon([x + bw2 + gap2, 17, x + bw2 + gap2 - 4, 19, x + bw2 + gap2 - 4, 15], fillColor=UI_DIM, strokeColor=None))
    return d


def mod_assign_diagram(width=504, height=120):
    d = Drawing(width, height)
    _rr(d, 0, 0, width, height, fill=UI_PANEL, stroke=UI_LINE, r=6)

    def chip(x, y, label, col):
        _rr(d, x, y, 74, 20, fill=colors.Color(col.red, col.green, col.blue, 0.25), stroke=col, r=5)
        d.add(Circle(x + 11, y + 10, 4.2, fillColor=None, strokeColor=col, strokeWidth=1))
        d.add(Line(x + 11, y + 3, x + 11, y + 17, strokeColor=col, strokeWidth=0.8))
        d.add(Line(x + 4, y + 10, x + 18, y + 10, strokeColor=col, strokeWidth=0.8))
        _s(d, x + 24, y + 6.5, label, size=7.4, bold=True)

    chip(18, 78, "Mod 2", CYAN)
    chip(18, 48, "Macro 1", MAGENTA)
    chip(18, 18, "Perf 1", AMBER)
    # drag arrow
    d.add(PolyLine([100, 88, 190, 70, 262, 66], strokeColor=UI_DIM, strokeWidth=1.2, strokeDashArray=[4, 3]))
    d.add(PolyLine([100, 58, 190, 62, 262, 62], strokeColor=UI_DIM, strokeWidth=1.2, strokeDashArray=[4, 3]))
    d.add(PolyLine([100, 28, 190, 50, 262, 60], strokeColor=UI_DIM, strokeWidth=1.2, strokeDashArray=[4, 3]))
    _s(d, 170, 100, "drag the chip onto any knob", size=7.4, color=UI_DIM, anchor="middle", bold=True)
    # knob
    kx, ky, r = 300, 56, 30
    d.add(Circle(kx, ky, r * 0.78, fillColor=HC("#222840"), strokeColor=None))
    a0, a1 = math.radians(225), math.radians(-45)

    def arc(frm, to, rad, col, sw):
        pts = []
        for i in range(31):
            a = frm + (to - frm) * i / 30
            pts += [kx + rad * math.cos(a), ky + rad * math.sin(a)]
        d.add(PolyLine(pts, strokeColor=col, strokeWidth=sw))

    arc(a0, a1, r - 1.5, HC("#30385A"), 3)
    arc(a0, a0 + (a1 - a0) * 0.45, r - 1.5, CYAN, 3)
    arc(a0 + (a1 - a0) * 0.45, a0 + (a1 - a0) * 0.75, r + 3, MAGENTA, 2.2)
    pa = a0 + (a1 - a0) * 0.45
    d.add(Line(kx + 8 * math.cos(pa), ky + 8 * math.sin(pa), kx + 22 * math.cos(pa), ky + 22 * math.sin(pa), strokeColor=UI_TEXT, strokeWidth=2))
    la = a0 + (a1 - a0) * 0.62
    d.add(Circle(kx + (r - 1.5) * math.cos(la), ky + (r - 1.5) * math.sin(la), 2.4, fillColor=UI_TEXT, strokeColor=None))
    _s(d, kx, ky - r - 14, "Filter 1 Cutoff", size=7.4, anchor="middle", color=UI_DIM)
    _s(d, 354, 80, "coloured ring = modulation range", size=7.2, color=MAGENTA, bold=True)
    _s(d, 354, 66, "white dot = live modulated value", size=7.2, color=UI_TEXT)
    _s(d, 354, 52, "default amount = +50% of the knob travel", size=7.2, color=UI_DIM)
    _s(d, 354, 38, "right-click the knob: Edit amount / Remove", size=7.2, color=UI_DIM)
    _s(d, 354, 24, "negative amounts invert the effect", size=7.2, color=UI_DIM)
    return d


def ui_layout_diagram(width=504, keys=True):
    """Schematic of the 1260 x 700 (+150 keyboard) editor with numbered callouts."""
    s = width / 1260.0
    H = 850 if keys else 700
    d = Drawing(width, H * s)

    def Y(y, h=0):
        return (H - y - h) * s

    def box(x, y, w, h, label=None, col=UI_LINE, fill=UI_PANEL, size=6.4, lc=UI_DIM):
        _rr(d, x * s, Y(y, h), w * s, h * s, fill=fill, stroke=col, r=3)
        if label:
            _s(d, (x + 6) * s, Y(y, h) + (h - 14) * s, label, size=size, color=lc, bold=True)

    def badge(n, x, y):
        d.add(Circle(x * s, Y(y), 6.2, fillColor=MAGENTA, strokeColor=colors.white, strokeWidth=0.8))
        _s(d, x * s, Y(y) - 2.6, str(n), size=7.4, color=colors.white, anchor="middle", bold=True)

    _rr(d, 0, 0, width, H * s, fill=UI_BG, stroke=UI_LINE, r=6)
    # top bar
    _rr(d, 0, Y(0, 44), width, 44 * s, fill=UI_PANEL, stroke=UI_LINE, r=0)
    _s(d, 48 * s, Y(0, 44) + 22 * s, "MASSIVE", size=8, bold=True)
    _s(d, 128 * s, Y(0, 44) + 22 * s, "PSXL", size=8, color=CYAN, bold=True)
    for x, w, t in [(212, 52, "Menu"), (276, 140, "Edit | Browse"), (440, 30, "<"), (474, 320, "preset name"), (798, 30, ">"),
                    (1260 - 284, 52, "Undo"), (1260 - 228, 52, "Redo"), (1260 - 172, 64, "Light"), (1260 - 100, 64, "Keys")]:
        _rr(d, x * s, Y(8, 28), w * s, 28 * s, fill=UI_HI, stroke=UI_LINE, r=3)
        _s(d, (x + w / 2) * s, Y(8, 28) + 9 * s, t, size=5.6, anchor="middle")
    d.add(Circle((1260 - 318) * s, Y(22), 9 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=1))
    badge(1, 22, 22); badge(2, 238, 2); badge(3, 634, 2); badge(4, 1160, 2)
    # synth row
    xs = [6]
    wd = [100, 342, 96, 226, 124, 92, 232]
    lab = ["PITCH", "", "NOISE", "", "INSERT", "AMP", ""]
    x = 6
    boxes = []
    for w_, l in zip(wd, lab):
        box(x, 48, w_, 270, l)
        boxes.append((x, w_))
        x += w_ + 6
    # osc details
    ox, ow = boxes[1]
    _rr(d, (ox + 10) * s, Y(56, 22), (ow - 20) * s, 22 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    _s(d, (ox + ow / 2) * s, Y(56, 22) + 7 * s, "Osc 1 | Osc 2", size=5.8, anchor="middle")
    _rr(d, (ox + 10) * s, Y(82, 104), (ow - 20) * s, 104 * s, fill=UI_HI, stroke=CYAN, r=3)
    for k in range(7):
        pts = []
        for i in range(41):
            t = i / 40
            pts += [(ox + 30 + (ow - 90) * t + k * 6) * s, Y(100 + k * 9) + math.sin(t * 6.28 * (1 + k * 0.1)) * 5 * s]
        d.add(PolyLine(pts, strokeColor=CYAN if k == 3 else UI_DIM, strokeWidth=0.8))
    _s(d, (ox + ow / 2) * s, Y(194, 24) + 8 * s, "wavetable selector  <  >  +", size=5.8, anchor="middle")
    for i in range(8):
        d.add(Circle((ox + 28 + i * 40.5) * s, Y(260), 8 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=0.9))
    _s(d, (ox + ow / 2) * s, Y(290, 10) + 2 * s, "Pos  Pitch  Fine  Level  Unison  Detune  PhaseMod  Fold", size=5.2, color=UI_DIM, anchor="middle")
    px, pw_ = boxes[0]
    d.add(Circle((px + 50) * s, Y(76), 16 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=1))
    d.add(Circle((px + 50) * s, Y(165), 10 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=1))
    _rr(d, (px + 10) * s, Y(206, 24), 80 * s, 24 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    _s(d, (px + 50) * s, Y(206, 24) + 8 * s, "Poly/Mono", size=5.4, anchor="middle")
    _rr(d, (px + 10) * s, Y(236, 22), 80 * s, 22 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    _s(d, (px + 50) * s, Y(236, 22) + 7 * s, "Expo", size=5.4, anchor="middle")
    nx, nw_ = boxes[2]
    for yy in (74, 164):
        d.add(Circle((nx + 48) * s, Y(yy), 14 * s, fillColor=HC("#222840"), strokeColor=GREEN, strokeWidth=1))
    _rr(d, (nx + 8) * s, Y(222, 24), 80 * s, 24 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    fx_, fw_ = boxes[3]
    _rr(d, (fx_ + 10) * s, Y(56, 22), (fw_ - 20) * s, 22 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    _s(d, (fx_ + fw_ / 2) * s, Y(56, 22) + 7 * s, "Filter 1 | Filter 2", size=5.8, anchor="middle")
    _rr(d, (fx_ + 10) * s, Y(86, 24), (fw_ - 20) * s, 24 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    _s(d, (fx_ + fw_ / 2) * s, Y(86, 24) + 8 * s, "Model | Mode", size=5.8, anchor="middle")
    d.add(Circle((fx_ + fw_ / 2) * s, Y(170), 26 * s, fillColor=HC("#222840"), strokeColor=MAGENTA, strokeWidth=1.2))
    for i in range(3):
        d.add(Circle((fx_ + 40 + i * 73) * s, Y(250), 9 * s, fillColor=HC("#222840"), strokeColor=MAGENTA, strokeWidth=0.9))
    ix, iw = boxes[4]
    _rr(d, (ix + 10) * s, Y(76, 24), 104 * s, 24 * s, fill=UI_HI, stroke=UI_LINE, r=3)
    d.add(Circle((ix + 62) * s, Y(150), 20 * s, fillColor=HC("#222840"), strokeColor=AMBER, strokeWidth=1))
    d.add(Circle((ix + 62) * s, Y(240), 14 * s, fillColor=HC("#222840"), strokeColor=AMBER, strokeWidth=1))
    ax, aw_ = boxes[5]
    for yy in (68, 150, 232):
        d.add(Circle((ax + 46) * s, Y(yy), 12 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=1))
    gx, gw = boxes[6]
    _s(d, (gx + 12) * s, Y(56, 22) + 7 * s, "EQ  Delay  Verb  Chor  Dist", size=5.8)
    for i in range(7):
        d.add(Circle((gx + 28 + (i % 4) * 58) * s, Y(112 + (i // 4) * 84), 10 * s, fillColor=HC("#222840"), strokeColor=CYAN, strokeWidth=0.9))
    badge(5, boxes[0][0] + 86, 56); badge(6, ox + ow - 6, 52); badge(7, nx + 84, 56); badge(8, fx_ + fw_ - 6, 52)
    badge(9, ix + 110, 56); badge(10, ax + 78, 56); badge(11, gx + gw - 6, 52)
    # tab strip
    names = ["Voice", "Routing", "Amp Env"] + [f"Mod {i}" for i in range(2, 10)] + ["Perf 1", "Perf 2", "Perf 3"]
    tw = (1260 - 12) / len(names)
    for i, n in enumerate(names):
        _rr(d, (6 + i * tw + 1) * s, Y(322, 28), (tw - 2) * s, 26 * s, fill=UI_HI if i != 1 else HC("#1C3A4A"), stroke=UI_LINE if i != 1 else CYAN, r=3)
        _s(d, (6 + i * tw + tw / 2) * s, Y(322, 28) + 8 * s, n, size=5.4, anchor="middle", bold=(i == 1))
    badge(12, 1246, 322)
    # lower area: routing view
    _rr(d, 6 * s, Y(354, 274), 1248 * s, 274 * s, fill=UI_PANEL, stroke=UI_LINE, r=6)
    wires = [(0, 3), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6)]
    cxn = [0.10, 0.10, 0.10, 0.32, 0.54, 0.74, 0.91]
    cyn = [0.22, 0.50, 0.78, 0.34, 0.66, 0.50, 0.50]
    nwid = 130
    cen = [(6 + cxn[i] * 1248, 354 + cyn[i] * 274) for i in range(7)]
    for a, b in wires:
        p0 = ((cen[a][0] + nwid / 2) * s, Y(cen[a][1])); p1 = ((cen[b][0] - nwid / 2) * s, Y(cen[b][1]))
        dx = max(40, abs(p1[0] - p0[0]) / s * 0.5) * s
        d.add(PolyLine(_bezier(p0, (p0[0] + dx, p0[1]), (p1[0] - dx, p1[1]), p1), strokeColor=NODE_COLS[a], strokeWidth=1.1))
    for i, (cxx, cyy) in enumerate(cen):
        _rr(d, (cxx - nwid / 2) * s, Y(cyy - 27, 54), nwid * s, 54 * s, fill=UI_HI, stroke=NODE_COLS[i], r=4)
        _s(d, (cxx - nwid / 2 + 8) * s, Y(cyy - 27, 54) + 34 * s, NODE_NAMES[i], size=6, bold=True)
    _s(d, 620 * s, Y(354, 274) + 6 * s, "ROUTING VIEW (default lower tab)", size=5.6, color=UI_DIM, anchor="middle", bold=True)
    # macro strip
    _rr(d, 6 * s, Y(632, 66), 1248 * s, 66 * s, fill=UI_PANEL, stroke=UI_LINE, r=6)
    for i, n in enumerate(["Pitch", "ModWhl", "AftTch", "Velocity", "KeyTrk", "Random"]):
        _rr(d, (12 + (i % 2) * 67) * s, Y(635 + (i // 2) * 21, 19), 65 * s, 19 * s, fill=HC("#173D2A"), stroke=GREEN, r=3)
        _s(d, (46 + (i % 2) * 67) * s, Y(635 + (i // 2) * 21, 19) + 6 * s, n, size=4.8, anchor="middle")
    cw = (1248 - 12 - 134 - 8) / 16
    for i in range(16):
        kx = (6 + 6 + 134 + 8 + i * cw + cw / 2) * s
        d.add(Circle(kx, Y(652), 10 * s, fillColor=HC("#222840"), strokeColor=MAGENTA, strokeWidth=0.9))
        _rr(d, kx - 14 * s, Y(682, 14), 28 * s, 14 * s, fill=HC("#3a1d4a"), stroke=MAGENTA, r=3)
        _s(d, kx, Y(682, 14) + 4 * s, f"M{i + 1}", size=4.4, anchor="middle")
    badge(13, 142, 634); badge(14, 1244, 634)
    # keyboard
    if keys:
        _rr(d, 6 * s, Y(702, 144), 1248 * s, 144 * s, fill=UI_PANEL, stroke=UI_LINE, r=6)
        for i in range(2):
            _rr(d, (16 + i * 38) * s, Y(712, 100), 30 * s, 100 * s, fill=UI_HI, stroke=UI_LINE, r=3)
        _s(d, 31 * s, Y(822, 12) + 2 * s, "PITCH", size=4.8, anchor="middle")
        _s(d, 69 * s, Y(822, 12) + 2 * s, "MOD", size=4.8, anchor="middle")
        nk = 36
        kw = (1260 - 150) / nk
        for i in range(nk):
            _rr(d, (140 + i * kw) * s, Y(708, 134), (kw - 1) * s, 134 * s, fill=HC("#E9EDF9"), stroke=UI_LINE, sw=0.4, r=0)
        for i in range(nk):
            if i % 7 in (2, 6):
                continue
            _rr(d, (140 + i * kw + kw * 0.65) * s, Y(708, 80), kw * 0.7 * s, 80 * s, fill=HC("#12141C"), stroke=None, r=0)
        badge(15, 126, 712)
    return d


def keys_note():
    return None


# ------------------------------------------------------------------ cover
def make_cover(title, subtitle, tagline, kind="manual", extra=None):
    def draw(c, doc):
        w, h = doc.pw, doc.ph
        c.setFillColor(UI_BG)
        c.rect(0, 0, w, h, stroke=0, fill=1)
        splash = os.path.join(ART, "splash.png")
        if os.path.exists(splash):
            ih = w * 900 / 1600.0
            c.drawImage(splash, 0, h - ih, width=w, height=ih, mask="auto")
            c.setFillColor(colors.Color(0.04, 0.05, 0.08, 0.0))
        # lower block
        c.setFillColor(INDIGO)
        c.rect(0, 0, w, h - w * 900 / 1600.0, stroke=0, fill=1)
        y0 = h - w * 900 / 1600.0
        c.setFillColor(CYAN); c.rect(0, y0 - 4, w / 3, 4, stroke=0, fill=1)
        c.setFillColor(MAGENTA); c.rect(w / 3, y0 - 4, w / 3, 4, stroke=0, fill=1)
        c.setFillColor(AMBER); c.rect(2 * w / 3, y0 - 4, w / 3, 4, stroke=0, fill=1)
        icon = os.path.join(ART, "icon_512.png")
        mx = 54 if w < 700 else 60
        if os.path.exists(icon):
            c.drawImage(icon, mx, y0 - 4 - 22 - 86, width=86, height=86, mask="auto")
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 30 if w < 700 else 28)
        c.drawString(mx + 104, y0 - 4 - 22 - 34, title)
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(mx + 104, y0 - 4 - 22 - 56, subtitle)
        c.setFillColor(HC("#B9BFF0"))
        c.setFont("Helvetica", 10.5)
        c.drawString(mx + 104, y0 - 4 - 22 - 76, tagline)
        c.setFont("Helvetica", 9.5)
        yy = y0 - 4 - 22 - 86 - 30
        for ln in (extra or []):
            c.drawString(mx, yy, ln)
            yy -= 14
        c.setFillColor(HC("#8A93B0"))
        c.setFont("Helvetica", 8.5)
        c.drawString(mx, 34, f"Version {VERSION}   |   Phil S Audio   |   VST3, Audio Unit and Standalone for macOS (Apple Silicon)")
    return draw


def part_title(doc_story, part_no, title, blurb):
    from reportlab.platypus import NextPageTemplate as NPT
    pk = ParagraphStyle("pk", fontName="Helvetica-Bold", fontSize=13, textColor=CYAN, leading=16, spaceAfter=4)
    pt = ParagraphStyle("pt", fontName="Helvetica-Bold", fontSize=34, textColor=colors.white, leading=40, spaceAfter=10)
    pb = ParagraphStyle("pb", fontName="Helvetica", fontSize=12, textColor=HC("#B9BFF0"), leading=17)
    doc_story.append(NPT("part"))
    doc_story.append(PageBreak())
    doc_story.append(Paragraph(f"PART {part_no}", pk))
    big = Paragraph(title, pt)
    big.toc_level = 0
    big.toc_text = f"Part {part_no}: {title}"
    doc_story.append(big)
    doc_story.append(Paragraph(blurb, pb))
    doc_story.append(NPT("body"))
    doc_story.append(PageBreak())
