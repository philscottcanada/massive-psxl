#!/usr/bin/env python
"""
gen_art.py - procedural artwork generator for "Massive PSXL" (Phil S Audio).

Deterministic (seeded), re-runnable.  Everything is original and procedurally
drawn: a stacked, perspective "wavetable waterfall" of glowing ribbons that
morph from sine to saw, a bespoke geometric 'P' monogram, plus text rendered
with a system font.

Usage:
    python tools/gen_art.py            # generate everything
    python tools/gen_art.py icon bg    # only groups whose name matches

Requires: pillow, numpy, scipy.  Fonts: C:\\Windows\\Fonts\\bahnschrift.ttf
(falls back to segoeuib.ttf).

Output: <project>/Resources/art/...
"""
import os
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Resources" / "art"
NKS = OUT / "nks"
FONT_DIR = r"C:\Windows\Fonts"
SEED = 20260101
TAU = 2 * np.pi

# --------------------------------------------------------------------------
# basic helpers
# --------------------------------------------------------------------------


def rng_for(name):
    return np.random.default_rng(SEED + zlib.crc32(name.encode()))


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def grad(stops, t):
    """Piecewise-linear colour ramp. stops=[(pos,(r,g,b)),...]; returns (...,3)."""
    t = np.clip(np.asarray(t, float), 0, 1)
    pos = [s[0] for s in stops]
    return np.stack([np.interp(t, pos, [s[1][c] for s in stops]) for c in range(3)], -1)


# cyan -> violet -> magenta -> amber
PAL = [(0.0, (0.02, 0.88, 1.0)), (0.30, (0.42, 0.28, 1.0)),
       (0.58, (1.0, 0.12, 0.66)), (0.90, (1.0, 0.62, 0.05)), (1.0, (1.0, 0.78, 0.15))]


def resize_f(a, size, resample=Image.BICUBIC):
    """Resize float array (H,W[,C]) to size=(w,h)."""
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize(size, resample))
    return np.stack([resize_f(a[..., c], size, resample) for c in range(a.shape[2])], -1)


def box_down(a, ss):
    if ss == 1:
        return a
    H, W = a.shape[0] // ss, a.shape[1] // ss
    if a.ndim == 2:
        return a.reshape(H, ss, W, ss).mean((1, 3))
    return a.reshape(H, ss, W, ss, a.shape[2]).mean((1, 3))


def blur(a, sigma, wrap_x=False):
    """Gaussian blur; big sigmas are done on a downsampled copy for speed."""
    if sigma <= 0.3:
        return a
    H, W = a.shape[:2]
    f = 1 if wrap_x else int(max(1, sigma // 3))
    if f > 1:
        small = resize_f(a, (-(-W // f), -(-H // f)), Image.BOX)
    else:
        small = a
    s = sigma / f
    if a.ndim == 2:
        mode = ("constant", "wrap") if wrap_x else "constant"
        small = ndi.gaussian_filter(small, s, mode=mode)
    else:
        mode = ("constant", "wrap", "constant") if wrap_x else "constant"
        small = ndi.gaussian_filter(small, (s, s, 0), mode=mode)
    if f > 1:
        small = resize_f(small, (W, H), Image.BICUBIC)
    return small


def bloom(E, S, weights=((0.004, 0.50), (0.012, 0.40), (0.035, 0.32), (0.09, 0.22)), wrap_x=False, gain=1.0):
    """Additive multi-scale bloom. sigmas expressed as fractions of S."""
    out = E.copy()
    for sig, w in weights:
        out += blur(E, max(0.6, sig * S), wrap_x) * w * gain
    return out


def expose(bg, E, g=1.7):
    """Composite emissive light E over background bg (both float, 0..1 bg)."""
    return 1.0 - (1.0 - bg) * np.exp(-g * E)


def to_u8(a, rng=None, dither=True):
    a = np.clip(a, 0, 1) * 255.0
    if dither and rng is not None:
        a = a + rng.uniform(-0.5, 0.5, a.shape)
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def save_rgba_straight(path, rgb, alpha, rng=None):
    rgb = np.clip(rgb, 0, 1) * (alpha[..., None] > 0.002)
    out = np.dstack([to_u8(rgb, rng), to_u8(alpha, None, False)])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(path, optimize=True)


def save_rgb_opaque(path, rgb, rng=None):
    rgb8 = to_u8(rgb, rng)
    out = np.dstack([rgb8, np.full(rgb8.shape[:2], 255, np.uint8)])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(path, optimize=True)


def light_to_rgba(E, g=1.7):
    """Emissive light on transparent -> straight RGBA (screen-like)."""
    C = 1.0 - np.exp(-g * E)
    a = np.clip(1.0 - np.exp(-g * 1.8 * E.max(-1)), 0, 1)
    rgb = np.where(a[..., None] > 1e-4, C / np.maximum(a[..., None], 1e-4), 0)
    return np.clip(rgb, 0, 1), a


def over(dst_rgb, layer):
    """Composite premultiplied RGBA layer (H,W,4) over opaque rgb."""
    return layer[..., :3] + dst_rgb * (1 - layer[..., 3:4])


def sdf_round_rect(W, H, half, r):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    px = np.abs(xx + 0.5 - W / 2) - (half - r)
    py = np.abs(yy + 0.5 - H / 2) - (half - r)
    return np.hypot(np.maximum(px, 0), np.maximum(py, 0)) + np.minimum(np.maximum(px, py), 0) - r


def radial(W, H, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)


def stars(W, H, rng, n, ymax=1.0, strength=0.8):
    a = np.zeros((H, W), np.float32)
    xs = rng.integers(0, W, n)
    ys = rng.integers(0, int(H * ymax), n)
    br = rng.exponential(0.35, n).clip(0.05, 1.0) * strength
    a[ys, xs] = br
    a = blur(a, 0.7) * 2.2
    return a


# --------------------------------------------------------------------------
# waveform shapes
# --------------------------------------------------------------------------


def wave_morph(phi, m, K=8):
    """sine (m=0) -> saw (m=1) via additive harmonics, peak-normalised."""
    def raw(p):
        out = 0
        for k in range(1, K + 1):
            a = (1.0 - m) * (1.0 if k == 1 else 0.0) + m / k
            out = out + a * np.sin(k * p)
        return out
    g = np.linspace(0, TAU, 720)
    return raw(phi) / np.max(np.abs(raw(g)))


def shape_morph(cycles=1.75, drift=0.9, phase0=0.3, K=8, m0=0.0, m1=1.0):
    def f(xs, z):
        m = lerp(m0, m1, smoothstep(0.0, 1.0, z) ** 0.9)
        return wave_morph(xs * np.pi * cycles + phase0 + z * drift, m, K)
    return f


def shape_fat(cycles=1.0, drive=1.8):
    def f(xs, z):
        p = xs * np.pi * cycles + 0.4 + z * 0.6
        w = np.sin(p) + 0.28 * np.sin(2 * p + 1.0 + z)
        return np.tanh(drive * w) / np.tanh(drive)
    return f


def shape_pad(cycles=1.2):
    def f(xs, z):
        p = xs * np.pi * cycles
        w = np.sin(p + z * 1.3) + 0.55 * np.sin(1.9 * p + 2 * z + 0.7) + 0.3 * np.sin(3.1 * p - 3 * z)
        return w / 1.85
    return f


def shape_pluck(cycles=5.5):
    def f(xs, z):
        t = (xs + 1) / 2
        w = np.sin(t * TAU * cycles + z * 1.2) * np.exp(-2.6 * t)
        return np.clip(w * 1.2, -1, 1)
    return f


def shape_tri(cycles=2.5):
    def f(xs, z):
        p = xs * np.pi * cycles + 0.2 + z * 0.8
        tri = (2 / np.pi) * np.arcsin(np.sin(p))
        return 0.85 * tri + 0.15 * np.sin(3 * p + z)
    return f


def shape_kick():
    def f(xs, z):
        t = (xs + 1) / 2
        ph = 26.0 * (1 - np.exp(-5.0 * t)) + z * 0.9
        env = np.exp(-3.2 * t) * (1 - np.exp(-60 * t))
        return np.sin(ph) * env * 1.05
    return f


def shape_fm():
    def f(xs, z):
        p = xs * np.pi * 1.6 + z * 1.4
        return np.sin(p + (0.8 + 1.8 * z) * np.sin(2.3 * p + z))
    return f


def shape_steps(n=8, seed=7):
    pat = np.random.default_rng(seed).uniform(-1, 1, (64, n))

    def f(xs, z):
        t = (xs + 1) / 2 * n
        i = np.clip(np.floor(t).astype(int), 0, n - 1)
        fr = t - np.floor(t)
        zi = int(round(z * 63))
        v = pat[zi, i]
        vn = pat[zi, np.clip(i + 1, 0, n - 1)]
        k = smoothstep(0.80, 1.0, fr)
        return (v * (1 - k) + vn * k) * 0.9
    return f


# --------------------------------------------------------------------------
# ribbon waterfall
# --------------------------------------------------------------------------


def make_lines(cx, y0, y1, half, amp, shape, N, pal=PAL, pal_span=(0.0, 1.0), curve=1.5,
               env_p=2.4, M=520, bright=(0.30, 1.0), pal_xshift=0.10):
    """Build N perspective ribbon polylines, back (z=0) to front (z=1)."""
    lines = []
    for i in range(N):
        z = i / (N - 1) if N > 1 else 1.0
        xs = np.linspace(-1, 1, M)
        base = lerp(y0, y1, z ** curve)
        hw = lerp(half[0], half[1], z)
        a = lerp(amp[0], amp[1], z)
        w = shape(xs, z)
        env = np.clip(1 - np.abs(xs) ** env_p, 0, 1) ** 0.8
        px = cx + xs * hw
        py = base - a * w * env
        t = lerp(pal_span[0], pal_span[1], np.clip(z + pal_xshift * xs, 0, 1))
        col = grad(pal, t)
        edge = np.clip(1 - np.abs(xs) ** 3, 0, 1) ** 0.7
        b = lerp(bright[0], bright[1], z ** 0.8) * (0.15 + 0.85 * edge) * (0.84 + 0.30 * np.clip(w * env, 0, 1))
        lines.append(dict(x=px, y=py, col=col * b[:, None], z=z, base=base))
    return lines


def render_ribbons(W, H, lines, ss=2, width=(1.5, 4.0), fill_k=0.0, core=0.5, curtain=None):
    """Draw hidden-line ribbons. Returns (E float HxWx3, occ float HxW)."""
    img = Image.new("RGB", (W * ss, H * ss))
    occ = Image.new("L", (W * ss, H * ss))
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(occ)
    prev_max = -1e9
    for L in lines:
        pts = [(float(x) * ss, float(y) * ss) for x, y in zip(L["x"], L["y"])]
        yb = (max(float(L["y"].max()), prev_max) + 2) * ss
        prev_max = float(L["y"].max())
        poly = pts + [(pts[-1][0], yb), (pts[0][0], yb)]
        fc = tuple(int(c) for c in np.clip(L["col"].mean(0) * fill_k * 255 * 1.0, 0, 255))
        d.polygon(poly, fill=fc)
        do.polygon(poly, fill=255)
        w = lerp(width[0], width[1], L["z"]) * ss
        wi = max(1, int(round(w)))
        c8 = np.clip(L["col"] * 255, 0, 255).astype(np.uint8)
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=tuple(int(v) for v in c8[i]), width=wi)
            if wi >= 3:
                r = wi / 2.0
                x, y = pts[i]
                d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in c8[i]))
        do.line(pts, fill=255, width=wi, joint="curve")
        if core > 0:
            wc = max(1, int(round(w * core)))
            hot = np.clip((L["col"] * 0.45 + 0.55 * L["col"].max(-1, keepdims=True)) * 1.15, 0, 1)
            h8 = np.clip(hot * 255, 0, 255).astype(np.uint8)
            for i in range(len(pts) - 1):
                d.line([pts[i], pts[i + 1]], fill=tuple(int(v) for v in h8[i]), width=wc)
                if wc >= 3:
                    r = wc / 2.0
                    x, y = pts[i]
                    d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in h8[i]))
    E = box_down(np.asarray(img, np.float32) / 255.0, ss)
    O = box_down(np.asarray(occ, np.float32) / 255.0, ss)
    if curtain:  # soft light curtain falling below each ribbon
        L_px, gain = curtain
        a = float(np.exp(-1.0 / max(L_px, 1.0)))
        cur = lfilter([1.0], [1.0, -a], E, axis=0).astype(np.float32) * (1 - a) * gain
        E = E + 0.45 * np.tanh(cur / 0.45)
    return E, O


# --------------------------------------------------------------------------
# 'P' monogram
# --------------------------------------------------------------------------


def p_polys(cx, cy, h, shear=0.10):
    """Return (outer polygon, counter polygon, bbox) for the geometric P."""
    s, R, thick = 0.27, 0.335, 0.215
    cyb, cxb = R, 0.50
    r = R - thick

    def T(u, v):
        x = cx + (u - 0.415) * h + shear * (0.5 - v) * h
        y = cy + (v - 0.5) * h
        return (x, y)

    a = np.linspace(-np.pi / 2, np.pi / 2, 40)
    outer = [(0.0, 0.0)]
    outer += [(cxb + R * np.cos(t), cyb + R * np.sin(t)) for t in a]
    outer += [(s, 2 * R), (s, 0.935), (0.0, 1.0)]
    counter = [(s, cyb - r)]
    counter += [(cxb + r * np.cos(t), cyb + r * np.sin(t)) for t in a]
    counter += [(s, cyb + r)]
    po = [T(u, v) for u, v in outer]
    pc = [T(u, v) for u, v in counter]
    xs = [p[0] for p in po]
    ys = [p[1] for p in po]
    return po, pc, (min(xs), min(ys), max(xs), max(ys))


def p_mask(W, H, cx, cy, h, shear=0.10, ss=3):
    po, pc, bbox = p_polys(cx, cy, h, shear)
    im = Image.new("L", (W * ss, H * ss))
    d = ImageDraw.Draw(im)
    d.polygon([(x * ss, y * ss) for x, y in po], fill=255)
    d.polygon([(x * ss, y * ss) for x, y in pc], fill=0)
    return box_down(np.asarray(im, np.float32) / 255.0, ss), bbox


def p_shade(mask, bbox, S, simple=False):
    """Light-domain colour for the P: gradient + top-left bevel."""
    H, W = mask.shape
    x0, y0, x1, y1 = bbox
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.clip((yy - y0) / (y1 - y0), 0, 1)
    u = np.clip((xx - x0) / (x1 - x0), 0, 1)
    t = 0.65 * v + 0.35 * u
    base = grad([(0.0, (0.72, 0.96, 1.0)), (0.42, (0.62, 0.50, 1.0)), (1.0, (1.0, 0.36, 0.78))], t)
    hgt = blur(mask, max(1.0, 0.012 * S))
    gy, gx = np.gradient(hgt)
    sh = (-gx - gy) * (0.012 * S) * 1.4
    lit = np.clip(sh, 0, 1)[..., None]
    dark = np.clip(-sh, 0, 1)[..., None]
    edgef = np.clip(2.2 * (1 - blur(mask, max(1.0, 0.014 * S))), 0, 1)[..., None] * mask[..., None]
    inner = 0.62 if not simple else 0.9
    col = base * inner * (1 - 0.40 * dark) + lit * 0.45 + edgef * np.array([0.55, 0.60, 0.70]) * (0.8 if not simple else 0.4)
    return col


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------


def get_font(size, wght=700, wdth=100):
    path = os.path.join(FONT_DIR, "bahnschrift.ttf")
    try:
        f = ImageFont.truetype(path, size)
        f.set_variation_by_axes([wght, wdth])
        return f
    except Exception:
        return ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), size)


def adv(text, f, trk):
    return sum(f.getlength(c) for c in text) + trk * (len(text) - 1)


def draw_tracked(draw, x, base, text, f, trk_ss, ss):
    """x/base in final px; f is an ss-scaled font; trk_ss is tracking in ss px."""
    xs = x * ss
    for c in text:
        draw.text((xs, base * ss), c, font=f, fill=255, anchor="ls")
        xs += f.getlength(c) + trk_ss
    return xs / ss


def wordmark_layer(W, H, cx, cy, width_target, sub=True, ss=3, glow=1.0, sub_frac=0.21, theme="dark"):
    """Premultiplied RGBA (H,W,4): 'MASSIVE PSXL' + 'Phil S Audio'."""
    ref = 100.0
    trk_f = 0.17
    wM = adv("MASSIVE", get_font(int(ref), 520), trk_f * ref)
    wP = adv("PSXL", get_font(int(ref), 700), trk_f * ref)
    total = wM + 0.55 * ref + wP
    s = ref * width_target / total
    fM = get_font(max(1, int(round(s * ss))), 520)
    fP = get_font(max(1, int(round(s * ss))), 700)
    fS = get_font(max(1, int(round(s * sub_frac * ss))), 430)
    trk = trk_f * s
    wM = adv("MASSIVE", fM, trk * ss) / ss
    wP = adv("PSXL", fP, trk * ss) / ss
    total = wM + 0.55 * s + wP
    cap = 0.70 * s
    subh = s * sub_frac * 0.72 if sub else 0
    blockh = cap + (0.42 * s + subh if sub else 0)
    base = cy - blockh / 2 + cap
    x0 = cx - total / 2

    mM = Image.new("L", (W * ss, H * ss))
    mP = Image.new("L", (W * ss, H * ss))
    mS = Image.new("L", (W * ss, H * ss))
    draw_tracked(ImageDraw.Draw(mM), x0, base, "MASSIVE", fM, trk * ss, ss)
    xp = x0 + wM + 0.55 * s
    draw_tracked(ImageDraw.Draw(mP), xp, base, "PSXL", fP, trk * ss, ss)
    if sub:
        t = "Phil S Audio"
        ts = 0.42 * s * sub_frac * 2.2
        wS = adv(t, fS, ts * ss) / ss
        draw_tracked(ImageDraw.Draw(mS), cx - wS / 2, base + 0.42 * s + subh, t, fS, ts * ss, ss)
    M = box_down(np.asarray(mM, np.float32) / 255, ss)
    P = box_down(np.asarray(mP, np.float32) / 255, ss)
    S_ = box_down(np.asarray(mS, np.float32) / 255, ss)

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if theme == "dark":
        cM = grad([(0, (0.97, 0.97, 1.0)), (1, (0.76, 0.79, 0.96))], np.clip((yy - (base - cap)) / cap, 0, 1))
        cS = np.array([0.72, 0.70, 0.96], np.float32)
    else:
        cM = grad([(0, (0.10, 0.09, 0.26)), (1, (0.22, 0.21, 0.46))], np.clip((yy - (base - cap)) / cap, 0, 1))
        cS = np.array([0.30, 0.28, 0.55], np.float32)
        glow *= 0.45
    tP = np.clip((xx - xp) / wP, 0, 1)
    cP = grad(PAL, tP)
    cP = np.clip(cP * 0.85 + 0.15 * np.clip((yy - (base - cap)) / cap, 0, 1)[..., None] * 0 + 0.10, 0, 1)
    rgb = M[..., None] * cM + P[..., None] * cP + S_[..., None] * cS * 0.92
    a = np.clip(M + P + S_ * 0.92, 0, 1)
    # glow
    gp = blur(P[..., None] * cP, 0.11 * s) * 1.5 * glow + blur(P[..., None] * cP, 0.03 * s) * 0.5 * glow
    ga = np.clip(blur(P, 0.11 * s) * 1.5 * glow + blur(P, 0.03 * s) * 0.5 * glow, 0, 1)
    gm = blur(M[..., None] * cM, 0.05 * s) * 0.25 * glow
    gma = np.clip(blur(M, 0.05 * s) * 0.25 * glow, 0, 1)
    grgb = gp + gm
    ga = np.clip(ga + gma, 0, 1)
    out_rgb = rgb + grgb * (1 - a[..., None])
    out_a = np.clip(a + ga * (1 - a), 0, 1)
    out_rgb = np.minimum(out_rgb, out_a[..., None])
    return np.dstack([out_rgb, out_a])


def premult_to_straight(layer):
    a = layer[..., 3]
    rgb = np.where(a[..., None] > 1e-5, layer[..., :3] / np.maximum(a[..., None], 1e-5), 0)
    return np.clip(rgb, 0, 1), a


# --------------------------------------------------------------------------
# icon / mark
# --------------------------------------------------------------------------


def mark_light(S, simple=False, free=False):
    """Emissive light (S,S,3) of waterfall + P (no background)."""
    ss = 2 if S >= 512 else 3
    if not simple:
        N, y0, y1 = 20, 0.33 * S, 0.93 * S
        half = (0.30 * S, 0.54 * S)
        amp = (0.030 * S, 0.150 * S)
        width = (0.0030 * S, 0.0085 * S)
        P_h, P_cy, zsplit = 0.46 * S, 0.30 * S, 0.40
        cycles = 1.35
        cur = (0.030 * S, 1.5)
        if free:  # free-standing mark: keep everything inside the canvas
            y0, y1, half, amp = 0.30 * S, 0.84 * S, (0.26 * S, 0.45 * S), (0.028 * S, 0.125 * S)
            P_cy = 0.26 * S
    else:
        N, y0, y1 = 8, 0.40 * S, 0.93 * S
        half = (0.32 * S, 0.54 * S)
        amp = (0.04 * S, 0.15 * S)
        width = (0.020 * S, 0.042 * S)
        P_h, P_cy, zsplit = 0.56 * S, 0.34 * S, 0.55
        cycles = 1.15
        cur = (0.05 * S, 1.2)
    lines = make_lines(S / 2, y0, y1, half, amp, shape_morph(cycles=cycles, drift=0.7, K=7), N,
                       env_p=2.4, M=360 if simple else 560, bright=(0.50, 0.95), curve=1.5, pal_xshift=0.06)
    back = [l for l in lines if l["z"] < zsplit]
    front = [l for l in lines if l["z"] >= zsplit]
    core = 0.5 if not simple else 0.35
    Eb, _ = render_ribbons(S, S, back, ss, width, core=core, curtain=cur)
    Ef, Of = render_ribbons(S, S, front, ss, width, core=core, curtain=cur)
    Pm, bbox = p_mask(S, S, 0.5 * S, P_cy, P_h, shear=0.10, ss=3)
    halo = blur(Pm, 0.018 * S)
    Eb = Eb * (1 - 0.70 * np.clip(halo, 0, 1))[..., None]
    Pcol = p_shade(Pm, bbox, S, simple) * (0.80 if not simple else 0.85)
    E = Eb * (1 - Pm[..., None]) + Pcol * Pm[..., None]
    E = E * (1 - Of[..., None]) + Ef
    return bloom(E, S, gain=0.62 if not simple else 0.5)


def icon_bg(S, rng):
    rr = radial(S, S, 0.5 * S, 0.36 * S, 0.80 * S, 0.80 * S)
    t = np.clip(rr, 0, 1)[..., None]
    c0 = np.array([0.125, 0.085, 0.340])
    c1 = np.array([0.020, 0.016, 0.085])
    bg = c0 * (1 - t) ** 1.2 + c1 * (1 - (1 - t) ** 1.2)
    # warm horizon glow behind the waterfall
    g = np.exp(-radial(S, S, 0.5 * S, 0.80 * S, 0.62 * S, 0.24 * S) ** 2 * 1.4)[..., None]
    bg = bg + g * np.array([0.30, 0.055, 0.28]) * 0.55
    g2 = np.exp(-radial(S, S, 0.5 * S, 0.46 * S, 0.40 * S, 0.30 * S) ** 2 * 2.0)[..., None]
    bg = bg + g2 * np.array([0.10, 0.05, 0.30]) * 0.5
    st = stars(S, S, rng, int(S * S / 9000), 0.55, 0.9)
    bg = bg + st[..., None] * np.array([0.7, 0.8, 1.0]) * 0.55
    return np.clip(bg, 0, 1)


def render_icon(S, simple=False):
    rng = rng_for("icon%d%s" % (S, simple))
    bg = icon_bg(S, rng)
    E = mark_light(S, simple)
    img = expose(bg, E, 1.7)
    margin = (0.028 if S >= 64 else 0.02) * S
    half = S / 2 - margin
    sdf = sdf_round_rect(S, S, half, 0.22 * 2 * half)
    alpha = np.clip(0.5 - sdf, 0, 1)
    d_in = np.clip(-sdf, 0, None)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # glass sheen (upper ellipse)
    t = 1 - ((xx - 0.5 * S) / (0.95 * S)) ** 2 - ((yy + 0.22 * S) / (0.78 * S)) ** 2
    sheen = smoothstep(0.0, 0.7, np.clip(t, 0, 1)) * (0.12 if not simple else 0.07)
    img = img + (1 - img) * sheen[..., None] * np.array([0.85, 0.88, 1.0])
    # inner edge darkening for depth
    edge = 1 - smoothstep(0, 0.07 * S, d_in)
    img = img * (1 - 0.30 * edge[..., None])
    # bright rim, brighter at the top
    rim_w = max(0.9, 0.0055 * S)
    rim = np.exp(-(d_in / rim_w) ** 2) * (0.10 + 0.55 * (1 - yy / S) ** 2)
    img = img + (1 - img) * rim[..., None] * np.array([0.65, 0.7, 1.0]) * 0.8
    # soft outer feather inside the AA edge already via alpha
    rgb = np.clip(img, 0, 1)
    return rgb, alpha, rng


def save_icon(S, simple=False, master=None):
    rgb, alpha, rng = render_icon(S, simple)
    path = OUT / ("icon_%d.png" % S)
    save_rgba_straight(path, rgb, alpha, rng)
    return path


def save_icon_scaled(S, src_S, simple):
    rgb, alpha, rng = render_icon(src_S, simple)
    # premultiply for correct downsampling
    pm = np.dstack([rgb * alpha[..., None], alpha])
    pm = pm.astype(np.float32)
    chans = [Image.fromarray(pm[..., c].astype(np.float32), "F").resize((S, S), Image.LANCZOS) for c in range(4)]
    pm2 = np.stack([np.asarray(c) for c in chans], -1)
    a = np.clip(pm2[..., 3], 0, 1)
    rgbs = np.where(a[..., None] > 1e-4, pm2[..., :3] / np.maximum(a[..., None], 1e-4), 0)
    if S <= 32:  # light unsharp for tiny sizes
        bl = ndi.gaussian_filter(rgbs, (0.8, 0.8, 0))
        rgbs = rgbs + 0.45 * (rgbs - bl)
    path = OUT / ("icon_%d.png" % S)
    save_rgba_straight(path, rgbs, a, None)
    return path


def gen_icons():
    files = []
    # 1024 master + large derived sizes from full detail
    master_rgb, master_alpha, rng = render_icon(1024, False)
    p = OUT / "icon_1024.png"
    save_rgba_straight(p, master_rgb, master_alpha, rng)
    files.append(p)
    pm = np.dstack([master_rgb * master_alpha[..., None], master_alpha]).astype(np.float32)
    for S in (512, 256, 128):
        chans = [np.asarray(Image.fromarray(pm[..., c], "F").resize((S, S), Image.LANCZOS)) for c in range(4)]
        pm2 = np.stack(chans, -1)
        a = np.clip(pm2[..., 3], 0, 1)
        rgb = np.where(a[..., None] > 1e-4, pm2[..., :3] / np.maximum(a[..., None], 1e-4), 0)
        p = OUT / ("icon_%d.png" % S)
        save_rgba_straight(p, rgb, a, None)
        files.append(p)
    # simplified versions for small sizes
    for S in (64, 32, 16):
        files.append(save_icon_scaled(S, 512, True))
    return files


def gen_mark():
    S = 512
    E = mark_light(S, False, free=True)
    rgb, a = light_to_rgba(E)
    p = OUT / "logo_mark.png"
    save_rgba_straight(p, rgb, a, rng_for("mark"))
    return [p]


# --------------------------------------------------------------------------
# wordmark
# --------------------------------------------------------------------------


def gen_wordmark():
    W, H = 1200, 240
    files = []
    for theme, fn in (("dark", "logo_wordmark.png"), ("light", "logo_wordmark_light.png")):
        layer = wordmark_layer(W, H, W / 2, H / 2 - 2, 1040, sub=True, glow=0.9, theme=theme)
        rgb, a = premult_to_straight(layer)
        p = OUT / fn
        save_rgba_straight(p, rgb, a, None)
        files.append(p)
    return files


# --------------------------------------------------------------------------
# backgrounds
# --------------------------------------------------------------------------


def flow_lines(W, H, rng, n=15, ss=2):
    """Faint flowing sine->saw morph lines. Returns coverage (H,W) 0..1."""
    img = Image.new("L", (W * ss, H * ss))
    d = ImageDraw.Draw(img)
    xs = np.linspace(0, 1, 900)
    for i in range(n):
        z = i / (n - 1)
        yb = H * (0.12 + 0.78 * z) + rng.uniform(-0.03, 0.03) * H
        cyc = 1.3 + 0.5 * rng.random()
        phi = xs * TAU * cyc + rng.uniform(0, TAU)
        w = wave_morph(phi, 0.15 + 0.8 * z, 9)
        amp = H * (0.035 + 0.05 * z)
        y = yb + amp * w + (xs - 0.5) * H * 0.22 + H * 0.025 * np.sin(xs * TAU * 0.8 + i)
        fade = np.clip(np.sin(np.pi * xs), 0, 1) ** 0.6
        pts = [(x * W * ss, yy * ss) for x, yy in zip(xs, y)]
        val = int(255 * (0.55 + 0.45 * rng.random()))
        d.line(pts, fill=val, width=2 * ss, joint="curve")
        # modulate per-line by fade afterwards via global mask (approx using horizontal window)
    cov = box_down(np.asarray(img, np.float32) / 255.0, ss)
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    cov = cov * (np.clip(np.sin(np.pi * xx), 0, 1) ** 0.5)
    return np.clip(blur(cov, 1.1) * 1.0 + blur(cov, 7.0) * 2.2, 0, 1.5)


def gen_backgrounds():
    W, H = 2560, 1400
    files = []
    # dark
    rng = rng_for("bg_dark")
    r = np.clip(radial(W, H, 0.5 * W, 0.44 * H, 0.75 * W, 0.80 * W), 0, 1.4)
    base = np.array([0.098, 0.102, 0.165])
    edge = np.array([0.040, 0.042, 0.075])
    t = smoothstep(0, 1.15, r)[..., None]
    bg = base * (1 - t) + edge * t
    gl = np.exp(-radial(W, H, 0.5 * W, 1.05 * H, 0.7 * W, 0.35 * H) ** 2)[..., None]
    bg = bg + gl * np.array([0.05, 0.02, 0.08])
    fl = flow_lines(W, H, rng)
    bg = bg + fl[..., None] * np.array([0.10, 0.16, 0.34]) * 0.12
    grain = rng.normal(0, 1.7 / 255, (H, W, 1)) + rng.normal(0, 0.5 / 255, (H, W, 3))
    bg = bg + grain
    p = OUT / "bg_dark.png"
    save_rgb_opaque(p, bg, rng)
    files.append(p)
    # light
    rng = rng_for("bg_light")
    base = np.array([0.945, 0.948, 0.972])
    edge = np.array([0.855, 0.865, 0.920])
    bg = base * (1 - t) + edge * t
    gl = np.exp(-radial(W, H, 0.5 * W, -0.05 * H, 0.7 * W, 0.4 * H) ** 2)[..., None]
    bg = bg + gl * np.array([0.02, 0.02, 0.02])
    fl = flow_lines(W, H, rng)
    bg = bg - fl[..., None] * np.array([0.30, 0.26, 0.12]) * 0.10
    grain = rng.normal(0, 1.7 / 255, (H, W, 1)) + rng.normal(0, 0.5 / 255, (H, W, 3))
    bg = bg + grain
    p = OUT / "bg_light.png"
    save_rgb_opaque(p, bg, rng)
    files.append(p)
    return files


# --------------------------------------------------------------------------
# hero art (splash + NKS banners)
# --------------------------------------------------------------------------


def hero(W, H, name, text_w=0.60, text_cy=0.27, wf=(0.50, 0.985), N=34):
    rng = rng_for(name)
    # background
    rr = radial(W, H, 0.5 * W, 0.40 * H, 0.85 * W, 0.85 * W)
    t = np.clip(rr, 0, 1)[..., None]
    bg = np.array([0.105, 0.075, 0.300]) * (1 - t) ** 1.3 + np.array([0.018, 0.014, 0.075]) * (1 - (1 - t) ** 1.3)
    hz = np.exp(-radial(W, H, 0.5 * W, 0.60 * H, 0.60 * W, 0.20 * H) ** 2 * 1.3)[..., None]
    bg = bg + hz * np.array([0.34, 0.06, 0.32]) * 0.55
    hz2 = np.exp(-radial(W, H, 0.5 * W, 0.32 * H, 0.42 * W, 0.26 * H) ** 2 * 1.6)[..., None]
    bg = bg + hz2 * np.array([0.10, 0.05, 0.28]) * 0.45
    st = stars(W, H, rng, int(W * H / 5000), 0.5, 0.9)
    bg = bg + st[..., None] * np.array([0.7, 0.8, 1.0]) * 0.55

    k = W / 1600.0
    lines = make_lines(W / 2, wf[0] * H, wf[1] * H, (0.30 * W, 0.62 * W),
                       (0.010 * H, 0.105 * H), shape_morph(cycles=3.0, drift=1.0, phase0=0.5), N,
                       env_p=2.6, M=900, bright=(0.28, 1.0), curve=1.6)
    E, _ = render_ribbons(W, H, lines, 2, (1.1 * k, 3.4 * k), core=0.5)
    E = bloom(E, max(W, H) * 0.62, weights=((0.003, 0.5), (0.009, 0.4), (0.026, 0.3), (0.07, 0.22)))
    img = expose(bg, E, 1.6)
    wm = wordmark_layer(W, H, W / 2, text_cy * H, text_w * W, sub=True, glow=1.0)
    img = over(img, wm)
    vig = 1 - 0.28 * smoothstep(0.55, 1.25, radial(W, H, 0.5 * W, 0.5 * H, 0.5 * W, 0.5 * H))[..., None]
    img = img * vig
    return img, rng


def gen_splash():
    img, rng = hero(1600, 900, "splash", text_w=0.62, text_cy=0.25)
    p = OUT / "splash.png"
    save_rgb_opaque(p, img, rng)
    return [p]


# --------------------------------------------------------------------------
# NKS
# --------------------------------------------------------------------------

TILES = {
    "Bass": dict(pal=[(0, (0.25, 0.22, 1.0)), (0.5, (0.62, 0.18, 1.0)), (1, (0.98, 0.25, 0.85))],
                 bg=((0.075, 0.045, 0.24), (0.014, 0.010, 0.07)), shape=shape_fat(1.0, 1.9), N=9,
                 amp=(0.05, 0.15), width=(0.008, 0.020), glow=1.2),
    "Leads": dict(pal=[(0, (1.0, 0.22, 0.75)), (0.5, (1.0, 0.38, 0.50)), (1, (1.0, 0.70, 0.25))],
                  bg=((0.26, 0.045, 0.17), (0.07, 0.01, 0.05)), shape=shape_morph(2.6, 0.9, 0.5, 14, 0.55, 1.0), N=18,
                  amp=(0.03, 0.115), width=(0.003, 0.009), glow=1.0),
    "Pads": dict(pal=[(0, (0.10, 0.92, 0.80)), (0.5, (0.22, 0.72, 1.0)), (1, (0.75, 0.92, 1.0))],
                 bg=((0.02, 0.15, 0.20), (0.005, 0.04, 0.07)), shape=shape_pad(1.2), N=10,
                 amp=(0.05, 0.13), width=(0.012, 0.028), glow=1.7),
    "Plucks": dict(pal=[(0, (0.80, 1.0, 0.20)), (0.5, (0.22, 0.96, 0.45)), (1, (0.10, 0.85, 0.82))],
                   bg=((0.04, 0.20, 0.10), (0.008, 0.055, 0.03)), shape=shape_pluck(5.5), N=15,
                   amp=(0.04, 0.12), width=(0.003, 0.009), glow=1.0),
    "Keys": dict(pal=[(0, (1.0, 0.88, 0.32)), (0.5, (1.0, 0.66, 0.20)), (1, (1.0, 0.40, 0.40))],
                 bg=((0.22, 0.13, 0.04), (0.06, 0.03, 0.01)), shape=shape_tri(2.5), N=15,
                 amp=(0.035, 0.115), width=(0.003, 0.009), glow=1.0),
    "Drums": dict(pal=[(0, (1.0, 0.14, 0.22)), (0.5, (1.0, 0.40, 0.14)), (1, (1.0, 0.82, 0.28))],
                  bg=((0.24, 0.055, 0.05), (0.065, 0.012, 0.015)), shape=shape_kick(), N=15,
                  amp=(0.04, 0.125), width=(0.003, 0.010), glow=1.0),
    "FX": dict(pal=[(0, (0.95, 0.98, 1.0)), (1, (0.85, 0.92, 1.0))],
               bg=((0.10, 0.10, 0.14), (0.015, 0.015, 0.03)), shape=shape_fm(), N=14,
               amp=(0.03, 0.11), width=(0.003, 0.008), glow=0.9, chroma=6),
    "Sequence": dict(pal=[(0, (0.15, 0.55, 1.0)), (0.5, (0.42, 0.52, 1.0)), (1, (0.88, 0.93, 1.0))],
                     bg=((0.045, 0.10, 0.28), (0.008, 0.02, 0.08)), shape=shape_steps(8), N=12,
                     amp=(0.04, 0.12), width=(0.004, 0.012), glow=1.0),
}


def render_tile(name, cfg, S=512):
    rng = rng_for("tile" + name)
    hi, lo = [np.array(c) for c in cfg["bg"]]
    rr = np.clip(radial(S, S, 0.5 * S, 0.45 * S, 0.80 * S, 0.80 * S), 0, 1)[..., None]
    bg = hi * (1 - rr) ** 1.2 + lo * (1 - (1 - rr) ** 1.2)
    pc = grad(cfg["pal"], 0.5)
    # faint ring motif
    r = radial(S, S, 0.5 * S, 0.54 * S, 1, 1)
    ring = np.exp(-((r - 0.36 * S) / (0.006 * S)) ** 2)[..., None] * 0.18
    ring2 = np.exp(-((r - 0.45 * S) / (0.004 * S)) ** 2)[..., None] * 0.08
    bg = bg + (ring + ring2) * pc * 0.9
    gl = np.exp(-radial(S, S, 0.5 * S, 0.60 * S, 0.45 * S, 0.22 * S) ** 2 * 1.4)[..., None]
    bg = bg + gl * pc * 0.16
    st = stars(S, S, rng, int(S * S / 7000), 0.4, 0.7)
    bg = bg + st[..., None] * 0.35

    lines = make_lines(S / 2, 0.31 * S, 0.69 * S, (0.20 * S, 0.40 * S),
                       (cfg["amp"][0] * S * 0.9, cfg["amp"][1] * S * 0.85), cfg["shape"], cfg["N"], pal=cfg["pal"],
                       env_p=2.6, M=480, bright=(0.30, 1.0), curve=1.4)
    E, _ = render_ribbons(S, S, lines, 3, (cfg["width"][0] * S, cfg["width"][1] * S), core=0.28)
    if cfg.get("chroma"):
        c = cfg["chroma"]
        E = np.stack([np.roll(E[..., 0], -c, 1), np.roll(E[..., 1], 0, 1), np.roll(E[..., 2], c, 1)], -1)
        # tint channels so each ghost carries colour
        E = E * np.array([1.0, 1.0, 1.0])
        E[..., 0] = np.roll(E[..., 0], -2, 0)
        E[..., 2] = np.roll(E[..., 2], 2, 0)
    gscale = cfg.get("glow", 1.0)
    E = bloom(E, S, gain=0.8 * gscale)
    img = expose(bg, E, 1.5)

    # label
    f = get_font(int(0.078 * S * 3), 700)
    text = name.upper()
    trk = 0.22 * 0.078 * S
    w = adv(text, f, trk * 3) / 3
    m = Image.new("L", (S * 3, S * 3))
    draw_tracked(ImageDraw.Draw(m), S / 2 - w / 2, 0.915 * S, text, f, trk * 3, 3)
    M = box_down(np.asarray(m, np.float32) / 255, 3)
    lab = M[..., None] * np.array([0.95, 0.96, 1.0]) * 0.9
    glow = blur(M[..., None] * pc, 0.012 * S) * 1.3
    img = img + glow * 0.8
    img = img * (1 - M[..., None] * 0.9) + lab
    # thin accent rule above the label
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rule = np.exp(-((yy - 0.835 * S) / (0.0035 * S)) ** 2) * np.clip(1 - np.abs(xx - 0.5 * S) / (0.30 * S), 0, 1) ** 0.8
    img = img + rule[..., None] * pc * 0.55
    # vignette + inner rim
    vig = 1 - 0.30 * smoothstep(0.5, 1.25, radial(S, S, 0.5 * S, 0.5 * S, 0.5 * S, 0.5 * S))[..., None]
    img = img * vig
    d_in = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    rim = np.exp(-(d_in / (0.004 * S)) ** 2) * 0.35
    img = img + rim[..., None] * pc * 0.5
    img = img + rng.normal(0, 1.0 / 255, img.shape)
    return np.clip(img, 0, 1), rng


def gen_nks():
    files = []
    NKS.mkdir(parents=True, exist_ok=True)
    # plugin logo: mark on dark indigo square
    for S in (256, 128):
        rng = rng_for("nkslogo%d" % S)
        base = 512
        bg = icon_bg(base, rng_for("nkslogo_bg"))
        E = mark_light(base, False if S >= 256 else True) if False else mark_light(base, S < 256)
        img = expose(bg, E, 1.7)
        # full-bleed square (hardware screens are rectangular), light vignette
        vig = 1 - 0.25 * smoothstep(0.6, 1.3, radial(base, base, 0.5 * base, 0.5 * base, 0.5 * base, 0.5 * base))[..., None]
        img = np.clip(img * vig, 0, 1)
        im = Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGB").resize((S, S), Image.LANCZOS)
        out = np.dstack([np.asarray(im), np.full((S, S), 255, np.uint8)])
        p = NKS / ("plugin_logo_%d.png" % S)
        Image.fromarray(out, "RGBA").save(p, optimize=True)
        files.append(p)
    # banners
    img, rng = hero(1200, 600, "banner", text_w=0.66, text_cy=0.27, wf=(0.50, 0.985), N=30)
    p = NKS / "banner_1200x600.png"
    save_rgb_opaque(p, img, rng)
    files.append(p)
    im = Image.open(p).convert("RGB").resize((600, 300), Image.LANCZOS)
    p2 = NKS / "banner_600x300.png"
    Image.fromarray(np.dstack([np.asarray(im), np.full((300, 600), 255, np.uint8)]), "RGBA").save(p2, optimize=True)
    files.append(p2)
    # category tiles
    for name, cfg in TILES.items():
        img, rng = render_tile(name, cfg)
        p = NKS / ("category_%s.png" % name.lower())
        save_rgb_opaque(p, img, rng)
        files.append(p)
    readme = NKS / "README.txt"
    readme.write_text(
        "Massive PSXL - NKS artwork (provisional)\r\n"
        "=======================================\r\n\r\n"
        "IMPORTANT: The exact artwork sizes/formats required for NKS (Native Kontrol Standard)\r\n"
        "must be checked against Native Instruments' NKS Developer Kit / SDK documentation.\r\n"
        "The sizes used here are PROVISIONAL placeholders and may need to be regenerated:\r\n\r\n"
        "  plugin_logo_256.png / plugin_logo_128.png   plugin logo (square)\r\n"
        "  banner_1200x600.png / banner_600x300.png    hero banner with product name\r\n"
        "  category_*.png  (512x512)                   category tiles: bass, leads, pads, plucks,\r\n"
        "                                              keys, drums, fx, sequence\r\n\r\n"
        "All artwork is original, generated by tools/gen_art.py (deterministic, seeded).\r\n"
        "To change sizes, edit gen_nks() in that script and re-run it.\r\n", encoding="utf-8")
    files.append(readme)
    return files


# --------------------------------------------------------------------------
# waveform bar
# --------------------------------------------------------------------------


def gen_bar():
    W, H, ss = 2400, 48, 3
    n = W * ss
    xs = np.arange(n) / n  # periodic over [0,1)
    img = Image.new("RGB", (n, H * ss))
    d = ImageDraw.Draw(img)
    specs = [  # cycles, phase, amp, offset, brightness, width
        (6, 0.0, 0.30, 0.0, 0.55, 1.4),
        (6, 1.4, 0.28, 0.0, 0.70, 1.6),
        (8, 2.6, 0.24, 0.0, 0.85, 1.8),
        (10, 4.0, 0.20, 0.0, 0.70, 1.4),
        (6, 5.2, 0.26, 0.0, 1.00, 2.4),
    ]
    for k, (cyc, ph, amp, off, br, wd) in enumerate(specs):
        m = 0.5 - 0.5 * np.cos(TAU * (xs * 2 + 0.07 * k))  # periodic morph sine<->saw
        phi = TAU * cyc * xs + ph
        w = 0
        for h in range(1, 13):
            a = (1 - m) * (1.0 if h == 1 else 0.0) + m / h
            w = w + a * np.sin(h * phi)
        w = w / (1 + 0.8 * m)
        y = (H / 2 - amp * H * w) * ss
        tcol = 0.5 - 0.5 * np.cos(TAU * (xs + 0.12 * k))
        col = np.clip(grad(PAL, tcol) * br, 0, 1)
        c8 = (col * 255).astype(np.uint8)
        pts = np.stack([np.arange(n), y], 1)
        wi = max(1, int(round(wd * ss)))
        for i in range(0, n - 1, 2):
            d.line([tuple(pts[i]), tuple(pts[i + 2 if i + 2 < n else n - 1])],
                   fill=tuple(int(v) for v in c8[i]), width=wi)
    E = box_down(np.asarray(img, np.float32) / 255.0, ss)
    E = bloom(E, 48, weights=((0.04, 0.5), (0.12, 0.4), (0.3, 0.3)), wrap_x=True)
    rgb, a = light_to_rgba(E, 1.5)
    p = OUT / "waveform_bar.png"
    save_rgba_straight(p, rgb, a, rng_for("bar"))
    return [p]


# --------------------------------------------------------------------------

GROUPS = {
    "icon": gen_icons,
    "mark": gen_mark,
    "wordmark": gen_wordmark,
    "bg": gen_backgrounds,
    "splash": gen_splash,
    "nks": gen_nks,
    "bar": gen_bar,
}


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    sel = argv[1:] or list(GROUPS)
    produced = []
    for name, fn in GROUPS.items():
        if any(s in name for s in sel):
            print("generating", name, "...", flush=True)
            produced += fn()
    for p in produced:
        if str(p).endswith(".png"):
            with Image.open(p) as im:
                print("%-52s %dx%d %s" % (os.path.relpath(p, ROOT), im.width, im.height, im.mode))
        else:
            print(os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main(sys.argv)
