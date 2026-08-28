import {
  ITEMS,
  STORAGE_KEY,
  load,
  clipboardValue,
  groupCardNumber,
  maskCardNumber,
  maskValue,
} from './store.js';

const GROUPS = {
  identity: { section: 'group-identity', rows: 'rows-identity' },
  card: { section: 'group-card', rows: 'rows-card' },
};

const revealed = new Set();
let details = {};
let order = [];
let toastTimer = null;

// ------------------------------------------------------------------ render

// Sensitive values are masked until asked for, so the panel can sit open beside
// the booking form without a card number on show.
function displayValue(item) {
  const raw = details[item.key] || '';
  if (!raw) return { text: 'Not set', unset: true };
  if (item.sensitive && !revealed.has(item.key)) {
    return { text: item.key === 'cardNumber' ? maskCardNumber(raw) : maskValue(raw), unset: false };
  }
  if (item.key === 'cardNumber') return { text: groupCardNumber(raw), unset: false };
  return { text: raw, unset: false };
}

function eyeIcon(open) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute(
    'd',
    open
      ? 'M12 5c5 0 9 4.5 9 7s-4 7-9 7-9-4.5-9-7 4-7 9-7Zm0 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z'
      : 'M2.8 3.5 21 21.7l-1.4 1.4-3.3-3.3A10.6 10.6 0 0 1 12 20c-5 0-9-4.5-9-7 0-1.4 1.3-3.4 3.4-5L1.4 4.9 2.8 3.5ZM12 6c5 0 9 4.5 9 7 0 1.1-.8 2.6-2.3 4l-3-3a4 4 0 0 0-4.7-4.7L8.7 6.9c1-.6 2.1-.9 3.3-.9Z'
  );
  svg.appendChild(path);
  return svg;
}

function buildRow(item, index) {
  const row = document.createElement('div');
  row.className = 'row';
  row.dataset.key = item.key;

  const shown = displayValue(item);

  const copy = document.createElement('button');
  copy.type = 'button';
  copy.className = 'row-copy';
  copy.disabled = shown.unset;
  copy.dataset.key = item.key;
  copy.setAttribute('aria-label', 'Copy ' + item.label.toLowerCase());

  const badge = document.createElement('span');
  badge.className = 'row-index';
  badge.textContent = String(index + 1);
  badge.setAttribute('aria-hidden', 'true');

  const label = document.createElement('span');
  label.className = 'row-label';
  label.textContent = item.label;

  const value = document.createElement('span');
  value.className = 'row-value' + (shown.unset ? ' is-unset' : '');
  value.textContent = shown.text;

  copy.append(badge, label, value);
  row.appendChild(copy);

  if (item.sensitive && !shown.unset) {
    const side = document.createElement('div');
    side.className = 'row-side';
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'icon-button';
    const isOpen = revealed.has(item.key);
    toggle.title = isOpen ? 'Hide' : 'Show';
    toggle.setAttribute('aria-label', (isOpen ? 'Hide ' : 'Show ') + item.label.toLowerCase());
    toggle.appendChild(eyeIcon(isOpen));
    toggle.addEventListener('click', () => {
      if (revealed.has(item.key)) revealed.delete(item.key);
      else revealed.add(item.key);
      render();
    });
    side.appendChild(toggle);
    row.appendChild(side);
  }

  return row;
}

function render() {
  const filled = ITEMS.filter((item) => details[item.key]);
  document.getElementById('empty').hidden = filled.length > 0;

  // Numbered for the 1-6 shortcuts, counting only rows there is something to
  // copy from, so the numbers match what you can actually see.
  order = [];
  let index = 0;

  Object.keys(GROUPS).forEach((group) => {
    const items = ITEMS.filter((item) => item.group === group);
    const anyFilled = items.some((item) => details[item.key]);
    document.getElementById(GROUPS[group].section).hidden = !anyFilled;

    const container = document.getElementById(GROUPS[group].rows);
    container.replaceChildren();
    if (!anyFilled) return;

    items.forEach((item) => {
      const row = buildRow(item, index);
      if (details[item.key]) {
        order.push(item.key);
        index += 1;
      } else {
        const badge = row.querySelector('.row-index');
        if (badge) badge.textContent = '';
      }
      container.appendChild(row);
    });
  });
}

// ------------------------------------------------------------------ copying

function toast(message) {
  const node = document.getElementById('toast');
  node.textContent = message;
  node.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    node.hidden = true;
  }, 1800);
}

function flashRow(key) {
  const row = document.querySelector('.row[data-key="' + key + '"]');
  if (!row) return;
  row.classList.add('is-copied');
  window.setTimeout(() => row.classList.remove('is-copied'), 900);
}

async function copyKey(key) {
  const item = ITEMS.find((entry) => entry.key === key);
  if (!item) return;
  const value = clipboardValue(key, details);
  if (!value) return;

  try {
    await navigator.clipboard.writeText(value);
    flashRow(key);
    toast(item.label + ' copied');
  } catch (err) {
    toast('Could not reach the clipboard');
  }
}

// ------------------------------------------------------------------- wiring

document.addEventListener('click', (event) => {
  const copy = event.target.closest('.row-copy');
  if (copy && !copy.disabled) copyKey(copy.dataset.key);
});

document.addEventListener('keydown', (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const target = event.target;
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) return;
  const position = Number(event.key);
  if (!Number.isInteger(position) || position < 1 || position > order.length) return;
  event.preventDefault();
  copyKey(order[position - 1]);
});

document.getElementById('settings').addEventListener('click', () => chrome.runtime.openOptionsPage());
document.getElementById('empty-settings').addEventListener('click', () => chrome.runtime.openOptionsPage());

document.getElementById('clear-clipboard').addEventListener('click', async () => {
  try {
    // Chrome rejects writing an empty string, so overwrite with a space.
    await navigator.clipboard.writeText(' ');
    toast('Clipboard cleared');
  } catch (err) {
    toast('Could not reach the clipboard');
  }
});

// Keep the panel honest if the details are edited in another tab.
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local' || !changes[STORAGE_KEY]) return;
  details = Object.assign({}, changes[STORAGE_KEY].newValue || {});
  revealed.clear();
  render();
});

load().then((stored) => {
  details = stored;
  render();
});
