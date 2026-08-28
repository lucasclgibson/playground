// Loads the built extension into a real Chrome profile and drives the options
// page and the side panel. Run with: node test/extension.js
//
// Extensions need the full Chromium build rather than the headless shell, hence
// channel: 'chromium'.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const EXTENSION = path.join(__dirname, '..', 'extension');
const STORAGE_KEY = 'spicy-test-booker';

const SAMPLE = {
  licence: 'TESTX905317JB9UU',
  theory: '111222333',
  cardName: 'A Sample',
  // A Visa test number that passes the Luhn check. Not a real card.
  cardNumber: '4111111111111111',
  cardExpiry: '11/34',
  cardCvv: '123',
};

let failures = 0;

function check(name, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures += 1;
  console.log(
    `${ok ? 'PASS' : 'FAIL'}  ${name}` +
      (ok ? '' : ` (got ${JSON.stringify(actual)}, wanted ${JSON.stringify(expected)})`)
  );
}

async function launch() {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'dvsa-ext-'));
  const context = await chromium.launchPersistentContext(userDataDir, {
    channel: 'chromium',
    args: [`--disable-extensions-except=${EXTENSION}`, `--load-extension=${EXTENSION}`],
  });

  // Record what the page hands to the clipboard. The real clipboard needs a
  // focused document and user activation, which a headless run can't reliably
  // give us; what matters here is the exact value our code copies.
  await context.addInitScript(() => {
    window.__copied = [];
    if (!navigator.clipboard) Object.defineProperty(navigator, 'clipboard', { value: {}, writable: true });
    navigator.clipboard.writeText = (text) => {
      window.__copied.push(text);
      return Promise.resolve();
    };
  });

  let [worker] = context.serviceWorkers();
  if (!worker) worker = await context.waitForEvent('serviceworker');
  const id = new URL(worker.url()).host;

  return { context, id, userDataDir };
}

async function seed(page, details) {
  await page.evaluate(
    ([key, value]) => chrome.storage.local.set({ [key]: value }),
    [STORAGE_KEY, details]
  );
}

(async () => {
  const { context, id, userDataDir } = await launch();
  const url = (file) => `chrome-extension://${id}/${file}`;

  console.log('\n— options page —');

  const options = await context.newPage();
  await options.goto(url('options.html'));

  await options.fill('#licence', SAMPLE.licence);
  await options.fill('#theory', SAMPLE.theory);
  await options.fill('#cardName', SAMPLE.cardName);
  await options.type('#cardNumber', SAMPLE.cardNumber);
  await options.type('#cardExpiry', '1134');
  await options.type('#cardCvv', SAMPLE.cardCvv);

  check('card number groups itself as you type', await options.inputValue('#cardNumber'), '4111 1111 1111 1111');
  check('expiry gains its slash', await options.inputValue('#cardExpiry'), '11/34');

  await options.click('#save');
  await options.waitForTimeout(200);

  const stored = await options.evaluate(
    (key) => chrome.storage.local.get(key).then((all) => all[key]),
    STORAGE_KEY
  );
  check('licence saved', stored.licence, SAMPLE.licence);
  check('card number saved grouped for display', stored.cardNumber, '4111 1111 1111 1111');
  check('cvv saved', stored.cardCvv, SAMPLE.cardCvv);

  const synced = await options.evaluate(() => chrome.storage.sync.get(null));
  check('nothing written to synced storage', Object.keys(synced).length, 0);

  await options.fill('#cardNumber', '4111 1111 1111 1112');
  await options.click('#save');
  await options.waitForTimeout(150);
  check(
    'a mistyped card number is caught',
    await options.evaluate(() => !document.getElementById('error-cardNumber').hidden),
    true
  );

  await options.fill('#cardNumber', SAMPLE.cardNumber);
  await options.fill('#cardExpiry', '01/20');
  await options.click('#save');
  await options.waitForTimeout(150);
  check(
    'an expired card is caught',
    await options.evaluate(() => document.getElementById('error-cardExpiry').textContent),
    'That card has expired.'
  );

  // A licence typed with its 2-digit issue number on the end must survive
  // intact — silently eating two characters would hand the DVSA form a wrong
  // number with nothing on screen to explain it.
  await options.fill('#cardExpiry', SAMPLE.cardExpiry);
  await options.fill('#licence', '');
  await options.type('#licence', 'TESTX905317JB9UU14');
  check('licence with issue number is not truncated', await options.inputValue('#licence'), 'TESTX905317JB9UU14');

  await options.click('#save');
  await options.waitForTimeout(200);
  check(
    'the extra two digits are explained, not swallowed',
    await options.evaluate(() => document.getElementById('error-licence').textContent.includes('issue number')),
    true
  );
  check(
    'and it still saves, because that may be what the licence says',
    await options.evaluate(
      (key) => chrome.storage.local.get(key).then((all) => all[key].licence),
      STORAGE_KEY
    ),
    'TESTX905317JB9UU14'
  );
  check(
    'a non-blocking note is styled as a note, not an error',
    await options.evaluate(() => document.getElementById('error-licence').classList.contains('is-warning')),
    true
  );
  await options.close();

  console.log('\n— side panel —');

  const empty = await context.newPage();
  await empty.goto(url('sidepanel.html'));
  await empty.evaluate((key) => chrome.storage.local.remove(key), STORAGE_KEY);
  await empty.reload();
  await empty.waitForTimeout(200);
  check('empty state shown with nothing saved', await empty.isVisible('#empty'), true);
  check('no rows rendered', await empty.locator('.row').count(), 0);
  await empty.close();

  const panel = await context.newPage();
  await panel.goto(url('sidepanel.html'));
  await seed(panel, SAMPLE);
  await panel.reload();
  await panel.waitForTimeout(250);

  check('a row per saved detail', await panel.locator('.row').count(), 6);
  check('empty state hidden', await panel.isVisible('#empty'), false);

  const cardRow = panel.locator('.row[data-key="cardNumber"]');
  check('card number masked to the last four', await cardRow.locator('.row-value').innerText(), '•••• •••• •••• 1111');
  check('cvv masked', await panel.locator('.row[data-key="cardCvv"] .row-value').innerText(), '•••');
  check(
    'licence shown in full',
    await panel.locator('.row[data-key="licence"] .row-value').innerText(),
    SAMPLE.licence
  );

  await cardRow.locator('.icon-button').click();
  await panel.waitForTimeout(150);
  check('reveal shows the grouped number', await cardRow.locator('.row-value').innerText(), '4111 1111 1111 1111');

  await panel.locator('.row[data-key="cardNumber"] .row-copy').click();
  await panel.waitForTimeout(150);
  check(
    'copying the card gives bare digits, not the spaced display',
    await panel.evaluate(() => window.__copied[window.__copied.length - 1]),
    '4111111111111111'
  );

  await panel.locator('.row[data-key="licence"] .row-copy').click();
  await panel.waitForTimeout(150);
  check(
    'copying the licence gives the licence',
    await panel.evaluate(() => window.__copied[window.__copied.length - 1]),
    SAMPLE.licence
  );

  await panel.locator('body').press('4');
  await panel.waitForTimeout(150);
  check(
    'number key copies the matching row',
    await panel.evaluate(() => window.__copied[window.__copied.length - 1]),
    '4111111111111111'
  );

  await panel.click('#clear-clipboard');
  await panel.waitForTimeout(150);
  check(
    'clear clipboard overwrites it',
    await panel.evaluate(() => window.__copied[window.__copied.length - 1]),
    ' '
  );

  console.log('\n— permissions —');

  const manifest = JSON.parse(fs.readFileSync(path.join(EXTENSION, 'manifest.json'), 'utf8'));
  check('named as asked', manifest.name, 'Jacks Spicy Test Booker');
  check('asks for storage and sidePanel only', manifest.permissions.join(','), 'storage,sidePanel');
  check('host access limited to dvsa.gov.uk', manifest.host_permissions.join(','), 'https://*.dvsa.gov.uk/*');
  check('extension pages cannot make network calls', manifest.content_security_policy.extension_pages.includes("connect-src 'none'"), true);

  const contentScript = fs.readFileSync(path.join(EXTENSION, 'content.js'), 'utf8');
  const cardKeys = ['cardNumber', 'cardCvv', 'cardName', 'cardExpiry'];
  check(
    'the content script never names a card field',
    cardKeys.some((key) => contentScript.includes(key)),
    false
  );

  await context.close();
  fs.rmSync(userDataDir, { recursive: true, force: true });

  console.log(failures === 0 ? '\nAll checks passed.' : `\n${failures} check(s) failed.`);
  process.exit(failures === 0 ? 0 : 1);
})();
