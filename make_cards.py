"""Still image cards (1080x1350, Instagram 4:5) for feed posts, drawn in the same style as the reels.

Each card illustrates the first line of its caption, so the picture always matches the tag line:
    python3 make_cards.py            # renders every card in CARDS into cards/
    python3 make_cards.py home_reset # one card

Cards are listed in CARDS at the bottom: key, headline, sub line, accent colour, badge and the
drawing to use (a character from make_reels.CAST plus a prop, or a small scene drawn here).
"""
import math, os, sys
from PIL import Image, ImageDraw
import make_reels as R
from make_reels import font, wrap, sprite, tint, shade, CORAL, TEAL, SAGE, SUN, INK, WHITE, VIOLET, SKY, PINK, LIME, PARTNER

CW, CH = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("WCM_OUT", os.path.join(HERE, "cards"))
NAVY = (36, 44, 92)


def gradient(top, bottom):
    import numpy as np
    col = np.linspace(np.array(top, float), np.array(bottom, float), CH)
    return Image.fromarray(np.repeat(col[:, None, :], CW, axis=1).astype("uint8"), "RGB")


def background(accent, dark=False):
    partner = PARTNER.get(accent, SUN)
    if dark:
        im = gradient(NAVY, shade(VIOLET, 0.45))
    else:
        im = gradient(tint(accent, 0.72), tint(partner, 0.62))
    d = ImageDraw.Draw(im, "RGBA")
    for (x, y, r, c) in [(150, 260, 290, accent), (980, 420, 230, partner), (960, 1180, 300, accent), (90, 1280, 240, partner)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (40 if dark else 70,))
    d.polygon([(700, 0), (960, 0), (460, CH), (200, CH)], fill=WHITE + (40,))
    for i, (x, y, r) in enumerate([(120, 700, 14), (990, 180, 12), (880, 820, 10), (60, 1000, 16), (1010, 1000, 12), (300, 1200, 10), (760, 110, 18)]):
        c = [accent, partner, WHITE, SUN, PINK, SKY][i % 6] + (170,)
        if i % 3 == 0: d.rectangle([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], fill=c)
        else: d.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=c)
    return im


def badge(im, label, color):
    d = ImageDraw.Draw(im); f = font("Bold", 32)
    tw = d.textlength(label.upper(), font=f)
    d.rounded_rectangle([CW / 2 - tw / 2 - 30, 70, CW / 2 + tw / 2 + 30, 132], 31, fill=shade(color, 0.1))
    d.text((CW / 2 - tw / 2, 77), label.upper(), font=f, fill=WHITE)


def text_block(im, text, f, y, color=INK, maxw=940, lh=1.16, box=None, shadow=None):
    d = ImageDraw.Draw(im, "RGBA"); lines = wrap(d, text, f, maxw); hh = int(f.size * lh)
    if box:
        widest = max(d.textlength(l, font=f) for l in lines); pad = 34
        d.rounded_rectangle([CW / 2 - widest / 2 - pad, y - pad * 0.6, CW / 2 + widest / 2 + pad, y + hh * len(lines) + pad * 0.4], 34, fill=box)
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f); x = (CW - tw) / 2
        if shadow: d.text((x + 4, y + i * hh + 5), l, font=f, fill=shadow)
        d.text((x, y + i * hh), l, font=f, fill=color)
    return y + hh * len(lines)


def wordmark(im, y=1265, light=False):
    d = ImageDraw.Draw(im); f = font("Bold", 36); s = "Wholeness Community"; tw = d.textlength(s, font=f)
    c = WHITE if light else shade(TEAL, 0.2)
    cx, cy, r = CW / 2 - tw / 2 - 40, y + 24, 22
    d.polygon([(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)], fill=c)
    d.text((CW / 2 - tw / 2 + 5, y), s, font=f, fill=c)


def sticker(im, text, color, x, y, angle=-10):
    f = font("Bold", 34); tmp = ImageDraw.Draw(im); tw = int(tmp.textlength(text.upper(), font=f))
    lab = Image.new("RGBA", (tw + 60, 80), (0, 0, 0, 0)); d = ImageDraw.Draw(lab)
    d.rounded_rectangle([0, 0, tw + 60, 80], 20, fill=color, outline=WHITE, width=5); d.text((30, 16), text.upper(), font=f, fill=WHITE)
    lab = lab.rotate(angle, expand=True, resample=Image.BICUBIC)
    im.paste(lab, (int(x - lab.width / 2), int(y - lab.height / 2)), lab)


def card(im, x0, y0, x1, y1, fill=WHITE + (235,), r=40):
    ImageDraw.Draw(im, "RGBA").rounded_rectangle([x0, y0, x1, y1], r, fill=fill)


def numbered(im, items, y, accent, x0=90, x1=CW - 90, row=150, f=None):
    f = f or font("Medium", 40); d = ImageDraw.Draw(im, "RGBA")
    for i, item in enumerate(items):
        card(im, x0, y, x1, y + row - 20)
        d.rounded_rectangle([x0, y, x0 + 22, y + row - 20], 10, fill=accent)
        d.ellipse([x0 + 42, y + 26, x0 + 120, y + 104], fill=accent)
        num = str(i + 1); fn = font("Bold", 44); tw = d.textlength(num, font=fn)
        d.text((x0 + 81 - tw / 2, y + 32), num, font=fn, fill=WHITE)
        lines = wrap(d, item, f, x1 - x0 - 190)
        ty = y + (row - 20) / 2 - 25 * len(lines)
        for j, l in enumerate(lines[:2]): d.text((x0 + 150, ty + j * 50), l, font=f, fill=INK)
        y += row
    return y


# ---------------- small scenes ----------------
def draw_person(im, who, x, y, pose="stand", prop=None, scale=0.8, outfit=None):
    spr = sprite(who, pose, prop, scale, outfit); im.paste(spr, (int(x - spr.width / 2), int(y)), spr)


def sc_counter(im, p):
    """a clean kitchen counter with one plant and a sparkle: home reset"""
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([110, 900, 970, 960], 20, fill=(222, 196, 160)); d.rectangle([150, 960, 930, 1180], fill=(236, 220, 196))
    d.rectangle([150, 960, 930, 1180], outline=(205, 185, 160), width=4)
    for x in (410, 670): d.line([(x, 960), (x, 1180)], fill=(205, 185, 160), width=4)
    # plant
    d.rounded_rectangle([760, 800, 860, 900], 18, fill=CORAL)
    for (dx, dy, r) in [(-40, -60, 48), (40, -70, 48), (0, -110, 52), (-70, -120, 40), (70, -125, 40)]:
        d.ellipse([810 + dx - r, 800 + dy - r, 810 + dx + r, 800 + dy + r], fill=(82, 170, 110))
    # sparkle
    for (cx, cy, s) in [(300, 820, 46), (560, 770, 30)]:
        d.polygon([(cx, cy - s), (cx + s * 0.25, cy - s * 0.25), (cx + s, cy), (cx + s * 0.25, cy + s * 0.25), (cx, cy + s), (cx - s * 0.25, cy + s * 0.25), (cx - s, cy), (cx - s * 0.25, cy - s * 0.25)], fill=SUN)
    draw_person(im, "grace", 300, 540, "wave", scale=0.62)


def sc_notebook(im, p):
    """open notebook with lines (and optional checked items) and a pen"""
    d = ImageDraw.Draw(im, "RGBA"); x0, y0, x1, y1 = 160, 620, 760, 1180
    d.rounded_rectangle([x0 + 14, y0 + 14, x1 + 14, y1 + 14], 30, fill=shade(p["accent"], 0.3) + (90,))
    d.rounded_rectangle([x0, y0, x1, y1], 30, fill=WHITE, outline=(215, 215, 220), width=4)
    d.rectangle([x0, y0, x0 + 70, y1], fill=tint(p["accent"], 0.3))
    for k in range(7): d.ellipse([x0 + 22, y0 + 60 + k * 72, x0 + 48, y0 + 86 + k * 72], fill=WHITE)
    labels = p.get("lines", ["", "", "", "", ""]); f = font("Medium", 36)
    for k, lab in enumerate(labels):
        yy = y0 + 70 + k * 92
        if p.get("checks"):
            d.rounded_rectangle([x0 + 100, yy - 6, x0 + 150, yy + 44], 12, fill=tint(SAGE, 0.6), outline=SAGE, width=4)
            d.line([(x0 + 112, yy + 20), (x0 + 124, yy + 34), (x0 + 142, yy + 4)], fill=shade(TEAL, 0.2), width=7)
            d.text((x0 + 170, yy), lab, font=f, fill=INK)
        elif lab:
            d.text((x0 + 100, yy), lab, font=f, fill=INK)
        else:
            d.line([(x0 + 100, yy + 24), (x1 - 60, yy + 24)], fill=(205, 210, 220), width=5)
    # pen
    d.rounded_rectangle([800, 700, 860, 1120], 28, fill=p["accent"]); d.polygon([(800, 1120), (860, 1120), (830, 1180)], fill=SUN)
    draw_person(im, p.get("who", "leah"), 930, 740, "stand", scale=0.46)


def sc_bed(im, p):
    """bed under a moon and stars: sleep space"""
    d = ImageDraw.Draw(im, "RGBA")
    for (x, y, r) in [(160, 560, 9), (300, 500, 6), (900, 540, 8), (820, 640, 5), (1000, 700, 6), (120, 700, 5)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE + (230,))
    d.ellipse([740, 470, 880, 610], fill=SUN); d.ellipse([700, 450, 830, 580], fill=NAVY)
    d.ellipse([706, 452, 836, 582], fill=shade(VIOLET, 0.45))
    # bed
    d.rounded_rectangle([170, 800, 250, 1150], 20, fill=(110, 80, 60)); d.rounded_rectangle([830, 860, 910, 1150], 20, fill=(110, 80, 60))
    d.rounded_rectangle([200, 940, 880, 1100], 30, fill=(238, 240, 250)); d.rounded_rectangle([200, 990, 880, 1130], 30, fill=p["accent"])
    d.rounded_rectangle([230, 900, 450, 990], 30, fill=WHITE, outline=(215, 215, 230), width=3)
    d.rounded_rectangle([470, 900, 690, 990], 30, fill=WHITE, outline=(215, 215, 230), width=3)
    f = font("Bold", 40)
    for i, (lab, x) in enumerate([("Cool", 300), ("Dark", 540), ("Quiet", 780)]):
        d.rounded_rectangle([x - 90, 700, x + 90, 770], 35, fill=WHITE + (235,)); tw = d.textlength(lab, font=f); d.text((x - tw / 2, 711), lab, font=f, fill=NAVY)


def sc_rating(im, p):
    """1 to 5 sleep rating and a sun: morning check-in"""
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([800, 560, 980, 740], fill=SUN)
    for k in range(12):
        a = math.radians(k * 30); d.line([(890 + 110 * math.cos(a), 650 + 110 * math.sin(a)), (890 + 140 * math.cos(a), 650 + 140 * math.sin(a))], fill=SUN, width=10)
    card(im, 90, 800, 990, 1030)
    f = font("Bold", 58); fs = font("Medium", 34)
    for k in range(5):
        x = 190 + k * 175; c = [CORAL, SUN, LIME, SAGE, TEAL][k]
        d.ellipse([x - 62, 850, x + 62, 974], fill=c); tw = d.textlength(str(k + 1), font=f); d.text((x - tw / 2, 877), str(k + 1), font=f, fill=WHITE)
    for lab, x in (("Rough", 190), ("Great", 890)):
        tw = d.textlength(lab, font=fs); d.text((x - tw / 2, 1050), lab, font=fs, fill=INK)
    draw_person(im, "dev", 230, 480, "wave", scale=0.5)


def sc_box(im, p):
    """box breathing square with the four counts"""
    d = ImageDraw.Draw(im, "RGBA"); x0, y0, s = 300, 640, 480
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], 40, outline=WHITE, width=26)
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], 40, outline=p["accent"], width=14)
    f = font("Bold", 40)
    for lab, (x, y) in (("In 4", (x0 + s / 2, y0 - 70)), ("Hold 4", (x0 + s + 120, y0 + s / 2)), ("Out 4", (x0 + s / 2, y0 + s + 40)), ("Hold 4", (x0 - 120, y0 + s / 2))):
        tw = d.textlength(lab, font=f); d.rounded_rectangle([x - tw / 2 - 24, y - 8, x + tw / 2 + 24, y + 56], 28, fill=WHITE + (235,)); d.text((x - tw / 2, y), lab, font=f, fill=shade(p["accent"], 0.25))
    for (x, y) in ((x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)): d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=SUN, outline=WHITE, width=6)
    draw_person(im, "maya", 540, 690, "stand", scale=0.36)


def sc_library(im, p):
    """stack of books, a play button and headphones: the Learn library"""
    d = ImageDraw.Draw(im, "RGBA")
    for i, c in enumerate([CORAL, SUN, TEAL, VIOLET]):
        y = 1120 - i * 70; dx = (i % 2) * 24
        d.rounded_rectangle([150 + dx, y - 60, 560 + dx, y], 16, fill=c); d.rounded_rectangle([170 + dx, y - 48, 540 + dx, y - 40], 4, fill=WHITE + (150,))
    # play button
    d.ellipse([640, 760, 880, 1000], fill=WHITE); d.polygon([(730, 820), (730, 940), (830, 880)], fill=CORAL)
    # headphones
    d.arc([620, 1000, 900, 1240], 180, 360, fill=INK, width=22)
    d.rounded_rectangle([606, 1100, 666, 1200], 20, fill=INK); d.rounded_rectangle([854, 1100, 914, 1200], 20, fill=INK)
    draw_person(im, "marcus", 330, 560, "wave", scale=0.42)


def sc_legs(im, p):
    """person lying on the floor with legs up a wall"""
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([700, 560, 760, 1180], fill=(236, 228, 214)); d.rectangle([150, 1120, 760, 1180], fill=(222, 196, 160))
    d.rounded_rectangle([200, 1060, 700, 1120], 24, fill=tint(p["accent"], 0.2))   # mat
    skin, shirt, pants = (198, 134, 96), p["accent"], INK
    d.rounded_rectangle([330, 1000, 650, 1070], 40, fill=shirt)              # torso on the floor
    for x in (560, 630):                                                     # legs up the wall
        d.rounded_rectangle([x, 620, x + 60, 1030], 30, fill=pants)
        d.rounded_rectangle([x - 6, 580, x + 66, 630], 20, fill=WHITE, outline=(215, 215, 215), width=3)
    d.ellipse([200, 960, 340, 1100], fill=skin)                              # head
    d.chord([190, 940, 350, 1050], 180, 360, fill=(40, 28, 24))
    d.arc([245, 1010, 300, 1050], 0, 180, fill=INK, width=5)                 # closed eye curve, calm smile
    d.arc([255, 1035, 305, 1070], 0, 180, fill=(150, 45, 55), width=5)
    f = font("Medium", 36); lab = "A few slow breaths"; tw = d.textlength(lab, font=f)
    d.rounded_rectangle([CW / 2 - tw / 2 - 24, 700, CW / 2 + tw / 2 + 24, 760], 30, fill=WHITE + (235,)); d.text((CW / 2 - tw / 2, 709), lab, font=f, fill=shade(p["accent"], 0.3))


def sc_pumpkin(im, p):
    """a friendly pumpkin, one wrapped sweet and an apple: balance"""
    d = ImageDraw.Draw(im, "RGBA"); cx, cy = 420, 930
    d.rounded_rectangle([cx - 30, cy - 260, cx + 30, cy - 180], 16, fill=(90, 130, 60))
    for dx in (-150, 150, 0): d.ellipse([cx + dx - 150, cy - 200, cx + dx + 150, cy + 200], fill=(255, 140, 40), outline=(220, 110, 30), width=5)
    d.ellipse([cx - 150, cy - 200, cx + 150, cy + 200], fill=(255, 150, 50))
    for ex in (-60, 60): d.polygon([(cx + ex - 30, cy - 40), (cx + ex + 30, cy - 40), (cx + ex, cy - 95)], fill=INK)
    d.chord([cx - 90, cy + 20, cx + 90, cy + 130], 0, 180, fill=INK)
    # sweet
    d.ellipse([740, 820, 860, 940], fill=PINK); d.polygon([(740, 880), (690, 840), (690, 920)], fill=PINK); d.polygon([(860, 880), (910, 840), (910, 920)], fill=PINK)
    # apple
    d.ellipse([760, 980, 900, 1120], fill=(220, 50, 60)); d.rounded_rectangle([824, 950, 838, 1000], 6, fill=(90, 60, 40)); d.ellipse([838, 955, 888, 990], fill=(82, 170, 110))
    f = font("Bold", 40)
    for lab, x, y in (("Treat", 800, 740), ("Kindness", 800, 1140)):
        tw = d.textlength(lab, font=f); d.rounded_rectangle([x - tw / 2 - 22, y, x + tw / 2 + 22, y + 60], 30, fill=WHITE + (235,)); d.text((x - tw / 2, y + 8), lab, font=f, fill=shade(CORAL, 0.2))


def sc_clock(im, p):
    """a clock reading 2:00 under a moon: clocks fall back"""
    d = ImageDraw.Draw(im, "RGBA"); cx, cy, r = 470, 900, 230
    for (x, y, rr) in [(160, 560, 8), (300, 520, 6), (900, 600, 7), (1000, 760, 5), (120, 760, 5)]: d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=WHITE + (230,))
    d.ellipse([820, 520, 960, 660], fill=SUN); d.ellipse([780, 500, 910, 630], fill=shade(VIOLET, 0.45))
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=p["accent"]); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    f = font("Bold", 44)
    for h in range(12):
        a = math.radians(h * 30 - 90); lab = str(12 if h == 0 else h)
        if h % 3 == 0:
            tw = d.textlength(lab, font=f); d.text((cx + (r - 60) * math.cos(a) - tw / 2, cy + (r - 60) * math.sin(a) - 26), lab, font=f, fill=INK)
        else:
            d.ellipse([cx + (r - 40) * math.cos(a) - 8, cy + (r - 40) * math.sin(a) - 8, cx + (r - 40) * math.cos(a) + 8, cy + (r - 40) * math.sin(a) + 8], fill=INK)
    d.line([(cx, cy), (cx, cy - 150)], fill=INK, width=16); d.line([(cx, cy), (cx + 95, cy - 55)], fill=INK, width=20)   # 2:00
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=CORAL)
    f2 = font("Bold", 48); lab = "2:00 becomes 1:00"; tw = d.textlength(lab, font=f2)
    d.rounded_rectangle([CW / 2 - tw / 2 - 26, 1170, CW / 2 + tw / 2 + 26, 1240], 34, fill=WHITE + (235,)); d.text((CW / 2 - tw / 2, 1178), lab, font=f2, fill=NAVY)
    draw_person(im, "leah", 880, 820, "wave", scale=0.42)


def sc_jar(im, p):
    """a savings jar filling with coins: health cushion"""
    d = ImageDraw.Draw(im, "RGBA"); x0, y0, x1, y1 = 330, 680, 750, 1120
    d.rounded_rectangle([x0 + 40, y0 - 60, x1 - 40, y0 + 10], 20, fill=TEAL)
    d.rounded_rectangle([x0, y0, x1, y1], 60, fill=(200, 235, 245, 200), outline=(140, 200, 220), width=8)
    for k in range(5):
        for j in range(4):
            x = x0 + 70 + j * 95 + (k % 2) * 40; y = y1 - 60 - k * 56
            if x + 80 > x1 - 20: continue
            d.ellipse([x, y, x + 80, y + 40], fill=SUN, outline=(220, 160, 0), width=4)
    d.ellipse([560, 560, 640, 640], fill=SUN, outline=(220, 160, 0), width=4); f = font("Bold", 38); d.text((585, 575), "$", font=f, fill=(150, 100, 0))
    f2 = font("Bold", 48); lab = "$5 a week adds up"; tw = d.textlength(lab, font=f2)
    d.rounded_rectangle([CW / 2 - tw / 2 - 26, 1150, CW / 2 + tw / 2 + 26, 1220], 34, fill=WHITE + (235,)); d.text((CW / 2 - tw / 2, 1158), lab, font=f2, fill=shade(TEAL, 0.2))
    draw_person(im, "marcus", 170, 700, "wave", scale=0.5)


def sc_bubbles(im, p):
    """two speech bubbles: a vague offer and a specific ask"""
    d = ImageDraw.Draw(im, "RGBA"); f = font("Medium", 38); fb = font("Bold", 38)
    def bubble(text, x0, y0, x1, fill, color, tail_right, fnt):
        lines = wrap(d, text, fnt, x1 - x0 - 70); h = 50 * len(lines) + 50
        d.rounded_rectangle([x0, y0, x1, y0 + h], 36, fill=fill)
        tx = x1 - 90 if tail_right else x0 + 90
        d.polygon([(tx - 30, y0 + h - 2), (tx + 30, y0 + h - 2), (tx + (40 if tail_right else -40), y0 + h + 40)], fill=fill)
        for i, l in enumerate(lines): d.text((x0 + 35, y0 + 25 + i * 50), l, font=fnt, fill=color)
        return y0 + h
    bubble("Let me know if you need anything!", 120, 640, 760, WHITE + (235,), INK, False, f)
    bubble("Could you pick up groceries Thursday?", 320, 850, 960, p["accent"], WHITE, True, fb)
    draw_person(im, "leah", 170, 850, "stand", scale=0.44); draw_person(im, "dev", 920, 1000, "hold", "phone", scale=0.4)
    sticker(im, "Specific asks win", SUN, 300, 1150, angle=-8)


def sc_providers(im, p):
    """three reasons to list, with a provider waving"""
    numbered(im, p["items"], 640, p["accent"], x0=90, x1=720, row=140, f=font("Medium", 36))
    draw_person(im, "marcus", 900, 600, "wave", scale=0.5)
    sticker(im, "Providers welcome", SUN, 880, 1200, angle=8)


def sc_stretch(im, p):
    """a chair and three stretches listed"""
    d = ImageDraw.Draw(im, "RGBA")
    numbered(im, p["items"], 640, p["accent"], x0=90, x1=720, row=140, f=font("Medium", 36))
    # chair
    d.rounded_rectangle([830, 760, 1010, 790], 12, fill=(110, 80, 60)); d.rounded_rectangle([830, 620, 860, 790], 12, fill=(110, 80, 60))
    d.rounded_rectangle([850, 790, 870, 940], 8, fill=(110, 80, 60)); d.rounded_rectangle([980, 790, 1000, 940], 8, fill=(110, 80, 60))
    draw_person(im, "grace", 920, 560, "arms_up", scale=0.42)


def sc_story(im, p):
    """a person with a phone, a DM bubble and a heart"""
    d = ImageDraw.Draw(im, "RGBA")
    draw_person(im, "maya", 400, 600, "hold", "phone", scale=0.62)
    d.rounded_rectangle([620, 700, 960, 820], 36, fill=WHITE + (235,)); d.polygon([(660, 818), (720, 818), (650, 860)], fill=WHITE + (235,))
    f = font("Bold", 40); d.text((660, 734), "DM us your story", font=f, fill=shade(p["accent"], 0.3))
    cx, cy = 820, 960
    d.ellipse([cx - 80, cy - 80, cx, cy], fill=PINK); d.ellipse([cx, cy - 80, cx + 80, cy], fill=PINK)
    d.polygon([(cx - 78, cy - 20), (cx + 78, cy - 20), (cx, cy + 80)], fill=PINK)
    sticker(im, "Your story matters", SUN, 300, 1150, angle=-8)


def sc_path(im, p):
    """a winding path with milestones, rising to a flag"""
    d = ImageDraw.Draw(im, "RGBA")
    pts = [(120, 1150), (260, 1080), (330, 1130), (470, 980), (560, 1030), (690, 860), (760, 900), (900, 720)]
    d.line(pts, fill=WHITE, width=34, joint="curve"); d.line(pts, fill=p["accent"], width=18, joint="curve")
    for i, (x, y) in enumerate(pts):
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=SUN if i % 2 else WHITE, outline=p["accent"], width=5)
    d.rounded_rectangle([890, 560, 910, 720], 8, fill=INK); d.polygon([(910, 570), (1010, 605), (910, 640)], fill=CORAL)
    f = font("Bold", 36)
    for lab, (x, y) in (("Tough week", (330, 1180)), ("Showed up", (690, 940)), ("Kept going", (560, 1080))):
        tw = d.textlength(lab, font=f); d.rounded_rectangle([x - tw / 2 - 18, y, x + tw / 2 + 18, y + 54], 27, fill=WHITE + (235,)); d.text((x - tw / 2, y + 7), lab, font=f, fill=INK)
    draw_person(im, "dev", 230, 600, "wave", scale=0.48)


def sc_person(im, p):
    draw_person(im, p["who"], CW / 2, p.get("y", 560), p.get("pose", "stand"), p.get("prop"), p.get("scale", 0.78), p.get("outfit"))


SCENES = dict(counter=sc_counter, notebook=sc_notebook, bed=sc_bed, rating=sc_rating, box=sc_box, library=sc_library, legs=sc_legs,
              pumpkin=sc_pumpkin, clock=sc_clock, jar=sc_jar, bubbles=sc_bubbles, providers=sc_providers, stretch=sc_stretch,
              story=sc_story, path=sc_path, person=sc_person)


def render_card(p, out_dir=OUT):
    os.makedirs(out_dir, exist_ok=True)
    dark = p.get("dark", False); im = background(p["accent"], dark)
    badge(im, p["badge"], p["accent"])
    ye = text_block(im, p["headline"], font("Bold", p.get("size", 66)), 170, WHITE if dark else INK, maxw=940, shadow=(shade(p["accent"], 0.5) if dark else WHITE + (160,)))
    if p.get("sub"): text_block(im, p["sub"], font("Medium", 38), ye + 30, shade(p["accent"], 0.35), box=WHITE + (205,), maxw=900)
    SCENES[p["scene"]](im, p)
    if p.get("sticker"): sticker(im, p["sticker"], PARTNER.get(p["accent"], SUN) if p["accent"] != SUN else CORAL, p.get("sticker_x", 860), p.get("sticker_y", 600))
    wordmark(im, light=dark)
    path = os.path.join(out_dir, p["key"] + ".jpg"); im.convert("RGB").save(path, quality=92); return path


CARDS = [
    dict(key="home_reset", headline="Five-minute home reset: clear one surface", sub="A nightstand, a counter, the table by your chair", accent=CORAL, badge="Home & Lifestyle", scene="counter", sticker="Try it today", sticker_x=840, sticker_y=640),
    dict(key="breakfast", headline="Before the week takes over, eat something that nourishes you", sub="Oatmeal, an egg, or yogurt with fruit", accent=CORAL, badge="Nutrition & Healing", scene="person", who="layla", prop="oats", pose="hold", y=560, scale=0.76, size=60),
    dict(key="symptom_journal", headline="Try keeping a simple symptom journal", sub="Date, how you felt, what helped, questions for your care team", accent=TEAL, badge="Conditions & Recovery", scene="notebook", lines=["Date", "How I felt", "What helped", "What hurt", "Ask my doctor"], who="leah"),
    dict(key="sleep_space", headline="Make your bedroom a sleep space", sub="Cool, dark and quiet works best for most people", accent=VIOLET, badge="Stress Relief & Rest", scene="bed", dark=True),
    dict(key="sleep_checkin", headline="Morning check-in: how did you sleep?", sub="Rate it 1 to 5 in the comments", accent=SKY, badge="Stress Relief & Rest", scene="rating"),
    dict(key="box_breathing", headline="Midweek stress? Try box breathing", sub="Four rounds, two minutes", accent=SAGE, badge="Stress Relief & Rest", scene="box", sticker="Save this", sticker_x=880, sticker_y=1150),
    dict(key="learn_library", headline="Lunch break reading, anyone?", sub="Articles, guides, videos and podcasts across all nine dimensions", accent=SKY, badge="Learn library", scene="library"),
    dict(key="three_good_things", headline="Before bed, try three good things", sub="Three things that went well today, and why", accent=VIOLET, badge="Mind & Emotions", scene="notebook", lines=["Finished my walk", "Called my sister", "Slept 7 hours"], checks=True, who="maya"),
    dict(key="legs_up", headline="A gentle way to unwind: legs up the wall", sub="A few minutes of slow breathing at the end of the day", accent=SAGE, badge="Stress Relief & Rest", scene="legs"),
    dict(key="halloween", headline="Happy Halloween! Balance beats guilt", sub="Enjoy a treat if you want one. One day does not undo your progress.", accent=SUN, badge="Nutrition & Healing", scene="pumpkin"),
    dict(key="clocks_back", headline="Reminder: clocks fall back an hour tonight", sub="Use the extra hour for sleep, then get morning light", accent=VIOLET, badge="Stress Relief & Rest", scene="clock", dark=True, size=60),
    dict(key="health_cushion", headline="New month money move: start a small health cushion", sub="For copays, prescriptions and wellness services", accent=SUN, badge="Financial Wellness", scene="jar", size=60),
    dict(key="specific_asks", headline="How to actually take people up on their offer to help", sub="Be specific. Specific asks are easier to say yes to.", accent=PINK, badge="Relationships & Support", scene="bubbles", size=58),
    dict(key="providers", headline="Wellness providers: why list on Wholeness?", sub="Health coaches, counselors, nutritionists, yoga teachers and more", accent=TEAL, badge="For providers", scene="providers", items=["You set your own rates", "Sessions by video", "Found by people looking for support"]),
    dict(key="seated_stretches", headline="Been sitting a while? Three seated stretches", sub="Move slowly and stop if anything hurts", accent=TEAL, badge="Physical Wellness", scene="stretch", items=["Slow neck rolls, five each way", "Shoulder shrugs, then let them drop", "A gentle seated twist to each side"]),
    dict(key="share_story", headline="Someone out there is where you were a year ago", sub="If you write or film about your health journey, we would love to feature you", accent=PINK, badge="Community", scene="story", size=60),
    dict(key="progress", headline="Progress, not perfection", sub="You just have to keep coming back to what helps", accent=SKY, badge="Mind & Emotions", scene="path", size=76),
]

if __name__ == "__main__":
    keys = sys.argv[1:] or [c["key"] for c in CARDS]
    for c in CARDS:
        if c["key"] in keys: print(render_card(c), flush=True)
