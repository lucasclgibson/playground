// Finds the DVSA sign-in inputs. The service's markup changes from time to
// time, so rather than pinning to element ids we score every text input against
// everything the page says about it and take the best match.
//
// Shared by the content script; loaded into the same isolated world.

var DvsaFields = (function () {
  'use strict';

  const SPECS = [
    {
      key: 'licence',
      hints: ['driving-licence', 'drivinglicence', 'driving licence', 'licence', 'license', 'dln'],
      penalties: ['instructor', 'trainer'],
    },
    {
      key: 'theory',
      hints: [
        'theory',
        'certificate',
        'application-reference',
        'applicationreference',
        'application reference',
        'reference',
        'booking',
      ],
      penalties: ['postcode', 'email', 'phone'],
    },
  ];

  function isUsable(input) {
    if (input.type === 'hidden' || input.disabled || input.readOnly) return false;
    const rect = input.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return false;
    return window.getComputedStyle(input).visibility !== 'hidden';
  }

  function describe(input) {
    const parts = [input.id, input.name, input.placeholder, input.getAttribute('aria-label')];

    if (input.id) {
      const label = document.querySelector('label[for="' + CSS.escape(input.id) + '"]');
      if (label) parts.push(label.textContent);
    }

    const wrappingLabel = input.closest('label');
    if (wrappingLabel) parts.push(wrappingLabel.textContent);

    const describedBy = input.getAttribute('aria-describedby');
    if (describedBy) {
      describedBy.split(/\s+/).forEach(function (id) {
        const hint = document.getElementById(id);
        if (hint) parts.push(hint.textContent);
      });
    }

    const group = input.closest('.govuk-form-group, fieldset, div');
    if (group) {
      const legend = group.querySelector('legend, label, .govuk-label');
      if (legend) parts.push(legend.textContent);
    }

    return parts.filter(Boolean).join(' ').toLowerCase().replace(/\s+/g, ' ');
  }

  function scoreFor(spec, input) {
    const text = describe(input);
    let score = 0;
    spec.hints.forEach(function (hint, index) {
      // Earlier hints are more specific, so they are worth more.
      if (text.indexOf(hint) !== -1) score += spec.hints.length - index;
    });
    spec.penalties.forEach(function (penalty) {
      if (text.indexOf(penalty) !== -1) score -= 5;
    });
    return score;
  }

  function find() {
    const candidates = Array.prototype.slice
      .call(document.querySelectorAll('input:not([type=hidden])'))
      .filter(isUsable);

    const found = {};
    const taken = [];

    SPECS.forEach(function (spec) {
      let best = null;
      let bestScore = 0;
      candidates.forEach(function (input) {
        if (taken.indexOf(input) !== -1) return;
        const score = scoreFor(spec, input);
        if (score > bestScore) {
          bestScore = score;
          best = input;
        }
      });
      if (best) {
        found[spec.key] = best;
        taken.push(best);
      }
    });

    return found;
  }

  function findSubmit(ignoreIds) {
    const skip = ignoreIds || [];
    const buttons = Array.prototype.slice.call(document.querySelectorAll('button, input[type=submit]'));
    const wanted = ['continue', 'sign in', 'signin', 'log in', 'login', 'submit', 'next'];

    for (let i = 0; i < buttons.length; i += 1) {
      const button = buttons[i];
      if (button.disabled || skip.indexOf(button.id) !== -1) continue;
      const text = (button.textContent || button.value || '').toLowerCase();
      for (let j = 0; j < wanted.length; j += 1) {
        if (text.indexOf(wanted[j]) !== -1) return button;
      }
    }
    return null;
  }

  // Assigning .value directly is invisible to frameworks that patch the input
  // setter, so go through the native descriptor and fire the events by hand.
  function setValue(input, value) {
    const descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
    if (descriptor && descriptor.set) descriptor.set.call(input, value);
    else input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  return { find: find, findSubmit: findSubmit, setValue: setValue, describe: describe };
})();

if (typeof module !== 'undefined') module.exports = DvsaFields;
