import {
  ITEMS,
  load,
  save,
  clear,
  validate,
  blocking,
  normaliseExpiry,
  groupCardNumber,
  digitsOnly,
} from './store.js';

const form = document.getElementById('form');
const savedFlag = document.getElementById('saved');
let savedTimer = null;

function inputFor(key) {
  return document.getElementById(key);
}

function readForm() {
  const details = {};
  ITEMS.forEach((item) => {
    details[item.key] = inputFor(item.key).value;
  });
  return details;
}

function showProblems(problems) {
  ITEMS.forEach((item) => {
    const problem = problems[item.key];
    const note = document.getElementById('error-' + item.key);
    const input = inputFor(item.key);
    note.textContent = problem ? problem.message : '';
    note.hidden = !problem;
    note.classList.toggle('is-warning', Boolean(problem) && !problem.blocking);
    if (problem && problem.blocking) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
  });
}

// Typing aids: the card number groups itself in fours and the expiry gains its
// slash, so what you type looks like what is printed on the card.
inputFor('cardNumber').addEventListener('input', (event) => {
  const input = event.target;
  const before = input.selectionStart;
  const digitsBefore = digitsOnly(input.value.slice(0, before)).length;
  input.value = groupCardNumber(input.value).slice(0, 23);
  // Put the caret back where the same digit now sits.
  let seen = 0;
  let position = input.value.length;
  for (let i = 0; i < input.value.length; i += 1) {
    if (/\d/.test(input.value[i])) seen += 1;
    if (seen === digitsBefore) {
      position = i + 1;
      break;
    }
  }
  if (digitsBefore === 0) position = 0;
  input.setSelectionRange(position, position);
});

inputFor('cardExpiry').addEventListener('input', (event) => {
  event.target.value = normaliseExpiry(event.target.value);
});

inputFor('cardCvv').addEventListener('input', (event) => {
  event.target.value = digitsOnly(event.target.value).slice(0, 4);
});

inputFor('licence').addEventListener('input', (event) => {
  // Capped at 18, not 16: plenty of people type the driver number with the
  // issue number on the end, and silently eating two characters they typed is
  // worse than telling them about it when they save.
  event.target.value = event.target.value.toUpperCase().replace(/\s/g, '').slice(0, 18);
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const details = readForm();
  const problems = validate(details);
  showProblems(problems);

  const blockers = blocking(problems);
  if (blockers.length > 0) {
    const first = ITEMS.find((item) => blockers.includes(item.key));
    if (first) inputFor(first.key).focus();
    return;
  }

  await save(details);
  savedFlag.hidden = false;
  window.clearTimeout(savedTimer);
  savedTimer = window.setTimeout(() => {
    savedFlag.hidden = true;
  }, 2200);
});

document.getElementById('clear').addEventListener('click', async () => {
  const sure = window.confirm('Delete the saved licence, theory and card details from this browser?');
  if (!sure) return;
  await clear();
  ITEMS.forEach((item) => {
    inputFor(item.key).value = '';
  });
  showProblems({});
});

load().then((details) => {
  ITEMS.forEach((item) => {
    const value = details[item.key] || '';
    inputFor(item.key).value = item.key === 'cardNumber' ? groupCardNumber(value) : value;
  });
});
