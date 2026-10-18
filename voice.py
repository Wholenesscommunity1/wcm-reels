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


def say(text, path, voice=VOICE, speed=0.96):
    """Synthesize text to a 44.1 kHz mono wav at path. Returns the duration in seconds."""
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
