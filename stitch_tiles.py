"""Rebuild a full-resolution 1080x1920 image from the eight 540x480 tile thumbnails that Canva's
read-design returns (600x533 each, 2 columns x 4 rows). The render box cannot download Canva exports
directly, so a generated image is placed at 1080x1920 across eight tile pages and read back as
thumbnails, which this script stitches together.

    python3 stitch_tiles.py OUT.jpg            # uses the 8 newest Canva blobs in the tool-results dir
    python3 stitch_tiles.py OUT.jpg t0.png ... t7.png
"""
import glob, os, sys
from PIL import Image, ImageFilter

BLOBS = os.environ.get("WCM_BLOBS", "/root/.claude/projects/-home-claude-wcm-reels/940c46b8-85e6-5708-b779-8e952aa99299/tool-results")


def newest(n=8):
    fs = glob.glob(os.path.join(BLOBS, "mcp-Canva-blob-*.png"))
    fs.sort(key=lambda f: (os.stat(f).st_mtime_ns, f))
    fs = fs[-n:]
    span = (os.stat(fs[-1]).st_mtime_ns - os.stat(fs[0]).st_mtime_ns) / 1e9
    assert span < 3.0, f"newest {n} blobs span {span:.1f}s; they are not one read-design batch"
    return fs


def edge(a, side):
    import numpy as np
    x = np.asarray(a, dtype=float)
    return {"l": x[:, 0], "r": x[:, -1], "t": x[0], "b": x[-1]}[side]


def seam(a, b, horizontal):
    """Mean colour jump across the seam between a (left/top) and b (right/bottom)."""
    import numpy as np
    return float(np.abs(edge(a, "r" if horizontal else "b") - edge(b, "l" if horizontal else "t")).mean())


def arrange(tiles):
    """The eight thumbnails land on disk in an unreliable order, so try every layout and keep the one
    whose tile seams are most continuous (precomputed seam costs make the 8! search cheap)."""
    import itertools
    n = len(tiles)
    H = [[seam(a, b, True) for b in tiles] for a in tiles]     # H[a][b]: a left of b
    V = [[seam(a, b, False) for b in tiles] for a in tiles]    # V[a][b]: a above b
    best = None
    for p in itertools.permutations(range(n)):
        s = 0.0
        for r in range(4):
            s += H[p[2 * r]][p[2 * r + 1]]
            if r < 3:
                s += V[p[2 * r]][p[2 * r + 2]] + V[p[2 * r + 1]][p[2 * r + 3]]
        if best is None or s < best[0]:
            best = (s, p)
    return [tiles[i] for i in best[1]]


def clusters(min_size=8):
    """Groups of 600x533 tile blobs written within 3 s of each other, oldest first (one per read-design)."""
    fs = glob.glob(os.path.join(BLOBS, "mcp-Canva-blob-*.png"))
    fs.sort(key=lambda f: os.stat(f).st_mtime_ns)
    out, cur = [], []
    for f in fs:
        if Image.open(f).size != (600, 533):
            continue
        if cur and os.stat(f).st_mtime_ns - os.stat(cur[-1]).st_mtime_ns > 3e9:
            if len(cur) >= min_size: out.append(cur)
            cur = []
        cur.append(f)
    if len(cur) >= min_size: out.append(cur)
    return out


def stitch(out, files):
    tiles = [Image.open(f).convert("RGB") for f in files]
    tw, th = tiles[0].size                      # about 600 x 533
    tiles = [t if t.size == (tw, th) else t.resize((tw, th), Image.LANCZOS) for t in tiles]
    tiles = arrange(tiles)
    canvas = Image.new("RGB", (tw * 2, th * 4))
    for k, t in enumerate(tiles):
        col, row = k % 2, k // 2
        canvas.paste(t, (col * tw, row * th))
    im = canvas.resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    im.save(out, quality=94)
    return im.size


if __name__ == "__main__":
    out = sys.argv[1]
    files = sys.argv[2:] if len(sys.argv) > 2 else newest()
    assert len(files) == 8, files
    print(stitch(out, files), [os.path.basename(f) for f in files])
