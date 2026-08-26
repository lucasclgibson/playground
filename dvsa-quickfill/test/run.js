// Drives the userscript against mock sign-in pages in a real browser, so we
// know the field matching and the fill/submit path work before anyone installs
// it. The mobile block is the one that matters most — iPhone Safari is the
// primary target. Run with: node test/run.js
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium, devices } = require('/opt/node22/lib/node_modules/playwright');
const { LABELLED, ANONYMOUS, UNRELATED } = require('./fixtures');

const SCRIPT = fs.readFileSync(path.join(__dirname, '..', 'dvsa-quickfill.user.js'), 'utf8');
const DETAILS = { licence: 'TESTX123456AB7CD89', theory: '111222333' };
const IPHONE = devices['iPhone 14'] || devices['iPhone 13'];

let failures = 0;

function check(name, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures += 1;
  console.log(
    `${ok ? 'PASS' : 'FAIL'}  ${name}` +
      (ok ? '' : ` (got ${JSON.stringify(actual)}, wanted ${JSON.stringify(expected)})`)
  );
}

async function withPage(server, options, fn) {
  server.html = options.html;
  const browser = await chromium.launch();
  const context = await browser.newContext(
    options.mobile
      ? {
          viewport: IPHONE.viewport,
          userAgent: IPHONE.userAgent,
          deviceScaleFactor: IPHONE.deviceScaleFactor,
          isMobile: true,
          hasTouch: true,
        }
      : {}
  );
  const page = await context.newPage();
  if (options.details !== null) {
    await page.addInitScript((details) => {
      window.localStorage.setItem('dvsa-quickfill:details', JSON.stringify(details));
    }, options.details || DETAILS);
  }
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.evaluate(SCRIPT);
  await page.waitForTimeout(250);
  try {
    await fn(page);
  } finally {
    await browser.close();
  }
}

const button = (page) => page.locator('#dvsa-quickfill-button');
const panelPresent = (page) => page.evaluate(() => Boolean(document.getElementById('dvsa-quickfill-panel')));
const submitted = (page) => page.evaluate(() => document.body.dataset.submitted || 'no');

async function pressAndHold(page, ms) {
  const box = await button(page).boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.waitForTimeout(ms);
  await page.mouse.up();
}

(async () => {
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(server.html);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));

  console.log('\n— iPhone —');

  await withPage(server, { html: LABELLED, mobile: true }, async (page) => {
    check('autofills on load', await page.inputValue('#driving-licence-number'), DETAILS.licence);
    check('autofills second field', await page.inputValue('#application-reference-number'), DETAILS.theory);
    check('does not submit on its own', await submitted(page), 'no');
    check('floating button shown', await button(page).count(), 1);
  });

  await withPage(server, { html: LABELLED, mobile: true }, async (page) => {
    const box = await button(page).boundingBox();
    // Apple's minimum comfortable tap target is 44pt square.
    check('button is thumb-sized', box.height >= 44 && box.width >= 44, true);
    check('button sits inside the viewport', box.x >= 0 && box.x + box.width <= IPHONE.viewport.width, true);
  });

  await withPage(server, { html: LABELLED, mobile: true }, async (page) => {
    await button(page).tap();
    await page.waitForTimeout(250);
    check('tap fills and signs in', await submitted(page), 'yes');
  });

  await withPage(server, { html: LABELLED, mobile: true }, async (page) => {
    await pressAndHold(page, 800);
    await page.waitForTimeout(150);
    check('press and hold opens the panel', await panelPresent(page), true);
    check('press and hold does not sign in', await submitted(page), 'no');
  });

  await withPage(server, { html: LABELLED, mobile: true, details: null }, async (page) => {
    check('first run prompts for details', await panelPresent(page), true);
    const width = await page.evaluate(() => document.getElementById('dvsa-quickfill-panel').getBoundingClientRect().width);
    check('panel fits the screen', width <= IPHONE.viewport.width - 24, true);
    check('no horizontal overflow', await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  });

  await withPage(server, { html: UNRELATED, mobile: true }, async (page) => {
    check('button hidden on pages with no form', await button(page).count(), 0);
  });

  console.log('\n— field matching —');

  await withPage(server, { html: ANONYMOUS, mobile: true }, async (page) => {
    check('licence matched by label text alone', await page.inputValue('#field-a'), DETAILS.licence);
    check('theory matched by label text alone', await page.inputValue('#field-b'), DETAILS.theory);
    check('postcode left alone', await page.inputValue('#field-c'), '');
  });

  console.log('\n— desktop —');

  await withPage(server, { html: LABELLED, mobile: false }, async (page) => {
    check('submit focused after autofill', await page.evaluate(() => document.activeElement.textContent), 'Continue');
    await page.keyboard.press('Control+Enter');
    await page.waitForTimeout(250);
    check('ctrl+enter fills and submits', await submitted(page), 'yes');
  });

  await withPage(server, { html: LABELLED, mobile: false }, async (page) => {
    await page.keyboard.press('Control+Shift+D');
    await page.waitForTimeout(150);
    check('ctrl+shift+d opens the panel', await panelPresent(page), true);
  });

  server.close();
  console.log(failures === 0 ? '\nAll checks passed.' : `\n${failures} check(s) failed.`);
  process.exit(failures === 0 ? 0 : 1);
})();
