#!/usr/bin/env python3
"""Render draft 1 of the 90-second sample: the P1 animatic, locked to the George voice track.

Every frame is a pure function of time, drawn with pycairo and piped to ffmpeg. Shot slots
come from the plan's cut table and visual cues from the voice track's word timestamps, so
the picture stays on the narration. Blockout quality: the world is the AI placeholder still
from prep_still.py, moved in 2.5D; the computation layer uses the plan's palette; there is
no music or sound design yet.

Why not Manim for this draft: Manim's Cairo renderer resizes every image to its on-screen
size and composites each one through a full-frame buffer. The 50x zoom into single pixels
(S4) and 196 moving patches (S5) make that impractical, while cairo draws both directly.

Inputs (made by prep_still.py and tools/narrate.py; kept out of git):
  sample/frames/{world_wide_half,machine_view,model_input_224}.png, sample/frames/still.json
  sample/audio/narration/elevenlabs-george-0.9/{timeline.wav,words.json}
  words.json must carry the SHA-256 of the current timeline.wav, or the render stops.

Config example (constants below): TAKE = elevenlabs-george-0.9, W x H = 1920 x 1080, FPS = 30.

Usage (from the repo root, with the project venv that has pycairo, numpy, Pillow):
  .venv/bin/python episodes/01-how-machines-see/sample/draft/render_draft.py --stills 5,18,40
  .venv/bin/python episodes/01-how-machines-see/sample/draft/render_draft.py --scale 0.5   # quick preview
  .venv/bin/python episodes/01-how-machines-see/sample/draft/render_draft.py              # full 1080p30

Writes sample/renders/sample-draft-1[-preview].mp4 (or PNG stills) and prints an ffprobe check.
"""

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import cairo
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SAMPLE = HERE.parent
FRAMES = SAMPLE / "frames"
TAKE = SAMPLE / "audio" / "narration" / "elevenlabs-george-0.9"
RENDERS = SAMPLE / "renders"
PLAN = SAMPLE.parent / "sample-90s-plan.md"
sys.path.insert(0, str(SAMPLE.parents[2] / "tools"))
import narrate  # noqa: E402  (the plan parser gives the shot slots)

W, H, FPS = 1920, 1080, 30
PAPER, INK, INK2 = "#EEEAE3", "#22201C", "#625D55"
VISION, VISION_DARK, VISION_LIGHT = "#12806A", "#0B4A3E", "#D3ECE6"
NIGHT, BADGE, CREAM = "#0B0B0A", "#8A857C", "#F5F1EA"
SANS, MONO = "Helvetica Neue", "Menlo"
N, SQ = 14, 896.0
P = SQ / N  # 64 px per patch when the square is 896 px
SQX, SQY = (W - SQ) / 2, (H - SQ) / 2
CX, CY = W / 2, H / 2
ZOOM_PIXEL = (105, 134)  # the model pixel the S4 zoom lands on: the rim's white-to-blue edge
ZOOM = 50.0  # 4 px per model pixel at 896, 200 px when zoomed
CELL_W, CELL_H, CELL_GAP, VEC_Y = 84, 70, 18, 197  # vector cells line up with the 8 tiles of E

_KEEP = []  # numpy buffers behind cairo surfaces


def fail(msg):
    sys.exit(f"render_draft: {msg}")


for needed in [FRAMES / "still.json", TAKE / "words.json", TAKE / "timeline.wav"]:
    if not needed.exists():
        fail(f"missing {needed}; build the George take with tools/narrate.py and run prep_still.py first")

STILL = json.loads((FRAMES / "still.json").read_text())
RIM = (STILL["rim_patch"]["row"], STILL["rim_patch"]["col"])
RIM_K = RIM[0] * N + RIM[1]
CROP = STILL["crop"]
WORDS_DOC = json.loads((TAKE / "words.json").read_text())
if not isinstance(WORDS_DOC, dict) or WORDS_DOC.get("timeline_sha256") != hashlib.sha256(
        (TAKE / "timeline.wav").read_bytes()).hexdigest():
    fail(f"{TAKE / 'words.json'} does not match timeline.wav; rebuild the take with tools/narrate.py")
WORDS = WORDS_DOC["words"]
SHOTS, LENGTH = narrate.parse_plan(PLAN)
SLOT = {s["id"]: (float(s["start"]), float(s["end"])) for s in SHOTS}
SLOT["S8"] = (SLOT["S7"][1], float(LENGTH))


def cue(word, after, end=False):
    """Start (or end) time of the first occurrence of `word` after `after` seconds."""
    for w in WORDS:
        if w["start"] >= after and re.sub(r"[^a-z0-9']", "", w["text"].lower()) == word:
            return w["end"] if end else w["start"]
    fail(f"the voice track has no '{word}' after {after:.1f}s")


# ---------------------------------------------------------------- drawing helpers

def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, x):
    return a + (b - a) * x


def ease(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    x = clamp((t - t0) / (t1 - t0))
    return x * x * (3 - 2 * x)


def ramp(t, t0, t1):
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def window(t, t0, t1, fade=0.35):
    return ease(t, t0, t0 + fade) * (1 - ease(t, t1 - fade, t1))


def bump(t, t0, dur):
    return math.sin(math.pi * clamp((t - t0) / dur))


def surface(arr):
    h, w = arr.shape[:2]
    bgra = np.empty((h, w, 4), np.uint8)
    bgra[..., 0], bgra[..., 1], bgra[..., 2], bgra[..., 3] = arr[..., 2], arr[..., 1], arr[..., 0], 255
    _KEEP.append(bgra)
    return cairo.ImageSurface.create_for_data(memoryview(bgra), cairo.FORMAT_ARGB32, w, h, w * 4)


def paint(ctx, surf, x, y, w, h, alpha=1.0, nearest=False):
    if alpha <= 0:
        return
    sw, sh = surf.get_width(), surf.get_height()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(w / sw, h / sh)
    ctx.set_source_surface(surf, 0, 0)
    pat = ctx.get_source()
    pat.set_filter(cairo.FILTER_NEAREST if nearest else cairo.FILTER_GOOD)
    pat.set_extend(cairo.EXTEND_PAD)
    ctx.rectangle(0, 0, sw, sh)
    ctx.clip()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def rect(ctx, x, y, w, h, fill=None, stroke=None, lw=1.5, alpha=1.0, radius=0.0):
    if alpha <= 0:
        return
    ctx.save()
    if radius:
        ctx.new_sub_path()
        ctx.arc(x + w - radius, y + radius, radius, -math.pi / 2, 0)
        ctx.arc(x + w - radius, y + h - radius, radius, 0, math.pi / 2)
        ctx.arc(x + radius, y + h - radius, radius, math.pi / 2, math.pi)
        ctx.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        ctx.close_path()
    else:
        ctx.rectangle(x, y, w, h)
    if fill:
        ctx.set_source_rgba(*rgb(fill), alpha)
        ctx.fill_preserve()
    if stroke:
        ctx.set_source_rgba(*rgb(stroke), alpha)
        ctx.set_line_width(lw)
        ctx.stroke()
    ctx.new_path()
    ctx.restore()


def line(ctx, x0, y0, x1, y1, color, lw=1.5, alpha=1.0, dash=None):
    if alpha <= 0:
        return
    ctx.save()
    ctx.set_source_rgba(*rgb(color), alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if dash:
        ctx.set_dash(dash)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    ctx.restore()


def text(ctx, s, x, y, size, color=INK, font=SANS, bold=False, anchor="c", alpha=1.0):
    if alpha <= 0:
        return 0.0
    ctx.save()
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, _, tw, _, _, _ = ctx.text_extents(s)
    ascent, descent = ctx.font_extents()[:2]
    px = {"c": x - tw / 2 - xb, "l": x - xb, "r": x - tw - xb}[anchor]
    ctx.move_to(px, y + (ascent - descent) / 2)
    ctx.set_source_rgba(*rgb(color), alpha)
    ctx.show_text(s)
    ctx.restore()
    return tw


def chip(ctx, s, alpha):
    """A tag on a paper chip at the bottom left, as the plan's on-screen tags."""
    if alpha <= 0:
        return
    ctx.save()
    ctx.select_font_face(SANS, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(21)
    tw = ctx.text_extents(s)[2]
    ctx.restore()
    rect(ctx, 36, H - 76, tw + 32, 42, fill=PAPER, alpha=0.93 * alpha, radius=8)
    text(ctx, s, 52, H - 55, 21, INK2, anchor="l", alpha=alpha)


def arrow(ctx, x0, y, x1, color=INK2, alpha=1.0):
    line(ctx, x0, y, x1 - 4, y, color, 2, alpha)
    ctx.save()
    ctx.set_source_rgba(*rgb(color), alpha)
    ctx.move_to(x1, y)
    ctx.line_to(x1 - 12, y - 7)
    ctx.line_to(x1 - 12, y + 7)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


def mixhex(a, b, x):
    ca, cb = rgb(a), rgb(b)
    return "#" + "".join(f"{round(255 * lerp(u, v, x)):02x}" for u, v in zip(ca, cb))


def vision_ramp(v):
    v = clamp(v)
    return mixhex(VISION_LIGHT, VISION, v * 2) if v < 0.5 else mixhex(VISION, VISION_DARK, v * 2 - 1)


# ---------------------------------------------------------------- assets and illustrative math

WIDE_ARR = np.array(Image.open(FRAMES / "world_wide_half.png").convert("RGB"))
VIEW_ARR = np.array(Image.open(FRAMES / "machine_view.png").convert("RGB"))
M224 = np.array(Image.open(FRAMES / "model_input_224.png").convert("RGB"))
WIDE, VIEW, PIX = surface(WIDE_ARR), surface(VIEW_ARR), surface(M224)
WH, WW = WIDE_ARR.shape[:2]  # half-size still, 1536 x 2752

PATCH_ARR = M224.reshape(N, 16, N, 16, 3).transpose(0, 2, 1, 3, 4).reshape(N * N, 16, 16, 3)
PATCHES = [surface(np.ascontiguousarray(p)) for p in PATCH_ARR]


def patterns():
    """Eight simple patch-sized patterns that stand in for the rows of E (illustration only)."""
    y, x = np.mgrid[0:16, 0:16] / 15.0 * 2 - 1
    grey = [np.ones((16, 16)), x, -y, (x - y) / 2, np.sin(np.pi * (y + 1) * 2), np.sin(np.pi * (x + 1) * 2),
            np.where((np.floor((x + 1) * 2) + np.floor((y + 1) * 2)) % 2 == 0, 1.0, -1.0)]
    pats = [np.repeat(g[..., None], 3, axis=2) for g in grey]
    opp = np.stack([-x, -x, x], axis=2)  # yellow to blue
    return np.stack(pats + [opp])


PATTERNS = patterns()
TILES = [surface(np.ascontiguousarray(((p + 1) / 2 * 255).clip(0, 255).astype(np.uint8))) for p in PATTERNS]
EMB = np.einsum("nhwc,khwc->nk", PATCH_ARR / 127.5 - 1, PATTERNS) / (16 * 16 * 3)
EMB_T = ((EMB - EMB.mean(0)) / (EMB.std(0) + 1e-8)).clip(-2, 2) / 4 + 0.5  # 0..1 per dimension


def attention_weights():
    """Hand-made, plausible weights for the S7 illustration: the cup and the rim's neighbors matter most."""
    p = PATCH_ARR.astype(int)
    blue = ((p[..., 2] > p[..., 0] + 40) & (p[..., 2] > 60)).mean(axis=(1, 2))
    rr, cc = np.divmod(np.arange(N * N), N)
    d = np.hypot(rr - RIM[0], cc - RIM[1])
    w = np.exp(3.0 * (2.0 * blue + np.exp(-d / 2.5)))
    return w / w.sum(), d


WEIGHTS, DIST = attention_weights()
NEW_RIM = 0.55 * EMB_T[RIM_K] + 0.45 * (WEIGHTS @ EMB_T)
STREAMS = np.argsort(-WEIGHTS)[:28]

col = PATCH_ARR[RIM_K].reshape(-1)  # 768 values, pixel by pixel, R G B
tint = np.zeros((768, 1, 3), np.uint8)
for ch in range(3):
    v = col[ch::3].astype(float)
    tint[ch::3, 0, :] = (v[:, None] * 0.25).astype(np.uint8)
    tint[ch::3, 0, ch] = v.astype(np.uint8)
COLUMN = surface(tint)

# ---------------------------------------------------------------- cues from the voice track

S1, S2, S3, S4, S5, S6, S7, S8 = (SLOT[f"S{i}"] for i in range(1, 9))
T = {
    "in_end": cue("in", S2[0], end=True), "its": cue("it's", S2[0]), "nothing": cue("nothing", S2[0]),
    "this3": cue("this", S3[0]), "camera_end": cue("camera", S3[0], end=True),
    "this4": cue("this", S4[0] + 2.5), "pixels": cue("pixels", S4[0]), "for": cue("for", S4[0]),
    "three": cue("three", S4[0]), "red": cue("red", S4[0]), "green": cue("green", S4[0]),
    "blue": cue("blue", S4[0]), "blue_end": cue("blue", S4[0], end=True),
    "cut": cue("cut", S5[0]), "then": cue("then", S5[0]),
    "every": cue("every", S6[0]), "matrix": cue("matrix", S6[0]), "so": cue("so", S6[0]),
    "only": cue("only", S6[0]), "square_end": cue("square", S6[0], end=True),
    "asks": cue("asks", S7[0]), "this7": cue("this", S7[0] + 5), "includes": cue("includes", S7[0]),
}

RIM_C = (SQX + (RIM[1] + 0.5) * P, SQY + (RIM[0] + 0.5) * P)  # rim patch center at the 896 layout
FIT = H / WH  # the wide still fills the frame height
CROP_H = (CROP["x"] / 2, CROP["y"] / 2, CROP["size"] / 2)  # crop box in half-size pixels


def wide_to_screen(xh, yh, cx, cy, s):
    return cx + (xh - WW / 2) * s, cy + (yh - WH / 2) * s


CROP_CENTER_H = (CROP_H[0] + CROP_H[2] / 2, CROP_H[1] + CROP_H[2] / 2)
START_CENTER = (CX + (WW / 2 - CROP_CENTER_H[0]), CY + (WH / 2 - CROP_CENTER_H[1]))  # crop centered at 1:1
LENS_H = (322, 662)  # the camera lens in the half-size still


# ---------------------------------------------------------------- shots

def cold_open(ctx, t):
    """S1-S2: one patch alone, then the rings return while the view zooms out to the full square."""
    rect(ctx, 0, 0, W, H, fill=NIGHT)
    z0 = 8 * (1 + 0.075 * ease(t, 1.3, S1[1] - 0.2))
    t0, t1 = T["in_end"] + 0.05, T["its"] - 0.3
    e = ease(t, t0, t1)
    z = math.exp(lerp(math.log(z0), 0.0, e))
    sx, sy = lerp(CX, RIM_C[0], e), lerp(CY, RIM_C[1], e)  # where the rim center sits on screen
    camx, camy = RIM_C[0] - (sx - CX) / z, RIM_C[1] - (sy - CY) / z
    rings = 8 * ramp(t, t0, t1 - 0.4)
    ctx.save()
    ctx.translate(CX, CY)
    ctx.scale(z, z)
    ctx.translate(-camx, -camy)

    def region(m):
        r0, r1 = max(0, RIM[0] - m), min(N - 1, RIM[0] + m)
        c0, c1 = max(0, RIM[1] - m), min(N - 1, RIM[1] + m)
        return SQX + c0 * P, SQY + r0 * P, (c1 - c0 + 1) * P, (r1 - r0 + 1) * P

    alpha = ease(t, 0.3, 1.3)
    m = int(rings)
    for ring, a in ((m + 1, (rings - m) * alpha), (m, alpha)):
        if a <= 0 or ring > 8:
            continue
        ctx.save()
        ctx.rectangle(*region(ring))
        ctx.clip()
        paint(ctx, VIEW, SQX, SQY, SQ, SQ, a)
        ctx.restore()
    lw = (1.6 + 2.4 * bump(t, T["nothing"] + 0.1, 1.0)) / z
    rect(ctx, RIM_C[0] - P / 2, RIM_C[1] - P / 2, P, P, stroke=CREAM, lw=lw, alpha=0.85 * alpha)
    ctx.restore()


def world_transform(t):
    e = ease(t, S3[0] + 1.3, T["this3"] - 0.1)
    s = math.exp(lerp(0.0, math.log(FIT), e))
    return lerp(START_CENTER[0], CX, e), lerp(START_CENTER[1], CY, e), s


def world(ctx, t):
    """S3 and the start of S4: the frame fills with the room, pulls back, and shows the camera's view."""
    fade = 1 - ease(t, S4[0] + 0.4, T["this4"] - 0.3)
    if fade <= 0:
        return
    rect(ctx, 0, 0, W, H, fill=NIGHT, alpha=fade)
    cx, cy, s = world_transform(t)
    k = math.floor(8.999 * ramp(t, S3[0], S3[0] + 1.2))
    hw, hh = SQ / 2 + P * k, SQ / 2 + P * k
    ctx.save()
    if t < S3[0] + 1.25:
        ctx.rectangle(CX - hw, CY - hh, 2 * hw, 2 * hh)
        ctx.clip()
    x, y = wide_to_screen(0, 0, cx, cy, s)
    paint(ctx, WIDE, x, y, WW * s, WH * s, fade)
    ctx.restore()
    a = window(t, T["this3"] + 0.1, S4[0] + 3.0, 0.6) * fade
    if a > 0:
        lx, ly = wide_to_screen(*LENS_H, cx, cy, s)
        x0, y0 = wide_to_screen(CROP_H[0], CROP_H[1], cx, cy, s)
        size = CROP_H[2] * s
        ctx.save()
        ctx.move_to(lx, ly)
        ctx.line_to(x0, y0)
        ctx.line_to(x0, y0 + size)
        ctx.close_path()
        ctx.set_source_rgba(*rgb(CREAM), 0.28 * a)
        ctx.fill()
        ctx.restore()
        line(ctx, lx, ly, x0, y0, CREAM, 1.5, 0.9 * a)
        line(ctx, lx, ly, x0, y0 + size, CREAM, 1.5, 0.9 * a)
        rect(ctx, x0, y0, size, size, stroke=CREAM, lw=2, alpha=0.95 * a)
    text(ctx, "IN TOUCH", CX, 940, 64, INK, bold=True,
         alpha=window(t, T["camera_end"] - 0.5, T["camera_end"] + 1.7, 0.4))


def pixel_camera(t):
    zin = ease(t, T["for"] - 0.1, T["three"] - 0.05)
    zout = ease(t, T["blue_end"] + 0.8, S5[0] - 0.4)
    e = zin * (1 - zout)
    z = math.exp(lerp(0.0, math.log(ZOOM), e))
    tx, ty = SQX + (ZOOM_PIXEL[1] + 0.5) * 4, SQY + (ZOOM_PIXEL[0] + 0.5) * 4
    sx, sy = lerp(tx, CX, e), lerp(ty, CY, e)
    return z, tx - (sx - CX) / z, ty - (sy - CY) / z


def pixels(ctx, t):
    """S4: the view lifts out of the room, snaps to 224 x 224, and zooms to single pixels with their values."""
    cx, cy, s = world_transform(S4[0])
    x0, y0 = wide_to_screen(CROP_H[0], CROP_H[1], cx, cy, s)
    e = ease(t, S4[0] + 0.4, T["this4"] - 0.2)
    size = lerp(CROP_H[2] * s, SQ, e)
    x, y = lerp(x0, SQX, e), lerp(y0, SQY, e)
    appear = ease(t, S4[0], S4[0] + 0.35)
    snapped = t >= T["pixels"]
    shadow = 0.18 * appear * (1 - ease(t, T["for"] - 0.1, T["for"] + 0.4))
    rect(ctx, x + 10, y + 12, size, size, fill="#000000", alpha=shadow)
    if not snapped:
        paint(ctx, VIEW, x, y, size, size, appear)
        return
    z, camx, camy = pixel_camera(t)
    ctx.save()
    ctx.translate(CX, CY)
    ctx.scale(z, z)
    ctx.translate(-camx, -camy)
    paint(ctx, PIX, SQX, SQY, SQ, SQ, 1.0, nearest=True)
    ctx.restore()
    rect(ctx, SQX, SQY, SQ, SQ, fill="#FFFFFF", alpha=0.35 * (1 - ease(t, T["pixels"], T["pixels"] + 0.3)))
    a = window(t, T["three"], T["blue_end"] + 0.7, 0.4)
    if a > 0 and z > 20:
        pulses = [bump(t, T["red"] - 0.05, 0.6), bump(t, T["green"] - 0.05, 0.6), bump(t, T["blue"] - 0.05, 0.6)]
        for i in range(ZOOM_PIXEL[0] - 4, ZOOM_PIXEL[0] + 5):
            for j in range(ZOOM_PIXEL[1] - 6, ZOOM_PIXEL[1] + 7):
                px = (SQX + (j + 0.5) * 4 - camx) * z + CX
                py = (SQY + (i + 0.5) * 4 - camy) * z + CY
                if not (-120 < px < W + 120 and -120 < py < H + 120):
                    continue
                r, g, b = (int(v) for v in M224[i, j])
                color = INK if 0.2126 * r + 0.7152 * g + 0.0722 * b > 140 else CREAM
                for n, v in enumerate((r, g, b)):
                    text(ctx, f"{v}", px, py + (n - 1) * 0.21 * 4 * z, 0.14 * 4 * z * (1 + 0.35 * pulses[n]),
                         color, MONO, alpha=a)
    chip(ctx, "Real pixel values from this frame (red, green, blue: 0 to 255)", window(t, T["three"], S5[0] - 0.2))


def grid_geom(t):
    """Scale and center of the patch grid from S6 on."""
    g = lerp(1.0, 0.62, ease(t, S6[0], S6[0] + 0.9))
    gx = lerp(CX, 407.0, ease(t, S6[0], S6[0] + 0.9))
    g = lerp(g, 0.9, ease(t, S7[0], S7[0] + 1.0))
    gx = lerp(gx, 609.0, ease(t, S7[0], S7[0] + 1.0))
    return g, gx, CY


def patch_box(k, g, gx, gy):
    r, c = divmod(k, N)
    ps = P * g
    return gx + (c - N / 2) * ps, gy + (r - N / 2) * ps, ps


def patches(ctx, t):
    """S5: grid lines cut the picture; the patches lift, line up in reading order, and fold back."""
    lines_a = 1 - ease(t, T["then"], T["then"] + 0.35)
    if t < T["then"]:
        paint(ctx, PIX, SQX, SQY, SQ, SQ, 1.0, nearest=True)
    else:
        lift = lerp(1.0, 0.9, ease(t, T["then"], T["then"] + 0.35))
        order = list(range(N * N))
        order.remove(RIM_K)
        for k in order + [RIM_K]:
            r, c = divmod(k, N)
            gxk, gyk = SQX + (c + 0.5) * P, SQY + (r + 0.5) * P
            rxk, ryk = CX + (k - RIM_K) * P, CY
            go = ease(t, T["then"] + 0.4 + k * 0.0102, T["then"] + 1.4 + k * 0.0102)
            back = ease(t, 56.3 + k * 0.0035, 57.3 + k * 0.0035)
            x, y = lerp(lerp(gxk, rxk, go), gxk, back), lerp(lerp(gyk, ryk, go), gyk, back)
            ps = P * lerp(lift, 1.0, back)
            if -P < x < W + P:
                paint(ctx, PATCHES[k], x - ps / 2, y - ps / 2, ps, ps, 1.0, nearest=True)
            if k == RIM_K:
                rect(ctx, x - ps / 2, y - ps / 2, ps, ps, stroke=CREAM, lw=2.2)
    for i in range(N + 1):
        a = ease(t, T["cut"] + i * 0.05, T["cut"] + i * 0.05 + 0.3) * lines_a
        line(ctx, SQX + i * P, SQY, SQX + i * P, SQY + SQ, PAPER, 2, a)
        line(ctx, SQX, SQY + i * P, SQX + SQ, SQY + i * P, PAPER, 2, a)
    a = window(t, T["then"] + 3.2, 56.3, 0.4)
    text(ctx, str(RIM_K + 1), CX, CY - 58, 24, INK2, alpha=a)
    text(ctx, "196 patches, in reading order", CX, CY + 92, 26, INK2, alpha=a)


def vector_cells(ctx, x, y, values, alpha=1.0):
    for i, v in enumerate(values):
        rect(ctx, x, y + i * (CELL_H + CELL_GAP), CELL_W, CELL_H, fill=vision_ramp(v), stroke=INK2, lw=1,
             alpha=alpha, radius=4)


def pipeline(ctx, t):
    """S6-S7: one patch becomes a vector through E; then the rim patch gathers from the others."""
    g, gx, gy = grid_geom(t)
    x0, y0, ps = patch_box(0, g, gx, gy)
    fade_all = 1 - ease(t, S8[0], S8[0] + 0.6)
    if fade_all <= 0:
        return
    paint(ctx, PIX, x0, y0, ps * N, ps * N, fade_all, nearest=True)
    rx, ry, _ = patch_box(RIM_K, g, gx, gy)
    rim_cx, rim_cy = rx + ps / 2, ry + ps / 2

    # S7 weights: tinted squares over the grid, rippling out from the rim patch.
    wmax = WEIGHTS.max()
    wa = (1 - ease(t, 84.2, 85.6)) * fade_all
    boost = 1 + 0.6 * bump(t, T["includes"], 1.4)
    if t > S7[0]:
        for k in range(N * N):
            bx, by, _ = patch_box(k, g, gx, gy)
            a = ease(t, 71.5 + DIST[k] * 0.12, 71.85 + DIST[k] * 0.12) * wa
            rect(ctx, bx, by, ps, ps, fill=VISION, alpha=min(0.85, (0.06 + 0.72 * (WEIGHTS[k] / wmax) ** 0.6) * boost) * a)

    # Mini vectors inside every patch (S6 ripple). They settle to a faint layer and leave before S7.
    settle = (1 - 0.55 * ease(t, T["so"] + 2.0, T["so"] + 2.8)) * (1 - ease(t, S7[0], S7[0] + 0.8))
    if T["so"] < t < S7[0] + 0.8:
        for k in range(N * N):
            a = ease(t, T["so"] + k * 0.0075, T["so"] + 0.2 + k * 0.0075) * settle * fade_all
            if a <= 0:
                continue
            bx, by, _ = patch_box(k, g, gx, gy)
            cw, chh = ps * 0.14, ps * 0.56 / 8
            for i, v in enumerate(EMB_T[k]):
                rect(ctx, bx + ps * 0.8, by + ps * 0.22 + i * chh, cw, chh, fill=vision_ramp(v), alpha=a)
    rect(ctx, rx, ry, ps, ps, stroke=CREAM, lw=2.2 + 3 * bump(t, T["square_end"] - 0.5, 0.7)
         + 3 * bump(t, T["this7"] + 0.3, 0.8), alpha=fade_all)

    # The rim vector, big, on the right.
    vx = lerp(1242.0, 1445.0, ease(t, S7[0], S7[0] + 1.0))
    vy = VEC_Y
    cells_a = ease(t, T["matrix"] + 0.3, T["matrix"] + 1.3) * fade_all
    merge = ease(t, 75.8, 76.4)
    values = [lerp(a, b, merge) for a, b in zip(EMB_T[RIM_K], NEW_RIM)]
    if t < T["matrix"] + 1.4:
        for i, v in enumerate(EMB_T[RIM_K]):
            a = ease(t, T["matrix"] + 0.3 + i * 0.11, T["matrix"] + 0.5 + i * 0.11) * fade_all
            vector_cells(ctx, vx, vy + i * (CELL_H + CELL_GAP), [v], alpha=a)
    else:
        vector_cells(ctx, vx, vy, values, alpha=cells_a)

    # S6 pipeline: patch -> 768 numbers -> E -> vector.
    pa = window(t, T["every"] + 0.3, 63.5, 0.4) * fade_all
    if pa > 0:
        e = ease(t, S6[0] + 1.0, S6[0] + 1.9)
        colx, coly, colw, colh = 787.0, 176.0, 22.0, 729.0
        bx, by = lerp(rx, colx, e), lerp(ry, coly, e)
        bw, bh = lerp(ps, colw, e), lerp(ps, colh, e)
        paint(ctx, PATCHES[RIM_K], bx, by, bw, bh, (1 - e) * pa, nearest=True)
        paint(ctx, COLUMN, bx, by, bw, bh, e * pa, nearest=True)
        text(ctx, "768 numbers", colx + colw / 2, 140, 24, INK2, alpha=ease(t, S6[0] + 1.9, S6[0] + 2.3) * pa)
        text(ctx, "16 × 16 × 3", colx + colw / 2, 940, 22, INK2, alpha=ease(t, S6[0] + 1.9, S6[0] + 2.3) * pa)
        ea = ease(t, T["matrix"] - 0.1, T["matrix"] + 0.3) * pa
        text(ctx, "E", 1041, 140, 30, INK, bold=True, alpha=ea)
        for i in range(8):
            ty = 197 + i * 88
            hi = bump(t, T["matrix"] + 0.3 + i * 0.11, 0.3)
            paint(ctx, TILES[i], 1006, ty, 70, 70, ea, nearest=True)
            rect(ctx, 1006, ty, 70, 70, stroke=VISION if hi > 0.05 else INK2, lw=1 + 3 * hi, alpha=ea)
        arrow(ctx, 830, CY, 990, alpha=ea)
        arrow(ctx, 1092, CY, 1230, alpha=ea)
        cap = ease(t, T["matrix"] + 1.0, T["matrix"] + 1.4) * pa
        text(ctx, "Drawn with 8 numbers. ViT-Base uses 768.", vx + CELL_W / 2, 940, 24, INK2, alpha=cap)
        text(ctx, "the same matrix for all 196 patches", 1041, 985, 20, INK2, alpha=cap)

    # Tether from the rim vector to its patch.
    ta = ease(t, T["only"] + 0.2, T["only"] + 0.9) * fade_all
    if ta > 0:
        tx0, ty0 = vx, CY
        prog = ease(t, T["only"] + 0.2, T["only"] + 0.9)
        lw = 1.6 + 2.5 * bump(t, T["this7"] + 0.3, 0.8)
        line(ctx, tx0, ty0, lerp(tx0, rim_cx, prog), lerp(ty0, rim_cy, prog), INK2, lw, 0.9 * fade_all)

    if t < S7[0]:
        return
    # S7: the query ring, the streams of values, and the merge.
    qa = window(t, T["asks"], 85.4, 0.3) * fade_all
    text(ctx, "query", rim_cx, ry - 22, 22, VISION_DARK, bold=True, alpha=qa)
    rp = ramp(t, T["asks"] + 0.05, T["asks"] + 1.6)
    if 0 < rp < 1:
        ctx.save()
        ctx.arc(rim_cx, rim_cy, lerp(12, 1000, rp), 0, 2 * math.pi)
        ctx.set_source_rgba(*rgb(VISION), 0.9 * (1 - rp) * fade_all)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()
    text(ctx, "weights add up to 1", gx, gy + ps * N / 2 + 34, 22, INK2, alpha=window(t, 72.4, 85.6) * fade_all)
    sa = (1 - 0.7 * ease(t, 75.6, 76.2)) * (1 - ease(t, 84.2, 85.6)) * fade_all
    ex, ey = vx - 14, CY
    for n, k in enumerate(STREAMS):
        prog = ease(t, 73.0 + n * 0.05, 74.2 + n * 0.05)
        if prog <= 0 or sa <= 0:
            continue
        bx, by, _ = patch_box(k, g, gx, gy)
        sx, sy = bx + ps / 2, by + ps / 2
        mx, my = (sx + ex) / 2, min(sy, ey) - 120
        ctx.save()
        ctx.move_to(sx, sy)
        steps = max(2, int(24 * prog))
        for i in range(1, steps + 1):
            u = prog * i / steps
            qx = (1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * ex
            qy = (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ey
            ctx.line_to(qx, qy)
        ctx.set_source_rgba(*rgb(VISION), 0.75 * sa)
        ctx.set_line_width(1.2 + 9 * WEIGHTS[k] / wmax)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.restore()
    inc = ease(t, 75.2, 75.8)
    ia = window(t, 75.2, 76.3, 0.25) * fade_all
    if ia > 0:
        ix = lerp(vx - 150, vx, inc)
        vector_cells(ctx, ix, vy, WEIGHTS @ EMB_T, alpha=0.9 * ia)
        text(ctx, "+", vx - 34, vy - 30, 36, INK, bold=True, alpha=ia)
    chip(ctx, "Illustration · weights drawn for explanation", window(t, 71.5, 85.6) * fade_all)


def end_card(ctx, t):
    a = ease(t, S8[0] + 0.6, S8[0] + 1.3)
    text(ctx, "In Touch", CX, 490, 96, INK, bold=True, alpha=a)
    text(ctx, "Episode 1 · How Machines See", CX, 585, 40, INK2, alpha=a)


def draw(ctx, t):
    rect(ctx, 0, 0, W, H, fill=PAPER)
    if t < S3[0]:
        cold_open(ctx, t)
    if S3[0] <= t < S4[0] + 4:
        world(ctx, t)
    if S4[0] <= t < S5[0]:
        pixels(ctx, t)
    if S5[0] <= t < S6[0]:
        patches(ctx, t)
    if S6[0] <= t < S8[0] + 0.6:
        pipeline(ctx, t)
    if t >= S8[0]:
        end_card(ctx, t)
    if t >= S3[0] + 0.2:
        text(ctx, "DRAFT 1 · placeholder world still (AI-generated) · voice only, no music", 36, 40, 18, BADGE,
             anchor="l", alpha=ease(t, S3[0] + 0.2, S3[0] + 0.8))


# ---------------------------------------------------------------- output

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--scale", type=float, default=1.0, help="output scale; 0.5 renders a 960x540 preview")
    ap.add_argument("--stills", help="comma-separated times in seconds; write PNG frames instead of a video")
    args = ap.parse_args()
    w, h = round(W * args.scale), round(H * args.scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    RENDERS.mkdir(exist_ok=True)

    def frame(t):
        ctx.save()
        ctx.scale(args.scale, args.scale)
        draw(ctx, t)
        ctx.restore()
        surf.flush()

    if args.stills:
        for s in args.stills.split(","):
            frame(float(s))
            out = RENDERS / f"still-{float(s):05.1f}s.png"
            surf.write_to_png(str(out))
            print(out)
        return

    suffix = "" if args.scale == 1.0 else "-preview"
    out = RENDERS / f"sample-draft-1{suffix}.mp4"
    frames = round(LENGTH * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(FPS),
           "-i", "-", "-i", str(TAKE / "timeline.wav"), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)]
    print(f"render_draft: {frames} frames at {w}x{h}, {FPS} fps -> {out}")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(frames):
        frame(f / FPS)
        proc.stdin.write(bytes(surf.get_data()))
        if f % (FPS * 10) == 0:
            print(f"  {f / FPS:5.1f}s")
    proc.stdin.close()
    if proc.wait():
        fail("ffmpeg failed")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                            "-of", "json", str(out)], capture_output=True, text=True)
    info = json.loads(probe.stdout)
    streams = {s["codec_type"]: s for s in info["streams"]}
    dur = float(info["format"]["duration"])
    v = streams.get("video", {})
    print(f"render_draft: {out.name} duration {dur:.2f}s, video {v.get('width')}x{v.get('height')} "
          f"@ {v.get('r_frame_rate')}, audio {'yes' if 'audio' in streams else 'MISSING'}")
    if abs(dur - LENGTH) > 0.1 or "audio" not in streams:
        fail("the output does not match the cut (length or audio)")


if __name__ == "__main__":
    main()
