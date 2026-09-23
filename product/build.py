#!/usr/bin/env python3
"""Build The Skinny Laws Vault (interactive HTML + printable PDF source) from content/*.json."""
import base64, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
FONTS = ROOT.parent / "brand" / "fonts"

TITLE = "The Skinny Laws Vault"
SUBTITLE = "120 unusual hacks to get lean & stay lean — without starving"
TAGS = {
    "quick-win": "Quick wins", "hunger": "Hunger", "cravings": "Cravings", "kitchen": "Kitchen",
    "eating-out": "Eating out", "drinks": "Drinks", "sleep": "Sleep", "stress": "Stress",
    "movement": "Movement", "mindset": "Mindset", "bloat": "Bloat", "shape": "Shape",
    "maintenance": "Maintenance", "shopping": "Shopping", "social": "Social",
}
EMOJI = ["🍽️", "🏠", "🍫", "👟", "🌙", "🥂", "🛒", "🥤", "🧠", "🎈", "💪", "♾️"]

e = lambda s: html.escape(str(s), quote=True)


def paras(text):
    return "".join(f"<p>{e(p).replace(chr(10), '<br>')}</p>" for p in str(text).split("\n\n") if p.strip())


def font_face():
    out = []
    for fam, file, style, weight in [
        ("DM Serif Display", "DMSerifDisplay-normal.woff2", "normal", "400"),
        ("DM Serif Display", "DMSerifDisplay-italic.woff2", "italic", "400"),
        ("Inter", "Inter-normal.woff2", "normal", "400 800"),
    ]:
        b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};font-display:swap;"
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(out)


def load():
    chapters = [json.loads(p.read_text()) for p in sorted(CONTENT.glob("ch*.json"))]
    chapters.sort(key=lambda c: c["number"])
    bonus = json.loads((CONTENT / "bonus.json").read_text())
    n = 0
    for ch in chapters:
        for h in ch["hacks"]:
            n += 1
            h["n"] = n
            h["id"] = f"hack-{n}"
    return chapters, bonus, n


def hack_card(h, ch):
    tags = "".join(f'<span class="tag">{e(TAGS.get(t, t))}</span>' for t in h.get("tags", []))
    steps = "".join(f"<li>{e(s)}</li>" for s in h["how"])
    pro = f'<p class="pro"><b>Pro move:</b> {e(h["pro"])}</p>' if h.get("pro") else ""
    return f"""
<article class="hack" id="{h['id']}" data-tags="{e(' '.join(h.get('tags', [])))}">
  <div class="hack-top"><span class="hack-num">#{h['n']:03d}</span>{tags}</div>
  <h3>{e(h['title'])}</h3>
  <p class="hook">{e(h['hook'])}</p>
  <p>{e(h['what'])}</p>
  <div class="why"><h4>Why it works</h4><p>{e(h['why'])}</p></div>
  <div class="how"><h4>How to do it</h4><ol>{steps}</ol></div>
  {pro}
  <div class="hack-actions">
    <label class="chk"><input type="checkbox" data-save="tried-{h['n']}"><span>I tried this</span></label>
    <label class="chk fav"><input type="checkbox" data-save="fav-{h['n']}" data-fav="{h['n']}"><span>★ Favorite</span></label>
  </div>
</article>"""


def chapter_html(ch):
    i = ch["number"]
    hacks = "".join(hack_card(h, ch) for h in ch["hacks"])
    journal = "".join(
        f'<div class="prompt"><p>{e(q)}</p><textarea data-save="j-{ch["id"]}-{k}" rows="3" placeholder="Write here…"></textarea></div>'
        for k, q in enumerate(ch["journal"]))
    return f"""
<section class="chapter" id="{ch['id']}">
  <div class="ch-hero">
    <div class="ch-kicker">Law {i:02d} of 12 <span>{EMOJI[i-1]}</span></div>
    <h2>{e(ch['title'])}</h2>
    <p class="ch-sub">{e(ch['subtitle'])}</p>
    <blockquote class="law">“{e(ch['law'])}”</blockquote>
  </div>
  <div class="intro">{paras(ch['intro'])}</div>
  <div class="minitoc"><b>In this Law:</b> {''.join(f'<a href="#{h["id"]}">{e(h["title"])}</a>' for h in ch['hacks'])}</div>
  {hacks}
  <div class="myth card-alt">
    <div class="label">Myth vs. Truth</div>
    <p class="myth-m"><s>{e(ch['mythBust']['myth'])}</s></p>
    <p>{e(ch['mythBust']['truth'])}</p>
  </div>
  <div class="try card-alt">
    <div class="label">{e(ch['tryThis']['title'])}</div>
    <p>{e(ch['tryThis']['text'])}</p>
    <label class="chk"><input type="checkbox" data-save="trythis-{ch['id']}"><span>Done</span></label>
  </div>
  <div class="journal">
    <div class="label">Journal prompts</div>
    {journal}
  </div>
  <div class="quote-page"><p>“{e(ch['quote'])}”</p><span>— The Skinny Laws</span></div>
  <div class="ch-nav"><a href="#contents">↑ Contents</a>{f'<a href="#ch{i+1:02d}">Next Law →</a>' if i < 12 else '<a href="#bonus-challenge">Bonuses →</a>'}</div>
</section>"""


def build():
    chapters, bonus, total = load()
    DIST.mkdir(exist_ok=True)

    toc_items = "".join(
        f'<a class="toc-row" href="#{c["id"]}"><span class="toc-n">{c["number"]:02d}</span>'
        f'<span class="toc-t">{e(c["title"])}<small>{e(c["subtitle"])}</small></span><span class="toc-e">{EMOJI[c["number"]-1]}</span></a>'
        for c in chapters)
    bonus_links = [("start-here", "Start here"), ("quiz", "The 60-second eating-type quiz"),
                   ("bonus-challenge", "30-Day Skinny Laws Challenge"), ("bonus-grocery", "The Lean Grocery List"),
                   ("bonus-restaurant", "Restaurant Cheat Sheet"), ("bonus-tracker", "Weekly Average Tracker"),
                   ("bonus-summary", "The 12 Laws on one page"), ("favorites", "My Favorites"),
                   ("safety", "Safety & support")]
    bonus_toc = "".join(f'<a class="toc-row small" href="#{a}"><span class="toc-t">{e(t)}</span></a>' for a, t in bonus_links)

    drawer_ch = "".join(f'<a href="#{c["id"]}">{c["number"]:02d} · {e(c["title"])}</a>' for c in chapters)
    drawer_bonus = "".join(f'<a href="#{a}">{e(t)}</a>' for a, t in bonus_links)
    chips = "".join(f'<button class="chip" data-tag="{k}">{e(v)}</button>' for k, v in TAGS.items())

    howto = "".join(f'<div class="step"><span>{k+1}</span><div><b>{e(s["t"])}</b><p>{e(s["d"])}</p></div></div>'
                    for k, s in enumerate(bonus["howTo"]))
    q = bonus["quiz"]
    quiz_qs = "".join(
        f'<fieldset class="qq"><legend>{k+1}. {e(item["q"])}</legend>' +
        "".join(f'<label><input type="radio" name="q{k}" value="{v}"><span>{e(a)}</span></label>' for a, v in item["a"]) +
        "</fieldset>" for k, item in enumerate(q["questions"]))
    chap_titles = {c["id"]: c["title"] for c in chapters}
    quiz_types = {k: {**v, "readTitles": [chap_titles.get(r, r) for r in v["read"]]} for k, v in q["types"].items()}

    challenge = "".join(
        f'<label class="day"><input type="checkbox" data-save="day-{k+1}"><span class="dn">Day {k+1}</span><span class="dt">{e(t)}</span></label>'
        for k, t in enumerate(bonus["challenge"]))
    grocery = "".join(
        f'<div class="gcol"><h4>{e(cat)}</h4>' +
        "".join(f'<label class="chk g"><input type="checkbox" data-save="g-{e(cat)}-{j}"><span>{e(it)}</span></label>' for j, it in enumerate(items)) +
        "</div>" for cat, items in bonus["grocery"].items())
    rest = "".join(f'<div class="rrow"><h4>{e(r["place"])}</h4><p><b>Order:</b> {e(r["order"])}</p><p class="watch"><b>Watch out:</b> {e(r["watch"])}</p></div>'
                   for r in bonus["restaurant"])
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tracker = "".join(f'<label><span>{d}</span><input type="number" step="0.1" inputmode="decimal" data-save="w-{d}" class="w"></label>' for d in days)
    summary = "".join(f'<div class="sum"><span>{c["number"]:02d}</span><div><b>{e(c["title"])}</b><p>{e(c["law"])}</p></div></div>' for c in chapters)
    fav_index = {h["n"]: {"t": h["title"], "id": h["id"], "c": c["title"]} for c in chapters for h in c["hacks"]}
    search_index = [{"n": h["n"], "id": h["id"], "t": h["title"], "c": c["title"],
                     "tags": h.get("tags", []), "x": " ".join([h["title"], h["hook"], h["what"], h["why"], " ".join(h["how"])]).lower()}
                    for c in chapters for h in c["hacks"]]

    css = (ROOT / "vault.css").read_text()
    js = (ROOT / "vault.js").read_text()
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{e(SUBTITLE)}">
<style>{font_face()}
{css}</style></head>
<body>
<header class="bar">
  <a href="#top" class="brand">THE SKINNY LAWS <em>Vault</em></a>
  <div class="prog" title="Hacks you've tried"><span id="progN">0</span>/{total}<i><b id="progBar"></b></i></div>
  <button id="menuBtn" class="menu" aria-label="Open menu">☰ Menu</button>
</header>
<aside id="drawer" class="drawer" aria-hidden="true">
  <div class="drawer-in">
    <div class="drawer-head"><b>Jump to…</b><button id="closeBtn" aria-label="Close menu">✕</button></div>
    <input id="search" type="search" placeholder="Search 120 hacks (e.g. night snacking)">
    <div class="chips">{chips}</div>
    <div id="results" class="results"></div>
    <nav class="dnav"><div class="dlabel">The 12 Laws</div>{drawer_ch}<div class="dlabel">Start here & bonuses</div>{drawer_bonus}</nav>
  </div>
</aside>
<div id="scrim" class="scrim"></div>

<main>
<section class="cover" id="top">
  <div class="cover-in">
    <div class="cover-kicker">@theskinnylaws presents</div>
    <h1>The Skinny Laws<br><em>Vault</em></h1>
    <p class="cover-sub">{e(SUBTITLE)}</p>
    <div class="cover-stats"><div><b>{total}</b>hacks</div><div><b>12</b>laws</div><div><b>30</b>day plan</div><div><b>6</b>bonuses</div></div>
    <a class="btn" href="#start-here">Start here ↓</a>
  </div>
</section>

<section id="contents" class="contents">
  <h2>Contents</h2>
  <p class="muted">Tap any line to jump straight there. Tap <b>☰ Menu</b> at the top anytime to search or jump.</p>
  <div class="toc-group"><div class="dlabel">Start here</div>{bonus_toc}</div>
  <div class="toc-group"><div class="dlabel">The 12 Laws</div>{toc_items}</div>
</section>

<section id="start-here" class="plain">
  <h2>Welcome to the Vault</h2>
  {paras(bonus['welcome'])}
  <h3>How to use it</h3>
  <div class="steps">{howto}</div>
</section>

<section id="quiz" class="plain">
  <h2>What's your eating type?</h2>
  <p class="muted">{e(q['intro'])}</p>
  <form id="quizForm">{quiz_qs}<button type="submit" class="btn">Show my type</button></form>
  <div id="quizResult" class="quiz-result" hidden></div>
</section>

{''.join(chapter_html(c) for c in chapters)}

<section id="bonus-challenge" class="plain bonus">
  <div class="ch-kicker">Bonus 1</div><h2>The 30-Day Skinny Laws Challenge</h2>
  <p class="muted">One tiny action per day. Tick it off when it's done. Missed a day? Never miss twice — just do today's.</p>
  <div class="days">{challenge}</div>
</section>
<section id="bonus-grocery" class="plain bonus">
  <div class="ch-kicker">Bonus 2</div><h2>The Lean Grocery List</h2>
  <p class="muted">Screenshot this or tick items as you shop.</p>
  <div class="grocery">{grocery}</div>
</section>
<section id="bonus-restaurant" class="plain bonus">
  <div class="ch-kicker">Bonus 3</div><h2>Restaurant Cheat Sheet</h2>
  <p class="muted">What to order (and what to watch) at 8 kinds of places. No salads-only rule required.</p>
  <div class="rest">{rest}</div>
</section>
<section id="bonus-tracker" class="plain bonus">
  <div class="ch-kicker">Bonus 4</div><h2>Weekly Average Tracker</h2>
  <p class="muted">Daily weight jumps around with water, salt and hormones. Only the weekly average matters. Enter what you have — it does the math and saves on this device.</p>
  <div class="tracker">{tracker}</div>
  <div class="tracker-out"><div>This week's average: <b id="avgNow">—</b></div>
  <div>Last week's average: <input type="number" step="0.1" inputmode="decimal" data-save="w-last" id="lastWeek"></div>
  <div id="avgDiff" class="muted"></div>
  <button id="newWeek" class="btn ghost" type="button">Start a new week</button></div>
</section>
<section id="bonus-summary" class="plain bonus">
  <div class="ch-kicker">Bonus 5</div><h2>The 12 Laws on one page</h2>
  <div class="summary">{summary}</div>
</section>
<section id="favorites" class="plain bonus">
  <div class="ch-kicker">Bonus 6</div><h2>My Favorites</h2>
  <p class="muted">Tap “★ Favorite” on any hack and it shows up here — your personal cheat sheet.</p>
  <div id="favList" class="fav-list"></div>
</section>
<section id="safety" class="plain">
  <h2>Safety & support</h2>
  {paras(bonus['safety'])}
</section>
<section class="closing">
  {paras(bonus['closing'])}
  <p class="handle">@theskinnylaws</p>
  <a class="btn" href="#contents">Back to contents</a>
</section>
</main>
<a href="#contents" class="fab" aria-label="Back to contents">↑</a>
<script>
const TOTAL={total};
const QUIZ={json.dumps(quiz_types)};
const FAVS={json.dumps(fav_index)};
const INDEX={json.dumps(search_index)};
const TAGNAMES={json.dumps(TAGS)};
{js}
</script>
</body></html>"""
    out = DIST / "the-skinny-laws-vault.html"
    out.write_text(page)
    print(f"built {out} ({out.stat().st_size//1024} KB, {total} hacks, {len(chapters)} chapters)")


if __name__ == "__main__":
    build()
