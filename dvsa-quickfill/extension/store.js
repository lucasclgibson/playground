// Shared storage and validation for the side panel and the options page.
//
// Everything lives in chrome.storage.local rather than storage.sync: sync would
// push card details through a Google account and onto every signed-in machine,
// which is not a trade anyone asked for.

export const STORAGE_KEY = 'spicy-test-booker';

export const ITEMS = [
  { key: 'licence', label: 'Driving licence number', group: 'identity', sensitive: false },
  { key: 'theory', label: 'Theory test pass number', group: 'identity', sensitive: false },
  { key: 'cardName', label: 'Name on card', group: 'card', sensitive: false },
  { key: 'cardNumber', label: 'Card number', group: 'card', sensitive: true },
  { key: 'cardExpiry', label: 'Expiry date', group: 'card', sensitive: false },
  { key: 'cardCvv', label: 'Security code', group: 'card', sensitive: true },
];

const EMPTY = ITEMS.reduce((acc, item) => {
  acc[item.key] = '';
  return acc;
}, {});

export async function load() {
  const stored = await chrome.storage.local.get(STORAGE_KEY);
  return Object.assign({}, EMPTY, stored[STORAGE_KEY] || {});
}

export async function save(details) {
  const clean = {};
  ITEMS.forEach((item) => {
    clean[item.key] = (details[item.key] || '').trim();
  });
  await chrome.storage.local.set({ [STORAGE_KEY]: clean });
  return clean;
}

export async function clear() {
  await chrome.storage.local.remove(STORAGE_KEY);
}

// ------------------------------------------------------------- formatting

export function digitsOnly(value) {
  return (value || '').replace(/\D/g, '');
}

// Grouped in fours for reading and checking against the physical card. The
// value copied to the clipboard is always the bare digits.
export function groupCardNumber(value) {
  const digits = digitsOnly(value);
  return digits.replace(/(.{4})/g, '$1 ').trim();
}

export function maskCardNumber(value) {
  const digits = digitsOnly(value);
  if (digits.length < 4) return '••••';
  return '•••• •••• •••• ' + digits.slice(-4);
}

export function maskValue(value) {
  return '•'.repeat(Math.max((value || '').length, 3));
}

export function normaliseExpiry(value) {
  const digits = digitsOnly(value).slice(0, 4);
  if (digits.length <= 2) return digits;
  return digits.slice(0, 2) + '/' + digits.slice(2);
}

// ------------------------------------------------------------- validation

// The Luhn check catches a mistyped digit before it costs a booking attempt.
export function luhn(value) {
  const digits = digitsOnly(value);
  if (digits.length < 12) return false;
  let sum = 0;
  let double = false;
  for (let i = digits.length - 1; i >= 0; i -= 1) {
    let digit = Number(digits[i]);
    if (double) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    double = !double;
  }
  return sum % 10 === 0;
}

// Problems come back with a severity. Blocking ones are certain typos and stop
// a save; non-blocking ones are worth saying out loud but might legitimately be
// what the licence says, so they never stand in the way.
export function validate(details, now) {
  const problems = {};
  const today = now || new Date();

  const licence = (details.licence || '').replace(/\s/g, '');
  if (licence && licence.length !== 16) {
    // A DVLA driver number is 16 characters. Licences also print a 2-digit
    // issue number, and people often run the two together — hence 18.
    problems.licence =
      licence.length === 18
        ? {
            message:
              'That looks like the 16-character driver number with the 2-digit issue number on the end. The DVSA form wants just the first 16.',
            blocking: false,
          }
        : { message: 'A DVLA driver number is 16 characters.', blocking: false };
  }

  const theory = digitsOnly(details.theory);
  if (details.theory && theory.length < 8) {
    problems.theory = { message: 'Theory test pass numbers are usually at least 8 digits.', blocking: false };
  }

  const cardNumber = digitsOnly(details.cardNumber);
  if (cardNumber && !luhn(cardNumber)) {
    problems.cardNumber = {
      message: "That card number doesn't check out — worth re-reading the digits.",
      blocking: true,
    };
  }

  const expiry = digitsOnly(details.cardExpiry);
  if (details.cardExpiry) {
    if (expiry.length !== 4) {
      problems.cardExpiry = { message: 'Use MM/YY.', blocking: true };
    } else {
      const month = Number(expiry.slice(0, 2));
      const year = 2000 + Number(expiry.slice(2));
      if (month < 1 || month > 12) {
        problems.cardExpiry = { message: 'Month must be 01 to 12.', blocking: true };
      } else {
        // A card is good through the last day of its expiry month.
        const expiresAfter = new Date(year, month, 1);
        if (expiresAfter <= today) problems.cardExpiry = { message: 'That card has expired.', blocking: true };
      }
    }
  }

  const cvv = digitsOnly(details.cardCvv);
  if (details.cardCvv && (cvv.length < 3 || cvv.length > 4)) {
    problems.cardCvv = {
      message: 'Security codes are 3 digits, or 4 on American Express.',
      blocking: true,
    };
  }

  return problems;
}

export function blocking(problems) {
  return Object.keys(problems).filter((key) => problems[key].blocking);
}

// What actually goes on the clipboard: spaces and slashes are for reading, not
// for pasting into a payment form.
export function clipboardValue(key, details) {
  const raw = details[key] || '';
  if (key === 'cardNumber') return digitsOnly(raw);
  if (key === 'cardCvv') return digitsOnly(raw);
  if (key === 'licence') return raw.replace(/\s/g, '').toUpperCase();
  return raw.trim();
}
