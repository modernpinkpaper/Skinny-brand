"""TikTok link -> every comment -> video ideas -> finished scripts, written by Claude with FORMULA.md.

  python tiktok_to_scripts.py links/my-post --out scripts/ [--dispatch videos-my-post]
  (needs the ANTHROPIC_API_KEY environment variable; on GitHub it comes from the repo's secret)
  --dispatch: on GitHub, start the "Make video" workflow for each script the moment it is written

The link file holds the TikTok link, plus optional settings (see links/README.md). Claude follows
FORMULA.md (how to write a script) and PICKING.md (how to pick topics from comments). Each topic is written
several times, each with a different hook from the formula, so one topic becomes several different videos.
Steps:
  1. grab every comment on the post (tools/tiktok_comments.py, the Comment Grabber's code)
  2. Claude reads the comments a few hundred at a time and lists the different video ideas they hold,
     skipping jokes, spam and anything that doesn't fit the formula
  3. Claude writes one script per idea, following FORMULA.md
  4. each script is checked against the formula's rules; one that fails is sent back once with the problems
  5. each script is saved as its own file, ready for make_from_file.py
Scripts are written while Claude is still reading the rest of the comments, and (with --dispatch) each video
starts being made as soon as its script is done."""
import os, re, sys, time, argparse, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Literal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

MODEL = "claude-opus-5"
CHUNK = 250            # comments Claude reads per planning request
MAX_COMMENTS = 3000    # the most-liked comments that are read at all
HARD_CAP = 1000        # never more videos than this from one link
WORDS = (120, 190)     # script length allowed (the formula aims for 140-170)
LOOKS = ["moody", "vintage", "bright", "pastel", "black and white"]

WRITER_RULES = """You write TikTok voiceover scripts for my video maker. Follow my script system and formula above
exactly, opening with the hook template you are told to use.

Rules for every script:
- Build it from the pattern in the real comments you are given: their situations, feelings, questions and small
  details. Do not quote or copy the comments; say it in your own words, speaking to the viewer ("you"). Never use a
  username. Don't invent dramatic facts that no comment supports.
- Match the topic's kind: if the audience needs a practical solution, give them one; if it is educational, give
  clear tips or explanations; use the emotional approach only for emotional topics.
- Output only the script body: one short line per clip, a blank line between thoughts (two blank lines for a
  longer pause). Plain words only: no brackets, stars, stage directions or voice notes.
  No settings, no part labels, no title, no code block fences, no notes before or after."""

PLAN_RULES = """You are going through real comments from one TikTok post (id, likes, text) to find script topics,
following my picking instructions above. You get the comments a few hundred at a time; topics already found from
earlier batches are listed so you don't repeat them.

For every strong topic in this batch, return:
- title: the theme in 3 to 7 plain words (it becomes the file name)
- surface, deeper: what is happening on the surface, and the deeper pain / problem / need
- kind: Emotional, Practical or Educational
- hooks: the numbers of the formula's hook templates (1-13) that fit this topic, best first (at least 3)
- why: one sentence on why this topic is worth making
- comment_ids: the comments it is built from, strongest first (several when possible, up to 12)
- look: the clip mood that fits (moody, vintage, bright, pastel, black and white)
- clips: animated, real (TV / movie scenes), or both
Return every strong topic, with no limit, and never repeat a topic already found. An empty list is fine if the
batch has nothing new."""


# ---------- the link file ----------
def read_link_file(path):
    text = open(path, encoding="utf-8-sig").read()
    m = re.search(r"https?://\S*tiktok\.com\S*", text)
    if not m: sys.exit(f"{path}: no TikTok link found in the file")
    o = dict(link=m.group(0).rstrip(").,"), videos="all", versions="3", look="auto", clips="auto", speed="", end="",
             tags="", notes="")
    for line in text.splitlines():
        if ":" not in line or line.strip().lower().startswith("http"): continue
        k, v = [x.strip() for x in line.split(":", 1)]; k = k.lower()
        if k in o and k != "link" and v: o[k] = v
    v = str(o["videos"]).lower()
    o["videos"] = HARD_CAP if not re.fullmatch(r"\d+", v) else max(1, min(int(v), HARD_CAP))
    v = str(o["versions"]).lower()
    o["versions"] = 13 if not re.fullmatch(r"\d+", v) else max(1, min(int(v), 13))
    return o


def slug(s, n=60):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "video"


# ---------- 1. comments ----------
def guidance():
    """The instruction files, in the order Claude reads them."""
    parts = []
    for f, title in (("FORMULA.md", "MY SCRIPT FORMULA"), ("PICKING.md", "HOW I PICK TOPICS FROM COMMENTS")):
        p = os.path.join(HERE, f)
        if os.path.exists(p): parts.append(f"# {title}\n\n" + open(p, encoding="utf-8").read().strip())
    return "\n\n---\n\n".join(parts)


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
    title: str             # the theme, 3-7 words
    surface: str           # what is happening on the surface
    deeper: str            # the deeper pain / problem / need
    kind: Literal["Emotional", "Practical", "Educational"]
    hooks: List[int]       # the formula's hook templates (1-13) that fit, best first
    why: str               # one sentence: why this topic is worth making
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
        taken = "\n".join(f"- {i['title']}: {i['deeper']}" for i in ideas) or "(none yet)"
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
    """The formula's rules that can be checked. Returns a list of problems (empty = good)."""
    probs = []
    body = script.strip().strip("`").strip()
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if not lines: return ["the script is empty"]
    words = sum(len(l.split()) for l in lines)
    if not (WORDS[0] <= words <= WORDS[1]): probs.append(f"it has {words} words; it must have 140-170")
    if any(re.search(r"[\[\]*]|\((?:long )?pause\)", l) for l in lines):
        probs.append("remove brackets, stars and notes like [calm] or (pause): plain words only")
    if any(re.match(r"[A-Z][A-Z ]{2,}:", l) for l in lines): probs.append("remove part labels like HOOK:")
    long = [l for l in lines if len(l.split()) > 14]
    if long: probs.append(f"{len(long)} lines are too long for one clip (keep lines under 12 words), e.g. \"{long[0]}\"")
    return probs


def write_one(formula, idea, comments, fmt=None):
    sys_ = formula + "\n\n---\n\n" + WRITER_RULES
    material = "\n".join(f"- ({comments[i]['likes']} likes) {comments[i]['text']}" for i in idea["comment_ids"])
    user = (f"Topic: {idea['title']}\nOn the surface: {idea['surface']}\nThe deeper pain / problem / need: {idea['deeper']}\n"
            f"Kind: {idea['kind']}\n" + (f"Open with hook template {fmt} from the formula.\n" if fmt else "") +
            f"\nThe real comments this topic comes from (for research only, don't quote them):\n{material}")
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
    formula = guidance()
    print(f"{batch}: {o['link']} (up to {o['videos']} videos, {o['versions']} per topic, "
          f"look={o['look']}, clips={o['clips']})", flush=True)

    import tiktok_comments
    _, rows = tiktok_comments.scrape(o["link"], replies=True, progress=lambda m: None)
    comments = good_comments(rows)
    print(f"{len(rows)} comments grabbed, {len(comments)} worth reading", flush=True)
    if not comments: sys.exit("No usable comments (the post may be private, or TikTok blocked the request).")

    by_id = {c["id"]: c for c in comments}
    folder = os.path.join(args.out, batch); os.makedirs(folder, exist_ok=True)
    made, report, lock = [], [], threading.Lock()
    ex = ThreadPoolExecutor(4)

    def job(n, idea, fmt):
        try: script, probs = write_one(formula, idea, by_id, fmt)
        except Exception as e: script, probs = None, [f"error: {e}"]
        with lock:
            if not script:
                report.append(f"- skipped: {idea['title']} ({'; '.join(probs)})"); return
            path = os.path.join(folder, f"{n:03d}-{slug(idea['title'], 50)}{f'-hook{fmt}' if fmt else ''}.txt")
            text = settings_header(o, idea) + script + "\n"
            open(path, "w", encoding="utf-8").write(text)
            made.append(path)
            off = f"  (still off: {'; '.join(probs)})" if probs else ""
            report.append(f"- {os.path.basename(path)}: {idea['kind']}, hook {fmt or '-'}. {idea['deeper']}{off}")
            print(f"script {len(made)}: {os.path.basename(path)}{off}", flush=True)
        if args.dispatch: start_video(path, text, args.dispatch)

    count = [0]
    def on_idea(idea):   # write the scripts right away, while Claude keeps reading comments
        hooks = list(dict.fromkeys(h for h in idea["hooks"] if 1 <= h <= 13))
        hooks += [h for h in range(1, 14) if h not in hooks]   # fewer fitting hooks than asked: use others too
        for fmt in hooks[:o["versions"]]:   # one video per hook: same topic, different opening
            if count[0] >= o["videos"]: return
            count[0] += 1; ex.submit(job, count[0], idea, fmt)
    ideas = plan(formula, comments, o["videos"], o["notes"], say=lambda m: print(m, flush=True), on_idea=on_idea)
    print(f"{len(ideas)} topics, {count[0]} scripts; finishing them", flush=True)
    ex.shutdown(wait=True)
    made.sort()
    open(os.path.join(folder, "README.md"), "w", encoding="utf-8").write(
        f"# {batch}\n\nFrom {o['link']}: {len(rows)} comments, {len(comments)} read, {len(ideas)} topics, "
        f"{len(made)} scripts.\n\n" + "\n".join(sorted(report)) + "\n")
    if args.list: open(args.list, "w").write("\n".join(made) + ("\n" if made else ""))
    print(f"DONE: {len(made)} scripts in {folder}", flush=True)


if __name__ == "__main__":
    main()
