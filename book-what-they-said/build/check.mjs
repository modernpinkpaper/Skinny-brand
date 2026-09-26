import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'path'; import { fileURLToPath } from 'url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const b = await chromium.launch(); const pg = await b.newPage();
await pg.goto('file://' + path.join(dir, 'book.html')); await pg.evaluate(() => document.fonts.ready);
const r = await pg.evaluate(() => [...document.querySelectorAll('section.page.entry')].map(s => ({no: s.querySelector('.folio')?.textContent, lines: Math.floor(s.querySelector('.lines').getBoundingClientRect().height / 50)})));
const ls = r.map(x => x.lines); console.log('entry pages', r.length, 'min lines', Math.min(...ls), 'avg', (ls.reduce((a,b)=>a+b)/ls.length).toFixed(1));
console.log('fewest:', r.sort((a,b)=>a.lines-b.lines).slice(0,6).map(x=>`p${x.no}:${x.lines}`).join(' '));
await b.close();
