#!/usr/bin/env python3
"""
SULEM profile widgets - all generated locally, zero external services.

  widget_typing.gif   typewriter lines (type - hold - erase - next)
  widget_quotes.gif   full-width quote reel: stoics / programmers / mine
  widget_neofetch.png terminal/neofetch-style system card
  widget_snake.gif    REAL contribution grid + a pixel-snake eating it
  wall_1/2/3.png      FULL-WIDTH horizontal wall slabs with the snake
                      crawling over the brickwork (sections = posts)
  footer.png          dark footer: "you are what you code"

Usage:  python3 make_widgets.py [all|snake]
"""

import os
import sys
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
from scipy.interpolate import CubicSpline, PchipInterpolator

CANVAS = (13, 17, 23)          # github dark canvas #0d1117
CARD_BG = (10, 7, 20)
CARD_BORDER = (42, 33, 64)
KEY_C = (167, 139, 250)        # #A78BFA
VAL_C = (216, 206, 244)        # #D8CEF4
DIM_C = (104, 92, 140)
TXT_C = (185, 166, 242)        # #B9A6F2
CURSOR_C = (124, 58, 237)      # #7C3AED

MONO = "assets/fonts/JetBrainsMono-Regular.ttf"
DISP = "assets/fonts/Michroma.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

def F(size, path=MONO):
    return ImageFont.truetype(path, size)

# --------------------------------------------------------------- snake src
raw = Image.open("assets/snake_raw.png").convert("RGB")

def grade(arr, lift=30):
    arr = 255.0 * np.power(np.clip(arr, 0, 255) / 255.0, 0.86)
    lum = arr.mean(axis=2, keepdims=True) / 255.0
    arr += (1.0 - lum) * np.array([lift, lift * 0.55, lift * 1.6], np.float32)
    return np.clip(arr, 0, 255)

def snake_mask(arr, strong=False):
    m = arr.max(axis=2) > 15
    lab, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (int(np.argmax(sizes)) + 1)
    m = ndimage.binary_closing(m, structure=np.ones((9, 9)))
    m = ndimage.binary_fill_holes(m)
    k1 = 61 if strong else 21
    m = ndimage.binary_closing(m, structure=np.ones((k1, k1)))
    m = ndimage.binary_fill_holes(m)
    k2 = 81 if strong else 45
    m = ndimage.binary_closing(m, structure=np.ones((k2, 1)))
    m = ndimage.binary_fill_holes(m)
    if strong:
        m = ndimage.binary_closing(m, structure=np.ones((7, 7)))
        m = ndimage.binary_opening(m, structure=np.ones((3, 3)))
    return m

# ================================================================== typing
LINES = [
    "if it happens twice, it becomes a script",
    "C on metal. Python on everything else.",
    "sharp angles. clean abstractions. zero fluff.",
    "the obstacle is the way - debug accordingly.",
    "memento mori - then ship it.",
]

def make_typing():
    W, H = 780, 74
    font = F(24)
    frames, durations = [], []

    def frame(text, cursor=True):
        img = Image.new("RGB", (W, H), CANVAS)
        d = ImageDraw.Draw(img)
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, 22), text, font=font, fill=TXT_C)
        d.text(((W - w) / 2 + w + 6, 22), "\u258c", font=font,
               fill=CURSOR_C if cursor else CANVAS)
        return img

    empty = frame("", cursor=False)
    frames.append(empty); durations.append(500)
    for line in LINES:
        for i in range(1, len(line) + 1):
            frames.append(frame(line[:i])); durations.append(65)
        for k in range(8):
            frames.append(frame(line, cursor=(k // 2) % 2 == 0))
            durations.append(120)
        for i in range(len(line), -1, -2):
            frames.append(frame(line[:i])); durations.append(35)
        frames.append(empty); durations.append(420)

    q = [f.quantize(96, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    q[0].save("assets/widget_typing.gif", save_all=True, append_images=q[1:],
              duration=durations, loop=0, optimize=True, disposal=2)
    print("typing gif:", len(frames), "frames")

# ================================================================ neofetch
def card_frame(w, h, title):
    img = Image.new("RGB", (w, h), CARD_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=16, outline=CARD_BORDER, width=1)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([24 + i * 27, 20, 40 + i * 27, 36], fill=c)
    d.text((116, 21), title, font=F(19), fill=(122, 106, 162))
    d.line([16, 54, w - 16, 54], fill=(30, 24, 48), width=1)
    return img, d

def snake_head_icon():
    c = raw.crop((10, 200, 400, 540))
    a = np.asarray(c).astype(np.float32)
    m = snake_mask(a)
    ys, xs = np.where(m)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape
    s = max(h, w) + 24
    pad = np.zeros((s, s, 3), np.float32); pm = np.zeros((s, s), bool)
    oy, ox = (s - h) // 2, (s - w) // 2
    pad[oy:oy + h, ox:ox + w] = a; pm[oy:oy + h, ox:ox + w] = m
    icon = Image.fromarray(grade(pad).astype(np.uint8)).resize((150, 150), Image.LANCZOS)
    imask = Image.fromarray((pm * 255).astype(np.uint8)).resize((150, 150), Image.LANCZOS)
    r = 26
    m2 = Image.new("L", (150, 150), 0)
    ImageDraw.Draw(m2).rounded_rectangle([0, 0, 149, 149], radius=r, fill=255)
    imask = Image.composite(imask, Image.new("L", (150, 150), 0), m2)
    out = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    out.paste(icon, (0, 0), imask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, 149, 149], radius=r, outline=(90, 70, 150, 255), width=2)
    return out

def make_neofetch():
    W, H = 780, 460
    img, d = card_frame(W, H, "sulem@kazan ~ zsh")
    icon = snake_head_icon()
    img.paste(icon, (40, 130), icon)
    d = ImageDraw.Draw(img)
    f22, f19 = F(22), F(19)
    x_key, x_val = 240, 380
    y = 96
    rows = [
        ("",        "sulem@kazan"),
        ("sep",     ""),
        ("OS",      "Linux x86_64"),
        ("Shell",   "zsh + tmux"),
        ("Editor",  "neovim"),
        ("Repos",   "37 public"),
        ("Focus",   "embedded - ML - automation"),
        ("Uptime",  "24/7, sleep is a cron"),
        ("Coffee",  "critical"),
        ("Pause",   ""),
        ("Loc",     "Kazan, RU - 55.7963N 49.1088E"),
    ]
    for k, v in rows:
        if k == "sep":
            d.line([x_key, y + 12, 520, y + 12], fill=(36, 28, 58), width=1)
        elif k == "":
            d.text((x_key, y), v, font=f22, fill=VAL_C)
        elif k == "Pause":
            pass
        else:
            d.text((x_key, y), k, font=f22, fill=KEY_C)
            d.text((x_val, y), v, font=f19, fill=VAL_C)
        y += 30
    img.save("assets/widget_neofetch.png")
    print("neofetch ok")

# ========================================================== contribution snake
LEVELS = [(23, 17, 35), (42, 27, 74), (69, 32, 122), (109, 40, 217), (167, 139, 250)]
EATEN = (18, 14, 30)
HEAD_C = (214, 198, 255)

def make_snake_gif():
    """Classic snk run, built from scratch:
    the snake starts short, crawls the serpentine path over the REAL grid,
    ONE cell per frame, steady speed, clean 90-degree turns at the edges,
    eats EVERY square (they go dark for good), grows as it eats."""
    data = json.load(open("assets/src/contrib.json"))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]

    path = []
    for wi, w_ in enumerate(weeks):
        days = w_["contributionDays"]
        order = range(len(days)) if wi % 2 == 0 else range(len(days) - 1, -1, -1)
        for di in order:
            path.append((wi, di, days[di]["contributionCount"]))

    counts = sorted(c for _, _, c in path if c > 0)
    q1 = counts[len(counts) // 4] if counts else 1
    q2 = counts[len(counts) // 2] if counts else 2
    q3 = counts[3 * len(counts) // 4] if counts else 3

    cell, gap = 12, 2
    n_w = len(weeks)
    W = 26 + n_w * (cell + gap) + 26
    H = 86 + 7 * (cell + gap) + 62
    gx = lambda wi: 26 + wi * (cell + gap)
    gy = lambda di: 86 + di * (cell + gap)

    def lvl(c):
        return 0 if c == 0 else (1 if c <= q1 else (2 if c <= q2 else (3 if c <= q3 else 4)))

    lv = {(wi, di): lvl(c) for wi, di, c in path}
    f18, f16, f13 = F(18), F(16), F(13)
    title = f"{total} contributions - last year"
    lx = W - 22 - 5 * 16 - 30

    MAX_LEN = 26
    TAIL_C = (86, 48, 150)

    SS = 3
    def worm_layer(body, head_dir, tongue):
        layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        pts = [((gx(wi) + cell / 2) * SS, (gy(di) + cell / 2) * SS) for wi, di in body]
        n = len(pts)
        for j in range(n - 1, 0, -1):
            t = j / max(1, n - 1)
            r = (5.8 - 3.6 * t) * SS
            col = (int(TAIL_C[0] + (HEAD_C[0] - TAIL_C[0]) * (1 - t)),
                   int(TAIL_C[1] + (HEAD_C[1] - TAIL_C[1]) * (1 - t)),
                   int(TAIL_C[2] + (HEAD_C[2] - TAIL_C[2]) * (1 - t)), 255)
            d.line([pts[j], pts[j - 1]], fill=col, width=max(3, int(2 * r)))
            d.ellipse([pts[j][0] - r, pts[j][1] - r, pts[j][0] + r, pts[j][1] + r], fill=col)
        hx, hy = pts[0]
        r_h = 6.4 * SS
        d.ellipse([hx - r_h, hy - r_h, hx + r_h, hy + r_h],
                  fill=(HEAD_C[0], HEAD_C[1], HEAD_C[2], 255))
        if head_dir is not None and n > 1:
            ex, ey = head_dir
            for sg in (-1, 1):
                px = hx + ex * 2.0 * SS - ey * sg * 2.6 * SS
                py = hy + ey * 2.0 * SS - ex * sg * 2.6 * SS
                d.ellipse([px - 1.8 * SS, py - 1.8 * SS, px + 1.8 * SS, py + 1.8 * SS],
                          fill=(251, 247, 255, 255))
                qx = px + ex * 0.9 * SS
                qy = py + ey * 0.9 * SS
                d.ellipse([qx - 1.0 * SS, qy - 1.0 * SS, qx + 1.0 * SS, qy + 1.0 * SS],
                          fill=(24, 14, 40, 255))
            if tongue:
                t1x = hx + ex * (r_h + 2 * SS) - ey * 1.4 * SS
                t1y = hy + ey * (r_h + 2 * SS) - ex * 1.4 * SS
                t2x = t1x + ex * 3 * SS - ey * 2 * SS
                t2y = t1y + ey * 3 * SS - ex * 2 * SS
                d.line([hx + ex * r_h * 0.7, hy + ey * r_h * 0.7, t1x, t1y],
                       fill=(255, 96, 160, 255), width=2 * SS)
                d.line([t1x, t1y, t2x, t2y], fill=(255, 96, 160, 255), width=2 * SS)
        return layer.resize((W, H), Image.LANCZOS)

    def frame(step_n, eaten_set, body, head_dir, tongue):
        img = Image.new("RGB", (W, H), CARD_BG)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=16, outline=CARD_BORDER, width=1)
        d.text((26, 20), title, font=f18, fill=(126, 110, 168))
        d.line([16, 52, W - 16, 52], fill=(30, 24, 48), width=1)
        for (wi, di), l in lv.items():
            d.rounded_rectangle([gx(wi), gy(di), gx(wi) + cell, gy(di) + cell],
                                radius=2, fill=LEVELS[l])
        for (wi, di) in eaten_set:
            d.rounded_rectangle([gx(wi), gy(di), gx(wi) + cell, gy(di) + cell],
                                radius=2, fill=EATEN)
        if body:
            wl = worm_layer(body, head_dir, tongue)
            img.paste(wl, (0, 0), wl)
        # progress bar
        bx0, bx1, by = 26, W - 26, H - 36
        d.rounded_rectangle([bx0, by, bx1, by + 9], radius=4, fill=(24, 19, 38))
        frac = step_n / max(1, len(path))
        fillw = int((bx1 - bx0) * frac)
        if fillw > 6:
            d.rounded_rectangle([bx0, by, bx0 + fillw, by + 9], radius=4,
                                fill=(139, 92, 246))
        for i, col in enumerate(LEVELS):
            d.rounded_rectangle([lx + i * 16, H - 62, lx + i * 16 + 11, H - 51],
                                radius=2, fill=col)
        d.text((lx + 5 * 16 + 6, H - 64), "less", font=f13, fill=DIM_C)
        d.text((26, H - 62),
               f"snake mode - {step_n}/{len(path)} - it never stops",
               font=f16, fill=DIM_C)
        return img

    frames, durations = [], []
    eaten = set()
    frames.append(frame(0, set(), [], None, False)); durations.append(600)

    body = []
    head_dir = None
    for k, (wi, di, c) in enumerate(path):
        eaten.add((wi, di))
        body.insert(0, (wi, di))
        if len(body) > MAX_LEN:
            body = body[:MAX_LEN]
        if k >= 1:
            pw, pd, _ = path[k - 1]
            head_dir = (1, 0) if wi > pw else ((-1, 0) if wi < pw else ((0, 1) if di > pd else (0, -1)))
        frames.append(frame(k + 1, set(eaten), list(body), head_dir,
                            tongue=(k % 32 == 24)))
        durations.append(78)

    frames.append(frame(len(path), set(eaten), list(body), None, False)); durations.append(1300)

    q = [f.quantize(26, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    q[0].save("assets/widget_snake.gif", save_all=True, append_images=q[1:],
              duration=durations, loop=0, optimize=True, disposal=1)
    print("contribution snake gif:", len(frames), "frames - eats all", len(path))

# ================================================================== quotes
QUOTES = [
    ("What stands in the way becomes the way.", "Marcus Aurelius"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("If I do it twice, it becomes a script.", "Sulem"),
    ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
    ("The obstacle is the way - debug accordingly.", "Sulem"),
]

def make_quotes():
    W, H = 1600, 250
    bgc = tuple(CANVAS)
    serif = ImageFont.truetype(SERIF, 46)
    mono = F(22)

    def layer(text, author):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.polygon([(W // 2 - 6, 36), (W // 2, 29), (W // 2 + 6, 36), (W // 2, 43)],
                  fill=(124, 58, 237, 255))
        q = "\u201c" + text + "\u201d"
        s = 46
        while s > 26:
            f = ImageFont.truetype(SERIF, s)
            if d.textlength(q, font=f) <= 1400:
                break
            s -= 2
        wq = d.textlength(q, font=f)
        d.text(((W - wq) / 2, 84), q, font=f, fill=(216, 204, 245, 255))
        # subtle fake-italic shear on the text block
        img = img.transform((W, H), Image.AFFINE, (1, -0.12, 30, 0, 1, 0),
                            resample=Image.BICUBIC)
        d = ImageDraw.Draw(img)
        au = "- " + author + " -"
        wa = d.textlength(au, font=mono)
        d.text(((W - wa) / 2, 186), au, font=mono, fill=(122, 106, 162, 255))
        return img

    bg = Image.new("RGB", (W, H), bgc).convert("RGBA")
    frames, durations = [], []
    NIN, NHOLD, NOUT = 9, 24, 9

    def scaled(lay, factor):
        if factor >= 0.999:
            return lay
        a = np.asarray(lay.getchannel("A"), np.float32) * factor
        l2 = lay.copy()
        l2.putalpha(Image.fromarray(a.astype(np.uint8)))
        return l2

    for text, author in QUOTES:
        lay = layer(text, author)
        for k in range(1, NIN + 1):                       # fade in + rise
            fr = bg.copy()
            fr.alpha_composite(scaled(lay, k / NIN), (0, int((1 - k / NIN) * 12)))
            frames.append(fr.convert("RGB")); durations.append(45)
        for _ in range(NHOLD):                            # hold
            fr = bg.copy(); fr.alpha_composite(lay)
            frames.append(fr.convert("RGB")); durations.append(120)
        for k in range(NOUT):                             # fade out + lift
            fr = bg.copy()
            fr.alpha_composite(scaled(lay, 1 - k / NOUT), (0, -int(k * 1.4)))
            frames.append(fr.convert("RGB")); durations.append(40)

    q = [f.quantize(64, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    q[0].save("assets/widget_quotes.gif", save_all=True, append_images=q[1:],
              duration=durations, loop=0, optimize=True, disposal=2)
    print("quotes gif:", len(frames), "frames,", len(QUOTES), "quotes")

# ============================================================= wall slabs
def wall_texture(W, H, seed, brick_w=210, brick_h=62):
    """Dark plastered brick wall: multi-scale noise, joints, stains."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32) + np.array([12, 9, 20], np.float32)
    big = rng.normal(0, 1, (H // 8 + 2, W // 8 + 2)).astype(np.float32)
    big = ndimage.zoom(big, 8, order=1)[:H, :W]
    base += big[..., None] * np.array([2.6, 2.2, 3.4], np.float32)
    base += rng.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    tex = Image.new("L", (W, H), 0)
    td = ImageDraw.Draw(tex)
    for row, y in enumerate(range(0, H, brick_h)):
        td.line([(0, y), (W, y)], fill=15, width=2)
        off = (row % 2) * (brick_w // 2)
        for x in range(off, W, brick_w):
            td.line([(x, y), (x, min(y + brick_h, H))], fill=10, width=2)
    t = np.asarray(tex, np.float32)[..., None] / 255.0
    base *= (1 - t * 0.55)
    for _ in range(4):
        sx, sy = rng.integers(0, W), rng.integers(0, H)
        rr = rng.integers(70, 200)
        msk = ((xx - sx) ** 2 + (yy - sy) ** 2) < rr ** 2
        base[msk] -= np.array([3.0, 2.5, 4.0], np.float32)
    shade = np.ones(H, np.float32)
    f = 70
    shade[:f] = np.linspace(0.55, 1, f)
    shade[-f:] = np.linspace(1, 0.55, f)
    base *= shade[:, None, None]
    return np.clip(base, 0, 255)

def make_walls():
    """Full-width horizontal slabs: snake crawling over real brickwork.
    Double joint-lines + bolts at top/bottom read as the edges of posts."""
    W = 1600
    specs = [  # (H, x0, x1, rot, flip, y_crop_frac, seed)
        (250, 0.05, 0.55, -2.4, False, 0.50, 41),
        (270, 0.24, 0.74,  1.9, True,  0.46, 42),
        (250, 0.10, 0.62, -1.4, False, 0.54, 43),
        (260, 0.33, 0.83,  2.2, False, 0.48, 44),
        (250, 0.16, 0.66, -2.0, True,  0.52, 45),
        (260, 0.40, 0.90,  1.6, False, 0.50, 46),
        (250, 0.28, 0.78, -1.8, True,  0.47, 47),
        (260, 0.14, 0.64,  2.1, False, 0.53, 48),
    ]
    for i, (Hh, x0f, x1f, ang, flip, ycf, seed) in enumerate(specs):
        canvas = Image.fromarray(wall_texture(W, Hh, seed).astype(np.uint8), "RGB")

        band = raw.crop((int(raw.width * x0f), 205, int(raw.width * x1f), 505))
        arr = np.asarray(band).astype(np.float32)
        m = snake_mask(arr, strong=True)
        ys, xs = np.where(m)
        arr = arr[max(0, ys.min() - 12):ys.max() + 12, max(0, xs.min() - 12):xs.max() + 12]
        m = m[max(0, ys.min() - 12):ys.max() + 12, max(0, xs.min() - 12):xs.max() + 12]
        img = Image.fromarray(grade(arr).astype(np.uint8))
        mim = Image.fromarray((m * 255).astype(np.uint8))
        img = img.rotate(ang, expand=True, resample=Image.BICUBIC)
        mim = mim.rotate(ang, expand=True, resample=Image.BICUBIC)
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            mim = mim.transpose(Image.FLIP_LEFT_RIGHT)
        sc = (W + 60) / img.width
        img = img.resize((W + 60, max(1, int(img.height * sc))), Image.LANCZOS)
        mim = mim.resize(img.size, Image.LANCZOS)
        cy0 = int(max(0, min((img.height - Hh) * ycf, img.height - Hh)))
        img = img.crop((0, cy0, W + 60, cy0 + Hh))
        mim = mim.crop((0, cy0, W + 60, cy0 + Hh))

        a = np.asarray(mim, np.float32) / 255.0
        sa = np.asarray(img, np.float32)
        if a.shape[0] < Hh:
            pa = np.zeros((Hh, W + 60), np.float32); pa[:a.shape[0]] = a; a = pa
            ps = np.zeros((Hh, W + 60, 3), np.float32); ps[:sa.shape[0]] = sa; sa = ps
        a, sa = a[:Hh, :W], sa[:Hh, :W]

        env = np.ones(W, np.float32)
        f = 110
        env[:f] = np.linspace(0, 1, f) ** 1.3
        env[-f:] = np.linspace(1, 0, f) ** 1.3
        aa = a * env[None, :]

        sh = Image.fromarray((aa * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(12))
        sh_a = np.asarray(sh, np.float32) / 255.0 * 0.6
        sh_shift = np.zeros_like(sh_a)
        sh_shift[10:, 14:] = sh_a[:-10, :-14]
        ca = np.asarray(canvas, np.float32)
        ca = ca * (1 - sh_shift[..., None])

        body = aa > 0.4
        rim = ndimage.binary_dilation(body, iterations=2) & ~body
        rim = ndimage.gaussian_filter(rim.astype(np.float32), 0.8) * 0.28
        ca = ca * (1 - aa[..., None]) + sa * aa[..., None]
        ca = ca * (1 - rim[..., None]) + np.array([172, 140, 255], np.float32) * rim[..., None]

        out = Image.fromarray(np.clip(ca, 0, 255).astype(np.uint8), "RGB")
        d = ImageDraw.Draw(out)
        d.line([0, 3, W, 3], fill=(46, 34, 72), width=1)
        d.line([0, 6, W, 6], fill=(26, 20, 42), width=1)
        d.line([0, Hh - 7, W, Hh - 7], fill=(26, 20, 42), width=1)
        d.line([0, Hh - 4, W, Hh - 4], fill=(46, 34, 72), width=1)
        for x in (18, W - 18):
            d.ellipse([x - 3, 10, x + 3, 16], fill=(58, 44, 92))
            d.ellipse([x - 3, Hh - 16, x + 3, Hh - 10], fill=(58, 44, 92))
        out.save(f"assets/wall_{i + 1}.png", optimize=True)
        out.save(f"assets/wall_{i + 1}.jpg", quality=88, optimize=True)
    print("walls ok: 8 horizontal full-width slabs")

# ==================================================================== footer
def shift_m(tm, dy):
    out = np.zeros_like(tm)
    h, w = tm.shape
    ys0, ys1 = max(0, dy), h + min(0, dy)
    out[ys0:ys1] = tm[ys0 - dy:ys1 - dy]
    return out

def make_footer():
    """Realistic tail, ZERO distortion. A genuine tail segment of the source
    snake - used as shot (uniform scale + 2 degree tilt only, no warping,
    no flattening) - runs under the wordmark, its real sharp tip rising
    past 'CODE.'."""
    W, H = 1600, 430
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.52)) ** 2 + ((yy - H * 0.58) / (H * 0.58)) ** 2)
    bloom = np.exp(-(r ** 2) * 2.4)[..., None] * np.array([16, 9, 30], np.float32)
    bg = np.zeros((H, W, 3), np.float32) + np.array([5, 3, 9], np.float32) + bloom
    rng = np.random.default_rng(3)
    bg += rng.normal(0, 1.8, (H, W, 1)).astype(np.float32)
    canvas = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")

    # ---------------- wordmark
    WORD = "YOU ARE WHAT YOU CODE."
    size = 52
    ftr = F(size, DISP)
    d0 = ImageDraw.Draw(Image.new("L", (10, 10)))
    words = WORD.split(" ")
    space_w = d0.textlength(" ", font=ftr)
    widths = [d0.textlength(w_, font=ftr) for w_ in words]
    tw = int(sum(widths) + space_w * (len(words) - 1))
    if tw > 1160:
        size = int(size * 1160 / tw)
        ftr = F(size, DISP)
        space_w = d0.textlength(" ", font=ftr)
        widths = [d0.textlength(w_, font=ftr) for w_ in words]
        tw = int(sum(widths) + space_w * (len(words) - 1))
    tx = (W - tw) // 2
    ty = 150

    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    x = tx
    for w_, w_w in zip(words, widths):
        md.text((x, ty), w_, font=ftr, fill=255)
        x += w_w + space_w
    tm = np.asarray(mask, np.float32) / 255.0
    bb = ftr.getbbox("YOU")
    band_bot = ty + bb[3]
    text_end = tx + tw

    # ---------------- REAL tail segment, as shot
    seg = raw.crop((int(raw.width * 0.38), 0, int(raw.width * 0.998), raw.height))
    arr = np.asarray(seg).astype(np.float32)
    m = arr.max(axis=2) > 15
    lab, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (int(np.argmax(sizes)) + 1)
    # gentle cavity repair only - keep the thin tip intact (no opening!)
    m = ndimage.binary_closing(m, structure=np.ones((9, 9)))
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_closing(m, structure=np.ones((21, 21)))
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_closing(m, structure=np.ones((41, 1)))
    m = ndimage.binary_fill_holes(m)
    ys, xs = np.where(m)
    y0, y1 = max(0, ys.min() - 26), min(arr.shape[0], ys.max() + 26)
    x0, x1 = 0, min(arr.shape[1], xs.max() + 12)
    arr = arr[y0:y1, x0:x1]
    m = m[y0:y1, x0:x1]

    img = Image.fromarray(grade(arr).astype(np.uint8))
    mim = Image.fromarray((m * 255).astype(np.uint8))
    img = img.rotate(2.2, expand=True, resample=Image.BICUBIC)     # rise to the right
    mim = mim.rotate(2.2, expand=True, resample=Image.BICUBIC)
    sc = (W + 30) / img.width                                      # uniform, ~1.1x only
    img = img.resize((W + 30, max(1, int(img.height * sc))), Image.LANCZOS)
    mim = mim.resize(img.size, Image.LANCZOS)

    ma = np.asarray(mim, np.float32) / 255.0
    ys2 = np.where(ma > 0.4)[0]
    tail_cy = float(ys2.mean())
    target_cy = band_bot + 118                                     # under the line
    off = (int(-20), int(target_cy - tail_cy))

    strand_rgb = Image.new("RGB", (W, H), (0, 0, 0))
    strand_am = Image.new("L", (W, H), 0)
    strand_rgb.paste(img, off, mim)
    strand_am.paste(mim, off, mim)
    strand_a = np.asarray(strand_am, np.float32) / 255.0
    sa = np.asarray(strand_rgb, np.float32)

    # ---------------- composite: tail behind the letters (plain)
    ca = np.asarray(canvas, np.float32).copy()
    sh = Image.fromarray((strand_a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(12))
    sh_a = np.asarray(sh, np.float32) / 255.0 * 0.45
    sh_shift = np.zeros_like(sh_a)
    sh_shift[10:, 12:] = sh_a[:-10, :-12]
    ca = ca * (1 - sh_shift[..., None])

    ca = ca * (1 - strand_a[..., None]) + sa * strand_a[..., None]

    grad = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    l_top = np.array([124, 95, 190], np.float32)
    l_bot = np.array([58, 39, 102], np.float32)
    lrgb = np.zeros((H, W, 3), np.float32) + l_top[None, None, :] \
        + (l_bot - l_top)[None, None, :] * grad[..., None]
    edge_top = np.clip(tm - shift_m(tm, 3), 0, 1)
    lrgb += edge_top[..., None] * np.array([205, 185, 250], np.float32) * 0.75
    halo = mask.filter(ImageFilter.GaussianBlur(24))
    halo_a = (np.asarray(halo, np.float32) / 255.0) * 0.5
    ca = ca * (1 - halo_a[..., None]) + np.array([52, 30, 96], np.float32) * halo_a[..., None]
    # letters cast a soft shadow on the tail beneath
    shl = Image.fromarray((tm * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(8))
    shl_a = np.asarray(shl, np.float32) / 255.0 * 0.4
    shl_shift = np.zeros_like(shl_a)
    shl_shift[8:, 10:] = shl_a[:-8, :-10]
    ca = ca * (1 - shl_shift[..., None])
    la = tm[..., None]
    ca = ca * (1 - la) + lrgb * la

    strand = strand_a > 0.4
    rim = ndimage.binary_dilation(strand, iterations=2) & ~strand
    rim = ndimage.gaussian_filter(rim.astype(np.float32), 0.8) * 0.26 * (1 - tm)
    ca = ca * (1 - rim[..., None]) + np.array([172, 140, 255], np.float32) * rim[..., None]
    canvas = Image.fromarray(np.clip(ca, 0, 255).astype(np.uint8), "RGB")

    d = ImageDraw.Draw(canvas)
    sub = "- built from an empty folder -"
    f19 = F(19)
    d.text(((W - d.textlength(sub, font=f19)) / 2, 372), sub, font=f19, fill=(120, 105, 160))
    d.text((34, H - 40), "OGSULEM", font=F(18), fill=(88, 76, 122))
    right = "KAZAN - 55.7963 N 49.1088 E"
    d.text((W - 34 - d.textlength(right, font=F(18)), H - 40), right, font=F(18), fill=(88, 76, 122))
    L, m_ = 26, 22
    for cx, cy, sx, sy in [(m_, m_, 1, 1), (W - m_, m_, -1, 1), (m_, H - m_, 1, -1), (W - m_, H - m_, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=(70, 56, 110), width=2)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=(70, 56, 110), width=2)
    canvas.save("assets/footer.png", optimize=True, compress_level=9)
    canvas.save("assets/footer.jpg", quality=88, optimize=True)
    print("footer ok: real tail, as-shot, zero warp")

# ================================================================ metrics
def make_metrics():
    data = json.load(open("assets/src/contrib.json"))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    days = [dd["contributionCount"] for w_ in cal["weeks"] for dd in w_["contributionDays"]]
    active = sum(1 for c in days if c > 0)
    # longest streak
    best = cur = 0
    for c in days:
        cur = cur + 1 if c > 0 else 0
        best = max(best, cur)
    stats = [
        (str(total), "contributions / yr"),
        (str(active), "active days"),
        (str(best), "longest streak"),
        ("37", "public repos"),
        ("6+", "languages"),
        ("2023", "shipping since"),
    ]
    W, H = 1600, 150
    img = Image.new("RGB", (W, H), CARD_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=16, outline=CARD_BORDER, width=1)
    n = len(stats)
    seg = W // n
    f40, f17 = F(40), F(17)
    for i, (big, small) in enumerate(stats):
        cx = seg * i + seg // 2
        bw_ = d.textlength(big, font=f40)
        d.text((cx - bw_ / 2, 34), big, font=f40, fill=(216, 204, 245))
        sw_ = d.textlength(small, font=f17)
        d.text((cx - sw_ / 2, 92), small, font=f17, fill=(116, 100, 158))
        if i:
            d.line([seg * i, 26, seg * i, H - 26], fill=(30, 24, 48), width=1)
    img.save("assets/widget_metrics.png", optimize=True)
    print("metrics ok")

# ---------------------------------------------------------------- dispatcher
if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "snake":
        make_snake_gif()
    else:
        make_typing()
        make_neofetch()
        make_snake_gif()
        make_quotes()
        make_walls()
        make_footer()
        make_metrics()
