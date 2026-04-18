#!/usr/bin/env python3
"""
Generates the Veltro logo as a PNG.
Veltro — AI-powered logistics intelligence SaaS
Brand: deep navy #0A0F1E + electric cyan #00D4FF
"""

from PIL import Image, ImageDraw, ImageFont
import math, os

W, H = 480, 120
SCALE = 3  # render at 3x, downscale for crispness
WS, HS = W * SCALE, H * SCALE

navy  = (10, 15, 30)
cyan  = (0, 212, 255)
white = (255, 255, 255)

img = Image.new("RGBA", (WS, HS), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# ── Icon: stylized "V" chevron mark ──────────────────────────────────────────
# Pill-shaped background
pad = 12 * SCALE
icon_size = HS - pad * 2
ix = pad
iy = pad

r = 18 * SCALE
draw.rounded_rectangle([ix, iy, ix + icon_size, iy + icon_size], radius=r, fill=navy)

# Draw a bold "V" chevron inside using two thick lines
cx = ix + icon_size // 2
cy = iy + icon_size // 2

lw = 9 * SCALE   # line width
margin_x = 20 * SCALE
margin_top = 22 * SCALE
margin_bot = 18 * SCALE

# Left arm of V (top-left → bottom-center)
x0l = ix + margin_x
y0  = iy + margin_top
x1  = cx
y1  = iy + icon_size - margin_bot

# Right arm of V (bottom-center → top-right)
x0r = ix + icon_size - margin_x
y0r = iy + margin_top

# Draw left arm
draw.line([(x0l, y0), (x1, y1)], fill=cyan, width=lw)
# Draw right arm
draw.line([(x1, y1), (x0r, y0r)], fill=cyan, width=lw)

# Small cyan dot at top of each arm (cap accent)
dot_r = lw // 2
draw.ellipse([x0l - dot_r, y0 - dot_r, x0l + dot_r, y0 + dot_r], fill=cyan)
draw.ellipse([x0r - dot_r, y0r - dot_r, x0r + dot_r, y0r + dot_r], fill=cyan)

# ── Wordmark: "veltro" ────────────────────────────────────────────────────────
# Use a built-in font at large size; PIL's default is limited so we layer
# the wordmark as two colors: "vel" in navy, "tro" in cyan
text_x = ix + icon_size + 24 * SCALE
text_y_name = iy + 4 * SCALE
text_y_tag  = iy + icon_size - 28 * SCALE

# Try to load a system font, fall back gracefully
font_paths = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/SFNSDisplay.ttf",
]
font_name = None
font_tag  = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            font_name = ImageFont.truetype(fp, 58 * SCALE)
            font_tag  = ImageFont.truetype(fp, 17 * SCALE)
            break
        except Exception:
            continue

if font_name is None:
    font_name = ImageFont.load_default()
    font_tag  = ImageFont.load_default()

# Draw full wordmark in navy first
draw.text((text_x, text_y_name), "veltro", font=font_name, fill=navy)

# Re-draw just the last 3 chars "tro" in cyan by measuring "vel" width
vel_bbox  = font_name.getbbox("vel")
vel_width = vel_bbox[2] - vel_bbox[0]
draw.text((text_x + vel_width, text_y_name), "tro", font=font_name, fill=cyan)

# Tagline
draw.text(
    (text_x + 2 * SCALE, text_y_tag),
    "LOGISTICS INTELLIGENCE",
    font=font_tag,
    fill=(120, 140, 170),
)

# ── Downscale to final size ───────────────────────────────────────────────────
img = img.resize((W, H), Image.LANCZOS)

out = os.path.join(os.path.dirname(__file__), "logo.png")
img.save(out, "PNG")
print(f"Logo saved to {out}  ({W}×{H}px)")
