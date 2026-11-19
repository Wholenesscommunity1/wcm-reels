"""Wholeness wheel dimension reels (the 7:00 PM ET slot), built from photorealistic AI stills like the
recipe reels. One dimension per day, 45 to 60 seconds: hook over the hero still, a short "what this
dimension is" card, three or four numbered tips (bold headline plus one detail line, narrated at a
natural pace), and the CTA outro. Quick Ken Burns cuts every 2 to 3 seconds, music from music.py,
voice from voice.py (OpenAI voice with the day's accent when a key is available, Piper otherwise).

    python3 make_dimension_reels.py dimensions/2026-11-19/reel.json
    WCM_TAG=v2 python3 make_dimension_reels.py dimensions/2026-11-19/reel.json      # re-render under a new file name
"""
import json, os, shutil, subprocess, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from make_recipe_reels import (W, H, FPS, SAFE_TOP, SAFE_BOT, font, wrap, fit_font, outlined, ease, load, ken_burns, MOVES,
                               darken, darken_top, pill, brand_bar, mix_audio, shots_for, TEAL, SAGE, CORAL, SUN, WHITE, INK, SITE)
from music import make_track
from voice import say, accent_for

DIM_COLORS = {   # pill colour per dimension so the series is recognisable at a glance
    "Physical": (230, 92, 60), "Mind & Emotions": (108, 84, 200), "Stress Relief & Rest": (40, 110, 150),
    "Relationships & Support": (214, 72, 120), "Spirituality & Purpose": (150, 90, 170), "Financial Wellness": (30, 140, 100),
    "Home & Lifestyle": (200, 130, 30), "Conditions & Recovery": (0, 140, 128), "Nutrition & Healing": (82, 160, 60),
}


def hook_overlay(im, r, t):
    im = darken(im, 0.0, 0.62, 0.40); d = ImageDraw.Draw(im, "RGBA"); k = ease(t / 0.45)
    f = fit_font(d, r["hook"], "Bold", 76, W - 140, 5, 46); lines = wrap(d, r["hook"], f, W - 140)
    lh = int(f.size * 1.14); y = SAFE_BOT - 150 - lh * len(lines) + int((1 - k) * 40)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=8, anchor="ma"); y += lh
    pill(d, "Save this for tonight", font("Bold", 34), W / 2, SAFE_BOT - 110, CORAL)
    pill(d, r["dimension"] + "  |  Wholeness Wheel", fit_font(d, r["dimension"] + "  |  Wholeness Wheel", "Bold", 36, W - 260, 1, 26),
         W / 2, SAFE_TOP + 20, DIM_COLORS.get(r["dimension"], TEAL))
    return im


def what_overlay(im, r, t):
    im = darken_top(im, 0.72); d = ImageDraw.Draw(im, "RGBA"); k = ease(t / 0.4)
    pill(d, "What it is", font("Bold", 40), W / 2, SAFE_TOP + 30, DIM_COLORS.get(r["dimension"], TEAL))
    f = fit_font(d, r["what"], "Bold", 54, W - 160, 6, 38); lines = wrap(d, r["what"], f, W - 160)
    lh = int(f.size * 1.2); y = SAFE_TOP + 150 + int((1 - k) * 30)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=7, anchor="ma"); y += lh
    return im


def tip_overlay(im, r, idx, tip, t):
    im = darken(im, 0.0, 0.74, 0.42); d = ImageDraw.Draw(im, "RGBA"); k = ease(t / 0.35)
    fh = fit_font(d, tip["head"], "Bold", 66, W - 150, 3, 44); hl = wrap(d, tip["head"], fh, W - 150)
    fd = fit_font(d, tip["detail"], "Medium", 42, W - 170, 4, 32); dl = wrap(d, tip["detail"], fd, W - 170)
    lh_h, lh_d = int(fh.size * 1.14), int(fd.size * 1.25)
    block = lh_h * len(hl) + 24 + lh_d * len(dl)
    y = SAFE_BOT - 40 - block + int((1 - k) * 30)
    for ln in hl:
        outlined(d, (W / 2, y), ln, fh, fill=WHITE, width=8, anchor="ma"); y += lh_h
    y += 24
    for ln in dl:
        outlined(d, (W / 2, y), ln, fd, fill=(255, 240, 200), width=6, anchor="ma"); y += lh_d
    bx, by = W / 2, SAFE_BOT - 40 - block - 100
    d.ellipse([bx - 46, by - 46, bx + 46, by + 46], fill=CORAL)
    d.text((bx, by), str(idx), font=font("Bold", 48), fill=WHITE, anchor="mm")
    pill(d, f"{r['dimension']}  |  {idx} of {len(r['tips'])}", font("Medium", 30), W / 2, SAFE_TOP + 24, (0, 0, 0, 150))
    return im


def outro_overlay(im, r, t):
    im = darken(im, 0.1, 0.75, 0.30); d = ImageDraw.Draw(im, "RGBA"); k = ease(t / 0.4)
    f = fit_font(d, r["outro"], "Bold", 58, W - 160, 3, 38); lines = wrap(d, r["outro"], f, W - 160)
    lh = int(f.size * 1.18); y = SAFE_BOT - 290 - 60 - lh * len(lines) + int((1 - k) * 40)
    for ln in lines:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=7, anchor="ma"); y += lh
    pill(d, r.get("cta", "Take the free Wholeness Assessment"), font("Bold", 36), W / 2, SAFE_BOT - 290, TEAL)
    outlined(d, (W / 2, SAFE_BOT - 190), SITE, font("Bold", 40), fill=SUN, width=6, anchor="ma")
    outlined(d, (W / 2, SAFE_BOT - 120), "link in bio", font("Medium", 34), fill=WHITE, width=5, anchor="ma")
    pill(d, r["dimension"] + "  |  Wholeness Wheel", fit_font(d, r["dimension"] + "  |  Wholeness Wheel", "Bold", 34, W - 260, 1, 26),
         W / 2, SAFE_TOP + 20, DIM_COLORS.get(r["dimension"], TEAL))
    return im


def build(spec_path, tag="", target_max=60.0, piper_speed=1.0):
    root = os.path.dirname(os.path.abspath(spec_path)); r = json.load(open(spec_path))
    name = f"{r['date']}_{r['slug']}" + (f"_{tag}" if tag else "")
    tmp = os.path.join(root, "tmp"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    imgs = {k: load(os.path.join(root, v)) for k, v in r["images"].items()}
    hero = imgs["hero"]; keys = [k for k in imgs if k != "hero"]
    accent = r.get("accent") or os.environ.get("WCM_ACCENT") or accent_for(r["date"])

    # narration first so the scene lengths follow the voice; Piper pace relaxes toward 1.0 for the longer format
    lines = [("hook", r.get("hook_say") or r["hook"]), ("what", r.get("what_say") or r["what"])]
    lines += [(f"tip{i}", t.get("say") or (t["head"] + ". " + t["detail"])) for i, t in enumerate(r["tips"])]
    lines += [("outro", r.get("outro_say") or (r["outro"] + ". Take the free Wholeness Assessment. Link in bio."))]
    speed = piper_speed
    while True:
        clips, durs = {}, {}
        for k, (key, text) in enumerate(lines):
            p = os.path.join(tmp, f"vo_{k}.wav"); durs[key] = say(text, p, speed=speed, accent=accent); clips[key] = p
        total_est = sum(d + 0.7 for d in durs.values()) + 1.5
        if total_est <= target_max or speed <= 0.9:
            break
        speed = round(speed - 0.05, 2)

    scenes = [("hook", max(durs["hook"] + 0.6, 3.2), [hero, hero], None),
              ("what", durs["what"] + 0.7, [imgs[keys[0]], hero, imgs[keys[-1]]], None)]
    for i, tip in enumerate(r["tips"]):
        main = imgs.get(tip.get("img"), imgs[keys[i % len(keys)]])
        others = [imgs[k] for k in keys if imgs[k] is not main] or [hero]
        pool = [main, others[i % len(others)], main, hero, main]
        scenes.append((f"tip{i}", durs[f"tip{i}"] + 0.7, pool, (i + 1, tip)))
    scenes.append(("outro", max(durs["outro"] + 0.7, 4.0), [hero, imgs[keys[-1]], hero], None))

    total = sum(sc[1] for sc in scenes); N = int(total * FPS)
    fdir = os.path.join(tmp, "frames"); os.makedirs(fdir)
    voice_clips, t0, n, cover, mid, shot_index = [], 0.0, 0, None, None, 0
    for kind, T, pool, payload in scenes:
        voice_clips.append((t0 + 0.2, clips[kind]))
        shots = shots_for(pool, T, cut=(2.6 if kind.startswith("tip") else 2.9), start=shot_index); shot_index += len(shots)
        for fi in range(int(round(T * FPS))):
            t = fi / FPS
            img, s0, s1, mv = next((s for s in shots if s[1] <= t < s[2]), shots[-1])
            frame = ken_burns(img, t - s0, s1 - s0, *mv)
            if kind == "hook": frame = hook_overlay(frame, r, t)
            elif kind == "what": frame = what_overlay(frame, r, t)
            elif kind.startswith("tip"): frame = tip_overlay(frame, r, payload[0], payload[1], t)
            else: frame = outro_overlay(frame, r, t)
            brand_bar(frame, n / N)
            if cover is None and kind == "hook" and t >= 1.0: cover = frame.copy()
            if mid is None and kind == "tip1" and t >= 1.0: mid = frame.copy()
            frame.save(os.path.join(fdir, f"{n:05d}.jpg"), quality=90); n += 1
        t0 += T

    dur = n / FPS
    music = os.path.join(tmp, "music.wav"); mix = os.path.join(tmp, "mix.wav")
    make_track(name, dur, music, mood=r.get("mood", "warm")); mix_audio(music, voice_clips, dur, mix)
    out = os.path.join(root, name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "%05d.jpg"), "-i", mix,
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "29", "-preset", "medium",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1", out], check=True)
    # cover: hero still, dimension badge and the reel title
    cv = darken(hero.copy(), 0.0, 0.62, 0.42); d = ImageDraw.Draw(cv, "RGBA")
    f = fit_font(d, r["title"], "Bold", 84, W - 140, 3, 50); tl = wrap(d, r["title"], f, W - 140)
    lh = int(f.size * 1.14); y = SAFE_BOT - 160 - lh * len(tl)
    for ln in tl:
        outlined(d, (W / 2, y), ln, f, fill=WHITE, width=8, anchor="ma"); y += lh
    pill(d, "Full breakdown in the caption", font("Bold", 34), W / 2, SAFE_BOT - 120, CORAL)
    pill(d, r["dimension"] + "  |  Wholeness Wheel", fit_font(d, r["dimension"] + "  |  Wholeness Wheel", "Bold", 34, W - 260, 1, 26),
         W / 2, SAFE_TOP + 20, DIM_COLORS.get(r["dimension"], TEAL))
    cv.save(os.path.join(root, name + "_cover.jpg"), quality=92)
    if mid is not None: mid.save(os.path.join(root, name + "_mid.jpg"), quality=88)
    shutil.rmtree(tmp)
    return out, dur, speed, accent


if __name__ == "__main__":
    out, dur, speed, accent = build(sys.argv[1], os.environ.get("WCM_TAG", ""))
    print(f"{out}: {dur:.1f}s pace {speed} accent {accent}")
