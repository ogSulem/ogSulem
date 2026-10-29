#!/usr/bin/env python3
"""
SULEM banner v3 - "venom" edition.

black background - dark lettering - photoreal violet-black snake COILED
around the wordmark (Gucci/python style weave):
    head enters low from the left (behind S)
    -> crossing UP in the S|U gap   (back -> front)
    -> arc OVER U-L                 (front)
    -> crossing DOWN in the L|E gap (front -> back)
    -> dip UNDER E-M                (back, occluded by glyphs)
    -> crossing UP after M          (back -> front)
    -> tail exits rising into the right margin
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
from scipy.interpolate import CubicSpline

W, H = 1600, 640
CY = 300

# ----------------------------------------------------------------- helpers
def tracked_width(text, font, tracking):
    d = ImageDraw.Draw(Image.new("L", (10, 10)))
    return int(sum(d.textlength(c, font=font) for c in text) + tracking * (len(text) - 1))

def draw_tracked(dr, xy, text, font, tracking, fill=255):
    x, y = xy
    for c in text:
        dr.text((x, y), c, font=font, fill=fill)
        x += dr.textlength(c, font=font) + tracking

def shift(mask_f, dy, dx):
    out = np.zeros_like(mask_f)
    h, w = mask_f.shape
    ys0, ys1 = max(0, dy), h + min(0, dy)
    xs0, xs1 = max(0, dx), w + min(0, dx)
    out[ys0:ys1, xs0:xs1] = mask_f[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out

# --------------------------------------------------------------- background
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# pure black + a very dim purple ambient bloom behind the wordmark zone
r = np.sqrt(((xx - W / 2) / (W * 0.55)) ** 2 + ((yy - CY) / (H * 0.52)) ** 2)
bloom = np.exp(-(r ** 2) * 2.2)[..., None] * np.array([22, 12, 40], np.float32)
bg = np.zeros((H, W, 3), np.float32) + bloom
bg += rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)      # anti-banding noise
fade_h = 46
blend = np.linspace(1, 0, fade_h, dtype=np.float32)[:, None, None]
bg[-fade_h:] = bg[-fade_h:] * blend + np.array([13, 17, 23], np.float32) * (1 - blend)
canvas = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")

# ---------------------------------------------------------------- wordmark
FONT = "assets/fonts/Michroma.ttf"
WORD = "SULEM"
TRACK = 30

size = 300
font = ImageFont.truetype(FONT, size)
tw = tracked_width(WORD, font, TRACK)
size = int(size * 1300 / tw)
font = ImageFont.truetype(FONT, size)
tw = tracked_width(WORD, font, TRACK)

mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
bbox = font.getbbox(WORD)
tx = (W - tw) // 2
ty = CY - (bbox[1] + bbox[3]) // 2
draw_tracked(md, (tx, ty), WORD, font, TRACK)
text_mask = np.asarray(mask, np.float32) / 255.0

rows = np.where(text_mask.max(axis=1) > 0.5)[0]
glyph_top, glyph_bot = int(rows.min()), int(rows.max())
print("glyph band:", glyph_top, glyph_bot)

# letter column ranges -> centers and gaps
col_has = text_mask.sum(axis=0) > 0.5
ranges, start = [], None
for x in range(W):
    if col_has[x] and start is None:
        start = x
    elif not col_has[x] and start is not None:
        if x - start > 8:
            ranges.append((start, x))
        start = None
if start is not None:
    ranges.append((start, W))
print("letter ranges:", ranges)
S_c, U_c, L_c, E_c, M_c = [(a + b) / 2 for a, b in ranges]
g1 = (ranges[0][1] + ranges[1][0]) / 2      # S|U
g3 = (ranges[2][1] + ranges[3][0]) / 2      # L|E
M_end = ranges[4][1]
exit_x = min(W - 90, int(M_end + 55))

AMP_O = (CY - glyph_top) + 26               # arc apex above the caps
AMP_U = (glyph_bot - CY) + 40               # dip bottom under the baseline
AO = float(AMP_O)
AU = float(AMP_U)

# ---- lettering: plum gradient + bevel + 1px lavender outline + soft halo
grad = np.linspace(0, 1, H, dtype=np.float32)[:, None]
l_top = np.array([70, 46, 118], np.float32)     # #462E76
l_bot = np.array([30, 17, 56],  np.float32)     # #1E1138
lrgb = l_top[None, None, :] + (l_bot - l_top)[None, None, :] * grad[..., None]

tm = text_mask
edge_top = np.clip(tm - shift(tm, 3, 0), 0, 1)      # top 3px of strokes
edge_bot = np.clip(tm - shift(tm, -3, 0), 0, 1)
eroded = np.asarray(
    Image.fromarray((tm * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(5)),
    np.float32) / 255.0
outline = np.clip(tm - eroded, 0, 1)                # ~2px contour

letters_img = np.zeros((H, W, 4), np.float32)
letters_img[..., :3] = lrgb
letters_img[..., :3] += edge_top[..., None] * np.array([186, 158, 240], np.float32) * 0.78
letters_img[..., :3] += edge_bot[..., None] * np.array([12, 6, 24], np.float32) * 0.9
letters_img[..., :3] += outline[..., None] * np.array([152, 122, 224], np.float32) * 0.50
letters_img[..., 3] = tm * 255.0

# dark-violet halo behind the lettering (lifts it off the black bg)
halo = mask.filter(ImageFilter.GaussianBlur(26))
halo_a = (np.asarray(halo, np.float32) / 255.0) * 0.55
halo_col = np.array([46, 26, 86], np.float32)
canvas_arr0 = np.asarray(canvas, np.float32).copy()
canvas_arr0 = canvas_arr0 * (1 - halo_a[..., None]) + halo_col[None, None, :] * halo_a[..., None]
canvas = Image.fromarray(np.clip(canvas_arr0, 0, 255).astype(np.uint8), "RGB")

# ------------------------------------------------------------------- snake
raw = Image.open("assets/snake_raw.png").convert("RGB")
# keep only the clean front 62% of the source (head + first crest): the
# generation's tail zone has a faint phantom strand and a near-black belly
# that break the mask. the body then exits the banner's right edge.
raw = raw.crop((0, 0, int(raw.width * 0.62), raw.height))
arr = np.asarray(raw).astype(np.float32)
lum = arr.max(axis=2)
m_snake = lum > 15
lab, n = ndimage.label(m_snake)
if n > 1:
    sizes = ndimage.sum(m_snake, lab, range(1, n + 1))
    m_snake = lab == (int(np.argmax(sizes)) + 1)
m_snake = ndimage.binary_closing(m_snake, structure=np.ones((9, 9)))
m_snake = ndimage.binary_fill_holes(m_snake)

# bridge any residual near-black belly cavities (kept from earlier tunes)
m_snake = ndimage.binary_closing(m_snake, structure=np.ones((21, 21)))
m_snake = ndimage.binary_fill_holes(m_snake)
# vertical-only closing: heals "bites" where the dark belly dipped below
# the threshold and split the column run (main body + thin bottom sliver)
m_snake = ndimage.binary_closing(m_snake, structure=np.ones((45, 1)))
m_snake = ndimage.binary_fill_holes(m_snake)

# solidify the exit: at the crop edge the body is sliced vertically and
# threshold noise leaves notches - fill each column's full [top,bottom] span
xs0 = int(arr.shape[1] * 0.80)
for x in range(xs0, arr.shape[1]):
    ys_ = np.where(m_snake[:, x])[0]
    if len(ys_):
        m_snake[ys_.min():ys_.max() + 1, x] = True

# crop to the snake's vertical band (kill empty margins), pad a little
rows = np.where(m_snake.any(axis=1))[0]
r0, r1 = max(0, rows.min() - 45), min(arr.shape[0], rows.max() + 45)
arr = arr[r0:r1]
m_snake = m_snake[r0:r1]

# venom grade: deep blacks, violet push, slight gamma lift for readability
arr = np.clip((arr - 10) * 1.12 + 10, 0, 255)
arr = 255.0 * np.power(arr / 255.0, 0.86)
lum3 = arr.mean(axis=2, keepdims=True) / 255.0
arr += (1.0 - lum3) * np.array([36, 18, 58], np.float32)
arr[..., 0] = np.clip(arr[..., 0] * 1.06, 0, 255)
arr[..., 1] = np.clip(arr[..., 1] * 0.96, 0, 255)
arr[..., 2] = np.clip(arr[..., 2] * 1.12, 0, 255)
arr = np.clip(arr, 0, 255)

cw, ch = arr.shape[1], arr.shape[0]
th = min(int(ch * W / cw), 620)             # full width, clamp height
snake_r = np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((W, th), Image.LANCZOS), np.float32)
smask_r = np.asarray(Image.fromarray((m_snake * 255).astype(np.uint8)).resize((W, th), Image.LANCZOS), np.float32) / 255.0
y_off = (H - th) // 2
snake = np.zeros((H, W, 3), np.float32); snake[y_off:y_off + th] = snake_r
smask = np.zeros((H, W), np.float32);   smask[y_off:y_off + th] = smask_r

# raw centerline
sw = W
cols = np.where(smask.sum(axis=0) > 4)[0]
cy_cur = np.full(sw, np.nan)
for x in cols:
    ys = np.where(smask[:, x] > 0.5)[0]
    cy_cur[x] = ys.mean()
idx = np.arange(sw)
good = ~np.isnan(cy_cur)
cy_cur = np.interp(idx, idx[good], cy_cur[good])
cy_cur = ndimage.gaussian_filter1d(cy_cur, 21)

# designed coil trajectory
dip_bottom_x = (g3 + exit_x) / 2.0
wp_x = [0,   S_c,      g1,  (g1 + g3) / 2, g3,  E_c,             dip_bottom_x, exit_x, (exit_x + W) / 2, W - 1]
wp_y = [CY + 96, CY + 42, CY,  CY - AO,      CY,  CY + AU * 0.55,  CY + AU,      CY,     CY - 46,          CY - 74]
spline = CubicSpline(wp_x, wp_y)
y_t = spline(idx)

d = (cy_cur - y_t)[None, :]
ys = np.arange(H, dtype=np.float32)[:, None]
coords = np.stack([ys + np.repeat(d, H, axis=0), np.repeat(idx[None, :], H, axis=0)])
snake_w = np.stack([ndimage.map_coordinates(snake[..., c], coords, order=1, mode="constant", cval=0) for c in range(3)], axis=-1)
smask_w = ndimage.map_coordinates(smask, coords, order=1, mode="constant", cval=0)
smask_w = np.clip(ndimage.gaussian_filter(smask_w, 1.0) * 1.18, 0, 1)

# luminous rim along the silhouette
body_bin = smask_w > 0.4
rim = ndimage.binary_dilation(body_bin, iterations=3) & ~body_bin
rim = ndimage.gaussian_filter(rim.astype(np.float32), 0.8)
RIM_RGB = np.array([168, 132, 255], np.float32)
RIM_STR = 0.34

# weave: seams sit exactly at the crossings
segs = [(0, g1, False), (g1, g3, True), (g3, exit_x, False), (exit_x, W, True)]
print("seams at:", int(g1), int(g3), int(exit_x))

def paste_segment(dst_arr, seg_x0, seg_x1):
    x0, x1 = max(0, int(seg_x0) - 2), min(sw, int(seg_x1) + 2)
    a = smask_w[:, x0:x1][..., None]
    src = snake_w[:, x0:x1]
    dst_arr[:, x0:x1] = dst_arr[:, x0:x1] * (1 - a) + src * a
    rr = rim[:, x0:x1][..., None] * RIM_STR
    dst_arr[:, x0:x1] = dst_arr[:, x0:x1] * (1 - rr) + RIM_RGB[None, None, :] * rr

def add_shadow(dst_arr, seg_mask_full, blur, dx, dy, alpha):
    sh_img = Image.fromarray((seg_mask_full * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
    sh_a = np.asarray(sh_img, np.float32) / 255.0 * alpha
    shifted = np.zeros_like(sh_a)
    h_, w_ = sh_a.shape
    src = sh_a[max(0, -dy):h_ - max(0, dy), max(0, -dx):w_ - max(0, dx)]
    shifted[max(0, dy):h_ - max(0, -dy), max(0, dx):w_ - max(0, -dx)] = src
    dst_arr[...] = dst_arr * (1 - shifted[..., None])

front_any = np.zeros((H, W), np.float32)
for x0, x1, front in segs:
    if front:
        front_any[:, int(x0):int(x1)] = np.maximum(front_any[:, int(x0):int(x1)], smask_w[:, int(x0):int(x1)])

canvas_arr = np.asarray(canvas, np.float32).copy()

# pass 1: back segments (behind the letters)
for x0, x1, front in segs:
    if not front:
        paste_segment(canvas_arr, x0, x1)

# letters on top (numpy alpha composite)
la = letters_img[..., 3:4] / 255.0
canvas_arr = canvas_arr * (1 - la) + letters_img[..., :3] * la

# front strand casts a soft shadow onto the dark letters
add_shadow(canvas_arr, front_any, 10, 8, 11, 0.50)

# pass 2: front segments
for x0, x1, front in segs:
    if front:
        paste_segment(canvas_arr, x0, x1)

canvas = Image.fromarray(np.clip(canvas_arr, 0, 255).astype(np.uint8), "RGB")

# --------------------------------------------------------------- subtitles
sub = ImageDraw.Draw(canvas)
f1 = ImageFont.truetype("assets/fonts/JetBrainsMono-Regular.ttf", 24)
f2 = ImageFont.truetype("assets/fonts/JetBrainsMono-Regular.ttf", 20)
s1 = "BACKEND \u00b7 EMBEDDED \u00b7 NEURAL NETS \u00b7 AUTOMATION"
t1 = 10
w1 = tracked_width(s1, f1, t1)
draw_tracked(sub, ((W - w1) // 2, 576), s1, f1, t1, fill=(146, 126, 196))
# Kazan coordinates, corners
sub.text((30, H - 44), "55.7963\u00b0 N", font=f2, fill=(94, 82, 128))
wE = int(sub.textlength("49.1088\u00b0 E", font=f2))
sub.text((W - 30 - wE, H - 44), "49.1088\u00b0 E", font=f2, fill=(94, 82, 128))

canvas.save("assets/banner.png", optimize=True)
canvas.convert("RGB").save("assets/banner.jpg", quality=90, optimize=True)
print("banner saved", canvas.size)
