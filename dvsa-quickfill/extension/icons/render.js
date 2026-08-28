// Regenerates the PNG icons from the SVG sources. Run: node icons/render.js
//
// 16 and 32 come from icon-small.svg, a simplified mark — the detailed one
// loses its shape at that size.
const fs = require('fs');
const path = require('path');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (err) {
  ({ chromium } = require('/opt/node22/lib/node_modules/playwright'));
}

const DIR = __dirname;
const detailed = fs.readFileSync(path.join(DIR, 'icon.svg'), 'utf8');
const simple = fs.readFileSync(path.join(DIR, 'icon-small.svg'), 'utf8');

(async () => {
  const browser = await chromium.launch();
  for (const size of [16, 32, 48, 128]) {
    const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
    const svg = size <= 32 ? simple : detailed;
    await page.setContent(
      `<style>html,body{margin:0;padding:0}svg{display:block;width:${size}px;height:${size}px}</style>${svg}`
    );
    await page.screenshot({ path: path.join(DIR, `icon-${size}.png`), omitBackground: true });
    await page.close();
  }
  await browser.close();
  console.log('icons rendered');
})();
