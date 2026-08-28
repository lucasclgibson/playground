// Runs on DVSA pages. Two jobs: fill the sign-in fields, and give the page a
// button that opens the side panel (Chrome will only open it off a gesture).
//
// This script deliberately only ever reads the licence and theory numbers from
// storage. Card details stay in the side panel, which lives on the extension's
// own origin — putting them in this page's DOM would expose them to anything
// else running on the page.

(function () {
  'use strict';

  const STORAGE_KEY = 'spicy-test-booker';
  const PAGE_KEYS = ['licence', 'theory'];
  const BUTTON_ID = 'spicy-booker-open';
  const TOAST_ID = 'spicy-booker-toast';

  let filledOnce = false;

  async function pageDetails() {
    const stored = await chrome.storage.local.get(STORAGE_KEY);
    const all = stored[STORAGE_KEY] || {};
    const subset = {};
    PAGE_KEYS.forEach(function (key) {
      subset[key] = all[key] || '';
    });
    return subset;
  }

  function toast(message) {
    const existing = document.getElementById(TOAST_ID);
    if (existing) existing.remove();
    const node = document.createElement('div');
    node.id = TOAST_ID;
    node.textContent = message;
    node.style.cssText = [
      'position:fixed',
      'left:50%',
      'transform:translateX(-50%)',
      'bottom:84px',
      'z-index:2147483647',
      'background:#16191a',
      'color:#fff',
      'padding:9px 16px',
      'border-radius:18px',
      'font:14px/1.3 -apple-system, Arial, sans-serif',
      'box-shadow:0 2px 10px rgba(0,0,0,.3)',
      'pointer-events:none',
    ].join(';');
    document.body.appendChild(node);
    window.setTimeout(function () {
      node.remove();
    }, 2200);
  }

  async function autofill() {
    const fields = DvsaFields.find();
    if (!fields.licence && !fields.theory) return false;

    const details = await pageDetails();
    let filled = 0;

    PAGE_KEYS.forEach(function (key) {
      const input = fields[key];
      if (!input || !details[key] || input.value) return;
      DvsaFields.setValue(input, details[key]);
      const previous = input.style.boxShadow;
      input.style.boxShadow = '0 0 0 3px #00703c';
      window.setTimeout(function () {
        input.style.boxShadow = previous;
      }, 900);
      filled += 1;
    });

    if (filled > 0 && !filledOnce) {
      filledOnce = true;
      const submit = DvsaFields.findSubmit([BUTTON_ID]);
      if (submit) submit.focus();
      toast('Signed-in details filled');
    }

    return true;
  }

  function ensureButton() {
    if (document.getElementById(BUTTON_ID)) return;

    const button = document.createElement('button');
    button.id = BUTTON_ID;
    button.type = 'button';
    button.textContent = 'Test Booker';
    button.style.cssText = [
      'position:fixed',
      'right:16px',
      'bottom:16px',
      'z-index:2147483646',
      'min-height:44px',
      'padding:11px 18px',
      'background:#00703c',
      'color:#fff',
      'border:0',
      'border-radius:22px',
      'box-shadow:0 4px 14px rgba(0,0,0,.3)',
      'font:600 15px/1.2 -apple-system, Arial, sans-serif',
      'cursor:pointer',
    ].join(';');

    button.addEventListener('click', function () {
      chrome.runtime.sendMessage({ type: 'open-side-panel' }, function (response) {
        if (chrome.runtime.lastError || !response || !response.opened) {
          toast('Open it from the toolbar icon, or press Ctrl+Shift+Y');
        }
      });
    });

    document.body.appendChild(button);
  }

  function refresh() {
    ensureButton();
    autofill();
  }

  refresh();

  let pending = null;
  const observer = new MutationObserver(function (records) {
    const ours = records.every(function (record) {
      return record.target.id === BUTTON_ID || record.target.id === TOAST_ID;
    });
    if (ours) return;
    window.clearTimeout(pending);
    pending = window.setTimeout(refresh, 300);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
