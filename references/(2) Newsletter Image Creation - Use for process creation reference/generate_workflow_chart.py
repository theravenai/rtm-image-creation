"""
Generate Newsletter Image Creation Workflow as a PNG chart.
Output: out/Newsletter Image Creation Workflow.png
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

ROOT      = Path(__file__).parent
BFONT_DIR = ROOT / "(1) Banner Images" / "fonts" / "Archivo_Black"
GFONT_DIR = ROOT / "(2) GMB Share Images" / "fonts"

def lf(path, size):
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()

F_H1    = lf(BFONT_DIR / "ArchivoBlack-Regular.ttf", 21)
F_H2    = lf(BFONT_DIR / "ArchivoBlack-Regular.ttf", 17)
F_BODY  = lf(GFONT_DIR / "OpenSans-Regular.ttf", 15)
F_SMALL = lf(GFONT_DIR / "OpenSans-Regular.ttf", 13)
F_TINY  = lf(GFONT_DIR / "OpenSans-Regular.ttf", 11)

W    = 1200
img  = Image.new("RGB", (W, 3200), (245, 246, 250))
draw = ImageDraw.Draw(img)
CX   = W // 2

C = dict(
    start    = (26, 35, 126),
    process  = (21, 101, 192),
    sonar    = (13, 71, 161),
    ai       = (40, 53, 147),
    pexels   = (25, 118, 210),
    decision = (230, 81, 0),
    approval = (74, 20, 140),
    locked   = (27, 94, 32),
    cmt      = (136, 14, 79),
    askross  = (49, 27, 146),
    done     = (27, 94, 32),
    delete   = (183, 28, 28),
    arrow    = (80, 80, 80),
    revise   = (200, 60, 0),
    yes      = (27, 94, 32),
    white    = (255, 255, 255),
    stage1   = (13, 71, 161),
    stage2   = (27, 94, 32),
    stage3   = (49, 27, 146),
)

def fh(font):
    try:
        return font.size + 5
    except Exception:
        return 18

def wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        t = " ".join(cur + [w])
        bb = font.getbbox(t)
        if bb[2] - bb[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]

def textbox(cx, cy, text, font, color, max_w):
    lines = wrap(text, font, max_w)
    lh    = fh(font)
    sy    = cy - (len(lines) * lh) // 2
    for i, ln in enumerate(lines):
        bb = font.getbbox(ln)
        lw = bb[2] - bb[0]
        draw.text((cx - lw // 2, sy + i * lh), ln, font=font, fill=color)

def rbox(cx, cy, w, h, r, bg, border=None):
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = cx + w // 2, cy + h // 2
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=bg,
                            outline=border or bg, width=2)
    return y0, y1

def diam(cx, cy, w, h, bg, border=None):
    pts = [(cx, cy - h // 2), (cx + w // 2, cy),
           (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(pts, fill=bg)
    if border:
        draw.line(pts + [pts[0]], fill=border, width=2)
    return cy - h // 2, cy + h // 2

def arr(x1, y1, x2, y2, col):
    draw.line([(x1, y1), (x2, y2)], fill=col, width=2)
    a  = math.atan2(y2 - y1, x2 - x1)
    s  = 9
    p1 = (int(x2 - s * math.cos(a - 0.4)), int(y2 - s * math.sin(a - 0.4)))
    p2 = (int(x2 - s * math.cos(a + 0.4)), int(y2 - s * math.sin(a + 0.4)))
    draw.polygon([(x2, y2), p1, p2], fill=col)

def seg(pts, col):
    draw.line(pts, fill=col, width=2)

def lbl(x, y, text, font, col):
    draw.text((x, y), text, font=font, fill=col)

def stage_bar(y, text, col):
    draw.rectangle([60, y, W - 60, y + 40], fill=col)
    bb = F_H2.getbbox(text)
    lw = bb[2] - bb[0]
    draw.text((CX - lw // 2, y + 10), text, font=F_H2, fill=C["white"])

# ─────────────────────────────────────────────────────────────────────────────

y  = 45
LX = 210   # left branch centre
RX = 890   # right branch centre

# ── START ─────────────────────────────────────────────────────────────────────
rbox(CX, y + 28, 380, 56, 28, C["start"], (100, 110, 200))
textbox(CX, y + 28, "RECEIVE NEWSLETTER", F_H1, C["white"], 340)
arr(CX, y + 56, CX, y + 80)
y += 95

# ── STAGE 1 ───────────────────────────────────────────────────────────────────
stage_bar(y, "STAGE 1 — BANNER IMAGE", C["stage1"])
y += 52

arr(CX, y, CX, y + 20)
y += 25

_, d1bot = diam(CX, y + 45, 360, 90, C["decision"], (180, 60, 0))
textbox(CX, y + 45, "Politician or world event?", F_BODY, C["white"], 310)
D1Y = y + 45
y = d1bot + 15

arr(CX - 180, D1Y, LX + 15, y + 5, C["revise"])
lbl(LX - 68, D1Y - 8, "YES", F_TINY, C["revise"])
arr(CX + 180, D1Y, RX - 115, y + 5, C["arrow"])
lbl(CX + 185, D1Y - 8, "NO", F_TINY, C["arrow"])

# Sonar (left)
SY = y + 42
rbox(LX, SY, 270, 80, 10, C["sonar"], (0, 30, 100))
textbox(LX, SY, "Sonar Search\nBrowse candidates\nPick best + no-text rule", F_SMALL, C["white"], 240)

# AI + Pexels (right, stacked)
AI_Y  = y + 30
PX_Y  = y + 92
rbox(RX, AI_Y,  240, 52, 8, C["ai"],     (20, 30, 120))
textbox(RX, AI_Y,  "AI Banner  (Gemini Flash Image)", F_SMALL, C["white"], 215)
rbox(RX, PX_Y,  240, 52, 8, C["pexels"], (10, 80, 165))
textbox(RX, PX_Y,  "Pexels Banner  (stock photo)", F_SMALL, C["white"], 215)

y += 130

# Merge
MY = y
seg([(LX, SY + 40),  (LX, MY), (CX - 245, MY)], C["arrow"])
seg([(RX, PX_Y + 26), (RX, MY), (CX + 245, MY)], C["arrow"])
arr(CX, MY, CX, MY + 20)
y = MY + 25

rbox(CX, y + 42, 490, 78, 10, C["process"], (10, 75, 155))
textbox(CX, y + 42, "Apply Text Rules\nupper-left | lower-left | center | no-text\nFaces rule: text must NEVER cover a face", F_SMALL, C["white"], 455)
arr(CX, y + 81, CX, y + 99)
y += 115

rbox(CX, y + 28, 400, 56, 28, C["approval"], (50, 0, 120))
textbox(CX, y + 28, "Send banner options for APPROVAL", F_BODY, C["white"], 375)
arr(CX, y + 56, CX, y + 78)
y += 90

_, d2bot = diam(CX, y + 42, 310, 85, C["decision"], (180, 60, 0))
textbox(CX, y + 42, "Approved?", F_BODY, C["white"], 270)
D2Y = y + 42
y = d2bot + 12

seg([(CX - 155, D2Y), (30, D2Y), (30, D1Y)], C["revise"])
arr(30, D1Y, CX - 180, D1Y, C["revise"])
lbl(35, D2Y - 16, "Revise", F_TINY, C["revise"])

arr(CX, D2Y + 42, CX, y + 10, C["yes"])
lbl(CX + 6, D2Y + 44, "Approved", F_TINY, C["yes"])

rbox(CX, y + 30, 510, 55, 10, C["locked"], (0, 55, 0))
textbox(CX, y + 30, "BANNER RAW LOCKED   out/{name} Banner Raw.png", F_BODY, C["white"], 475)
y += 75

# ── STAGE 2 ───────────────────────────────────────────────────────────────────
y += 10
stage_bar(y, "STAGE 2 — GMB SHARE IMAGE", C["stage2"])
y += 52

arr(CX, y, CX, y + 20)
y += 25

GMB_Y = y + 42
rbox(CX, GMB_Y, 510, 80, 10, C["process"], (10, 75, 155))
textbox(CX, GMB_Y, "Build GMB Share  using approved Banner Raw\nbuild_newsletter_custom.py  --banner-image out/...\nWrite title1 + intro text", F_SMALL, C["white"], 475)
arr(CX, y + 82, CX, y + 100)
y += 115

rbox(CX, y + 28, 420, 56, 28, C["approval"], (50, 0, 120))
textbox(CX, y + 28, "Send GMB Share for APPROVAL  (title + intro)", F_BODY, C["white"], 395)
arr(CX, y + 56, CX, y + 78)
y += 90

_, d3bot = diam(CX, y + 42, 310, 85, C["decision"], (180, 60, 0))
textbox(CX, y + 42, "Approved?", F_BODY, C["white"], 270)
D3Y = y + 42
y = d3bot + 12

seg([(CX - 155, D3Y), (30, D3Y), (30, GMB_Y)], C["revise"])
arr(30, GMB_Y, CX - 255, GMB_Y, C["revise"])
lbl(35, D3Y - 16, "Revise title / intro", F_TINY, C["revise"])

arr(CX, D3Y + 42, CX, y + 10, C["yes"])
lbl(CX + 6, D3Y + 44, "Approved", F_TINY, C["yes"])

rbox(CX, y + 30, 510, 55, 10, C["locked"], (0, 55, 0))
textbox(CX, y + 30, "GMB SHARE LOCKED   out/{title1} GMB Share.png", F_BODY, C["white"], 475)
y += 75

# ── STAGE 3 ───────────────────────────────────────────────────────────────────
y += 10
stage_bar(y, "STAGE 3 — SECTION IMAGES  (one per section)", C["stage3"])
y += 52

arr(CX, y, CX, y + 20)
y += 25

rbox(CX, y + 28, 510, 50, 10, C["process"], (10, 75, 155))
textbox(CX, y + 28, "For each newsletter section — identify section type", F_BODY, C["white"], 475)
arr(CX, y + 53, CX, y + 73)
y += 85

_, d4bot = diam(CX, y + 45, 360, 90, C["askross"], (30, 0, 100))
textbox(CX, y + 45, "Section type?", F_BODY, C["white"], 310)
D4Y = y + 45
y = d4bot + 15

arr(CX - 180, D4Y, LX + 10, y + 8, (136, 14, 79))
lbl(LX - 70, D4Y - 8, "CMT", F_TINY, (136, 14, 79))
arr(CX + 180, D4Y, RX - 120, y + 8, C["askross"])
lbl(CX + 185, D4Y - 8, "Ask Ross", F_TINY, C["askross"])

CMT_CY = y + 45
AR_CY  = y + 45
rbox(LX,  CMT_CY, 275, 88, 8, C["cmt"],     (100, 0, 50))
textbox(LX,  CMT_CY, "CMT Section\nArticle OG image (default)\n+ Pexels option", F_SMALL, C["white"], 248)
rbox(RX,  AR_CY,  255, 88, 8, C["askross"], (30, 0, 90))
textbox(RX,  AR_CY,  "Ask Ross Section\nAI generated (default)\nPexels on request only", F_SMALL, C["white"], 228)
y += 125

MY2 = y
seg([(LX, CMT_CY + 44),  (LX, MY2), (CX - 245, MY2)], C["arrow"])
seg([(RX, AR_CY + 44),   (RX, MY2), (CX + 245, MY2)], C["arrow"])
arr(CX, MY2, CX, MY2 + 20)
y = MY2 + 25

_, d5bot = diam(CX, y + 42, 310, 85, C["decision"], (180, 60, 0))
textbox(CX, y + 42, "Faces cut off?", F_BODY, C["white"], 270)
D5Y = y + 42
y = d5bot + 12

RRX = W - 45
seg([(CX + 155, D5Y), (RRX, D5Y), (RRX, D4Y)], C["revise"])
arr(RRX, D4Y, CX + 180, D4Y, C["revise"])
lbl(RRX - 125, D5Y - 16, "YES  regenerate", F_TINY, C["revise"])

arr(CX, D5Y + 42, CX, y + 10, C["arrow"])
lbl(CX + 6, D5Y + 44, "NO  faces OK", F_TINY, C["arrow"])

rbox(CX, y + 28, 440, 56, 28, C["approval"], (50, 0, 120))
textbox(CX, y + 28, "Send all section images for APPROVAL", F_BODY, C["white"], 410)
arr(CX, y + 56, CX, y + 78)
y += 90

_, d6bot = diam(CX, y + 42, 310, 85, C["decision"], (180, 60, 0))
textbox(CX, y + 42, "Approved?", F_BODY, C["white"], 270)
D6Y = y + 42
y = d6bot + 12

seg([(CX - 155, D6Y), (30, D6Y), (30, D4Y)], C["revise"])
arr(30, D4Y, CX - 180, D4Y, C["revise"])
lbl(35, D6Y - 16, "Revise", F_TINY, C["revise"])

arr(CX, D6Y + 42, CX, y + 10, C["yes"])
lbl(CX + 6, D6Y + 44, "Approved", F_TINY, C["yes"])

rbox(CX, y + 30, 440, 55, 10, C["delete"], (120, 0, 0))
textbox(CX, y + 30, "Delete rejected assets from out/", F_BODY, C["white"], 415)
arr(CX, y + 57, CX, y + 77)
y += 92

rbox(CX, y + 30, 460, 60, 30, C["done"], (0, 55, 0))
textbox(CX, y + 30, "ALL IMAGES COMPLETE & APPROVED", F_H1, C["white"], 430)
y += 78

# ── Save ──────────────────────────────────────────────────────────────────────
final = img.crop((0, 0, W, y + 40))
out_p = ROOT / "out" / "Newsletter Image Creation Workflow.png"
final.save(str(out_p), "PNG", optimize=True)
print(f"Saved: {out_p}")
print(f"Size: {W} x {y + 40}")
