"""Recipe reels built from photorealistic AI stills (not the illustrated cast in make_reels.py).

Each recipe folder recipes/YYYY-MM-DD/src/ holds hero.jpg (finished dish), cook.jpg and enjoy.jpg
(a person cooking / eating). The reel opens on the finished dish with the hook, shows the key
ingredients with amounts, walks through every step with a narrated subtitle card, and closes on
the CTA. Quick cuts every 2 to 3 seconds come from alternating Ken Burns crops of the three stills.
Music comes from music.py (original, synthesized), the voice from voice.py (Piper, offline).

    python3 make_recipe_reels.py recipes/recipes_2026-11-11_to_11-24.json 2026-11-13
    python3 make_recipe_reels.py recipes/recipes_2026-11-11_to_11-24.json          # all with images
"""
import json, math, os, shutil, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOT = int(H * 0.12), int(H * 0.80)     # burned-in text stays inside this band
FD = "/usr/share/fonts/truetype/google-fonts/Poppins-"
if not os.path.exists(FD + "Bold.ttf"):
    FD = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
def font(w, s):
    if "Poppins" in FD:
        return ImageFont.truetype(FD + w + ".ttf", s)
    return ImageFont.truetype(FD + ("-Bold" if w in ("Bold", "Medium") else "") + ".ttf", s)

TEAL = (0, 140, 128); SAGE = (82, 196, 150); CORAL = (255, 112, 80); SUN = (255, 190, 0)
INK = (28, 36, 44); WHITE = (255, 255, 255); CREAM = (253, 248, 240)
SITE = "wholenesscommunitymarketplace.com"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from music import make_track
from voice import say


# ---------- text helpers ----------
def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def fit_font(d, text, weight, size, maxw, max_lines, min_size=34):
    while size > min_size:
        f = font(weight, size)
        if len(wrap(d, text, f, maxw)) <= max_lines: return f
        size -= 2
    return font(weight, min_size)

def outlined(d, xy, text, f, fill=WHITE, outline=INK, width=6, anchor="la"):
    d.text(xy, text, font=f, fill=outline, stroke_width=width, stroke_fill=outline, anchor=anchor)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)

def ease(x): return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0), 1))


# ---------- picture helpers ----------
def load(path):
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im

def ken_burns(src, t, T, z0, z1, cx0, cy0, cx1, cy1):
    """Crop a moving window out of src (W x H) and scale it back to full frame."""
    k = t / max(T, 1e-6)
    z = z0 + (z1 - z0) * k
    cx = (cx0 + (cx1 - cx0) * k) * W; cy = (cy0 + (cy1 - cy0) * k) * H
    cw, ch = W / z, H / z
    x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), H - ch)
    return src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

# a cycle of different moves so consecutive cuts feel different
MOVES = [(1.00, 1.12, .5, .5, .5, .45), (1.25, 1.10, .5, .40, .5, .55), (1.10, 1.25, .40, .55, .60, .45),
         (1.18, 1.05, .55, .50, .45, .50), (1.05, 1.20, .5, .60, .5, .40), (1.22, 1.12, .60, .45, .40, .55)]

def shots_for(images, dur, cut=2.6, start=0):
    """Plan the quick cuts for a scene: list of (image, t0, t1, move)."""
    out, t, k = [], 0.0, start
    n = max(1, round(dur / cut))
    seg = dur / n
    for i in range(n):
        out.append((images[k % len(images)], t, min(t + seg, dur), MOVES[k % len(MOVES)]))
        t += seg; k += 1
    return out

def darken(im, top=0.0, bottom=0.55, y_from=0.5):
    """Soft dark gradient over the lower part of the frame so white text reads on any photo."""
    grad = Image.new("L", (1, H))
    px = grad.load()
    for y in range(H):
        f = (y / H - y_from) / (1 - y_from)
        px[0, y] = int(255 * (top + (bottom - top) * ease(f))) if f > 0 else int(255 * top)
    grad = grad.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), (10, 14, 18)), im, grad)

def vignette(im):
    return Image.blend(im, darken(im, 0.0, 0.35, 0.0), 0.35)


# ---------- overlays ----------
def pill(d, text, f, cx, y, bg, fg=WHITE, pad=26):
    tw = d.textlength(text, font=f); h = f.size + 30
    d.rounded_rectangle([cx - tw/2 - pad, y, cx + tw/2 + pad, y + h], h // 2, fill=bg)
    d.text((cx, y + h/2), text, font=f, fill=fg, anchor="mm")

def brand_bar(im, frac):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([60, SAFE_TOP - 54, W - 60, SAFE_TOP - 44], 5, fill=(255, 255, 255, 110))
    d.rounded_rectangle([60, SAFE_TOP - 54, 60 + (W - 120) * frac, SAFE_TOP - 44], 5, fill=SUN)
    f = font("Bold", 30); s = "Wholeness Community"
    outlined(d, (W / 2, SAFE_TOP - 90), s, f, fill=WHITE, width=5, anchor="mm")

def hook_overlay(im, r, t, T):
    im = darken(im, 0.0, 0.62, 0.42)
    d = ImageDraw.Draw(im, "RGBA")
    k = ease(t / 0.45)
    f = fit_font(d, r["hook"], "Bold", 78, W - 140, 4, 48)
    lines = wrap(d, r["hook"], f, W - 140)
    lh = int(f.size * 1.14); block = lh * len(lines)
    y = SAFE_BOT - 150 - block + int((1 - k) * 40)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=8, anchor="ma"); y += lh
    pill(d, "Save this recipe", font("Bold", 34), W / 2, SAFE_BOT - 110, CORAL)
    # dish label at top of the safe zone
    pill(d, r["title"], fit_font(d, r["title"], "Bold", 38, W - 260, 1, 28), W / 2, SAFE_TOP + 20, (0, 0, 0, 150))
    return im

def darken_top(im, strength=0.66):
    grad = Image.new("L", (1, H)); px = grad.load()
    for y in range(H):
        f = 1 - y / (H * 0.78)
        px[0, y] = int(255 * strength * ease(f)) if f > 0 else 0
    return Image.composite(Image.new("RGB", (W, H), (10, 14, 18)), im, grad.resize((W, H)))

def ingredients_overlay(im, r, t, T, reveal):
    im = darken_top(im, 0.70)
    d = ImageDraw.Draw(im, "RGBA")
    items = r["key_ingredients"]
    pill(d, "You will need", font("Bold", 40), W / 2, SAFE_TOP + 30, TEAL)
    f = font("Bold", 44); lh = 78
    y0 = SAFE_TOP + 150
    for i, it in enumerate(items):
        if t < reveal[i] - 0.001: continue
        k = ease((t - reveal[i]) / 0.3)
        x = 110 + int((1 - k) * 60)
        d.rounded_rectangle([x - 20, y0 + i * lh - 8, x + 20, y0 + i * lh + 32], 8, fill=SUN)
        d.text((x, y0 + i * lh + 12), "", font=f, fill=INK, anchor="lm")
        lines = wrap(d, it, f, W - 240)
        outlined(d, (x + 50, y0 + i * lh - 2), lines[0], f, fill=WHITE, width=6)
    sv = r["servings"]
    sv = ("Serves " + sv.replace(" (", ", ").rstrip(")")) if sv[0].isdigit() and "serving" not in sv else sv   # "4 (8 wraps)" reads "Serves 4, 8 wraps"
    pill(d, sv, font("Medium", 32), W / 2, SAFE_BOT - 120, (0, 0, 0, 160))
    return im

def step_overlay(im, r, idx, text, t, T):
    im = darken(im, 0.0, 0.72, 0.45)
    d = ImageDraw.Draw(im, "RGBA")
    k = ease(t / 0.35)
    f = fit_font(d, text, "Bold", 50, W - 150, 5, 36)
    lines = wrap(d, text, f, W - 150)
    lh = int(f.size * 1.2); block = lh * len(lines)
    y = SAFE_BOT - 40 - block + int((1 - k) * 30)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=7, anchor="ma"); y += lh
    # step badge
    bx, by = W / 2, SAFE_BOT - 40 - block - 110
    d.ellipse([bx - 48, by - 48, bx + 48, by + 48], fill=CORAL)
    d.text((bx, by), str(idx), font=font("Bold", 50), fill=WHITE, anchor="mm")
    pill(d, f"Step {idx} of {len(r['steps'])}", font("Medium", 30), W / 2, SAFE_TOP + 24, (0, 0, 0, 150))
    return im

def outro_overlay(im, r, t, T):
    im = darken(im, 0.1, 0.75, 0.30)
    d = ImageDraw.Draw(im, "RGBA")
    k = ease(t / 0.4)
    f = fit_font(d, r["benefit"], "Bold", 52, W - 160, 3, 36)
    blines = wrap(d, r["benefit"], f, W - 160)
    y = SAFE_BOT - 290 - 60 - int(f.size * 1.2) * len(blines) + int((1 - k) * 40)
    for ln in blines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=7, anchor="ma"); y += int(f.size * 1.2)
    pill(d, "Take the free Wholeness Assessment", font("Bold", 36), W / 2, SAFE_BOT - 290, TEAL)
    f2 = font("Bold", 40)
    outlined(d, (W / 2, SAFE_BOT - 190), SITE, f2, fill=SUN, width=6, anchor="ma")
    outlined(d, (W / 2, SAFE_BOT - 120), "link in bio", font("Medium", 34), fill=WHITE, width=5, anchor="ma")
    return im


# ---------- audio ----------
def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32767
    return sr, (x.reshape(-1, ch).T if ch > 1 else x[None, :])

def mix_audio(music_wav, clips, dur, out_wav):
    sr, m = read_wav(music_wav)
    n = int(dur * sr); m = m[:, :n]
    if m.shape[1] < n: m = np.pad(m, ((0, 0), (0, n - m.shape[1])))
    v = np.zeros(n)
    for st, p in clips:
        _, c = read_wav(p); c = c[0]; i = int(st * sr); c = c[: max(0, n - i)]
        v[i:i + len(c)] += c
    env = np.abs(v); win = int(0.04 * sr)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    rel = int(0.25 * sr); env = np.convolve(env, np.ones(rel) / rel, mode="same") * 2.2
    g = 1 - 0.72 * np.clip(env / 0.08, 0, 1)
    out = m * g * 0.72 + v[None, :]
    out = np.tanh(out * 1.25) / 1.25
    out *= min(1.0, 0.89 / (np.abs(out).max() + 1e-9))
    pcm = (out.T * 32767).astype("<i2")
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def vo_lines(r):
    """What the narrator says, scene by scene."""
    return {
        "hook": r["hook"] + ".",
        "ingredients": "Here is everything you need. Full amounts are in the caption.",
        "steps": r.get("vo_steps") or r["steps"],
        "outro": r["benefit"] + ". Save this one and take the free Wholeness Assessment. Link in bio.",
    }


def build(r, root, tag="", target_max=45.0):
    day = r["date"]; name = f"{day}_{r['slug']}" + (f"_{tag}" if tag else "")
    folder = os.path.join(root, day); src = os.path.join(folder, "src"); tmp = os.path.join(folder, "tmp")
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    imgs = {k: load(os.path.join(src, k + ".jpg")) for k in ("hero", "cook", "enjoy") if os.path.exists(os.path.join(src, k + ".jpg"))}
    hero = imgs["hero"]; cook = imgs.get("cook", hero); enjoy = imgs.get("enjoy", cook)
    if r.get("crop_top"):          # keep a tighter upper-body framing on a named still
        for k in r["crop_top"]:
            im = imgs[k]; im = im.crop((0, 0, W, int(H * 0.78))).resize((W, H), Image.LANCZOS); imgs[k] = im
        hero = imgs["hero"]; cook = imgs.get("cook", hero); enjoy = imgs.get("enjoy", cook)

    # narration first, so scene lengths follow the voice
    lines = vo_lines(r)
    speed = 0.87
    while True:
        clips = {}; durs = {}
        k = 0
        for key, text in [("hook", lines["hook"]), ("ingredients", lines["ingredients"])] + \
                         [(f"step{i}", s) for i, s in enumerate(lines["steps"])] + [("outro", lines["outro"])]:
            p = os.path.join(tmp, f"vo_{k}.wav"); k += 1
            durs[key] = say(text, p, speed=speed); clips[key] = p
        total_est = sum(d + 0.6 for d in durs.values()) + 1.2
        if total_est <= target_max or speed <= 0.74: break
        speed = round(speed - 0.05, 2)

    # ingredient reveal timing: spread across the ingredients VO
    n_ing = len(r["key_ingredients"])
    ing_dur = max(durs["ingredients"] + 0.6, 1.4 + 0.62 * n_ing)
    reveal = [0.4 + i * (ing_dur - 1.2) / max(n_ing, 1) for i in range(n_ing)]

    scenes = []   # (kind, dur, images for cuts, payload)
    scenes.append(("hook", max(durs["hook"] + 0.5, 3.0), [hero, hero], None))
    scenes.append(("ingredients", ing_dur, [cook, hero, cook], reveal))
    for i, s in enumerate(r["steps"]):
        pool = [cook, hero, enjoy, cook, hero] if i % 2 == 0 else [hero, enjoy, cook, hero, enjoy]
        scenes.append((f"step{i}", durs[f"step{i}"] + 0.55, pool, (i + 1, s)))
    scenes.append(("outro", max(durs["outro"] + 0.6, 3.5), [enjoy, hero], None))

    total = sum(sc[1] for sc in scenes)
    fdir = os.path.join(tmp, "frames"); os.makedirs(fdir)
    voice_clips = []; t0 = 0.0; n = 0; cover = None; mid = None
    N = int(total * FPS); shot_index = 0
    for kind, T, pool, payload in scenes:
        voice_clips.append((t0 + 0.15, clips[kind]))
        shots = shots_for(pool, T, cut=(2.4 if kind.startswith("step") else 2.8), start=shot_index)
        shot_index += len(shots)
        for fi in range(int(round(T * FPS))):
            t = fi / FPS
            shot = next((s for s in shots if s[1] <= t < s[2]), shots[-1])
            img, s0, s1, mv = shot
            frame = ken_burns(img, t - s0, s1 - s0, *mv)
            if kind == "hook": frame = hook_overlay(frame, r, t, T)
            elif kind == "ingredients": frame = ingredients_overlay(frame, r, t, T, payload)
            elif kind.startswith("step"): frame = step_overlay(frame, r, payload[0], payload[1], t, T)
            else: frame = outro_overlay(frame, r, t, T)
            brand_bar(frame, n / N)
            if cover is None and kind == "hook" and t >= 1.0: cover = frame.copy()
            if mid is None and kind == "step1" and t >= 1.0: mid = frame.copy()
            frame.save(os.path.join(fdir, f"{n:05d}.jpg"), quality=90); n += 1
        t0 += T

    dur = n / FPS
    music = os.path.join(tmp, "music.wav"); mix = os.path.join(tmp, "mix.wav")
    make_track(name, dur, music, mood="upbeat")
    mix_audio(music, voice_clips, dur, mix)
    out = os.path.join(folder, name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "%05d.jpg"),
                    "-i", mix, "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "29",
                    "-preset", "medium", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1", out], check=True)
    # cover: the finished dish with the title, no progress bar
    cv = hero.copy(); cv = darken(cv, 0.0, 0.62, 0.42); d = ImageDraw.Draw(cv, "RGBA")
    f = fit_font(d, r["title"], "Bold", 84, W - 140, 3, 50); lines = wrap(d, r["title"], f, W - 140)
    lh = int(f.size * 1.14); y = SAFE_BOT - 160 - lh * len(lines)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=8, anchor="ma"); y += lh
    pill(d, "Full recipe in the caption", font("Bold", 34), W / 2, SAFE_BOT - 120, CORAL)
    pill(d, "Wholeness Community", font("Bold", 32), W / 2, SAFE_TOP + 20, (0, 0, 0, 150))
    cv.save(os.path.join(folder, name + "_cover.jpg"), quality=92)
    if mid is not None: mid.save(os.path.join(folder, name + "_mid.jpg"), quality=88)
    shutil.rmtree(tmp)
    return out, dur, speed


if __name__ == "__main__":
    recipes = json.load(open(sys.argv[1]))
    only = sys.argv[2:]
    root = os.path.join(HERE, "recipes")
    tag = os.environ.get("WCM_TAG", "")
    for r in recipes:
        if only and r["date"] not in only: continue
        if not os.path.exists(os.path.join(root, r["date"], "src", "hero.jpg")):
            print("skip (no images)", r["date"]); continue
        out, dur, speed = build(r, root, tag)
        print(f"{r['date']} {r['slug']}: {dur:.1f}s speed {speed} -> {out}")
