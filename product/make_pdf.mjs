// Makes the printable/clickable PDF + the store cover image from dist/the-skinny-laws-vault.html
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";
const require = createRequire("/opt/node22/lib/node_modules/");
const { chromium } = require("playwright");
const dir = path.dirname(fileURLToPath(import.meta.url));
const html = path.join(dir, "dist", "the-skinny-laws-vault.html");

const b = await chromium.launch();
const p = await b.newPage();
await p.goto("file://" + html);
await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: path.join(dir, "dist", "the-skinny-laws-vault.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true,
  displayHeaderFooter: true, headerTemplate: "<span></span>",
  footerTemplate: `<div style="width:100%;font:9px Inter,sans-serif;color:#9b8a90;padding:0 13mm;display:flex;justify-content:space-between"><span>The Skinny Laws Vault · @theskinnylaws</span><span class="pageNumber"></span></div>`,
  margin: { top: "12mm", bottom: "14mm", left: "0", right: "0" } });

// store cover / listing image (square, 2048px)
const c = await b.newPage({ viewport: { width: 1024, height: 1024 }, deviceScaleFactor: 2 });
await c.goto("file://" + html);
await c.evaluate(() => {
  document.body.innerHTML = `<div style="width:1024px;height:1024px;display:grid;place-items:center;background:radial-gradient(120% 90% at 50% 0%,#fff 0%,#FCEDEA 45%,#F6DCD8 100%);font-family:Inter">
   <div style="display:flex;gap:56px;align-items:center">
    <div style="width:440px;height:600px;border-radius:10px 28px 28px 10px;background:radial-gradient(120% 80% at 50% 0%,#fff 0%,#FCEDEA 50%,#F6DCD8 100%);box-shadow:-16px 0 0 #E7A1A6 inset,0 40px 90px rgba(74,34,51,.35);padding:56px 60px 56px 66px;display:flex;flex-direction:column;justify-content:center;position:relative">
      <div style="font:800 17px Inter;letter-spacing:.24em;color:#C8325F;margin-bottom:22px">@THESKINNYLAWS</div>
      <div style="font:400 78px/.98 'DM Serif Display';color:#2B1E23">The Skinny Laws<br><em style="color:#C8325F">Vault</em></div>
      <div style="margin-top:26px;max-width:270px;font:500 21px/1.4 Inter;color:#4A2233">120 unusual hacks to get lean & stay lean — without starving</div>
      <div style="position:absolute;right:40px;bottom:34px;font-size:46px">🔐</div></div>
    <div style="width:360px;font:500 24px/1.5 Inter;color:#2B1E23">
      <div style="font:400 50px/1.05 'DM Serif Display';margin-bottom:20px">Everything inside</div>
      ${["120 insider hacks","12 Laws you can jump to","60-sec eating-type quiz","30-Day Challenge","Lean Grocery List","Restaurant Cheat Sheet","Weekly Average Tracker","Journal prompts"].map(x=>`<div style="padding:9px 0;border-bottom:1px solid #EBDCD6">✓ ${x}</div>`).join("")}
      <div style="margin-top:20px;font:700 18px Inter;color:#C8325F;letter-spacing:.08em">INTERACTIVE · PHONE-FRIENDLY · INSTANT DOWNLOAD</div>
    </div></div></div>`;
  document.body.style.margin = 0;
});
await c.screenshot({ path: path.join(dir, "dist", "store-cover.png") });
await b.close();
console.log("pdf + cover done");
