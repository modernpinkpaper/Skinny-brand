// "Scroll & click" screen-recording videos of the real interactive Vault, on a phone-size screen.
// A finger dot taps around, with casual caption boxes on top. Output: tiktok-posts/demos/<name>/video.mp4
// Usage: node social/demo.mjs [name]
import { createRequire } from "module";
import { spawn, execFileSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
const require = createRequire("/opt/node22/lib/node_modules/");
const { chromium } = require("playwright");
const __dir = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dir, "..");
const VAULT = "file://" + path.join(ROOT, "product", "dist", "the-skinny-laws-vault.html");
const FFMPEG = execFileSync("python3", ["-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).toString().trim();
const FPS = 30, VW = 390, VH = 693, DSF = 1080 / 390; // → 1080x1920

const OVERLAY_CSS = `
html{scroll-behavior:auto!important}
#rec-cap{position:fixed;left:18px;right:18px;top:92px;z-index:9999;text-align:center;pointer-events:none;transition:none}
#rec-cap span{background:#fff;color:#111;font:700 19px/1.5 Inter,sans-serif;padding:3px 9px;border-radius:7px;-webkit-box-decoration-break:clone;box-decoration-break:clone;box-shadow:0 4px 18px rgba(0,0,0,.18)}
#rec-finger{position:fixed;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(255,255,255,.55);border:2px solid rgba(0,0,0,.25);box-shadow:0 2px 10px rgba(0,0,0,.25);z-index:10000;pointer-events:none;opacity:0}
#rec-status{position:fixed;left:0;right:0;top:0;height:30px;z-index:9998;display:flex;justify-content:space-between;align-items:center;padding:0 22px;font:600 14px Inter,sans-serif;color:#111;background:rgba(251,245,239,.96);pointer-events:none}
.bar{top:30px!important}
.drawer{top:30px!important}
`;

class Rec {
  constructor(page, file) {
    this.page = page;
    this.ff = spawn(FFMPEG, ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
      "-pix_fmt", "yuv420p", "-vf", "scale=1080:1920", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", file], { stdio: ["pipe", "inherit", "inherit"] });
    this.done = new Promise((res, rej) => this.ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
    this.frames = 0; this.fx = VW / 2; this.fy = VH * 0.7;
  }
  async frame() {
    const buf = await this.page.screenshot({ type: "jpeg", quality: 90 });
    if (!this.ff.stdin.write(buf)) await new Promise(r => this.ff.stdin.once("drain", r));
    this.frames++;
  }
  async hold(sec) { for (let i = 0; i < Math.round(sec * FPS); i++) await this.frame(); }
  async cap(text) { await this.page.evaluate(t => { document.getElementById("rec-cap").innerHTML = t ? `<span>${t}</span>` : ""; }, text); }
  async finger(x, y, opacity, scale = 1) {
    await this.page.evaluate(([x, y, o, s]) => { const f = document.getElementById("rec-finger"); f.style.left = x + "px"; f.style.top = y + "px"; f.style.opacity = o; f.style.transform = `scale(${s})`; }, [x, y, opacity, scale]);
  }
  async scrollTo(targetY, sec) {
    const from = await this.page.evaluate(() => scrollY);
    const n = Math.max(1, Math.round(sec * FPS));
    for (let i = 1; i <= n; i++) {
      const p = i / n, e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      await this.page.evaluate(y => scrollTo(0, y), from + (targetY - from) * e);
      await this.frame();
    }
  }
  async scrollToEl(sel, sec, offset = 70) {
    const y = await this.page.evaluate(([s, o]) => { const el = document.querySelector(s); return el.getBoundingClientRect().top + scrollY - o; }, [sel, offset]);
    await this.scrollTo(y, sec);
  }
  // move the finger to an element, tap it (runs the real click), then keep recording
  async tap(sel, { click = true, after = 0.5 } = {}) {
    const box = await this.page.evaluate(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }, sel);
    const [x0, y0] = [this.fx, this.fy], n = 10;
    for (let i = 1; i <= n; i++) { const p = i / n; await this.finger(x0 + (box[0] - x0) * p, y0 + (box[1] - y0) * p, Math.min(1, p * 2)); await this.frame(); }
    this.fx = box[0]; this.fy = box[1];
    await this.finger(box[0], box[1], 1, 0.75); await this.frame(); await this.frame();
    if (click) await this.page.evaluate(s => { const el = document.querySelector(s); el.click(); }, sel);
    await this.finger(box[0], box[1], 1, 1); await this.frame();
    await this.hold(after);
    await this.finger(box[0], box[1], 0);
  }
  async type(sel, text, cps = 9) {
    for (let i = 1; i <= text.length; i++) {
      await this.page.evaluate(([s, v]) => { const el = document.querySelector(s); el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); }, [sel, text.slice(0, i)]);
      for (let k = 0; k < Math.round(FPS / cps); k++) await this.frame();
    }
  }
  async end() { this.ff.stdin.end(); await this.done; return (this.frames / FPS).toFixed(1) + "s"; }
}

async function setup(browser) {
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: DSF, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  await page.goto(VAULT);
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await page.reload();
  await page.addStyleTag({ content: OVERLAY_CSS });
  await page.evaluate(() => {
    document.body.insertAdjacentHTML("beforeend", `<div id="rec-status"><span>9:41</span><span>▂▄▆ ᯤ 🔋</span></div><div id="rec-cap"></div><div id="rec-finger"></div>`);
  });
  await page.evaluate(() => document.fonts.ready);
  return { ctx, page };
}

const DEMOS = {
  // 1) the full tour
  "finally-made-it": async (r, page) => {
    await r.cap("ok I finally finished the thing I've been making 😭");
    await r.hold(2.2);
    await r.cap("it's every weird hack that actually worked for me");
    await r.scrollToEl("#contents", 1.6, 30); await r.hold(0.8);
    await r.cap("12 \"laws\" and you can tap straight to any of them");
    await r.tap('.toc-row[href="#ch01"]', { click: false, after: 0.2 });
    await r.scrollToEl("#ch01", 1.0, 0); await r.hold(0.9);
    await r.cap("120 hacks total. each one says why it works + exactly how");
    await r.scrollToEl("#hack-1", 1.2); await r.hold(0.4);
    await r.scrollTo(await page.evaluate(() => scrollY + 380), 1.8); await r.hold(0.3);
    await r.cap("and a little roast on every single one 💀");
    await r.scrollToEl("#hack-1 .callout", 0.8, 200); await r.hold(1.6);
    await r.cap("you tick the ones you tried and it saves");
    await r.scrollToEl("#hack-1 .hack-actions", 0.8, 360);
    await r.tap('#hack-1 [data-save="tried-1"]', { after: 1.0 });
    await r.cap("there's even a quiz that tells you where to start");
    await r.scrollToEl("#quiz", 1.4, 30); await r.hold(1.0);
    await r.cap("anyway. link's in my bio if you want it 🤍");
    await r.scrollToEl("#bonus-challenge", 1.6, 30); await r.hold(2.2);
  },
  // 2) "search your problem"
  "search-your-problem": async (r, page) => {
    await r.cap("the best part is you can literally search your problem");
    await r.hold(1.8);
    await r.tap("#menuBtn", { after: 0.6 });
    await r.cap("like… \"night\" (hi, 9pm snack girlies)");
    await r.tap("#search", { click: false, after: 0.1 });
    await r.type("#search", "night");
    await r.hold(1.4);
    const cnt = await page.evaluate(() => document.querySelectorAll(".results a").length);
    await r.cap(`${cnt} hacks just for that 😭`);
    await r.hold(1.2);
    await r.cap("or tap \"cravings\" and it filters everything");
    await r.page.evaluate(() => { const s = document.getElementById("search"); s.value = ""; s.dispatchEvent(new Event("input", { bubbles: true })); });
    await r.tap('.chip[data-tag="cravings"]', { after: 1.4 });
    await r.cap("tap one and it takes you right there");
    await r.tap(".results a:nth-of-type(2)", { after: 0.2 });
    await page.evaluate(() => { document.getElementById("drawer").classList.remove("open"); document.getElementById("scrim").classList.remove("on"); });
    const id = await page.evaluate(() => (location.hash || "#hack-21").slice(1));
    await r.scrollToEl("#" + id, 0.01); await r.hold(1.6);
    await r.scrollTo(await page.evaluate(() => scrollY + 420), 2.0);
    await r.cap("it's in my bio if you want it. no pressure lol");
    await r.hold(2.0);
  },
  // 3) the quiz
  "which-type-quiz": async (r, page) => {
    await r.scrollToEl("#quiz", 0.01, 30);
    await r.cap("not me making a quiz that exposed my own eating habits 💀");
    await r.hold(2.0);
    const picks = ["night", "night", "night", "night", "stress"];
    for (let i = 0; i < 5; i++) {
      await r.scrollToEl(`.qq:nth-of-type(${i + 1})`, 0.6, 90);
      if (i === 1) await r.cap("be honest with yourself here…");
      await r.tap(`input[name="q${i}"][value="${picks[i]}"]`, { after: 0.25 });
    }
    await r.cap("and…");
    await r.tap("#quizForm button", { after: 0.1 });
    await r.scrollToEl("#quizResult", 0.8, 90); await r.hold(0.6);
    await r.cap("yep. Night Nibbler. called out by my own ebook 😭");
    await r.hold(2.4);
    await r.cap("it even tells you which chapters to read first");
    await r.hold(1.8);
    await r.cap("take it, it's in my bio. tell me your type 👇");
    await r.hold(2.0);
  },
};

const only = process.argv[2];
const browser = await chromium.launch();
for (const [name, run] of Object.entries(DEMOS)) {
  if (only && !name.includes(only)) continue;
  const dir = path.join(ROOT, "tiktok-posts", "demos", name); fs.mkdirSync(dir, { recursive: true });
  const { ctx, page } = await setup(browser);
  const r = new Rec(page, path.join(dir, "video.mp4"));
  await run(r, page);
  console.log("✓", name, await r.end());
  await ctx.close();
}
await browser.close();
