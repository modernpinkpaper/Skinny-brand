// Renders every post in posts.mjs into ready-to-post files:
//   carousels -> PNG slides (1080x1920)   videos -> MP4 (1080x1920, 30fps, silent track)
// Usage: node social/render.mjs [postIdFilter] [--only=carousel|video] [--fps=30]
import { createRequire } from "module";
import { spawn, execFileSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { POSTS } from "./posts.mjs";

const require = createRequire("/opt/node22/lib/node_modules/");
const { chromium } = require("playwright");
const __dir = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dir, "..");
const OUT = path.join(ROOT, "tiktok-posts");
const FONTS = path.join(ROOT, "brand", "fonts");
const args = process.argv.slice(2);
const filter = args.find(a => !a.startsWith("--"));
const only = (args.find(a => a.startsWith("--only=")) || "").split("=")[1];
const FPS = +((args.find(a => a.startsWith("--fps=")) || "").split("=")[1] || 30);
const FFMPEG = execFileSync("python3", ["-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).toString().trim();
const W = 1080, H = 1920;

const font = (f) => `data:font/woff2;base64,${fs.readFileSync(path.join(FONTS, f)).toString("base64")}`;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const LAWS = ["The Hunger Laws", "The Kitchen Laws", "The Craving Laws", "The Movement Laws", "The Sleep & Stress Laws",
  "The Eating-Out & Social Laws", "The Grocery & Prep Laws", "The Drink Laws", "The Mindset Laws", "The De-Bloat Laws",
  "The Shape Laws", "The Stay-Skinny-Forever Laws"];

// ───────────────────────── shared CSS ─────────────────────────
const CSS = `
@font-face{font-family:DMSerif;src:url(${font("DMSerifDisplay-normal.woff2")})}
@font-face{font-family:DMSerif;font-style:italic;src:url(${font("DMSerifDisplay-italic.woff2")})}
@font-face{font-family:Inter;font-weight:400 800;src:url(${font("Inter-normal.woff2")})}
:root{--cream:#FBF5EF;--blush:#F6DCD8;--blush2:#FCEDEA;--hot:#C8325F;--ink:#2B1E23;--plum:#4A2233;--muted:#7B6A70}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${W}px;height:${H}px;overflow:hidden;background:var(--cream);font-family:Inter,sans-serif;color:var(--ink)}
.stage{position:absolute;inset:0;overflow:hidden}
.handle{position:absolute;left:0;right:0;bottom:430px;text-align:center;font:700 26px Inter;letter-spacing:.2em;color:rgba(43,30,35,.45);text-transform:uppercase}
.dark .handle{color:rgba(255,255,255,.55)}
.swipe{position:absolute;right:70px;bottom:470px;font:600 30px Inter;color:rgba(43,30,35,.5)}
/* backgrounds */
.bg-blush{background:radial-gradient(120% 70% at 50% 0%,#fff 0%,var(--blush2) 45%,var(--blush) 100%)}
.bg-ink{background:radial-gradient(120% 80% at 50% 10%,#4A2233 0%,#2B1E23 70%)}
.bg-window{background:linear-gradient(170deg,#F7EDE4 0%,#EFDFD2 60%,#E6D0C2 100%)}
.bg-green{background:#00FF00}
.win{position:absolute;inset:-300px;filter:blur(26px);opacity:.28;transform-origin:50% 50%}
.win i{position:absolute;background:#6B4A3A;border-radius:6px}
.glow{position:absolute;inset:0;background:radial-gradient(60% 45% at 70% 25%,rgba(255,236,200,.85),transparent 70%)}
.grain{position:absolute;inset:0;opacity:.09;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}
.dust{position:absolute;width:8px;height:8px;border-radius:50%;background:rgba(255,245,225,.9);filter:blur(1.5px)}
/* hook / big */
.center{position:absolute;left:90px;right:90px;top:260px;bottom:520px;display:flex;flex-direction:column;justify-content:center}
.hook h1{font:400 104px/1.04 DMSerif;letter-spacing:-.01em}
.hook .sub{margin-top:40px;font:500 40px/1.35 Inter;color:var(--plum)}
.dark{color:#fff}.dark .sub{color:#FFC2CF}
.kicker{font:800 28px Inter;letter-spacing:.22em;text-transform:uppercase;color:var(--hot);margin-bottom:30px}
.dark .kicker{color:#FFC2CF}
.big h2{font:400 92px/1.06 DMSerif}
.big p{margin-top:40px;font:400 38px/1.45 Inter;color:var(--plum)}
/* tip reveal */
.tipcard{background:#fff;border-radius:48px;padding:70px 64px;box-shadow:0 40px 100px rgba(74,34,51,.18)}
.tipcard .pill{display:inline-block;background:var(--hot);color:#fff;font:800 26px Inter;letter-spacing:.2em;padding:12px 26px;border-radius:99px;margin-bottom:34px}
.tipcard h2{font:400 84px/1.05 DMSerif;margin-bottom:30px}
.tipcard p{font:400 38px/1.45 Inter}
.tipcard .small{margin-top:30px;padding-top:30px;border-top:2px dashed #EBDCD6;font:500 32px/1.45 Inter;color:var(--muted)}
.tipcard .vault{margin-top:30px;font:700 28px Inter;color:var(--hot)}
/* notes app */
.notes{position:absolute;inset:0;background:#fff}
.notes .nbar{position:absolute;top:150px;left:50px;right:50px;display:flex;justify-content:space-between;font:500 44px Inter;color:#E0A100}
.notes .date{position:absolute;top:250px;left:0;right:0;text-align:center;font:500 28px Inter;color:#9A9A9F}
.notes .body{position:absolute;top:320px;left:70px;right:90px}
.notes h3{font:800 64px/1.15 Inter;margin-bottom:28px;letter-spacing:-.01em}
.notes .ln{font:400 46px/1.42 Inter;min-height:30px;white-space:pre-wrap}
.caret{display:inline-block;width:4px;height:52px;background:#E0A100;vertical-align:-10px;margin-left:2px}
/* chat */
.chat{position:absolute;inset:0;background:#fff}
.chat .chead{position:absolute;top:0;left:0;right:0;height:360px;background:rgba(246,246,248,.96);border-bottom:1px solid #E5E5EA;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:26px;z-index:2}
.chat .av{width:110px;height:110px;border-radius:50%;background:linear-gradient(135deg,#F6B6C5,#C8325F);display:grid;place-items:center;font-size:56px;color:#fff;margin-bottom:12px}
.chat .nm{font:500 32px Inter;color:#111}
.chat .msgs{position:absolute;left:40px;right:40px;top:400px;display:flex;flex-direction:column;gap:14px}
.b{max-width:76%;padding:22px 32px;border-radius:44px;font:400 42px/1.3 Inter;transform-origin:bottom left}
.b.them{align-self:flex-start;background:#E9E9EB;color:#111;border-bottom-left-radius:14px}
.b.me{align-self:flex-end;background:#0A84FF;color:#fff;border-bottom-right-radius:14px;transform-origin:bottom right}
.dots{align-self:flex-start;background:#E9E9EB;border-radius:44px;padding:28px 34px;display:flex;gap:12px}
.dots i{width:18px;height:18px;border-radius:50%;background:#9A9AA0}
/* search */
.search{position:absolute;inset:0;background:#fff}
.search .logo{position:absolute;top:300px;left:0;right:0;text-align:center;font:700 96px Inter;letter-spacing:-.03em;color:#2B1E23}
.search .logo span{color:var(--hot)}
.search .bar{position:absolute;top:470px;left:60px;right:60px;height:124px;border-radius:62px;border:2px solid #DFE1E5;box-shadow:0 4px 18px rgba(32,33,36,.12);display:flex;align-items:center;padding:0 40px;gap:26px;font:400 40px Inter;color:#202124}
.search .bar svg{flex:none}
.search .ans{position:absolute;top:650px;left:60px;right:60px;border:2px solid #E8EAED;border-radius:36px;padding:48px 50px;background:#fff}
.search .ans .lab{font:700 26px Inter;color:#5F6368;letter-spacing:.06em;text-transform:uppercase;margin-bottom:22px}
.search .ans p{font:400 44px/1.45 Inter;color:#202124}
.search .ans mark{background:#FDE7EC;color:inherit;padding:0 4px;border-radius:6px}
.search .ans .src{margin-top:28px;font:400 28px Inter;color:#1A0DAB}
/* sticky */
.sticky-wrap{position:absolute;left:70px;right:70px;top:230px;bottom:520px;display:grid;grid-template-columns:1fr 1fr;gap:44px;align-content:center}
.sticky{aspect-ratio:1;padding:44px 38px;font:600 44px/1.3 Inter;color:#3A2A20;box-shadow:0 22px 40px rgba(0,0,0,.14);display:flex;align-items:center}
.sticky:nth-child(1){background:#FFE98F;transform:rotate(-3deg)}
.sticky:nth-child(2){background:#FFC7D3;transform:rotate(2.5deg)}
.sticky:nth-child(3){background:#CDEFD8;transform:rotate(2deg)}
.sticky:nth-child(4){background:#D9E4FF;transform:rotate(-2deg)}
/* checklist */
.checkcard{background:#fff;border-radius:44px;padding:64px 60px;box-shadow:0 40px 100px rgba(74,34,51,.14)}
.checkcard h2{font:400 70px/1.1 DMSerif;margin-bottom:36px}
.ci{display:flex;align-items:flex-start;gap:28px;padding:22px 0;border-bottom:2px solid #F3E9E5;font:500 40px/1.35 Inter}
.ci:last-child{border:0}
.box{flex:none;width:56px;height:56px;border-radius:14px;border:4px solid #D9C5C0;display:grid;place-items:center;color:#fff;font:800 36px Inter;margin-top:-2px}
.ci.on .box{background:var(--hot);border-color:var(--hot)}
.ci.on span{color:var(--ink)}
/* tweet */
.tweet{background:#fff;border-radius:40px;padding:56px 56px 48px;box-shadow:0 30px 80px rgba(0,0,0,.18);color:#0F1419}
.tweet .who{display:flex;gap:24px;align-items:center;margin-bottom:34px}
.tweet .pic{width:100px;height:100px;border-radius:50%;background:linear-gradient(135deg,#F6B6C5,#C8325F);display:grid;place-items:center;font:400 44px DMSerif;color:#fff}
.tweet .n{font:800 36px Inter}.tweet .h{font:400 32px Inter;color:#536471}
.tweet p{font:400 52px/1.35 Inter}
.tweet .meta{margin-top:36px;font:400 28px Inter;color:#536471}
/* type card */
.typecard{text-align:center}
.typecard .em{font-size:220px;line-height:1;margin-bottom:40px}
.typecard h2{font:400 110px/1.05 DMSerif;margin-bottom:34px}
.typecard p{font:400 44px/1.4 Inter;color:var(--plum)}
/* toc */
.toc h2{font:400 80px/1.05 DMSerif;margin-bottom:34px}
.toc .row{display:flex;gap:26px;align-items:baseline;padding:13px 0;border-bottom:2px solid rgba(255,255,255,.12);font:500 36px Inter}
.toc .row b{font:400 44px DMSerif;color:#FFC2CF;min-width:62px}
/* CTA */
.cta{text-align:center;align-items:center}
.book{width:560px;height:760px;margin:0 auto 60px;border-radius:12px 34px 34px 12px;position:relative;
  background:radial-gradient(120% 80% at 50% 0%,#fff 0%,#FCEDEA 45%,#F6DCD8 100%);box-shadow:-18px 0 0 #E7A1A6 inset,0 50px 110px rgba(74,34,51,.35);
  display:flex;flex-direction:column;justify-content:center;padding:60px 70px 60px 80px;text-align:left}
.book .k{font:800 22px Inter;letter-spacing:.24em;color:var(--hot);text-transform:uppercase;margin-bottom:26px}
.book h3{font:400 92px/.98 DMSerif;color:var(--ink)}
.book h3 em{color:var(--hot)}
.book p{margin-top:30px;font:500 28px/1.4 Inter;color:var(--plum)}
.book .lock{position:absolute;right:48px;bottom:44px;font-size:60px}
.cta .l1{font:400 76px/1.08 DMSerif}
.cta .l2{margin-top:26px;font:500 36px/1.4 Inter;color:var(--plum)}
.cta .btn{display:inline-block;margin-top:44px;background:var(--hot);color:#fff;font:800 40px Inter;padding:30px 60px;border-radius:99px;letter-spacing:.02em}
/* photo layouts */
.pbg{position:absolute;inset:-2px;background-size:cover;background-position:center;transform-origin:50% 45%}
.shade-top{position:absolute;left:0;right:0;top:0;height:900px;background:linear-gradient(rgba(0,0,0,.28),rgba(0,0,0,0))}
.shade-bot{position:absolute;left:0;right:0;bottom:0;height:1250px;background:linear-gradient(rgba(20,10,14,0) 0%,rgba(20,10,14,.62) 38%,rgba(20,10,14,.86) 100%)}
.tt{position:absolute;left:70px;right:150px;top:250px;text-align:center}
.tt .l{display:inline;background:#fff;color:#111;font:700 60px/1.48 Inter;padding:6px 20px;border-radius:14px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.tt .s{display:inline-block;margin-top:26px;background:rgba(0,0,0,.72);color:#fff;font:600 38px/1.4 Inter;padding:8px 20px;border-radius:12px}
.pcard{position:absolute;left:70px;right:120px;bottom:470px;color:#fff}
.pcard .pill{display:inline-block;background:var(--hot);color:#fff;font:800 25px Inter;letter-spacing:.14em;text-transform:uppercase;padding:11px 22px;border-radius:99px;margin-bottom:26px}
.pcard h2{font:400 84px/1.04 DMSerif;margin-bottom:22px;text-shadow:0 2px 20px rgba(0,0,0,.3)}
.pcard p{font:500 40px/1.42 Inter}
.pcard .small{margin-top:22px;font:600 31px/1.4 Inter;color:#FFD1DC}
.ph-handle{position:absolute;left:0;right:0;bottom:420px;text-align:center;font:700 24px Inter;letter-spacing:.2em;color:rgba(255,255,255,.7)}
.ctaw{position:absolute;inset:0;background:rgba(20,10,14,.45)}
.ctab{position:absolute;left:0;right:0;top:230px;text-align:center;color:#fff}
.ctab .book{width:470px;height:640px;margin:0 auto 46px;padding:50px 56px 50px 66px}
.ctab .book h3{font-size:78px}.ctab .book p{font-size:25px}
.ctab .l1{font:400 78px/1.06 DMSerif;text-shadow:0 2px 24px rgba(0,0,0,.35)}
.ctab .l2{margin-top:18px;font:600 34px/1.4 Inter;color:#FFE3EA}
.ctab .btn{display:inline-block;margin-top:34px;background:var(--hot);color:#fff;font:800 40px Inter;padding:28px 58px;border-radius:99px}
/* video overlay text (TikTok style boxes) */
.ovl{position:absolute;left:90px;right:150px;top:560px;display:flex;flex-direction:column;align-items:center;text-align:center}
.ovl span{display:inline;background:#fff;color:#111;font:700 58px/1.5 Inter;padding:6px 20px;border-radius:14px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.vhook{position:absolute;left:80px;right:150px;top:190px;text-align:center;z-index:5}
.vhook span{background:#fff;color:#111;font:700 44px/1.55 Inter;padding:6px 18px;border-radius:12px;-webkit-box-decoration-break:clone;box-decoration-break:clone;box-shadow:0 8px 30px rgba(0,0,0,.12)}
.after{position:absolute;left:90px;right:150px;top:1320px;text-align:center}
.after div{display:inline-block;background:var(--ink);color:#fff;font:700 50px/1.4 Inter;padding:10px 26px;border-radius:16px;margin:6px 0}
`;

// ───────────────────────── background pieces ─────────────────────────
let ASSET_CSS = "";
async function prepareAssets(page) {
  // pre-render the expensive blurred window shadow + film grain once, reuse as images
  await page.setViewportSize({ width: 2000, height: 2800 });
  const bars = [];
  for (let i = 0; i < 5; i++) bars.push(`<i style="position:absolute;left:${340 + i * 360}px;top:0;width:48px;height:2800px;background:#6B4A3A;border-radius:6px"></i>`);
  for (let j = 0; j < 5; j++) bars.push(`<i style="position:absolute;left:0;top:${380 + j * 470}px;width:2000px;height:42px;background:#6B4A3A;border-radius:6px"></i>`);
  await page.setContent(`<html><body style="margin:0;background:transparent"><div style="position:absolute;inset:0;filter:blur(26px)">${bars.join("")}</div></body></html>`);
  const win = (await page.screenshot({ omitBackground: true })).toString("base64");
  await page.setViewportSize({ width: 440, height: 440 });
  await page.setContent(`<html><body style="margin:0;background:transparent"><svg xmlns='http://www.w3.org/2000/svg' width='440' height='440'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg></body></html>`);
  const grain = (await page.screenshot({ omitBackground: true })).toString("base64");
  await page.setViewportSize({ width: W, height: H });
  ASSET_CSS = `.win{position:absolute;left:-460px;top:-440px;width:2000px;height:2800px;opacity:.28;background:url(data:image/png;base64,${win}) no-repeat;transform-origin:50% 50%}
.grain{background-image:url(data:image/png;base64,${grain})!important;background-size:440px 440px}
.dust{filter:none!important;background:radial-gradient(circle,rgba(255,247,230,.95) 0,rgba(255,247,230,0) 70%)!important;width:14px!important;height:14px!important}`;
}
function windowBg(t = 0) {
  // soft window-light shadow on a warm wall, gently drifting
  const dx = Math.sin(t * 0.35) * 40, dy = Math.cos(t * 0.25) * 30, rot = -18 + Math.sin(t * 0.2) * 1.5;
  let dust = "";
  for (let k = 0; k < 22; k++) {
    const sx = (k * 197) % W, sy = (k * 331) % H, sp = 12 + (k % 5) * 6;
    const x = (sx + Math.sin(t * 0.5 + k) * 60 + t * sp) % W, y = (sy - t * sp * 1.4 + H * 5) % H;
    const o = 0.25 + 0.5 * (0.5 + 0.5 * Math.sin(t * 1.3 + k * 2));
    dust += `<div class="dust" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px;opacity:${o.toFixed(2)};transform:scale(${0.6 + (k % 4) * 0.3})"></div>`;
  }
  return `<div class="stage bg-window"><div class="glow"></div><div class="win" style="transform:translate(${dx.toFixed(1)}px,${dy.toFixed(1)}px) rotate(${rot.toFixed(2)}deg)"></div>${dust}<div class="grain"></div></div>`;
}
const bgFor = (bg, t = 0) => bg === "window" ? windowBg(t) : bg === "green" ? `<div class="stage bg-green"></div>` : `<div class="stage bg-${bg || "blush"}"><div class="grain"></div></div>`;

// ───────────────────────── media ─────────────────────────
const MY = path.join(__dir, "my-photos", "named");
function media(spec) {
  const key = String(spec).split("@")[0];
  for (const ext of [".png", ".jpg", ".jpeg", ".webp"]) {
    const f = path.join(MY, key + ext);
    if (fs.existsSync(f)) return "file://" + f;
  }
  throw new Error("missing photo: " + key + " (add social/my-photos/named/" + key + ".png)");
}
const pbg = (spec, style = "") => `<div class="pbg" style="background-image:url('${media(spec)}');${style}"></div>`;
const ttBox = (text, sub) => `<div class="tt"><span class="l">${esc(text)}</span>${sub ? `<br><span class="s">${esc(sub)}</span>` : ""}</div>`;
function photoCard(s) {
  return `${pbg(s.img)}<div class="shade-bot"></div><div class="pcard">${s.kicker ? `<div class="pill">${esc(s.kicker)}</div>` : ""}<h2>${esc(s.title)}</h2>${s.text ? `<p>${esc(s.text)}</p>` : ""}${s.small ? `<p class="small">${esc(s.small)}</p>` : ""}</div>`;
}
function ctaPhoto(img) {
  return `${pbg(img)}<div class="ctaw"></div><div class="ctab"><div class="book"><div class="k">@theskinnylaws</div><h3>The Skinny Laws<br><em>Vault</em></h3><p>120 unusual hacks to get lean & stay lean — without starving</p><div class="lock">🔐</div></div><div class="l1">Want the other 119?</div><div class="l2">12 Laws · 120 hacks · quiz · 30-day challenge</div><div class="btn">🔗 Link in bio</div></div>`;
}

// ───────────────────────── slide templates ─────────────────────────
const bubbles = (msgs) => msgs.map(m => `<div class="b ${m.me ? "me" : "them"}">${esc(m.text)}</div>`).join("");
function slideHTML(s, i, n) {
  const swipe = i < n - 1 ? `<div class="swipe">swipe →</div>` : "";
  const handle = `<div class="handle">@theskinnylaws</div>`;
  switch (s.t) {
    case "meme":
      return `${pbg(s.img)}<div class="shade-top"></div>${ttBox(s.text, s.sub)}`;
    case "photo":
      return photoCard(s);
    case "search":
      return searchHTML(s.query, s.answer, s.source, 1);
    case "hook": {
      const dark = s.bg === "ink";
      return `${bgFor(s.bg)}<div class="stage ${dark ? "dark" : ""}"><div class="center hook"><h1>${esc(s.text)}</h1>${s.sub ? `<div class="sub">${esc(s.sub)}</div>` : ""}</div>${handle}</div>`;
    }
    case "big":
      return `${bgFor("blush")}<div class="stage"><div class="center big"><div class="kicker">${esc(s.kicker)}</div><h2>${esc(s.text)}</h2>${s.small ? `<p>${esc(s.small)}</p>` : ""}</div>${handle}${swipe}</div>`;
    case "tip":
      return `${bgFor("window")}<div class="stage"><div class="center"><div class="tipcard"><div class="pill">${esc(s.num)}</div><h2>${esc(s.title)}</h2><p>${esc(s.text)}</p>${s.small ? `<p class="small">${esc(s.small)}</p>` : ""}<div class="vault">🔐 from The Skinny Laws Vault</div></div></div>${handle}</div>`;
    case "notes":
      return `<div class="notes"><div class="nbar"><span>‹ Notes</span><span>⋯</span></div><div class="date">${esc(s.date)}</div><div class="body"><h3>${esc(s.title)}</h3>${s.lines.map(l => `<div class="ln">${esc(l) || "&nbsp;"}</div>`).join("")}</div></div>`;
    case "imsg":
      return `<div class="chat"><div class="chead"><div class="av">✨</div><div class="nm">${esc(s.name || "Bestie 💕")} ›</div></div><div class="msgs">${bubbles(s.msgs)}</div></div>`;
    case "google":
      return searchHTML(s.query, s.answer, s.source, 1);
    case "sticky":
      return `${bgFor("window")}<div class="stage"><div class="sticky-wrap">${s.notes.map(x => `<div class="sticky">${esc(x)}</div>`).join("")}</div>${handle}</div>`;
    case "check":
      return `${bgFor("blush")}<div class="stage"><div class="center"><div class="checkcard"><h2>${esc(s.title)}</h2>${s.items.map(([x, on]) => `<div class="ci ${on ? "on" : ""}"><div class="box">${on ? "✓" : ""}</div><span>${esc(x)}</span></div>`).join("")}</div></div>${handle}${swipe}</div>`;
    case "tweet":
      return `${bgFor("ink")}<div class="stage dark"><div class="center"><div class="tweet"><div class="who"><div class="pic">S</div><div><div class="n">The Skinny Laws</div><div class="h">@theskinnylaws</div></div></div><p>${esc(s.text)}</p><div class="meta">9:41 PM · the vault 🔐</div></div></div>${swipe}</div>`;
    case "type":
      if (s.img) return photoCard({ img: s.img, kicker: "Which one are you?", title: s.name, text: s.text });
      return `${bgFor("blush")}<div class="stage"><div class="center typecard"><div class="em">${s.emoji}</div><h2>${esc(s.name)}</h2><p>${esc(s.text)}</p></div>${handle}${swipe}</div>`;
    case "toc":
      return `${bgFor("ink")}<div class="stage dark"><div class="center toc"><div class="kicker">The 12 Laws</div>${LAWS.map((l, k) => `<div class="row"><b>${String(k + 1).padStart(2, "0")}</b>${esc(l)}</div>`).join("")}</div></div>`;
    case "cta":
      return s.img ? ctaPhoto(s.img) : ctaHTML();
  }
  throw new Error("unknown slide type " + s.t);
}
function ctaHTML(bg = "blush") {
  return `${bgFor(bg)}<div class="stage"><div class="center cta"><div class="book"><div class="k">@theskinnylaws</div><h3>The Skinny Laws<br><em>Vault</em></h3><p>120 unusual hacks to get lean & stay lean — without starving</p><div class="lock">🔐</div></div><div class="l1">Want the other 119?</div><div class="l2">12 Laws · 120 hacks · quiz · 30-day challenge</div><div class="btn">🔗 Link in bio</div></div></div>`;
}
function searchHTML(q, answer, source, ansOpacity, caretOn = false) {
  const hl = esc(answer).replace(/^(.*?[.:])/, "<mark>$1</mark>");
  return `<div class="search"><div class="logo">search<span>.</span></div><div class="bar"><svg width="44" height="44" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" stroke="#9AA0A6" stroke-width="2.4" fill="none"/><path d="M15 15l6 6" stroke="#9AA0A6" stroke-width="2.4"/></svg><span>${esc(q)}${caretOn ? `<i class="caret" style="background:#1A73E8"></i>` : ""}</span></div>
  <div class="ans" style="opacity:${ansOpacity};transform:translateY(${(1 - ansOpacity) * 30}px)"><div class="lab">Top answer</div><p>${hl}</p>${source ? `<div class="src">${esc(source)}</div>` : ""}</div></div>`;
}

// ───────────────────────── video timelines ─────────────────────────
// Each returns {dur, frame(t) -> html}. Pure functions of t so frames are deterministic.
const ease = (x) => x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(1 - x, 3);
const pop = (x) => { if (x <= 0) return 0; if (x >= 1) return 1; const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const CTA_DUR = 3.2;
const hookBox = (text, t, until, top) => {
  const o = Math.min(ease(t / 0.4), until ? 1 - ease((t - until) / 0.4) : 1);
  return text && o > 0 ? `<div class="vhook" style="opacity:${o}${top ? `;top:${top}px` : ""}"><span>${esc(text)}</span></div>` : "";
};
const withCTA = (dur, frame) => ({
  dur: dur + CTA_DUR,
  frame: (t) => {
    if (t < dur) return frame(t);
    const o = ease((t - dur) / 0.35);
    return `${frame(dur)}<div class="stage" style="opacity:${o}">${ctaHTML()}</div>`;
  },
});

function notesVideo(v, hook) {
  const CPS = 26; // chars per second typing
  const lines = v.lines; const starts = []; let tt = 1.4;
  for (const l of lines) { starts.push(tt); tt += Math.max(l.length / CPS, 0.25) + 0.35; }
  const dur = tt + 2.2;
  return withCTA(dur, (t) => {
    let body = "";
    lines.forEach((l, k) => {
      if (t < starts[k]) return;
      const c = Math.min(l.length, Math.floor((t - starts[k]) * CPS));
      const typing = c < l.length || (k === lines.length - 1) || t < (starts[k + 1] ?? 1e9);
      const caret = typing && (Math.floor(t * 2) % 2 === 0 || c < l.length) && (starts[k + 1] === undefined || t < starts[k + 1]);
      body += `<div class="ln">${esc(l.slice(0, c)) || (caret ? "" : "&nbsp;")}${caret ? '<i class="caret"></i>' : ""}</div>`;
    });
    return `<div class="notes"><div class="nbar"><span>‹ Notes</span><span>⋯</span></div><div class="date">${esc(v.date)}</div><div class="body"><h3>${esc(v.title)}</h3>${body}</div></div>${hookBox(hook, t, 3.2)}`;
  });
}

function imsgVideo(v, hook) {
  const ev = []; let tt = 1.0;
  for (const m of v.msgs) {
    if (!m.me) { ev.push({ typing: [tt, tt + 0.9] }); tt += 0.9; }
    const read = Math.min(2.6, 0.9 + m.text.length / 30);
    ev.push({ m, at: tt }); tt += read;
  }
  const dur = tt + 1.2;
  return withCTA(dur, (t) => {
    let html = ""; let count = 0;
    for (const e of ev) {
      if (e.typing && t >= e.typing[0] && t < e.typing[1]) {
        html += `<div class="dots">${[0, 1, 2].map(k => `<i style="opacity:${0.35 + 0.65 * Math.max(0, Math.sin(t * 9 - k * 0.9))}"></i>`).join("")}</div>`;
      }
      if (e.m && t >= e.at) {
        const s = pop((t - e.at) / 0.35);
        html += `<div class="b ${e.m.me ? "me" : "them"}" style="transform:scale(${s})">${esc(e.m.text)}</div>`; count++;
      }
    }
    // keep last messages visible: estimate height and scroll up
    return `<div class="chat"><div class="chead"><div class="av">✨</div><div class="nm">${esc(v.name || "Bestie 💕")} ›</div></div><div class="msgs" id="msgs">${html}</div></div>${hookBox(hook, t, 3, 1150)}`;
  });
}

function searchVideo(v, hook) {
  const CPS = 16; const tq0 = 1.0, tq1 = tq0 + v.query.length / CPS; const tA = tq1 + 0.8;
  const afterAt = (v.after || []).map((_, k) => tA + 4.2 + k * 1.6);
  const dur = (afterAt.length ? afterAt[afterAt.length - 1] + 2.4 : tA + 5);
  return withCTA(dur, (t) => {
    const q = v.query.slice(0, Math.max(0, Math.floor((t - tq0) * CPS)));
    const loading = t > tq1 && t < tA;
    let html = searchHTML(q, v.answer, "theskinnylaws.vault", ease((t - tA) / 0.5), t < tA && Math.floor(t * 2) % 2 === 0);
    if (loading) html += `<div style="position:absolute;top:600px;left:60px;right:60px;height:6px;background:#E8EAED;overflow:hidden;border-radius:3px"><div style="width:30%;height:100%;background:#C8325F;margin-left:${((t - tq1) / 0.8) * 100}%"></div></div>`;
    const af = (v.after || []).map((a, k) => t >= afterAt[k] ? `<div style="transform:scale(${pop((t - afterAt[k]) / 0.35)})">${esc(a)}</div><br>` : "").join("");
    return html + `<div class="after">${af}</div>` + hookBox(hook, t, 2.6);
  });
}

function overlayVideo(v, green) {
  const starts = []; let tt = 0.3;
  for (const s of v.scenes) { starts.push(tt); tt += s.d; }
  const dur = tt + 0.4;
  return withCTA(dur, (t) => {
    let k = starts.findIndex((s, i) => t >= s && (i === starts.length - 1 || t < starts[i + 1]));
    if (k < 0) k = 0;
    const local = t - starts[k];
    const sc = v.scenes[k];
    const inO = ease(local / 0.3), outO = k === v.scenes.length - 1 ? 1 : 1 - ease((local - (sc.d - 0.25)) / 0.25);
    const o = Math.min(inO, outO), s = 0.92 + 0.08 * pop(local / 0.35);
    const bg = green ? bgFor("green") : windowBg(t);
    return `${bg}<div class="ovl" style="opacity:${o};transform:scale(${s})"><div><span>${esc(sc.text)}</span></div></div>` +
      (green ? "" : `<div class="handle">@theskinnylaws</div>`);
  });
}

function brollVideo(v, ctaImg) {
  const starts = []; let tt = 0;
  for (const sc of v.scenes) { starts.push(tt); tt += sc.d; }
  const dur = tt;
  const tl = (t) => {
    let k = starts.findIndex((st, i) => t >= st && (i === starts.length - 1 || t < starts[i + 1]));
    if (k < 0) k = starts.length - 1;
    const sc = v.scenes[k], p = Math.min(1, (t - starts[k]) / sc.d);
    // slow push-in with a gentle drift + tiny handheld sway so stills feel filmed
    const dir = k % 2 ? -1 : 1, sc0 = 1.04 + 0.1 * p;
    const sx = Math.sin(t * 1.7) * 3 + dir * 26 * p, sy = Math.cos(t * 1.3) * 3 - 12 * p;
    const s2 = pop(Math.min(1, (t - starts[k]) / 0.32));
    return `${pbg(sc.clip, `transform:translate(${sx.toFixed(1)}px,${sy.toFixed(1)}px) scale(${sc0.toFixed(4)})`)}<div class="shade-top"></div>` +
      `<div class="tt" style="transform:scale(${(0.9 + 0.1 * s2).toFixed(3)});opacity:${Math.min(1, s2 * 1.5).toFixed(2)}"><span class="l">${esc(sc.text)}</span></div>`;
  };
  return { dur: dur + CTA_DUR, frame: (t) => t < dur ? tl(t) : `${tl(dur - 0.001)}<div class="stage" style="opacity:${ease((t - dur) / 0.35)}">${ctaPhoto(ctaImg)}</div>` };
}

// ───────────────────────── rendering ─────────────────────────
const TMP = path.join(__dir, ".tmp-page.html");
async function show(page, inner) {
  fs.writeFileSync(TMP, page0(inner));
  await page.goto("file://" + TMP, { waitUntil: "load" });
  await page.evaluate(() => Promise.all([document.fonts.ready, ...[...document.querySelectorAll("img")].map(i => i.decode().catch(() => {}))]));
}
const page0 = (inner) => `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}${ASSET_CSS}</style></head><body>${inner}</body></html>`;

async function renderCarousel(page, post, dir) {
  const n = post.slides.length;
  for (let i = 0; i < n; i++) {
    await show(page, slideHTML(post.slides[i], i, n) + preload(post));
    await page.screenshot({ path: path.join(dir, `slide-${String(i + 1).padStart(2, "0")}.png`) });
  }
  return `${n} slides`;
}

async function renderVideo(page, tl, file) {
  await show(page, `<div id="root"></div>` + (tl.preload || ""));
  const frames = Math.ceil(tl.dur * FPS);
  const ff = spawn(FFMPEG, ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", String(FPS),
    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", file], { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
  for (let f = 0; f < frames; f++) {
    const html = tl.frame(f / FPS);
    await page.evaluate(([h]) => {
      const r = document.getElementById("root"); r.innerHTML = h;
      const m = document.getElementById("msgs");
      if (m) { const over = m.getBoundingClientRect().bottom - 1440; if (over > 0) m.style.top = (400 - over) + "px"; }
    }, [html]);
    const buf = await page.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await done;
  return `${tl.dur.toFixed(1)}s`;
}

function preload(post) {
  const specs = [...(post.slides || []).map(x => x.img), ...((post.video && post.video.scenes) || []).map(x => x.clip), post.video && (post.video.cta || "mirror_selfie")].filter(Boolean);
  return `<div style="position:absolute;left:-9999px">${[...new Set(specs.map(media))].map(u => `<img src="${u}">`).join("")}</div>`;
}
function timelineFor(post, green = false) {
  const v = post.video;
  if (v.t === "notes") return notesVideo(v, post.onScreenHook);
  if (v.t === "imsg") return imsgVideo(v, post.onScreenHook);
  if (v.t === "google" || v.t === "search") return searchVideo(v, post.onScreenHook);
  if (v.t === "overlay") return overlayVideo(v, green);
  if (v.t === "broll") return brollVideo(v, v.cta || "mirror_selfie");
  throw new Error("unknown video type " + v.t);
}

function writeCaption(post, dir) {
  const typeLine = post.format === "carousel"
    ? `FORMAT: Photo carousel (${post.slides.length} slides). Upload the PNGs in order in TikTok "Photo" mode.`
    : post.video.t === "broll"
      ? `FORMAT: Video — your photos with caption text (b-roll style). Post video.mp4 as is.`
      : post.video.t === "overlay"
      ? `FORMAT: Video with b-roll + text overlay.\n  • READY TO POST: video.mp4 (text over a soft window-light background)\n  • WANT REAL B-ROLL? Film the shots below, then in CapCut add overlay-greenscreen.mp4 on top → Remove BG → Chroma key → pick the green.`
      : `FORMAT: Video (${post.video.t === "notes" ? "Notes-app typing" : post.video.t === "imsg" ? "text-message chat" : "search-bar typing"}). Post video.mp4 as is.`;
  const broll = post.video?.broll ? `\nB-ROLL SHOT LIST (3–4 sec each, phone vertical, no face needed):\n${post.video.broll.map((b, i) => `  ${i + 1}. ${b}`).join("\n")}\n` : "";
  const hook = post.onScreenHook ? `\nON-SCREEN HOOK (already in the video — also use it as your TikTok cover text):\n  ${post.onScreenHook}\n` : "";
  const txt = `DAY ${post.day} · POST AT ${post.time}
${post.title}
${"=".repeat(50)}
${typeLine}
${hook}${broll}
CAPTION (copy + paste):
${post.caption}

${post.hashtags}

PINNED COMMENT (post it yourself, then pin it):
${post.pin}

SOUND: pick a trending sound in TikTok's sound library (search "aesthetic", "soft" or "viral"), set volume low so the text is the star.
TIP: add the "link in bio" sticker text if your account allows. Reply to every comment in the first hour.
`;
  fs.writeFileSync(path.join(dir, "caption.txt"), txt);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await prepareAssets(page);
fs.mkdirSync(OUT, { recursive: true });
for (const post of POSTS) {
  if (filter && !post.id.includes(filter)) continue;
  if (only && post.format !== only) continue;
  const dir = path.join(OUT, `day-${post.day}`, post.id);
  fs.mkdirSync(dir, { recursive: true });
  const t0 = Date.now();
  let info;
  if (post.format === "carousel") info = await renderCarousel(page, post, dir);
  else {
    const tlx = timelineFor(post); tlx.preload = preload(post);
    info = await renderVideo(page, tlx, path.join(dir, "video.mp4"));
    if (post.video.t === "overlay" && false) await renderVideo(page, timelineFor(post, true), path.join(dir, "overlay-greenscreen.mp4"));
  }
  writeCaption(post, dir);
  console.log(`✓ ${post.id} — ${info} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
await browser.close();
