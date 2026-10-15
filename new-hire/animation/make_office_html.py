"""Builds office.html: Sally (the character code from skits/animation/anim.html) + the nicer office and step scenes (scenes.js)."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "..", "skits", "animation", "anim.html"), encoding="utf-8").read()
scenes = open(os.path.join(HERE, "scenes.js"), encoding="utf-8").read()

head, rest = src.split("<script>", 1)
js = rest.split("</script>")[0]
# the parts of the script we keep: utils, the character, the arms
utils = js[:js.index("// ---------- scene looks ----------")]
char = js[js.index("// ---------- character ----------"):js.index("function frame(f){")]
head = head.replace("#8fc1ff", "#2a3a78")                       # sweater: brand navy
char = char.replace("#8fc1ff", "#2a3a78")
head = head.replace('<rect width="1080" height="1920" fill="url(#dots)"/>', "")
head = head.replace('<g id="props"></g>', '''<g id="panelWrap"><rect x="60" y="280" width="960" height="740" rx="48" fill="#000" opacity=".08" transform="translate(0 14)"/>
  <rect x="60" y="280" width="960" height="740" rx="48" fill="#fffdfb" stroke="#d4a84b" stroke-width="10"/><rect x="76" y="296" width="928" height="708" rx="36" fill="none" stroke="#f1e1bd" stroke-width="4"/>
  <g id="panel" transform="translate(80 300)"></g></g>''')
head = head.replace('<rect width="1080" height="1920" fill="url(#vig)" pointer-events="none"/>', "")
ui = re.search(r'<g id="ui">.*?</g>\s*</svg>', head, re.S)
head = head.replace(ui.group(0), '<g id="ui"><g id="chip"></g><g id="caps"></g></g>\n</svg>')
out = head + "<script>\n" + utils + char + scenes + "\n</script></body></html>\n"
open(os.path.join(HERE, "office.html"), "w", encoding="utf-8").write(out)
print("office.html written,", len(out), "bytes")
