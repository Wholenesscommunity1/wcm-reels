import math, os, subprocess, sys, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/usr/share/fonts/truetype/google-fonts/Poppins-"
def font(w, s): return ImageFont.truetype(F + w + ".ttf", s)

CREAM = (251, 246, 238); TEAL = (31, 94, 91); SAGE = (143, 185, 168)
CORAL = (242, 140, 107); SUN = (246, 195, 91); INK = (36, 48, 47); WHITE = (255, 255, 255)
SITE = "wholenesscommunitymarketplace.com"

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3

# ---------------- characters ----------------
def person(skin, hair, hstyle, shirt, pants, pose="stand", prop=None, eye=None, highlight=None, shape=None, apron=None):
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
    for i, sx in enumerate((-1, 1)):
        sh = (cx + sx * 130*S, shoulder_y + 30*S)
        L(sh, elb[i], arm, shirt); L(elb[i], hands[i], arm, skin)
        r = 30*S; hx, hy = hands[i]; d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=skin)
    # torso
    if shape == "hourglass":
        d.rounded_rectangle([cx - 152*S, shoulder_y, cx + 152*S, shoulder_y + 230*S], 90*S, fill=shirt)
        d.polygon([(cx - 152*S, shoulder_y + 150*S), (cx + 152*S, shoulder_y + 150*S), (cx + 112*S, hip_y - 110*S),
                   (cx + 150*S, hip_y), (cx - 150*S, hip_y), (cx - 112*S, hip_y - 110*S)], fill=shirt)
        dark = tuple(max(0, c - 28) for c in shirt[:3])
        d.arc([cx - 150*S, shoulder_y + 40*S, cx + 150*S, shoulder_y + 220*S], 20, 160, fill=dark, width=6*S)
    else:
        d.rounded_rectangle([cx - 150*S, shoulder_y, cx + 150*S, hip_y + 20*S], 90*S, fill=shirt)
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
    # face
    for e in (-1, 1):
        ex = hx0 + e * 55*S
        if eye:
            d.ellipse([ex - 19*S, hy0 + 0*S, ex + 19*S, hy0 + 40*S], fill=eye)
            d.ellipse([ex - 9*S, hy0 + 10*S, ex + 9*S, hy0 + 30*S], fill=INK)
            d.ellipse([ex + 2*S, hy0 + 8*S, ex + 9*S, hy0 + 15*S], fill=WHITE)
        else:
            d.ellipse([ex - 14*S, hy0 + 5*S, ex + 14*S, hy0 + 35*S], fill=INK)
        d.arc([ex - 30*S, hy0 - 35*S, ex + 30*S, hy0 - 5*S], 200, 340, fill=hair if hstyle != "fade" else INK, width=8*S)
        d.ellipse([ex + e*15*S - 25*S, hy0 + 55*S, ex + e*15*S + 25*S, hy0 + 85*S], fill=(240, 150, 140, 120))
    mouth_y = hy0 + 70*S if hstyle != "fade" else hy0 + 60*S
    d.chord([hx0 - 50*S, mouth_y, hx0 + 50*S, mouth_y + 70*S], 0, 180, fill=(120, 40, 40))
    d.rectangle([hx0 - 40*S, mouth_y + 32*S, hx0 + 40*S, mouth_y + 38*S], fill=None)
    d.chord([hx0 - 40*S, mouth_y + 2*S, hx0 + 40*S, mouth_y + 30*S], 0, 180, fill=WHITE)
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
            "soup": ((226, 150, 60), [(-40, 668, (250, 225, 110), 26), (50, 672, (70, 130, 60), 14), (90, 664, (190, 60, 40), 10), (-95, 676, (70, 130, 60), 12)])}
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
    "maya":   dict(skin=(198, 134, 96), hair=(40, 28, 24), hstyle="curly", shirt=CORAL, pants=TEAL),
    "marcus": dict(skin=(120, 78, 55), hair=(28, 22, 20), hstyle="fade", shirt=TEAL, pants=INK),
    "leah":   dict(skin=(240, 205, 180), hair=(170, 110, 60), hstyle="long", shirt=SAGE, pants=INK),
    "dev":    dict(skin=(210, 160, 120), hair=(30, 25, 25), hstyle="short", shirt=SUN, pants=TEAL),
    "layla":  dict(skin=(214, 164, 122), hair=(24, 20, 22), hstyle="curly_long", shirt=TEAL, pants=INK,
                   eye=(120, 78, 44), highlight=(176, 120, 70), shape="hourglass", apron=(245, 236, 220)),
    "grace":  dict(skin=(232, 190, 160), hair=(25, 25, 30), hstyle="bun", shirt=(120, 160, 210), pants=INK),
}
_cache = {}
def sprite(name, pose="stand", prop=None, scale=1.0):
    k = (name, pose, prop, scale)
    if k not in _cache:
        im = person(**CAST[name], pose=pose, prop=prop)
        if scale != 1.0: im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
        _cache[k] = im
    return _cache[k]

# ---------------- drawing helpers ----------------
def background(t, accent):
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im, "RGBA")
    blobs = [(180, 300, 260, accent), (900, 520, 200, SUN), (950, 1500, 300, SAGE), (120, 1650, 220, accent)]
    for i, (x, y, r, c) in enumerate(blobs):
        dx = 30 * math.sin(t * 0.8 + i); dy = 25 * math.cos(t * 0.6 + i * 2)
        d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=c + (55,))
    return im

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

def text_block(im, text, f, y, color=INK, t=1.0, maxw=920, align="center", lh=1.18, box=None):
    a = ease(t); off = int((1 - a) * 60)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    lines = wrap(d, text, f, maxw); hh = int(f.size * lh)
    if box:
        widest = max(d.textlength(l, font=f) for l in lines)
        pad = 36
        d.rounded_rectangle([W/2 - widest/2 - pad, y + off - pad*0.6, W/2 + widest/2 + pad, y + off + hh*len(lines) + pad*0.4], 36, fill=box)
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        x = (W - tw) / 2 if align == "center" else 80
        d.text((x, y + off + i * hh), l, font=f, fill=color)
    if a < 1:
        alpha = layer.split()[3].point(lambda v: int(v * a)); layer.putalpha(alpha)
    im.paste(layer, (0, 0), layer)
    return y + hh * len(lines)

def badge(im, label, color):
    d = ImageDraw.Draw(im); f = font("Bold", 34)
    tw = d.textlength(label.upper(), font=f)
    d.rounded_rectangle([W/2 - tw/2 - 30, 110, W/2 + tw/2 + 30, 175], 33, fill=color)
    d.text((W/2 - tw/2, 118), label.upper(), font=f, fill=WHITE)

def wordmark(im, y=1780, small=False):
    d = ImageDraw.Draw(im); f = font("Bold", 34 if small else 40)
    s = "Wholeness Community"; tw = d.textlength(s, font=f)
    # little hexagon mark
    cx, cy, r = W/2 - tw/2 - 40, y + 26, 24
    pts = [(cx + r*math.cos(math.radians(60*k+30)), cy + r*math.sin(math.radians(60*k+30))) for k in range(6)]
    d.polygon(pts, fill=TEAL)
    d.text((W/2 - tw/2 + 5, y), s, font=f, fill=TEAL)

def place(im, spr, x, y, t, bob=True):
    dy = int(10 * math.sin(t * 6)) if bob else 0
    im.paste(spr, (int(x - spr.width/2), int(y + dy)), spr)

# ---------------- scenes ----------------
def sc_hook(p):
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"])
        a = ease(t / 0.5)
        spr = sprite(p["who"], p.get("pose", "stand"), p.get("prop"), 0.95)
        place(im, spr, W/2, 800 + (1 - a) * 150, t)
        text_block(im, p["text"], font("Bold", 74), 260, INK, 1.0, maxw=940)
        if p.get("sub"): text_block(im, p["sub"], font("Medium", 44), 600, TEAL, (t - 0.5) / 0.4)
        wordmark(im, small=True)
        return im
    return f

def sc_list(p):
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"])
        y = text_block(im, p["title"], font("Bold", 64), 230, INK, t / 0.35)
        y += 40; step = (T - 0.6) / max(1, len(p["items"]))
        for i, item in enumerate(p["items"]):
            lt = (t - 0.4 - i * step) / 0.35
            if lt <= 0: break
            a = ease(lt); d = ImageDraw.Draw(im, "RGBA")
            rowy = y + int((1 - a) * 40)
            d.rounded_rectangle([70, rowy, W - 70, rowy + 150], 40, fill=WHITE + (int(235 * a),))
            d.ellipse([100, rowy + 35, 180, rowy + 115], fill=p["accent"])
            n = str(i + 1); fn = font("Bold", 44); tw = d.textlength(n, font=fn)
            d.text((140 - tw/2, rowy + 42), n, font=fn, fill=WHITE)
            lines = wrap(d, item, font("Medium", 40), W - 300)
            ty = rowy + 75 - 26 * len(lines)
            for j, l in enumerate(lines[:2]):
                d.text((210, ty + j * 50), l, font=font("Medium", 40), fill=INK + (int(255 * a),))
            y += 175
        if p.get("who"):
            spr = sprite(p["who"], p.get("pose", "stand"), p.get("prop"), 0.55)
            place(im, spr, W - 230, H - spr.height - 140, t)
        wordmark(im, small=True)
        return im
    return f

def sc_move(p):
    # exercise demo: alternate two poses
    def f(t, T):
        im = background(t, p["accent"]); badge(im, p["badge"], p["accent"])
        text_block(im, p["title"], font("Bold", 66), 230, INK, t / 0.35)
        text_block(im, p["reps"], font("Medium", 48), 420, TEAL, (t - 0.3) / 0.35, box=WHITE + (230,))
        pose = p["poses"][int(t * 1.6) % 2]
        spr = sprite(p["who"], pose, None, 0.95)
        place(im, spr, W/2, 640, t, bob=False)
        if p.get("joke"): text_block(im, p["joke"], font("Italic", 42), 1690 - 60, INK, (t - 1.0) / 0.4, maxw=900)
        wordmark(im, small=True)
        return im
    return f

def sc_punch(p):
    def f(t, T):
        im = Image.new("RGB", (W, H), p["accent"]); d = ImageDraw.Draw(im, "RGBA")
        for i in range(6):
            r = 200 + i * 160 + 40 * math.sin(t * 2 + i)
            d.ellipse([W/2 - r, H/2 - r, W/2 + r, H/2 + r], outline=WHITE + (40,), width=6)
        text_block(im, p["text"], font("Bold", 82), 620, WHITE, t / 0.35, maxw=900)
        if p.get("sub"): text_block(im, p["sub"], font("Medium", 46), 1050, WHITE, (t - 0.6) / 0.4, maxw=880)
        if p.get("who"):
            spr = sprite(p["who"], p.get("pose", "wave"), p.get("prop"), 0.45)
            place(im, spr, W/2, 1300, t)
        return im
    return f

def sc_cta(p):
    def f(t, T):
        im = background(t, TEAL); d = ImageDraw.Draw(im, "RGBA")
        spr1 = sprite(p["who"][0], "wave", None, 0.6); spr2 = sprite(p["who"][1], "wave", None, 0.6)
        a = ease(t / 0.5)
        place(im, spr1, 300 - (1 - a) * 500, 1050, t); place(im, spr2, 780 + (1 - a) * 500, 1050, t + 1)
        text_block(im, p["text"], font("Bold", 70), 200, INK, t / 0.35)
        y = text_block(im, "Take the free Wholeness Assessment", font("Bold", 50), 540, WHITE, (t - 0.4) / 0.35, box=TEAL + (255,))
        text_block(im, SITE, font("Medium", 40), y + 60, TEAL, (t - 0.7) / 0.35)
        text_block(im, "Link in bio", font("Bold", 44), y + 130, CORAL, (t - 0.9) / 0.35)
        wordmark(im)
        return im
    return f

KIND = dict(hook=sc_hook, list=sc_list, move=sc_move, punch=sc_punch, cta=sc_cta)

def render(name, scenes, out_dir, mood=None):
    fdir = os.path.join(out_dir, "frames_" + name); shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    n = 0; cover = None
    for sc in scenes:
        fn = KIND[sc["kind"]](sc); T = sc["dur"]
        for k in range(int(T * FPS)):
            t = k / FPS; im = fn(t, T)
            if cover is None and t >= 1.4: cover = im.copy()
            im.save(os.path.join(fdir, f"{n:05d}.jpg"), quality=92); n += 1
    out = os.path.join(out_dir, name + ".mp4")
    # original music bed (see music.py) so the reel is never silent
    from music import make_track, mood_for
    wav = os.path.join(out_dir, name + "_music.wav")
    make_track(name, n / FPS, wav, mood or mood_for(name))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "%05d.jpg"),
                    "-i", wav, "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "20", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1", out], check=True)
    cover.save(os.path.join(out_dir, name + "_cover.jpg"), quality=92)
    shutil.rmtree(fdir); os.remove(wav)
    return out
