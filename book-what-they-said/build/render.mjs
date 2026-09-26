// Renders book.html -> what-they-said-interior.pdf, cover.html -> cover.png/.pdf, and preview PNGs of chosen pages.
// Usage: node book-what-they-said/build/render.mjs [page numbers to preview, e.g. 1 3 5 9]
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'path'; import { fileURLToPath } from 'url';
const dir = path.dirname(fileURLToPath(import.meta.url)), out = path.join(dir, '..');
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1000, height: 1400 } });
await pg.goto('file://' + path.join(dir, 'book.html')); await pg.evaluate(() => document.fonts.ready);
const pages = await pg.$$('section.page');
for (const n of process.argv.slice(2).map(Number)) await pages[n - 1].screenshot({ path: path.join(dir, `preview-${String(n).padStart(3, '0')}.png`) });
await pg.pdf({ path: path.join(out, 'what-they-said-interior.pdf'), width: '900px', height: '1350px', printBackground: true });
await pg.goto('file://' + path.join(dir, 'cover.html')); await pg.evaluate(() => document.fonts.ready);
await (await pg.$('.cover')).screenshot({ path: path.join(out, 'what-they-said-cover.png') });
await pg.pdf({ path: path.join(out, 'what-they-said-cover.pdf'), width: '900px', height: '1350px', printBackground: true });
await b.close(); console.log('pages', pages.length);
