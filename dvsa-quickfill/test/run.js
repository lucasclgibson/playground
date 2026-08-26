// Drives the userscript against mock sign-in pages in a real browser, so we
// know the field matching and the fill/submit path actually work before anyone
// installs it. Run with: node test/run.js
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { LABELLED, ANONYMOUS } = require('./fixtures');

const SCRIPT = fs.readFileSync(path.join(__dirname, '..', 'dvsa-quickfill.user.js'), 'utf8');
const DETAILS = { licence: 'TESTX123456AB7CD89', theory: '111222333' };

let failures = 0;

function check(name, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures += 1;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : ` (got ${JSON.stringify(actual)}, wanted ${JSON.stringify(expected)})`}`);
}

async function withPage(server, html, fn) {
  server.html = html;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.addInitScript((details) => {
    window.localStorage.setItem('dvsa-quickfill:details', JSON.stringify(details));
  }, DETAILS);
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.evaluate(SCRIPT);
  await page.waitForTimeout(200);
  try {
    await fn(page);
  } finally {
    await browser.close();
  }
}

(async () => {
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(server.html);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));

  await withPage(server, LABELLED, async (page) => {
    check('labelled: licence filled', await page.inputValue('#driving-licence-number'), DETAILS.licence);
    check('labelled: theory filled', await page.inputValue('#application-reference-number'), DETAILS.theory);
    check(
      'labelled: submit focused',
      await page.evaluate(() => document.activeElement.textContent),
      'Continue'
    );
  });

  await withPage(server, ANONYMOUS, async (page) => {
    check('unlabelled ids: licence matched by label text', await page.inputValue('#field-a'), DETAILS.licence);
    check('unlabelled ids: theory matched by label text', await page.inputValue('#field-b'), DETAILS.theory);
    check('unlabelled ids: postcode left alone', await page.inputValue('#field-c'), '');
  });

  await withPage(server, LABELLED, async (page) => {
    await page.keyboard.press('Control+Enter');
    await page.waitForTimeout(200);
    check(
      'ctrl+enter fills and submits',
      await page.evaluate(() => document.body.dataset.submitted),
      'yes'
    );
  });

  await withPage(server, LABELLED, async (page) => {
    await page.keyboard.press('Control+Shift+D');
    await page.waitForTimeout(100);
    check(
      'ctrl+shift+d opens the settings panel',
      await page.evaluate(() => Boolean(document.getElementById('dvsa-quickfill-panel'))),
      true
    );
  });

  server.close();
  console.log(failures === 0 ? '\nAll checks passed.' : `\n${failures} check(s) failed.`);
  process.exit(failures === 0 ? 0 : 1);
})();
