"""Original background music for WCM reels.

Everything here is synthesized from scratch with numpy (no samples, no third-party
recordings), so the tracks are ours to use anywhere.

    from music import make_track
    make_track("day12_recipe", 14.0, "out/day12.wav", mood="bright")

Moods: bright (recipes, humor), drive (workouts), calm (rest, encouragement), warm (habits).
The same name always gives the same track; different names give different keys,
progressions and melodies so the feed does not sound like one loop.
"""
import hashlib, wave
import numpy as np

SR = 44100
MAJOR = [0, 2, 4, 5, 7, 9, 11]
PENTA = [0, 2, 4, 7, 9]
# progressions as scale degrees (0 = I, 4 = V, 5 = vi, 3 = IV, 1 = ii)
PROGS = [[0, 4, 5, 3], [0, 5, 3, 4], [5, 3, 0, 4], [0, 3, 5, 4], [0, 3, 0, 4], [3, 0, 4, 5]]
MOODS = {
    "bright": dict(bpm=(104, 112), keys=[0, 2, 5, 7], perc=0.9, pad=0.5, arp=1.0, lead=0.8),
    "drive":  dict(bpm=(116, 124), keys=[2, 4, 7, 9], perc=1.2, pad=0.4, arp=1.0, lead=0.7),
    "calm":   dict(bpm=(80, 88),   keys=[0, 3, 5, 10], perc=0.35, pad=1.0, arp=0.8, lead=0.6),
    "warm":   dict(bpm=(92, 100),  keys=[0, 5, 7, 9], perc=0.65, pad=0.8, arp=0.9, lead=0.7),
}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def chord(root_pc, degree):
    """Triad (as semitone offsets from C) built on a scale degree of the major key root_pc."""
    return [root_pc + MAJOR[(degree + k) % 7] + 12 * ((degree + k) // 7) for k in (0, 2, 4)]


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1] or i < 0:
        return
    sig = sig[: buf.shape[1] - i]
    l = gain * np.cos((pan + 1) * np.pi / 4); r = gain * np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(sig)] += l * sig
    buf[1, i:i + len(sig)] += r * sig


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def mallet(f, dur=0.9):
    """Soft marimba-like pluck: fundamental plus a quickly dying upper partial."""
    t = tvec(dur)
    att = np.minimum(t / 0.004, 1.0)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 5.0)
    s += 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 18.0)
    s += 0.12 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 9.0)
    return s * att


def bell(f, dur=1.4):
    t = tvec(dur)
    att = np.minimum(t / 0.006, 1.0)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2)
    s += 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 5.5)
    s += 0.10 * np.sin(2 * np.pi * 3.0 * f * t) * np.exp(-t * 9.0)
    return s * att


def pad(freqs, dur):
    t = tvec(dur)
    env = np.minimum(t / 0.5, 1.0) * np.minimum((dur - t) / 0.35, 1.0).clip(0, 1)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.35, 0.35):
            ff = f * 2 ** (det / 120.0)
            s += np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(2 * np.pi * 2 * ff * t)
    return s * env / (2 * len(freqs))


def bass(f, dur):
    t = tvec(dur)
    env = np.minimum(t / 0.012, 1.0) * np.exp(-t * 1.6) * np.minimum((dur - t) / 0.05, 1.0).clip(0, 1)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)) * env


def kick():
    t = tvec(0.28)
    f = 48 + 75 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 15)


def noise_hit(rng, dur, decay, lo, hi):
    """Band-limited noise burst via FFT masking (shaker, snap)."""
    n = int(dur * SR)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    y = np.fft.irfft(X, n)
    t = np.arange(n) / SR
    y *= np.exp(-t * decay) * np.minimum(t / 0.002, 1.0)
    return y / (np.abs(y).max() + 1e-9)


def make_track(name, dur, path, mood="warm"):
    seed = int(hashlib.sha1(name.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    m = MOODS[mood]
    bpm = int(rng.integers(m["bpm"][0], m["bpm"][1] + 1))
    key = int(rng.choice(m["keys"]))
    prog = PROGS[int(rng.integers(len(PROGS)))]
    beat = 60.0 / bpm; bar = 4 * beat
    nbars = int(np.ceil(dur / bar)) + 1
    buf = np.zeros((2, int((dur + 2.0) * SR)))
    k_s, shaker, snap = kick(), noise_hit(rng, 0.07, 55, 5000, 12000), noise_hit(rng, 0.14, 30, 1200, 5000)
    arp_pat = [[0, 1, 2, 1, 3, 2, 1, 2], [0, 2, 1, 2, 3, 2, 1, 2], [0, 1, 2, 3, 2, 1, 2, 1]][int(rng.integers(3))]
    mel_base = (72 if key <= 5 else 60) + key
    # a two-bar melodic motif on the pentatonic scale, mostly stepwise, repeated with a small variation
    steps = [0]
    for _ in range(7):
        steps.append(int(np.clip(steps[-1] + rng.choice([-2, -1, -1, 1, 1, 2]), -2, 6)))
    rhythm = [0, 1.5, 2, 3, 4, 5.5, 6, 7]  # in beats across two bars

    for b in range(nbars):
        t0 = b * bar
        deg = prog[b % len(prog)]
        ch = chord(key, deg)
        intro = b == 0
        # pad, mid register
        pr = 48 + ((ch[0] - 48) % 12)
        add(buf, t0, pad([hz(pr), hz(pr + ch[1] - ch[0]), hz(pr + ch[2] - ch[0])], bar + 0.3), 0.30 * m["pad"])
        # bass on beats 1 and 3 (root, then root or fifth)
        root = 36 + (ch[0] % 12)
        add(buf, t0, bass(hz(root), beat * 1.9), 0.20)
        if not intro:
            add(buf, t0 + 2 * beat, bass(hz(root + (7 if b % 2 else 0)), beat * 1.9), 0.16)
        # mallet arpeggio in eighth notes, chord tones plus the octave
        ar = 55 + ((ch[0] - 55) % 12)
        tones = [ar, ar + ch[1] - ch[0], ar + ch[2] - ch[0], ar + 12]
        for e in range(8):
            if intro and e % 2:  # sparser first bar
                continue
            vel = (1.0 if e % 4 == 0 else 0.72) * (0.9 + 0.2 * rng.random())
            swing = 0.012 * rng.standard_normal() * 0.3
            add(buf, t0 + e * beat / 2 + max(swing, 0), mallet(hz(tones[arp_pat[e]])), 0.34 * vel * m["arp"],
                pan=(-0.35 if e % 2 else 0.35))
        # percussion enters on bar 2
        if not intro:
            for q in (0, 2):
                add(buf, t0 + q * beat, k_s, 0.24 * m["perc"])
            for q in (1, 3):
                add(buf, t0 + q * beat, snap, 0.13 * m["perc"], pan=0.1)
            for e in range(8):
                add(buf, t0 + e * beat / 2, shaker, (0.05 if e % 2 else 0.03) * m["perc"], pan=-0.25)
        # bell melody from bar 2, motif spans two bars
        if b >= 1:
            half = (b - 1) % 2
            for i, r in enumerate(rhythm):
                if int(r // 4) != half:
                    continue
                st = steps[i] + (1 if ((b - 1) // 2) % 2 and i == 7 else 0)
                note = mel_base + PENTA[st % 5] + 12 * (st // 5)
                add(buf, t0 + (r - 4 * half) * beat, bell(hz(note)), 0.22 * m["lead"], pan=0.15)

    n = int(dur * SR)
    buf = buf[:, :n]
    # gentle fade in, longer fade out so the reel ends cleanly (and loops without a click)
    t = np.arange(n) / SR
    buf *= np.minimum(t / 0.15, 1.0) * np.minimum((dur - t) / 1.3, 1.0).clip(0, 1)
    buf = np.tanh(buf * 1.4) / 1.4                       # soft limiter
    buf *= 0.80 / (np.abs(buf).max() + 1e-9)             # about -2 dBFS peak
    pcm = (buf.T * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return dict(bpm=bpm, key=key, prog=prog, mood=mood)


THEME_MOOD = {"Recipe": "bright", "Humor": "bright", "Workout": "drive", "Good habit": "warm",
              "Encouragement": "calm", "Community": "warm"}


def mood_for(name):
    n = name.lower()
    if any(k in n for k in ("workout", "commercial_break")): return "drive"
    if any(k in n for k in ("recipe", "humor", "berry", "salmon", "monday")): return "bright"
    if any(k in n for k in ("encouragement", "stress_relief", "rest")): return "calm"
    return "warm"


if __name__ == "__main__":
    import sys
    print(make_track(sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else mood_for(sys.argv[1])))
