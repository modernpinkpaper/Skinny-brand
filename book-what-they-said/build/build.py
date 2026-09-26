#!/usr/bin/env python3
"""Builds the full "What They Said" guided journal (6x9 in, black & white interior).
Reads chapters.py (structure) + entries_*.json (written entries), picks the best 200 stories,
and writes book.html (interior) + cover.html. Render with render.mjs.
Usage: python3 book-what-they-said/build/build.py"""
import json, glob, os, html
from chapters import CHAPTERS

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = 200
esc = lambda s: html.escape(s, quote=False)

# ---- load entries ----
E = {}
for f in sorted(glob.glob(os.path.join(HERE, "entries_*.json"))):
    for e in json.load(open(f, encoding="utf-8")):
        E[str(e["cid"])] = e

# chapter -> subsection -> entries. Extra entries (cid like "225b", "193b") are extra triumph stories
# written for the last chapter, so they all go there, after that chapter's own entries.
extras = [E[k] for k in E if not k.isdigit()]
book = []
for ci, (title, intro, subs) in enumerate(CHAPTERS):
    chap = [[sub, [E[str(cid)] for cid in ids if str(cid) in E]] for sub, ids in subs]
    book.append([title, intro, chap])
book[-1][2][-1][1].extend(extras)

# ---- trim to TARGET: drop weakest, from the biggest chapters first; keep every subsection and the last chapter whole ----
def total(): return sum(len(s[1]) for ch in book for s in ch[2])
dropped = []
while total() > TARGET:
    cands = []
    for chi, ch in enumerate(book[:-1]):
        size = sum(len(s[1]) for s in ch[2])
        for s in ch[2]:
            if len(s[1]) > 1:
                for e in s[1]: cands.append((int(e.get("strength", 3)), -size, len(e["story"]) * -1, chi, s, e))
    cands.sort(key=lambda c: c[:3])
    _, _, _, chi, s, e = cands[0]
    s[1].remove(e); dropped.append((book[chi][0], e))
json.dump([{"chapter": c, **e} for c, e in dropped], open(os.path.join(HERE, "dropped.json"), "w"), ensure_ascii=False, indent=1)

BREATHE = [
 "Being loved less was never proof that you were worth less.",
 "You were never a mistake. You were a person who deserved to be wanted.",
 "Your body was never the problem. The words were.",
 "Grief is love with nowhere to go. You were allowed to feel every bit of it.",
 "Some weights were never yours to carry. You can set them down here.",
 "What happened to you was real, whether or not they believed you.",
 "Belonging isn't something anyone gets to take away from you.",
 "You were a mother, a daughter, a person, in every one of those moments.",
 "You were enough before you ever had to prove it.",
 "You were never just useful. You were always worth loving.",
 "Love that asks you to disappear isn't the kind you owe anything to.",
 "Who you are was never the problem.",
 "Their words were a prediction. Not a promise.",
 "And then you did.",
]

# ---- pages ----
pages = []   # (kind, html) ; folio added later for numbered pages
def page(cls, body, numbered=True, run=""):
    pages.append({"cls": cls, "body": body, "numbered": numbered, "run": run})

page("title", '<div class="small">a guided journal</div><h1>What They<br>Said</h1><div class="rule"></div>'
     '<p class="sub">200 things families said that we\'re still healing from — and what we needed to hear instead</p>', False)
page("blank", "", False)
page("prose", '<h2>I didn\'t write this book.</h2>'
     '<p>Thousands of strangers did. One question was asked online — <i>“What\'s something a family member said that you\'ll never fully forgive?”</i> — and people answered with things they had never said out loud.</p>'
     '<p>I read every answer. I kept the words that stayed with me. And under each one, I wrote what that person deserved to hear instead.</p>'
     '<p>You don\'t have to read this in order. Open it anywhere. Write, or don\'t. Put it down when it gets heavy — that\'s allowed too.</p>'
     '<div class="note">A gentle note: some pages touch on grief, abuse, pregnancy loss, rejection and suicide. Stories have been shortened and changed so no one can be identified. If this brings up something big, please reach out to someone you trust or a support line — there\'s a list at the back of this book.</div>', False)
page("prose howto", '<h2>How to use this book</h2>'
     '<p><b>Read the story.</b> Each page holds one real thing a family member said.</p>'
     '<p><b>Read what they needed to hear.</b> The words that person deserved — and maybe you did too.</p>'
     '<p><b>Then it\'s your turn.</b> Answer the prompt on the lines below. Write as much or as little as you want. Cross things out. Come back later.</p>'
     '<p>There are no wrong answers here, and no one is grading your healing.</p>', False)
toc_index = len(pages); page("toc", "", False)
if total() > 0: page("blank", "", False)

chapter_start = {}
for ci, (title, intro, chap) in enumerate(book):
    subs = [s for s, items in chap if s and items]
    chapter_start[ci] = len(pages)
    sublist = "".join(f"<li>{esc(s)}</li>" for s in subs)
    page("opener", f'<div class="num">{ci+1:02d}</div><h2>{esc(title)}</h2><p>{esc(intro)}</p>' + (f'<ul class="subs">{sublist}</ul>' if subs else ""), False)
    for sub, items in chap:
        for e in items:
            run = f"{esc(title)}" + (f" · {esc(sub)}" if sub else "")
            page("entry", f'<p class="said">{esc(e["story"])}</p><div class="who">— shared by {esc(e["shared_by"])}</div>'
                 f'<div class="needed"><div class="label">What you needed to hear</div><p>{esc(e["needed"])}</p></div>'
                 f'<div class="rule2"></div><div class="label">Your turn</div><p class="q">{esc(e["prompt"])}</p><div class="lines"></div>', True, run)
    page("breathe", f'<p>{esc(BREATHE[ci])}</p><div class="small">take a breath before you turn the page</div>', False)

letters_start = len(pages)
page("opener", '<div class="num">—</div><h2>Letters I\'ll Never Send</h2><p>Say the thing you never got to say. No one will read these but you — so say it all.</p>', False)
for k in range(6):
    page("letter", '<p class="dear">Dear ______________________,</p><div class="lines"></div>', True, "Letters I'll Never Send")
support_start = len(pages)
page("prose support", '<h2>Where to find support</h2>'
     '<p>If you\'re in danger or thinking about ending your life, please reach out right now. You deserve support.</p>'
     '<ul>'
     '<li><b>988 Suicide &amp; Crisis Lifeline</b> (US) — call or text <b>988</b></li>'
     '<li><b>Crisis Text Line</b> (US) — text <b>HOME</b> to <b>741741</b></li>'
     '<li><b>RAINN Sexual Assault Hotline</b> (US) — <b>1-800-656-4673</b></li>'
     '<li><b>National Domestic Violence Hotline</b> (US) — <b>1-800-799-7233</b></li>'
     '<li><b>Postpartum Support International</b> (US) — <b>1-800-944-4773</b></li>'
     '<li><b>The Trevor Project</b> (LGBTQ+ young people) — <b>1-866-488-7386</b></li>'
     '<li><b>Outside the US</b> — find a free, local helpline at <b>findahelpline.com</b></li>'
     '</ul><p>A therapist who understands family estrangement or childhood emotional neglect can also help. You don\'t have to heal alone.</p>', False)
page("breathe end", '<p>You made it to the last page.<br>What they said was never the whole story.<br>You are.</p>', False)

# page numbers: count every page from the title page as 1 (standard book numbering)
for i, p in enumerate(pages): p["no"] = i + 1
toc = []
for ci, (title, _, chap) in enumerate(book):
    toc.append(f'<div class="row"><b>{ci+1:02d}</b><span>{esc(title)}</span><i>{pages[chapter_start[ci]]["no"]}</i></div>')
toc.append(f'<div class="row"><b>—</b><span>Letters I\'ll Never Send</span><i>{pages[letters_start]["no"]}</i></div>')
toc.append(f'<div class="row"><b>—</b><span>Where to Find Support</span><i>{pages[support_start]["no"]}</i></div>')
pages[toc_index]["body"] = "<h2>Contents</h2>" + "".join(toc)

fonts = "../../brand/fonts"
CSS = f"""
@font-face{{font-family:Lora;font-weight:400 700;src:url({fonts}/Lora-normal.woff2)}}
@font-face{{font-family:Lora;font-style:italic;font-weight:400 700;src:url({fonts}/Lora-italic.woff2)}}
@font-face{{font-family:Inter;font-weight:100 900;src:url({fonts}/Inter-normal.woff2)}}
@font-face{{font-family:Caveat;src:url({fonts}/Caveat-normal.woff2)}}
@page{{size:900px 1350px;margin:0}}
:root{{--ink:#111;--soft:#666;--line:#c4c4c4}}
*{{box-sizing:border-box;margin:0}}
body{{background:#d9d4ce;font-family:Lora,Georgia,serif;color:var(--ink)}}
.page{{width:900px;height:1350px;background:#fff;position:relative;padding:100px 100px 105px;margin:30px auto;display:flex;flex-direction:column;overflow:hidden;page-break-after:always}}
@media print{{body{{background:#fff}}.page{{margin:0}}}}
.run{{position:absolute;top:50px;left:0;right:0;text-align:center;font:500 13px Inter;letter-spacing:.22em;text-transform:uppercase;color:var(--soft)}}
.folio{{position:absolute;bottom:48px;left:0;right:0;text-align:center;font:500 16px Inter;color:var(--soft)}}
.label{{font:600 12px Inter;letter-spacing:.2em;text-transform:uppercase;color:#333;margin-bottom:6px}}
.small{{font:600 14px Inter;letter-spacing:.24em;text-transform:uppercase;color:#444}}
.said{{font:400 22px/1.5 Lora}}
.who{{font:500 13px Inter;color:var(--soft);letter-spacing:.05em;margin:8px 0 18px}}
.needed{{border-left:2px solid #999;padding:2px 0 2px 18px;margin-bottom:22px}}
.needed p{{font:italic 400 19px/1.5 Lora;color:#222}}
.rule2{{height:1px;background:#bbb;margin:0 0 18px}}
.q{{font:600 19px/1.5 Lora;margin-bottom:4px}}
.lines{{flex:1;background:repeating-linear-gradient(to bottom,transparent 0,transparent 49px,var(--line) 49px,var(--line) 50px)}}
.title,.opener,.breathe{{justify-content:center;text-align:center}}
.title h1{{font:400 110px/1 Lora;margin:36px 0 34px}}
.rule{{width:60px;height:2px;background:#333;margin:0 auto}}
.title .sub{{font:italic 400 30px/1.45 Lora;color:#333;max-width:600px;margin:34px auto 0}}
.prose{{justify-content:center}}
.prose h2{{font:400 48px/1.15 Lora;margin-bottom:40px}}
.prose p{{font:400 24px/1.7 Lora;margin-bottom:24px}}
.prose .note{{margin-top:24px;padding:24px 28px;border:1.5px solid #9a9a9a;font:400 19px/1.6 Inter;color:#333}}
.support ul{{margin:0 0 24px 0;padding-left:22px}}.support li{{font:400 21px/1.6 Lora;margin-bottom:12px}}
.toc{{justify-content:flex-start;padding-top:110px}}
.toc h2{{font:400 52px Lora;margin-bottom:40px}}
.toc .row{{display:flex;align-items:baseline;gap:16px;padding:13px 0;border-bottom:1px solid #d0d0d0;font-size:22px}}
.toc .row b{{font:600 15px Inter;color:#333;min-width:36px}}.toc .row span{{flex:1}}.toc .row i{{font:500 16px Inter;color:var(--soft);font-style:normal}}
.opener .num{{font:400 130px/1 Lora;color:#333}}
.opener h2{{font:400 60px/1.1 Lora;margin:26px 0 24px}}
.opener p{{font:italic 400 27px/1.55 Lora;color:#333;max-width:620px;margin:0 auto}}
.opener .subs{{list-style:none;padding:0;margin:44px auto 0;font:600 14px Inter;letter-spacing:.2em;text-transform:uppercase;color:#555;line-height:2.3}}
.breathe p{{font:italic 400 50px/1.35 Lora;max-width:640px;margin:0 auto}}
.breathe .small{{margin-top:56px}}
.letter .dear{{font:400 26px Lora;margin:20px 0 10px}}
"""
out = [f'<!doctype html><html><head><meta charset="utf-8"><title>What They Said — interior</title><style>{CSS}</style></head><body>']
for p in pages:
    run = f'<div class="run">{p["run"]}</div>' if p["run"] else ""
    folio = f'<div class="folio">{p["no"]}</div>' if p["numbered"] else ""
    out.append(f'<section class="page {p["cls"]}">{run}{p["body"]}{folio}</section>')
out.append("</body></html>")
open(os.path.join(HERE, "book.html"), "w", encoding="utf-8").write("\n".join(out))

stories = total()
print(f"stories: {stories}  pages: {len(pages)}  dropped: {len(dropped)}")
for ci, (title, _, chap) in enumerate(book):
    print(f"  {ci+1:02d} {title}: {sum(len(i) for _, i in chap)}  ({', '.join(f'{s}={len(i)}' for s, i in chap if s)})")
