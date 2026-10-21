import math, os, subprocess, sys, shutil, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/usr/share/fonts/truetype/google-fonts/Poppins-"
def font(w, s): return ImageFont.truetype(F + w + ".ttf", s)

# brand palette, turned up a notch so the feed pops on a phone screen
CREAM = (253, 248, 240); TEAL = (0, 140, 128); SAGE = (82, 196, 150)
CORAL = (255, 112, 80); SUN = (255, 190, 0); INK = (28, 36, 44); WHITE = (255, 255, 255)
VIOLET = (128, 96, 232); SKY = (40, 160, 255); PINK = (255, 92, 150); LIME = (160, 214, 50)
PARTNER = {CORAL: SUN, TEAL: SAGE, SAGE: SKY, SUN: CORAL, VIOLET: PINK, SKY: SAGE, PINK: SUN}
SITE = "wholenesscommunitymarketplace.com"
_G = {"frac": 0.0}   # overall progress through the reel, set by render() for the top bar

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def pop(x):
    """ease out with a little overshoot, so things land with a bounce"""
    x = max(0, min(1, x)); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def tint(c, k):
    return tuple(int(c[i] + (255 - c[i]) * k) for i in range(3))
def shade(c, k):
    return tuple(int(c[i] * (1 - k)) for i in range(3))

# ---------------- characters ----------------
def person(skin, hair, hstyle, shirt, pants, pose="stand", prop=None, eye=None, highlight=None, shape=None, apron=None, outfit=None):
    S = 2; cw, ch = 700 * S, 1100 * S
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = cw // 2
    def L(p, q, w, c):
        d.line([p, q], fill=c, width=w); r = w // 2
        for (x, y) in (p, q): d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    shoulder_y, hip_y = 520 * S, 860 * S
    hx0, hy0, hr = cx, 300*S, 150*S
    if hstyle == "long":
        d.rounded_rectangle([hx0 - 180*S, 180*S, hx0 + 180*S, 640*S], 150*S, fill=hair)
    if hstyle == "curly":
        for a in range(150, 400, 22):
            x = hx0 + 175*S*math.cos(math.radians(a)); y = 290*S + 170*S*math.sin(math.radians(a))
            d.ellipse([x - 70*S, y - 70*S, x + 70*S, y + 70*S], fill=hair)
    if hstyle == "curly_long":
        import random; rnd = random.Random(7)
        d.rounded_rectangle([hx0 - 190*S, 200*S, hx0 + 190*S, 700*S], 150*S, fill=hair)
        curls = []
        for side in (-1, 1):
            for k in range(11):
                y = 190*S + k * 52*S
                x = hx0 + side * (175 + 22 * math.sin(k * 1.3)) * S
                curls.append((x, y, (62 + 8 * math.cos(k * 2.1)) * S))
        for (x, y, r) in curls: d.ellipse([x - r, y - r, x + r, y + r], fill=hair)
        if highlight:
            for (x, y, r) in curls[1::2]:
                ox = rnd.uniform(-0.3, 0.3) * r
                d.arc([x - r*0.7 + ox, y - r*0.7, x + r*0.7 + ox, y + r*0.7], 200, 340, fill=highlight, width=int(9*S))
    # legs
    if pose == "squat":
        L((cx - 70*S, hip_y), (cx - 160*S, 960*S), 62*S, pants); L((cx - 160*S, 960*S), (cx - 110*S, 1060*S), 62*S, pants)
        L((cx + 70*S, hip_y), (cx + 160*S, 960*S), 62*S, pants); L((cx + 160*S, 960*S), (cx + 110*S, 1060*S), 62*S, pants)
        foot_y = 1070*S
    else:
        L((cx - 55*S, hip_y), (cx - 70*S, 1050*S), 62*S, pants); L((cx + 55*S, hip_y), (cx + 70*S, 1050*S), 62*S, pants)
        foot_y = 1060*S
    for sx in (-1, 1):
        fx = cx + sx * (125 if pose == "squat" else 80) * S
        d.rounded_rectangle([fx - 50*S, foot_y - 20*S, fx + 50*S, foot_y + 20*S], 20*S, fill=WHITE, outline=(220,220,220), width=3*S)
        d.rounded_rectangle([fx - 50*S, foot_y - 20*S, fx + 50*S, foot_y - 6*S], 8*S, fill=shirt)   # sneaker stripe
    # arms behind torso
    arm = 44 * S
    if pose == "arms_up":
        hands = [(cx - 230*S, 230*S), (cx + 230*S, 230*S)]
        elb = [(cx - 200*S, 400*S), (cx + 200*S, 400*S)]
    elif pose == "flex":
        hands = [(cx - 200*S, 340*S), (cx + 200*S, 340*S)]
        elb = [(cx - 250*S, 560*S), (cx + 250*S, 560*S)]
    elif pose == "hold":
        hands = [(cx - 90*S, 690*S), (cx + 90*S, 690*S)]
        elb = [(cx - 190*S, 740*S), (cx + 190*S, 740*S)]
    elif pose == "wave":
        hands = [(cx - 150*S, 830*S), (cx + 260*S, 300*S)]
        elb = [(cx - 170*S, 690*S), (cx + 240*S, 480*S)]
    else:
        hands = [(cx - 150*S, 830*S), (cx + 150*S, 830*S)]
        elb = [(cx - 175*S, 690*S), (cx + 175*S, 690*S)]
    sleeve = skin if outfit == "tank" else shirt      # tank top shows the whole arm
    for i, sx in enumerate((-1, 1)):
        sh = (cx + sx * 130*S, shoulder_y + 30*S)
        L(sh, elb[i], arm, sleeve); L(elb[i], hands[i], arm, skin)
        r = 30*S; hx, hy = hands[i]; d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=skin)
    # torso (everyone gets a fit, tapered build; hourglass or athletic)
    if shape == "hourglass":
        d.rounded_rectangle([cx - 152*S, shoulder_y, cx + 152*S, shoulder_y + 230*S], 90*S, fill=shirt)
        d.polygon([(cx - 152*S, shoulder_y + 150*S), (cx + 152*S, shoulder_y + 150*S), (cx + 112*S, hip_y - 110*S),
                   (cx + 150*S, hip_y), (cx - 150*S, hip_y), (cx - 112*S, hip_y - 110*S)], fill=shirt)
        dark = tuple(max(0, c - 28) for c in shirt[:3])
        d.arc([cx - 150*S, shoulder_y + 40*S, cx + 150*S, shoulder_y + 220*S], 20, 160, fill=dark, width=6*S)
    elif shape == "athletic":
        d.rounded_rectangle([cx - 168*S, shoulder_y - 6*S, cx + 168*S, shoulder_y + 200*S], 90*S, fill=shirt)
        d.polygon([(cx - 168*S, shoulder_y + 120*S), (cx + 168*S, shoulder_y + 120*S), (cx + 118*S, hip_y - 60*S),
                   (cx + 130*S, hip_y), (cx - 130*S, hip_y), (cx - 118*S, hip_y - 60*S)], fill=shirt)
        dark = tuple(max(0, c - 28) for c in shirt[:3])
        d.line([(cx, shoulder_y + 60*S), (cx, hip_y - 80*S)], fill=dark, width=5*S)
    else:
        d.rounded_rectangle([cx - 150*S, shoulder_y, cx + 150*S, hip_y + 20*S], 90*S, fill=shirt)
    if outfit == "tank":
        for sx in (-1, 1):   # cut the shoulders of the top so the arms show
            d.ellipse([cx + sx*165*S - 70*S, shoulder_y - 40*S, cx + sx*165*S + 70*S, shoulder_y + 70*S], fill=skin)
    d.rounded_rectangle([cx - 150*S, hip_y - 60*S, cx + 150*S, hip_y + 40*S], 40*S, fill=pants)
    if apron:
        d.rounded_rectangle([cx - 150*S, hip_y - 100*S, cx + 150*S, hip_y + 85*S], 36*S, fill=apron)
        d.rectangle([cx - 150*S, hip_y - 104*S, cx + 150*S, hip_y - 78*S], fill=tuple(max(0, c - 30) for c in apron[:3]))
    # neck + head
    d.rounded_rectangle([cx - 38*S, 420*S, cx + 38*S, shoulder_y + 30*S], 30*S, fill=skin)
    hx0, hy0, hr = cx, 300*S, 150*S
    if hstyle == "bun":
        d.ellipse([hx0 - 80*S, 90*S, hx0 + 80*S, 240*S], fill=hair)
    for e in (-1, 1):
        d.ellipse([hx0 + e*150*S - 28*S, hy0 - 10*S, hx0 + e*150*S + 28*S, hy0 + 60*S], fill=skin)
    d.ellipse([hx0 - hr, hy0 - hr - 10*S, hx0 + hr, hy0 + hr + 20*S], fill=skin)
    # hair cap
    if hstyle in ("short", "fade"):
        d.chord([hx0 - hr - 6*S, hy0 - hr - 30*S, hx0 + hr + 6*S, hy0 + 90*S], 180, 360, fill=hair)
        if hstyle == "short":
            d.ellipse([hx0 - 60*S, hy0 - hr - 50*S, hx0 + 120*S, hy0 - 60*S], fill=hair)
    else:
        d.chord([hx0 - hr - 10*S, hy0 - hr - 40*S, hx0 + hr + 10*S, hy0 + 110*S], 180, 360, fill=hair)
    if hstyle == "curly_long":
        for a in range(185, 360, 16):
            x = hx0 + 150*S*math.cos(math.radians(a)); y = hy0 - 5*S + 165*S*math.sin(math.radians(a))
            d.ellipse([x - 52*S, y - 52*S, x + 52*S, y + 52*S], fill=hair)
        if highlight:
            for a in (205, 250, 300, 335):
                x = hx0 + 150*S*math.cos(math.radians(a)); y = hy0 - 5*S + 165*S*math.sin(math.radians(a))
                d.arc([x - 36*S, y - 36*S, x + 36*S, y + 36*S], 200, 340, fill=highlight, width=9*S)
    if hstyle == "fade":
        d.rounded_rectangle([hx0 - 70*S, hy0 + 95*S, hx0 + 70*S, hy0 + 170*S], 50*S, fill=hair)  # beard
    # face: bright eyes with a catch light, brows, blush, big smile
    eye = eye or (70, 50, 40)
    for e in (-1, 1):
        ex = hx0 + e * 55*S
        d.ellipse([ex - 22*S, hy0 - 4*S, ex + 22*S, hy0 + 42*S], fill=WHITE)
        d.ellipse([ex - 15*S, hy0 + 2*S, ex + 15*S, hy0 + 36*S], fill=eye)
        d.ellipse([ex - 9*S, hy0 + 8*S, ex + 9*S, hy0 + 30*S], fill=INK)
        d.ellipse([ex + 2*S, hy0 + 8*S, ex + 10*S, hy0 + 16*S], fill=WHITE)
        d.arc([ex - 30*S, hy0 - 38*S, ex + 30*S, hy0 - 6*S], 200, 340, fill=hair if hstyle != "fade" else INK, width=8*S)
        d.ellipse([ex + e*15*S - 27*S, hy0 + 56*S, ex + e*15*S + 27*S, hy0 + 88*S], fill=(255, 130, 130, 110))
    mouth_y = hy0 + 68*S if hstyle != "fade" else hy0 + 58*S
    d.chord([hx0 - 56*S, mouth_y - 4*S, hx0 + 56*S, mouth_y + 76*S], 0, 180, fill=(150, 45, 55))
    d.chord([hx0 - 46*S, mouth_y, hx0 + 46*S, mouth_y + 32*S], 0, 180, fill=WHITE)
    # props
    if prop == "bowl":
        d.chord([cx - 170*S, 600*S, cx + 170*S, 780*S], 0, 180, fill=WHITE, outline=(210,210,210), width=4*S)
        for (x, y, c) in [(-90, 680, (90, 60, 160)), (-30, 670, (200, 40, 60)), (40, 675, (90, 60, 160)), (100, 683, (200, 40, 60)), (0, 688, SUN)]:
            d.ellipse([cx + x*S - 28*S, y*S - 28*S, cx + x*S + 28*S, y*S + 28*S], fill=c)
    if prop == "pan":
        d.rounded_rectangle([cx - 230*S, 640*S, cx + 230*S, 720*S], 20*S, fill=(120, 125, 130))
        for (x, c) in [(-160, CORAL), (-80, (60, 140, 60)), (0, CORAL), (80, SUN), (160, (60, 140, 60))]:
            d.ellipse([cx + x*S - 40*S, 600*S, cx + x*S + 40*S, 660*S], fill=c)
    DISH = {"hummus": ((232, 205, 150), [(-60, 668, (190, 60, 40), 14), (20, 662, (190, 60, 40), 12), (70, 672, (70, 130, 60), 16), (-10, 676, (205, 170, 60), 34), (-100, 676, (70, 130, 60), 14)]),
            "tabbouleh": ((88, 150, 70), [(-90, 668, (215, 60, 50), 20), (-20, 660, (240, 235, 215), 12), (50, 668, (215, 60, 50), 20), (105, 676, (60, 120, 55), 22), (-55, 678, (60, 120, 55), 22), (10, 680, (240, 235, 215), 12)]),
            "soup": ((226, 150, 60), [(-40, 668, (250, 225, 110), 26), (50, 672, (70, 130, 60), 14), (90, 664, (190, 60, 40), 10), (-95, 676, (70, 130, 60), 12)]),
            "oats": ((222, 200, 165), [(-95, 672, (70, 60, 150), 16), (-45, 664, (70, 60, 150), 14), (15, 670, (215, 60, 70), 22), (75, 666, (250, 235, 170), 24), (110, 678, (70, 60, 150), 14), (-20, 684, (215, 60, 70), 14)])}
    if prop in DISH:
        fill, tops = DISH[prop]
        d.ellipse([cx - 170*S, 640*S, cx + 170*S, 715*S], fill=fill)
        for (x, y, c, r) in tops: d.ellipse([cx + x*S - r*S, y*S - r*S, cx + x*S + r*S, y*S + r*S], fill=c)
        d.chord([cx - 180*S, 590*S, cx + 180*S, 790*S], 0, 180, fill=WHITE, outline=(210,210,210), width=4*S)
    if prop == "shakshuka":
        d.rounded_rectangle([cx + 200*S, 664*S, cx + 330*S, 692*S], 14*S, fill=(70, 72, 78))
        d.rounded_rectangle([cx - 230*S, 650*S, cx + 230*S, 725*S], 24*S, fill=(70, 72, 78))
        d.ellipse([cx - 215*S, 618*S, cx + 215*S, 690*S], fill=(200, 60, 45))
        for x in (-120, 0, 120):
            d.ellipse([cx + x*S - 52*S, 628*S, cx + x*S + 52*S, 678*S], fill=WHITE)
            d.ellipse([cx + x*S - 20*S, 640*S, cx + x*S + 20*S, 666*S], fill=(250, 190, 50))
        for x in (-170, -60, 60, 175): d.ellipse([cx + x*S - 10*S, 640*S, cx + x*S + 10*S, 656*S], fill=(70, 130, 60))
    if prop == "tacos":   # plate with three folded tacos
        d.ellipse([cx - 230*S, 640*S, cx + 230*S, 740*S], fill=WHITE, outline=(210,210,210), width=4*S)
        for x in (-130, 0, 130):
            d.chord([cx + x*S - 70*S, 590*S, cx + x*S + 70*S, 730*S], 180, 360, fill=(240, 200, 90), outline=(205, 160, 60), width=4*S)
            for (dx, c, r) in ((-30, (60, 140, 60), 14), (0, (200, 50, 45), 16), (30, (120, 70, 40), 14)):
                d.ellipse([cx + (x + dx)*S - r*S, 650*S - r*S, cx + (x + dx)*S + r*S, 650*S + r*S], fill=c)
    if prop == "water":
        hx, hy = hands[1]
        d.rounded_rectangle([hx - 45*S, hy - 170*S, hx + 45*S, hy + 40*S], 25*S, fill=(170, 215, 235), outline=(110, 170, 200), width=5*S)
        d.rectangle([hx - 30*S, hy - 200*S, hx + 30*S, hy - 165*S], fill=TEAL)
    if prop == "phone":
        hx, hy = hands[1]
        d.rounded_rectangle([hx - 50*S, hy - 120*S, hx + 50*S, hy + 40*S], 18*S, fill=INK)
        d.rounded_rectangle([hx - 40*S, hy - 108*S, hx + 40*S, hy + 28*S], 12*S, fill=(150, 200, 240))
    return im.resize((cw // S, ch // S), Image.LANCZOS)

CAST = {
    "maya":   dict(skin=(198, 134, 96), hair=(40, 28, 24), hstyle="curly", shirt=CORAL, pants=TEAL, eye=(60, 40, 30), shape="hourglass"),
    "marcus": dict(skin=(120, 78, 55), hair=(28, 22, 20), hstyle="fade", shirt=TEAL, pants=INK, eye=(50, 35, 30), shape="athletic"),
    "leah":   dict(skin=(240, 205, 180), hair=(170, 110, 60), hstyle="long", shirt=SAGE, pants=INK, eye=(60, 120, 90), shape="hourglass"),
    "dev":    dict(skin=(210, 160, 120), hair=(30, 25, 25), hstyle="short", shirt=SUN, pants=TEAL, eye=(60, 40, 30), shape="athletic"),
    "layla":  dict(skin=(214, 164, 122), hair=(24, 20, 22), hstyle="curly_long", shirt=TEAL, pants=INK,
                   eye=(120, 78, 44), highlight=(176, 120, 70), shape="hourglass", apron=(245, 236, 220)),
    "grace":  dict(skin=(232, 190, 160), hair=(25, 25, 30), hstyle="bun", shirt=SKY, pants=INK, eye=(70, 90, 140), shape="hourglass"),
}
_cache = {}
def sprite(name, pose="stand", prop=None, scale=1.0, outfit=None):
    k = (name, pose, prop, scale, outfit)
    if k not in _cache:
        im = person(**CAST[name], pose=pose, prop=prop, outfit=outfit)
        if scale != 1.0: im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
        _cache[k] = im
    return _cache[k]

# ---------------- drawing helpers ----------------
_grad_cache = {}
def gradient(top, bottom):
    k = (top, bottom)
    if k not in _grad_cache:
        col = np.linspace(np.array(top, float), np.array(bottom, float), H)
        arr = np.repeat(col[:, None, :], W, axis=1).astype("uint8")
        _grad_cache[k] = Image.fromarray(arr, "RGB")
    return _grad_cache[k].copy()

CONFETTI = [(int(1080 * ((i * 0.618) % 1)), int(1920 * ((i * 0.381) % 1)), 10 + (i * 7) % 16, i) for i in range(18)]
def confetti(d, t, accent, alpha=170):
    cols = [accent, PARTNER.get(accent, SUN), WHITE, SUN, PINK, SKY]
    for (x, y, r, i) in CONFETTI:
        yy = (y - t * (90 + 20 * (i % 4))) % (H + 60) - 30
        xx = x + 25 * math.sin(t * 1.5 + i)
        c = cols[i % len(cols)] + (alpha,)
        if i % 3 == 0:
            d.rectangle([xx - r*0.7, yy - r*0.7, xx + r*0.7, yy + r*0.7], fill=c)
        else:
            d.ellipse([xx - r*0.6, yy - r*0.6, xx + r*0.6, yy + r*0.6], fill=c)

def background(t, accent, bold=False):
    partner = PARTNER.get(accent, SUN)
    im = gradient(tint(accent, 0.72), tint(partner, 0.62)); d = ImageDraw.Draw(im, "RGBA")
    blobs = [(160, 320, 300, accent), (960, 560, 240, partner), (980, 1480, 330, accent), (90, 1700, 260, partner)]
    for i, (x, y, r, c) in enumerate(blobs):
        dx = 40 * math.sin(t * 1.1 + i); dy = 32 * math.cos(t * 0.9 + i * 2); rr = r + 12 * math.sin(t * 2 + i)
        d.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill=c + (70,))
    # soft diagonal light sweep
    sx = (t * 500) % (W + 1600) - 800
    d.polygon([(sx, 0), (sx + 260, 0), (sx - 500 + 260, H), (sx - 500, H)], fill=WHITE + (45,))
    confetti(d, t, accent)
    progress(d, accent)
    return im

def progress(d, accent):
    d.rounded_rectangle([40, 36, W - 40, 50], 7, fill=WHITE + (140,))
    d.rounded_rectangle([40, 36, 40 + max(14, (W - 80) * _G["frac"]), 50], 7, fill=shade(accent, 0.15))

def wrap(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            tst = (cur + " " + w).strip()
            if d.textlength(tst, font=f) <= maxw: cur = tst
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def text_block(im, text, f, y, color=INK, t=1.0, maxw=920, align="center", lh=1.16, box=None, shadow=None, bounce=True):
    a = ease(t); off = int((1 - (pop(t) if bounce else a)) * 70)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    lines = wrap(d, text, f, maxw); hh = int(f.size * lh)
    if box:
        widest = max(d.textlength(l, font=f) for l in lines)
        pad = 36
        d.rounded_rectangle([W/2 - widest/2 - pad, y + off - pad*0.6, W/2 + widest/2 + pad, y + off + hh*len(lines) + pad*0.4], 36, fill=box)
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        x = (W - tw) / 2 if align == "center" else 80
        if shadow: d.text((x + 4, y + off + i * hh + 5), l, font=f, fill=shadow)
        d.text((x, y + off + i * hh), l, font=f, fill=color)
    if a < 1:
        alpha = layer.split()[3].point(lambda v: int(v * a)); layer.putalpha(alpha)
    im.paste(layer, (0, 0), layer)
    return y + hh * len(lines)

def badge(im, label, color, t=1.0):
    d = ImageDraw.Draw(im); f = font("Bold", 34)
    s = 0.92 + 0.08 * pop(t / 0.35) + 0.02 * math.sin(t * 7)
    tw = d.textlength(label.upper(), font=f) * s
    d.rounded_rectangle([W/2 - tw/2 - 30, 112, W/2 + tw/2 + 30, 177], 33, fill=shade(color, 0.1))
    d.text((W/2 - tw/2, 120), label.upper(), font=f, fill=WHITE)

def sticker(im, text, color, x, y, t=1.0, angle=-12):
    """small rotated label, like a sticker slapped on the corner"""
    f = font("Bold", 36); tmp = ImageDraw.Draw(im)
    tw = int(tmp.textlength(text.upper(), font=f))
    lab = Image.new("RGBA", (tw + 60, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(lab)
    d.rounded_rectangle([0, 0, tw + 60, 84], 20, fill=color, outline=WHITE, width=5)
    d.text((30, 18), text.upper(), font=f, fill=WHITE)
    s = pop(t / 0.3); lab = lab.rotate(angle + 6 * (1 - s), expand=True, resample=Image.BICUBIC)
    if s < 1: lab = lab.resize((max(1, int(lab.width * max(s, 0.05))), max(1, int(lab.height * max(s, 0.05)))))
    im.paste(lab, (int(x - lab.width / 2), int(y - lab.height / 2)), lab)

def wordmark(im, y=1780, small=False):
    d = ImageDraw.Draw(im); f = font("Bold", 34 if small else 40)
    s = "Wholeness Community"; tw = d.textlength(s, font=f)
    cx, cy, r = W/2 - tw/2 - 40, y + 26, 24
    pts = [(cx + r*math.cos(math.radians(60*k+30)), cy + r*math.sin(math.radians(60*k+30))) for k in range(6)]
    d.polygon(pts, fill=shade(TEAL, 0.2))
    d.text((W/2 - tw/2 + 5, y), s, font=f, fill=shade(TEAL, 0.2))

def place(im, spr, x, y, t, bob=True):
    dy = int(12 * math.sin(t * 7)) if bob else 0
    im.paste(spr, (int(x - spr.width/2), int(y + dy)), spr)

# ---------------- scenes ----------------
def sc_hook(p):
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"], t)
        a = pop(t / 0.45)
        spr = sprite(p["who"], p.get("pose", "stand"), p.get("prop"), 0.95, p.get("outfit"))
        place(im, spr, W/2, 800 + (1 - a) * 260, t)
        ye = text_block(im, p["text"], font("Bold", 76), 250, INK, t / 0.3, maxw=940, shadow=WHITE + (160,))
        if p.get("sub"): text_block(im, p["sub"], font("Medium", 42), ye + 40, shade(p["accent"], 0.35), (t - 0.35) / 0.3, box=WHITE + (200,))
        if p.get("sticker"): sticker(im, p["sticker"], PARTNER.get(p["accent"], SUN) if p["accent"] != SUN else CORAL, 850, 800, t - 0.5)
        wordmark(im, small=True)
        return im
    return f

def sc_list(p):
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"], t)
        y = text_block(im, p["title"], font("Bold", 64), 225, INK, t / 0.3, shadow=WHITE + (160,))
        y += 36; n = len(p["items"])
        reveal = p.get("reveal") or [0.4 + i * (T - 0.9) / n for i in range(n)]
        for i, item in enumerate(p["items"]):
            lt = (t - reveal[i]) / 0.32
            if lt <= 0: break
            a = pop(lt); d = ImageDraw.Draw(im, "RGBA")
            rowx = int((1 - a) * 160)
            d.rounded_rectangle([70 + rowx, y, W - 70 + rowx, y + 150], 40, fill=WHITE + (int(240 * ease(lt)),))
            d.rounded_rectangle([70 + rowx, y, 92 + rowx, y + 150], 10, fill=p["accent"])
            d.ellipse([112 + rowx, y + 35, 192 + rowx, y + 115], fill=p["accent"])
            num = str(i + 1); fn = font("Bold", 44); tw = d.textlength(num, font=fn)
            d.text((152 + rowx - tw/2, y + 42), num, font=fn, fill=WHITE)
            lines = wrap(d, item, font("Medium", 40), W - 320)
            ty = y + 75 - 26 * len(lines)
            for j, l in enumerate(lines[:2]):
                d.text((222 + rowx, ty + j * 50), l, font=font("Medium", 40), fill=INK + (int(255 * ease(lt)),))
            y += 175
        if p.get("who"):
            spr = sprite(p["who"], p.get("pose", "stand"), p.get("prop"), 0.62, p.get("outfit"))
            place(im, spr, W - 250, H - spr.height - 130, t)
        wordmark(im, small=True)
        return im
    return f

def sc_move(p):
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"], t)
        text_block(im, p["title"], font("Bold", 66), 225, INK, t / 0.3, shadow=WHITE + (160,))
        text_block(im, p["reps"], font("Medium", 48), 420, shade(TEAL, 0.2), (t - 0.25) / 0.3, box=WHITE + (235,))
        pose = p["poses"][int(t * 2.0) % 2]
        spr = sprite(p["who"], pose, None, 0.95, p.get("outfit", "tank"))
        place(im, spr, W/2, 640, t, bob=False)
        if p.get("joke"): text_block(im, p["joke"], font("Italic", 42), 1630, INK, (t - 0.8) / 0.35, maxw=900)
        wordmark(im, small=True)
        return im
    return f

def sc_punch(p):
    def f(t, T):
        acc = p["accent"]
        im = gradient(acc, shade(acc, 0.25)); d = ImageDraw.Draw(im, "RGBA")
        for k in range(14):   # slowly turning sunburst
            a0 = k * 360 / 14 + t * 18
            pts = [(W/2, H/2)] + [(W/2 + 2200 * math.cos(math.radians(a0 + q)), H/2 + 2200 * math.sin(math.radians(a0 + q))) for q in (0, 11)]
            d.polygon(pts, fill=WHITE + (22,))
        for i in range(5):
            r = 240 + i * 170 + 40 * math.sin(t * 2.5 + i)
            d.ellipse([W/2 - r, H/2 - r, W/2 + r, H/2 + r], outline=WHITE + (55,), width=6)
        confetti(d, t, acc, 220)
        text_block(im, p["text"], font("Bold", 84), 560, WHITE, t / 0.3, maxw=920, shadow=shade(acc, 0.45))
        if p.get("sub"): text_block(im, p["sub"], font("Medium", 46), 1050, WHITE, (t - 0.5) / 0.35, maxw=880)
        if p.get("who"):
            spr = sprite(p["who"], p.get("pose", "wave"), p.get("prop"), 0.48, p.get("outfit"))
            place(im, spr, W/2, 1240 + (1 - pop(t / 0.4)) * 300, t)
        sticker(im, p.get("sticker", "Save this"), SUN if acc != SUN else TEAL, 860, 1180, t - 0.6, angle=10)
        return im
    return f

def sc_cta(p):
    def f(t, T):
        im = background(t, TEAL); d = ImageDraw.Draw(im, "RGBA")
        spr1 = sprite(p["who"][0], "wave", None, 0.6); spr2 = sprite(p["who"][1], "wave", None, 0.6)
        a = pop(t / 0.45)
        place(im, spr1, 300 - (1 - a) * 600, 1050, t); place(im, spr2, 780 + (1 - a) * 600, 1050, t + 1)
        text_block(im, p["text"], font("Bold", 70), 190, INK, t / 0.3, shadow=WHITE + (160,))
        pulse = 1 + 0.025 * math.sin(t * 6)
        y = text_block(im, p.get("cta", "Take the free Wholeness Assessment"), font("Bold", int(50 * pulse)), 530, WHITE, (t - 0.3) / 0.3, box=shade(CORAL, 0.05) + (255,))
        text_block(im, SITE, font("Medium", 40), y + 60, shade(TEAL, 0.3), (t - 0.5) / 0.3)
        text_block(im, "Link in bio", font("Bold", 46), y + 130, shade(CORAL, 0.1), (t - 0.65) / 0.3)
        wordmark(im)
        return im
    return f

KIND = dict(hook=sc_hook, list=sc_list, move=sc_move, punch=sc_punch, cta=sc_cta)

# ---------------- audio ----------------
def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32767
    return sr, (x.reshape(-1, ch).T if ch > 1 else x[None, :])

def narrate(scenes, out_dir, name):
    """Synthesize narration for scenes that carry `vo` (one line) or `vo_items` (one per list item),
    stretch scene durations to fit, and return (voice_clips, total_dur). voice_clips = [(start_s, mono_array)]."""
    from voice import say
    clips = []; t0 = 0.0; k = 0
    for sc in scenes:
        if sc.get("vo"):
            p = os.path.join(out_dir, f"{name}_vo{k}.wav"); k += 1
            dur = say(sc["vo"], p); clips.append((t0 + 0.2, p))
            sc["dur"] = max(sc["dur"], 0.2 + dur + 0.45)
        elif sc.get("vo_items"):
            at = 0.55; reveal = []
            for item in sc["vo_items"]:
                p = os.path.join(out_dir, f"{name}_vo{k}.wav"); k += 1
                dur = say(item, p); clips.append((t0 + at, p)); reveal.append(max(0.1, at - 0.12))
                at += dur + 0.22
            sc["reveal"] = reveal; sc["dur"] = max(sc["dur"], at + 0.3)
        t0 += sc["dur"]
    return clips, t0

def mix_audio(music_wav, clips, dur, out_wav):
    sr, m = read_wav(music_wav)
    n = int(dur * sr); m = m[:, :n]
    if m.shape[1] < n: m = np.pad(m, ((0, 0), (0, n - m.shape[1])))
    v = np.zeros(n)
    for (st, p) in clips:
        _, c = read_wav(p); c = c[0]; i = int(st * sr); c = c[: max(0, n - i)]
        v[i:i + len(c)] += c; os.remove(p)
    if clips:
        # duck the music under the voice: envelope follower with a 40 ms window, 250 ms release
        env = np.abs(v); win = int(0.04 * sr)
        env = np.convolve(env, np.ones(win) / win, mode="same")
        rel = int(0.25 * sr); env = np.convolve(env, np.ones(rel) / rel, mode="same") * 2.2
        g = 1 - 0.70 * np.clip(env / 0.08, 0, 1)
        m = m * g * 0.75
    out = m + v[None, :]
    out = np.tanh(out * 1.25) / 1.25
    out *= min(1.0, 0.89 / (np.abs(out).max() + 1e-9))
    pcm = (out.T * 32767).astype("<i2")
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def render(name, scenes, out_dir, mood=None):
    fdir = os.path.join(out_dir, "frames_" + name); shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    clips, total = narrate(scenes, out_dir, name) if any(s.get("vo") or s.get("vo_items") for s in scenes) else ([], sum(s["dur"] for s in scenes))
    N = sum(int(s["dur"] * FPS) for s in scenes)
    n = 0; cover = None
    for sc in scenes:
        fn = KIND[sc["kind"]](sc); T = sc["dur"]
        for k in range(int(T * FPS)):
            t = k / FPS; _G["frac"] = n / N; im = fn(t, T)
            if cover is None and t >= 1.2: cover = im.copy()
            im.save(os.path.join(fdir, f"{n:05d}.jpg"), quality=92); n += 1
    out = os.path.join(out_dir, name + ".mp4")
    # original music bed (see music.py) plus narration when the scenes ask for it, so no reel goes out silent
    from music import make_track, mood_for
    wav = os.path.join(out_dir, name + "_music.wav"); mix = os.path.join(out_dir, name + "_mix.wav")
    make_track(name, n / FPS, wav, mood or mood_for(name))
    mix_audio(wav, clips, n / FPS, mix)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "%05d.jpg"),
                    "-i", mix, "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "20", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-map_metadata", "-1", out], check=True)
    cover.save(os.path.join(out_dir, name + "_cover.jpg"), quality=92)
    shutil.rmtree(fdir); os.remove(wav); os.remove(mix)
    return out
