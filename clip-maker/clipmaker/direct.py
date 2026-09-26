"""Voice directions written in the script (for example by Claude when it writes the script):

  [sad, slow] You miss them. Even though they *hurt* you.
  [firm] You were *never* supposed to earn being cared for (pause) by anyone.

  [feeling, speed] at the start of a line: how to say it. Lines without a tag keep the last tag; a new tag
                   starts fresh (what it leaves out is normal).
                   A tag alone on its own line sets it for the lines below.
  *word*           lean on this word (a bit louder and slower; big on screen).
  (pause), (long pause)   a breath inside a line.
None of the marks are shown on screen. A script without any marks works as before."""
import re

# feeling -> (Chatterbox exaggeration, Chatterbox cfg_weight, extra speed)
# exaggeration = how much emotion; a lower cfg_weight = slower, more deliberate pacing. More emotion also makes
# Chatterbox talk faster, so firm and intense are slowed back down a little.
FEELS = {"calm": (0.30, 0.40, 0.97), "soft": (0.35, 0.35, 0.95), "sad": (0.45, 0.30, 0.93),
         "normal": (0.40, 0.35, 1.00), "firm": (0.60, 0.45, 0.94), "intense": (0.75, 0.30, 0.92)}
SAME = {"quiet": "calm", "gentle": "soft", "warm": "soft", "tender": "soft", "hopeful": "soft", "sadly": "sad",
        "heavy": "sad", "hurt": "sad", "neutral": "normal", "strong": "firm", "confident": "firm", "serious": "firm",
        "powerful": "intense", "angry": "intense", "passionate": "intense", "emotional": "intense"}
PACES = {"slow": 0.88, "slower": 0.88, "normal": 1.0, "fast": 1.1, "faster": 1.1, "quick": 1.1}
PAUSES = {"pause": 0.45, "beat": 0.45, "breath": 0.45, "long pause": 1.0}

_TAG = re.compile(r"^\[([^\]]*)\]\s*")
_PAUSE = re.compile(r"\(\s*(long pause|pause|beat|breath)\s*\)", re.I)


def read_tag(inside, feel, pace):
    for w in re.findall(r"[a-z]+", inside.lower()):
        w = SAME.get(w, w)
        if w in FEELS: feel = w
        elif w in PACES: pace = w
    return feel, pace


def parse(text):
    """Returns (lines, breaks, dirs). lines: the clean text of each line (what the captions show).
    breaks: {line number: blank lines after it}. dirs: per line dict(feel, pace, emph={word numbers},
    pauses={word number: seconds}) - a pause after that word (-1 = before the first word)."""
    lines, breaks, dirs = [], {}, []
    feel, pace = "normal", "normal"
    for raw in text.splitlines():
        t = raw.strip().lstrip(">").strip()
        m = _TAG.match(t)
        if m:
            feel, pace = read_tag(m.group(1), "normal", "normal")   # a new tag starts fresh; t = t[m.end():].strip()
            if not t: continue          # a tag on its own line: applies to the lines below
        if not t:
            if lines: breaks[len(lines) - 1] = breaks.get(len(lines) - 1, 0) + 1
            continue
        t = re.sub(r"\[[^\]]*\]", " ", t)                       # stray tags in the middle of a line
        t = _PAUSE.sub(lambda p: " \x00%s " % p.group(1).lower().replace(" ", "_"), t)
        words, emph, pauses, inside = [], set(), {}, False
        for tok in t.split():
            if tok.startswith("\x00"):
                k = len(words) - 1; pauses[k] = pauses.get(k, 0) + PAUSES[tok[1:].replace("_", " ")]
                continue
            stars = tok.count("*"); w = tok.replace("*", "")
            if w:
                if inside or stars: emph.add(len(words))
                words.append(w)
            if stars % 2: inside = not inside
        if not words: continue
        lines.append(" ".join(words))
        dirs.append(dict(feel=feel, pace=pace, emph=emph, pauses=pauses))
    breaks.pop(len(lines) - 1, None)   # no pause needed after the very last line
    return lines, breaks, dirs


def has_marks(dirs):
    return any(d["feel"] != "normal" or d["pace"] != "normal" or d["emph"] or d["pauses"] for d in dirs)
