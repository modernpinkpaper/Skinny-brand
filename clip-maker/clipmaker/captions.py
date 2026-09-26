"""Word-by-word captions: each word pops in exactly when the voice says it.
Small linking words (the, of, to...) are small, the words that matter are big, and the words sit in a loose,
staggered stack over the clip - thick rounded white font with a soft shadow. A long line is split into
phrases; each phrase clears when the next one starts."""
import os, re, zlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .paths import ASSETS

W, H, FPS = 1080, 1920, 30
SMALL = set("""a an the and or but so if of to in on at for from with by as is are was were be been am it its
i me my you your we our they them their he she his her that this than then just not no do did does have has
had will would could should can may might up out off into about over too very""".split())
SIZE_SMALL, SIZE_BIG, SIZE_HERO = 54, 100, 124
CENTER_Y, MAX_WORDS = 860, 8
POP = [0.72, 1.12, 1.0]          # size of a new word on its first frames (the "pop")

_fonts = {}
def font(size):
    if size not in _fonts:
        f = ImageFont.truetype(os.path.join(ASSETS, "fonts", "Nunito.ttf"), size)
        f.set_variation_by_axes([1000 if size >= SIZE_BIG else 850]); _fonts[size] = f
    return _fonts[size]


_sprites = {}
def sprite(text, size):
    """The word drawn once (white, thin dark edge, soft shadow) and reused for every frame."""
    key = (text, size)
    if key not in _sprites:
        f = font(size); l, t, r, b = f.getbbox(text); pad = size // 3 + 8
        w, h = r - l + 2 * pad, b - t + 2 * pad
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 3, pad - t + 5), text, font=f, fill=(0, 0, 0, 190))
        im = sh.filter(ImageFilter.GaussianBlur(max(3, size // 14)))
        ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill="white",
                                stroke_width=max(1, size // 40), stroke_fill=(20, 20, 20, 140))
        im.base = pad - t + f.getmetrics()[0]   # where the text's baseline sits inside the image
        im.left = pad - l
        _sprites[key] = im
    return _sprites[key]


def _norm(w): return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def _phrases(words):
    """Splits a line's words into phrases of at most MAX_WORDS (as even as possible)."""
    n = len(words)
    if n <= MAX_WORDS: return [list(range(n))]
    k = -(-n // MAX_WORDS); size = -(-n // k)
    return [list(range(i, min(i + size, n))) for i in range(0, n, size)]


def _layout(texts, seed):
    """Where each word of a phrase goes: rows of words, staggered left/right, big words start a new row."""
    sizes = [SIZE_SMALL if _norm(t).strip("'") in SMALL else SIZE_BIG for t in texts]
    big = [i for i, s in enumerate(sizes) if s == SIZE_BIG]
    if big:  # the longest important word is the "hero"
        sizes[max(big, key=lambda i: len(texts[i]))] = SIZE_HERO
    rows, cur = [], []
    for i, t in enumerate(texts):
        width = sum(font(sizes[j]).getlength(texts[j] + " ") for j in cur + [i])
        starts_row = sizes[i] >= SIZE_BIG and any(sizes[j] >= SIZE_BIG for j in cur)
        if cur and (starts_row or width > 820 or len(cur) >= 3): rows.append(cur); cur = []
        cur.append(i)
    if cur: rows.append(cur)
    offsets = [-150, 110, -40, 170, -120, 60]
    heights = [max(sizes[j] for j in r) for r in rows]
    y = CENTER_Y - int(sum(h * 1.05 for h in heights) / 2)
    pos = {}
    for n, (r, h) in enumerate(zip(rows, heights)):
        widths = [font(sizes[j]).getlength(texts[j] + " ") + sizes[j] * 0.12 for j in r]
        widths = [int(w) for w in widths]
        x = W // 2 + offsets[(n + seed) % len(offsets)] - sum(widths) // 2
        x = max(40, min(x, W - 40 - sum(widths)))
        base = y + int(h * 0.8)   # all words in a row sit on the same baseline
        for j, w in zip(r, widths):
            s = sprite(texts[j], sizes[j])
            pos[j] = (x - s.left, base - s.base)
            x += w
        y += int(h * 1.05)
    return sizes, pos


def _frame(texts, sizes, pos, shown, pop=None, scale=1.0):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in shown:
        s = sprite(texts[i], sizes[i]); x, y = pos[i]
        if i == pop and scale != 1.0:
            s2 = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.LANCZOS)
            x += (s.width - s2.width) // 2; y += (s.height - s2.height) // 2; s = s2
        im.alpha_composite(s, (max(0, x), max(0, y)))
    return im


def line_overlay(line, times, dur, out):
    """line: the script line. times: (start, end) in seconds for each word of line.split().
    Writes the frames and an ffmpeg concat list for a clip lasting `dur` seconds; returns the list's path."""
    texts = line.split()
    if not texts: texts, times = [" "], [(0, 0)]
    events = []   # (time, image)
    seed = zlib.crc32(line.encode()) % 6
    for ph in _phrases(texts):
        ptexts = [texts[i] for i in ph]; sizes, pos = _layout(ptexts, seed); seed += 1
        for k in range(len(ph)):
            t = max(0.0, min(times[ph[k]][0], dur - 0.05))
            for f, sc in enumerate(POP):
                events.append((t + f / FPS, _frame(ptexts, sizes, pos, range(k + 1), pop=k, scale=sc)))
    events.sort(key=lambda e: e[0])
    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not events or events[0][0] > 0: events.insert(0, (0.0, blank))
    lst, prev = [], None
    for n, (t, im) in enumerate(events):
        nxt = events[n + 1][0] if n + 1 < len(events) else dur
        d = max(nxt - t, 0)
        if d <= 0: continue
        p = f"{out}_{n:03d}.png"; im.save(p, compress_level=1)
        lst.append(f"file '{p.replace(os.sep, '/')}'\nduration {d:.4f}\n"); prev = p
    lst.append(f"file '{prev.replace(os.sep, '/')}'\n")
    open(out + ".txt", "w").write("".join(lst))
    return out + ".txt"
