"""Narration for WCM reels (used on recipe reels so the cook talks you through it).

Runs Piper, a small offline text to speech engine, with a voice model pulled once from the
Piper GitHub releases into ~/.cache/wcm_voices. No cloud TTS, no account, nothing leaves the box.

    from voice import say
    secs = say("Drain one can of chickpeas.", "clip.wav")        # writes 44.1 kHz mono PCM

pip install --break-system-packages piper-tts   (already done on the render box)
"""
import os, re, subprocess, tarfile, urllib.request, wave

VOICE = os.environ.get("WCM_VOICE", "en-us-lessac-medium")   # clear, friendly, reads numbers well
RELEASE = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-{v}.tar.gz"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "wcm_voices")


def model_path(v=VOICE):
    p = os.path.join(CACHE, v + ".onnx")
    if not os.path.exists(p):
        os.makedirs(CACHE, exist_ok=True)
        tgz = os.path.join(CACHE, v + ".tar.gz")
        urllib.request.urlretrieve(RELEASE.format(v=v), tgz)
        with tarfile.open(tgz) as t:
            t.extractall(CACHE)
        os.remove(tgz)
    return p


UNITS = [(r"\btbsp\b", "tablespoon"), (r"\btsp\b", "teaspoon"), (r"\boz\b", "ounces"), (r"\blb\b", "pound"),
         (r"\bmin\b", "minutes"), (r"\bmins\b", "minutes"), (r"\bsec\b", "seconds"), (r"\bhr\b", "hour"),
         (r"\bw/\s*", "with "), (r"\bvs\.?\b", "versus"), (r"&", " and ")]


def spoken(text):
    """Make calendar text read naturally: 400F, $3, 1/2, 2x, tbsp and so on."""
    s = text
    s = re.sub(r"(\d+)\s*[Ff]\b", r"\1 degrees", s)
    s = re.sub(r"(\d+)\s*°\s*[FfCc]?", r"\1 degrees", s)
    s = re.sub(r"\$(\d+(?:\.\d+)?)", r"\1 dollars", s)
    s = re.sub(r"\b1/2\b", "half", s); s = re.sub(r"\b1/4\b", "a quarter", s); s = re.sub(r"\b3/4\b", "three quarters", s)
    s = re.sub(r"\b1/3\b", "a third", s); s = re.sub(r"\b2/3\b", "two thirds", s)
    s = re.sub(r"(\d+)\s*x\b", r"\1 times", s)
    s = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1 to \2", s)
    s = re.sub(r"\b(\d+)(am|pm)\b", r"\1 \2", s)
    for pat, rep in UNITS:
        s = re.sub(pat, rep, s, flags=re.I)
    s = s.replace('"', "").replace("+", " plus ").replace("#", "")
    s = re.sub(r"\s+", " ", s).strip()
    if s and s[-1] not in ".!?":
        s += "."
    return s


# ---------- cloud voice (OpenAI gpt-4o-mini-tts) with light regional accents ----------
# Sandip asked (Nov 19, 2026) for a more natural, human voice and an A/B test of light regional accents.
# The key is never stored in the repo: it comes from OPENAI_API_KEY, or from the file named in
# WCM_OPENAI_KEY_FILE (default ~/.config/wcm/openai_key), which each run fills from Sandip's private
# Google Drive file "wcm-openai-key" before rendering. With no key (or WCM_TTS=piper) Piper is used.
ACCENTS = {
    "southern":   "Speak with a very light Southern US accent, just a hint of warmth and drawl, never exaggerated or comic.",
    "midwest":    "Speak with a light Midwestern US accent (Minnesota, Wisconsin, Iowa), friendly and plain-spoken, never exaggerated.",
    "northern":   "Speak with a light Northeastern US accent (upstate New York, New England), relaxed and clear, never exaggerated.",
    "california": "Speak with a light Southern California accent, easygoing and sunny, never exaggerated or slangy.",
    "neutral":    "Speak in a neutral general American accent.",
}
ACCENT_ORDER = ["southern", "midwest", "northern", "california"]   # A/B rotation, 3 days each
OPENAI_VOICES = {"southern": "sage", "midwest": "coral", "northern": "ash", "california": "nova", "neutral": "sage"}
STYLE = ("You are a warm, friendly home cook and wellness coach talking to a friend in your kitchen, recording a short social "
         "video. Natural, unhurried, conversational pace with easy pauses between sentences; genuinely upbeat but calm. "
         "Never sound like an announcer or a commercial; no vocal fry, no breathiness. {accent}")


def openai_key():
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if k:
        return k
    f = os.environ.get("WCM_OPENAI_KEY_FILE", os.path.join(os.path.expanduser("~"), ".config", "wcm", "openai_key"))
    if os.path.exists(f):
        return open(f).read().strip()
    return ""


def accent_for(date_str, start="2026-11-20"):
    """Which accent the A/B test assigns to a date: 3 days each, cycling through ACCENT_ORDER from `start`."""
    from datetime import date
    d = (date.fromisoformat(date_str) - date.fromisoformat(start)).days
    if d < 0:
        return "neutral"
    return ACCENT_ORDER[(d // 3) % len(ACCENT_ORDER)]


def say_openai(text, path, accent="neutral", speed=1.0, key=None):
    import json
    key = key or openai_key()
    body = json.dumps({"model": "gpt-4o-mini-tts", "voice": OPENAI_VOICES.get(accent, "sage"), "input": spoken(text),
                       "instructions": STYLE.format(accent=ACCENTS.get(accent, ACCENTS["neutral"])),
                       "response_format": "wav", "speed": speed}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=body,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    raw = path + ".raw.wav"
    with urllib.request.urlopen(req, timeout=120) as r, open(raw, "wb") as out:
        out.write(r.read())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", "44100", "-ac", "1", "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
                    path], check=True)
    os.remove(raw)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def say(text, path, voice=VOICE, speed=0.87, accent=None):
    """Synthesize text to a 44.1 kHz mono wav at path. Returns the duration in seconds.

    Uses the OpenAI voice when a key is available and WCM_TTS is not "piper"; `accent` picks the A/B
    variant (WCM_ACCENT env overrides). Otherwise Piper, where `speed` is the length scale (higher is slower)."""
    if os.environ.get("WCM_TTS", "auto") != "piper" and openai_key():
        acc = accent or os.environ.get("WCM_ACCENT", "neutral")
        # Piper length-scale 0.87 is a brisk read; the cloud voice is told to be unhurried, so keep 1.0 there
        return say_openai(text, path, accent=acc, speed=1.0)
    raw = path + ".raw.wav"
    subprocess.run(["python3", "-m", "piper", "-m", model_path(voice), "-f", raw, "--length-scale", str(speed), "--", spoken(text)],
                   check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", "44100", "-ac", "1", "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
                    path], check=True)
    os.remove(raw)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


if __name__ == "__main__":
    import sys
    print(say(" ".join(sys.argv[2:]), sys.argv[1]))
