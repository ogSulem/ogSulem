#!/usr/bin/env python3
"""Divider + stack badges for the SULEM profile. Transparent, theme-proof."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

MONO = "assets/fonts/JetBrainsMono-Regular.ttf"

VIOLET = (167, 139, 250, 255)      # #A78BFA
VIOLET_DIM = (124, 92, 214, 255)
TEXT = (222, 214, 248, 255)

# ------------------------------------------------------------------ divider
# transparent 1600x120: 2px line fading in from both edges, sharp diamond node
W, H = 1600, 120
div = np.zeros((H, W, 4), np.float32)
cy = H // 2

x = np.arange(W, dtype=np.float32)
edge = np.minimum(x, W - 1 - x) / 420.0          # fade over 420px from edges
line_a = np.clip(edge, 0, 1) * 0.85
gap_l, gap_r = W // 2 - 26, W // 2 + 26          # diamond sits in the middle
line_a[gap_l:gap_r + 1] = 0
for yy_ in (cy - 1, cy):
    div[yy_, :, 0] = VIOLET[0]; div[yy_, :, 1] = VIOLET[1]
    div[yy_, :, 2] = VIOLET[2]; div[yy_, :, 3] = line_a * 255

img = Image.fromarray(div.astype(np.uint8), "RGBA")
d = ImageDraw.Draw(img)
S, t = 17, 4                                     # diamond half-diagonal, thickness
cx = W // 2
pts = [(cx, cy - S), (cx + S, cy), (cx, cy + S), (cx - S, cy)]
d.line(pts + [pts[0]], fill=VIOLET, width=t)
# tiny core dot
d.polygon([(cx, cy - 4), (cx + 4, cy), (cx, cy + 4), (cx - 4, cy)], fill=VIOLET)
img.save("assets/divider.png")
print("divider ok")

# ------------------------------------------------------------------- badges
# compact one-row badges: dark fill, 1px violet frame, mono lavender label
def make_badge(label, path):
    f = ImageFont.truetype(MONO, 17)
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    tw = int(tmp.textlength(label, font=f))
    w = tw + 22
    h = 34
    b = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rectangle([0, 0, w - 1, h - 1], fill=(20, 15, 33, 255), outline=(96, 74, 158, 255), width=1)
    d.text(((w - tw) // 2, (h - 17) // 2 - 3), label, font=f, fill=(216, 206, 244, 255))
    b.save(path)

badges = ["C", "C++", "C#", ".NET", "PYTHON", "JS", "TS",
          "STM32", "ESP32", "PYTORCH", "LINUX", "DOCKER"]

import os, glob
os.makedirs("assets/badges", exist_ok=True)
for old in glob.glob("assets/badges/*.png"):
    os.remove(old)
for label in badges:
    make_badge(label, f"assets/badges/{label.lower().replace(' ', '_').replace('-', '_').replace('#', 'sharp').replace('.', 'dot')}.png")
print("badges ok:", len(badges))
