"""TikTok link -> every comment -> video ideas -> finished scripts, written by Claude with FORMULA.md.

  python tiktok_to_scripts.py links/my-post --out scripts/ [--dispatch videos-my-post]
  (needs the ANTHROPIC_API_KEY environment variable; on GitHub it comes from the repo's secret)
  --dispatch: on GitHub, start the "Make video" workflow for each script the moment it is written

The link file holds the TikTok link, plus optional settings (see links/README.md).
Steps:
  1. grab every comment on the post (tools/tiktok_comments.py, the Comment Grabber's code)
  2. Claude reads the comments a few hundred at a time and lists the different video ideas they hold,
     skipping jokes, spam and anything that doesn't fit the formula
  3. Claude writes one script per idea, following FORMULA.md (voice marks included)
  4. each script is checked against the formula's rules; one that fails is sent back once with the problems
  5. each script is saved as its own file, ready for make_from_file.py
Scripts are written while Claude is still reading the rest of the comments, and (with --dispatch) each video
starts being made as soon as its script is done."""
import os, re, sys, time, argparse, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Literal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
from clipmaker import direct                      # noqa: E402  (reads the voice marks, like the video maker does)

MODEL = "claude-opus-5"
CHUNK = 250            # comments Claude reads per planning request
MAX_COMMENTS = 3000    # the most-liked comments that are read at all
HARD_CAP = 500         # never more scripts than this from one link
WORDS = (120, 190)     # script length allowed (the formula aims for 140-170)
LOOKS = ["moody", "vintage", "bright", "pastel", "black and white"]

WRITER_RULES = """You write TikTok voiceover scripts for my video maker. Follow the formula above exactly:
the numbers, the 6-part structure, the hook templates, the speaking tricks, the tone rules and the voice directions.

Rules for every script:
- Build it from the real comments you are given: their situations, feelings and small details. Retell them in
  your own words, speaking to the viewer ("you"). Never quote a username. Change small details so no one person
  can be identified. Don't invent dramatic facts that no comment mentions.
- Output only the script body: one short line per clip, voice marks included, blank lines between thoughts.
  No settings, no part labels, no title, no code block fences, no notes before or after."""

PLAN_RULES = """You plan TikTok videos. Below is my script formula, then a batch of real comments from one TikTok post
(id, likes, text). Find the different video ideas these comments hold that fit the formula: a feeling or truth
the viewer has lived, told to "you", with enough real material for a 60-second script.

- Each idea needs its own angle. Don't repeat an idea already taken (listed below) or one another in this batch.
- Back each idea with the comment ids it is built from (1 to 8 comments, the strongest first).
- Skip jokes, spam, arguments, tags, and comments with nothing to build on. It is fine to return few or no ideas.
- title: 3 to 7 words, plain, good as a file name. angle: 1 to 2 sentences saying what the video tells the viewer.
- look: the clip mood that fits (moody, vintage, bright, pastel, black and white).
- clips: animated, real (TV / movie scenes), or both."""


# ---------- the link file ----------
def read_link_file(path):
    text = open(path, encoding="utf-8-sig").read()
    m = re.search(r"https?://\S*tiktok\.com\S*", text)
    if not m: sys.exit(f"{path}: no TikTok link found in the file")
    o = dict(link=m.group(0).rstrip(").,"), videos="all", look="auto", clips="auto", speed="", end="", tags="", notes="")
    for line in text.splitlines():
        if ":" not in line or line.strip().lower().startswith("http"): continue
        k, v = [x.strip() for x in line.split(":", 1)]; k = k.lower()
        if k in o and k != "link" and v: o[k] = v
    v = str(o["videos"]).lower()
    o["videos"] = HARD_CAP if not re.fullmatch(r"\d+", v) else max(1, min(int(v), HARD_CAP))
    return o


def slug(s, n=60):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "video"


# ---------- 1. comments ----------
def good_comments(rows):
    """The comments worth reading: real sentences, no duplicates, most-liked first."""
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: -int(r.get("likes") or 0)):
        t = re.sub(r"\s+", " ", re.sub(r"@\S+", "", r.get("text") or "")).strip()
        key = re.sub(r"[^a-z]", "", t.lower())[:80]
        if len(t) < 25 or len(t.split()) < 5 or key in seen: continue
        seen.add(key); out.append(dict(id=str(len(out) + 1), likes=int(r.get("likes") or 0), text=t[:1200]))
        if len(out) >= MAX_COMMENTS: break
    return out


# ---------- Claude ----------
from pydantic import BaseModel  # noqa: E402

class Idea(BaseModel):
    title: str
    angle: str
    comment_ids: List[str]
    look: Literal["moody", "vintage", "bright", "pastel", "black and white"]
    clips: Literal["animated", "real", "both"]

class Ideas(BaseModel):
    ideas: List[Idea]

class Script(BaseModel):
    script: str


_client, _fallbacks = None, True
def ask(system, user, schema):
    """One request to Claude. Returns the parsed result, or None if Claude declined or ran out of room."""
    global _client, _fallbacks
    import anthropic
    if _client is None: _client = anthropic.Anthropic(max_retries=8)
    kw = dict(model=MODEL, max_tokens=16000, output_format=schema,
              system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
              messages=[{"role": "user", "content": user}])
    if _fallbacks:   # if Claude Opus 5 declines, the request is re-run on the recommended fallback model
        kw.update(extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"}, extra_body={"fallbacks": "default"})
    try:
        r = _client.messages.parse(**kw)
    except anthropic.BadRequestError as e:
        if not _fallbacks or "fallback" not in str(e).lower(): raise
        _fallbacks = False; return ask(system, user, schema)
    if r.stop_reason in ("refusal", "max_tokens") or r.parsed_output is None:
        print(f"  (skipped: {r.stop_reason})", flush=True); return None
    return r.parsed_output


# ---------- 2. ideas ----------
def plan(formula, comments, want, notes, say=print, on_idea=lambda idea: None):
    """on_idea(idea) is called for each new idea as soon as it is found."""
    ideas, by_id = [], {c["id"]: c for c in comments}
    for start in range(0, len(comments), CHUNK):
        if len(ideas) >= want: break
        batch = comments[start:start + CHUNK]
        taken = "\n".join(f"- {i['title']}: {i['angle']}" for i in ideas) or "(none yet)"
        user = (f"Notes from me: {notes or 'none'}\n\nIdeas already taken:\n{taken}\n\nComments:\n" +
                "\n".join(f"[{c['id']}] ({c['likes']} likes) {c['text']}" for c in batch))
        res = ask(formula + "\n\n---\n\n" + PLAN_RULES, user, Ideas)
        new = 0
        for i in (res.ideas if res else []):
            ids = [x.strip("[] ") for x in i.comment_ids if x.strip("[] ") in by_id]
            if not ids or any(slug(i.title) == slug(t["title"]) for t in ideas): continue
            if len(ideas) >= want: break
            ideas.append(dict(i.model_dump(), comment_ids=ids)); new += 1; on_idea(ideas[-1])
        say(f"read comments {start + 1}-{start + len(batch)} of {len(comments)}: {new} new ideas ({len(ideas)} total)")
    return ideas[:want]


# ---------- 3 + 4. scripts ----------
def check(script):
    """The formula's rules the video maker can check. Returns a list of problems (empty = good)."""
    probs = []
    body = script.strip().strip("`").strip()
    lines, _, dirs = direct.parse(body)
    words = sum(len(l.split()) for l in lines)
    if not lines: return ["the script is empty"]
    if not (WORDS[0] <= words <= WORDS[1]): probs.append(f"it has {words} words; it must have 140-170")
    first = next(l for l in body.splitlines() if l.strip())
    if not first.strip().startswith("["): probs.append("the first line must start with a voice tag like [calm, slow]")
    raw = [l for l in body.splitlines() if l.strip()]
    if any(l.count("*") > 2 for l in raw): probs.append("a line has more than one *stressed* word")
    if body.lower().count("(long pause)") > 1: probs.append("more than one (long pause)")
    if any(re.match(r"\s*(\[[^\]]*\]\s*)?[A-Z][A-Z ]{2,}:", l) for l in raw): probs.append("remove part labels like HOOK:")
    long = [l for l in lines if len(l.split()) > 14]
    if long: probs.append(f"{len(long)} lines are too long for one clip (keep lines under 12 words), e.g. \"{long[0]}\"")
    if sum(d["feel"] == "intense" for d in dirs) > max(2, len(lines) // 6): probs.append("too many [intense] lines")
    return probs


def write_one(formula, idea, comments):
    sys_ = formula + "\n\n---\n\n" + WRITER_RULES
    material = "\n".join(f"- ({comments[i]['likes']} likes) {comments[i]['text']}" for i in idea["comment_ids"])
    user = f"Video idea: {idea['title']}\nWhat it tells the viewer: {idea['angle']}\n\nThe real comments it is built from:\n{material}"
    res = ask(sys_, user, Script)
    if not res: return None, ["Claude declined"]
    probs = check(res.script)
    if probs:   # one second try with the problems spelled out
        res2 = ask(sys_, user + "\n\nYour first draft broke these rules:\n- " + "\n- ".join(probs) +
                   "\n\nFirst draft:\n" + res.script + "\n\nWrite the whole script again, fixed.", Script)
        if res2:
            p2 = check(res2.script)
            if len(p2) < len(probs) or not p2: res, probs = res2, p2
    return res.script.strip().strip("`").strip(), probs


def start_video(path, text, release):
    """Starts the "Make video" workflow on GitHub for one script (the script text goes with it)."""
    name = os.path.splitext(os.path.basename(path))[0]
    cmd = ["gh", "workflow", "run", "make-video.yml", "--ref", os.environ.get("GITHUB_REF_NAME", "main"),
           "-f", f"name={name}", "-f", f"release={release}", "-f", f"script={text}"]
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0: print(f"  video started: {name}", flush=True); return
        print(f"  could not start the video yet ({r.stderr.strip()[:200]}), retrying", flush=True)
        time.sleep(10 * (attempt + 1))
    print(f"::error::could not start the video for {name}", flush=True)


def settings_header(o, idea):
    look = o["look"] if o["look"] != "auto" else idea["look"]
    clips = o["clips"] if o["clips"] != "auto" else idea["clips"]
    h = [f"look: {look}", f"clips: {clips}"]
    for k in ("speed", "end", "tags"):
        if o[k]: h.append(f"{k}: {o[k]}")
    return "\n".join(h) + "\n---\n"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("linkfile"); ap.add_argument("--out", default="scripts")
    ap.add_argument("--list", help="write the new script paths (one per line) to this file")
    ap.add_argument("--dispatch", metavar="RELEASE", help="start a Make video run for each script, adding it to RELEASE")
    args = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY. On GitHub: Settings > Secrets and variables > Actions > New repository secret.")
    o = read_link_file(args.linkfile)
    batch = slug(os.path.splitext(os.path.basename(args.linkfile))[0], 40)
    formula = open(os.path.join(HERE, "FORMULA.md"), encoding="utf-8").read()
    print(f"{batch}: {o['link']} (up to {o['videos']} videos, look={o['look']}, clips={o['clips']})", flush=True)

    import tiktok_comments
    _, rows = tiktok_comments.scrape(o["link"], replies=True, progress=lambda m: None)
    comments = good_comments(rows)
    print(f"{len(rows)} comments grabbed, {len(comments)} worth reading", flush=True)
    if not comments: sys.exit("No usable comments (the post may be private, or TikTok blocked the request).")

    by_id = {c["id"]: c for c in comments}
    folder = os.path.join(args.out, batch); os.makedirs(folder, exist_ok=True)
    made, report, lock = [], [], threading.Lock()
    ex = ThreadPoolExecutor(4)

    def job(n, idea):
        try: script, probs = write_one(formula, idea, by_id)
        except Exception as e: script, probs = None, [f"error: {e}"]
        with lock:
            if not script:
                report.append(f"- skipped: {idea['title']} ({'; '.join(probs)})"); return
            path = os.path.join(folder, f"{n:03d}-{slug(idea['title'], 50)}.txt")
            text = settings_header(o, idea) + script + "\n"
            open(path, "w", encoding="utf-8").write(text)
            made.append(path)
            off = f"  (still off: {'; '.join(probs)})" if probs else ""
            report.append(f"- {os.path.basename(path)}: {idea['angle']}{off}")
            print(f"script {len(made)}: {os.path.basename(path)}{off}", flush=True)
        if args.dispatch: start_video(path, text, args.dispatch)

    count = [0]
    def on_idea(idea):   # write the script right away, while Claude keeps reading comments
        count[0] += 1; ex.submit(job, count[0], idea)
    ideas = plan(formula, comments, o["videos"], o["notes"], say=lambda m: print(m, flush=True), on_idea=on_idea)
    print(f"{len(ideas)} video ideas; finishing the scripts", flush=True)
    ex.shutdown(wait=True)
    made.sort()
    open(os.path.join(folder, "README.md"), "w", encoding="utf-8").write(
        f"# {batch}\n\nFrom {o['link']}: {len(rows)} comments, {len(comments)} read, {len(ideas)} ideas, "
        f"{len(made)} scripts.\n\n" + "\n".join(sorted(report)) + "\n")
    if args.list: open(args.list, "w").write("\n".join(made) + ("\n" if made else ""))
    print(f"DONE: {len(made)} scripts in {folder}", flush=True)


if __name__ == "__main__":
    main()
