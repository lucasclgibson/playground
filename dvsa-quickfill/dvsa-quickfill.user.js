// ==UserScript==
// @name         DVSA Quick Fill
// @namespace    https://github.com/lucasclgibson/playground
// @version      1.0.0
// @description  Fills the DVSA driving test sign-in form from details saved in your browser, so signing in is one keypress instead of two numbers typed by hand.
// @match        *://*.dvsa.gov.uk/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  // A "personal" build (see make-personal.sh) bakes the details in here so the
  // script works the moment it is installed. The copy in the repo is blank on
  // purpose — licence details never belong in version control.
  const PRESET = {
    licence: '',
    theory: '',
  };

  const STORE_KEY = 'dvsa-quickfill:details';
  const PANEL_ID = 'dvsa-quickfill-panel';

  const FIELDS = [
    {
      key: 'licence',
      label: 'Driving licence number',
      hints: ['driving-licence', 'drivinglicence', 'driving licence', 'licence', 'license', 'dln'],
      penalties: ['instructor', 'trainer'],
    },
    {
      key: 'theory',
      label: 'Theory test pass number',
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

  // ---------------------------------------------------------------- storage

  function loadDetails() {
    if (PRESET.licence || PRESET.theory) {
      return { licence: PRESET.licence, theory: PRESET.theory };
    }
    try {
      const raw = window.localStorage.getItem(STORE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || (!parsed.licence && !parsed.theory)) return null;
      return { licence: parsed.licence || '', theory: parsed.theory || '' };
    } catch (err) {
      return null;
    }
  }

  function saveDetails(details) {
    try {
      window.localStorage.setItem(STORE_KEY, JSON.stringify(details));
      return true;
    } catch (err) {
      return false;
    }
  }

  function clearDetails() {
    try {
      window.localStorage.removeItem(STORE_KEY);
    } catch (err) {
      /* nothing we can do, and nothing worth interrupting the user over */
    }
  }

  // ------------------------------------------------------- field discovery

  function isUsable(input) {
    if (input.type === 'hidden' || input.disabled || input.readOnly) return false;
    const rect = input.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return false;
    return window.getComputedStyle(input).visibility !== 'hidden';
  }

  // Everything the page says about an input, flattened into one lowercase blob
  // we can keyword-match against. The DVSA markup changes from time to time, so
  // we score several signals rather than pinning to one id.
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

  function findField(spec, candidates) {
    let best = null;
    let bestScore = 0;

    candidates.forEach(function (input) {
      const text = describe(input);
      let score = 0;

      spec.hints.forEach(function (hint, index) {
        if (text.indexOf(hint) !== -1) {
          // Earlier hints are more specific, so they are worth more.
          score += spec.hints.length - index;
        }
      });

      spec.penalties.forEach(function (penalty) {
        if (text.indexOf(penalty) !== -1) score -= 5;
      });

      if (score > bestScore) {
        bestScore = score;
        best = input;
      }
    });

    return best;
  }

  function findFields() {
    const candidates = Array.prototype.slice
      .call(document.querySelectorAll('input:not([type=hidden]), input[type=text], input[type=search]'))
      .filter(isUsable);

    const found = {};
    const taken = [];

    FIELDS.forEach(function (spec) {
      const available = candidates.filter(function (input) {
        return taken.indexOf(input) === -1;
      });
      const match = findField(spec, available);
      if (match) {
        found[spec.key] = match;
        taken.push(match);
      }
    });

    return found;
  }

  function findSubmit() {
    const buttons = Array.prototype.slice.call(
      document.querySelectorAll('button, input[type=submit]')
    );
    const wanted = ['continue', 'sign in', 'signin', 'log in', 'login', 'submit', 'next'];

    for (let i = 0; i < buttons.length; i += 1) {
      const button = buttons[i];
      if (button.disabled) continue;
      const text = (button.textContent || button.value || '').toLowerCase();
      for (let j = 0; j < wanted.length; j += 1) {
        if (text.indexOf(wanted[j]) !== -1) return button;
      }
    }

    return buttons.find(function (button) {
      return !button.disabled && button.type === 'submit';
    }) || null;
  }

  // ------------------------------------------------------------- filling in

  // Assigning .value directly is invisible to frameworks that patch the input
  // setter, so go through the native descriptor and fire the events by hand.
  function setValue(input, value) {
    const descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
    if (descriptor && descriptor.set) {
      descriptor.set.call(input, value);
    } else {
      input.value = value;
    }
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  function fill(options) {
    const details = loadDetails();
    if (!details) {
      openPanel('No details saved yet.');
      return 0;
    }

    const fields = findFields();
    let filled = 0;

    FIELDS.forEach(function (spec) {
      const input = fields[spec.key];
      const value = details[spec.key];
      if (!input || !value) return;
      // Don't clobber something the user has started typing unless asked to.
      if (input.value && !options.force) return;
      setValue(input, value);
      flash(input);
      filled += 1;
    });

    if (filled === 0) {
      toast('Nothing to fill on this page');
      return 0;
    }

    const submit = findSubmit();
    if (submit) {
      if (options.submit) {
        toast('Filled — submitting');
        submit.click();
        return filled;
      }
      submit.focus();
    }

    toast('Filled ' + filled + ' field' + (filled === 1 ? '' : 's') + ' — press Enter');
    return filled;
  }

  function flash(input) {
    const previous = input.style.boxShadow;
    input.style.boxShadow = '0 0 0 3px #00703c';
    window.setTimeout(function () {
      input.style.boxShadow = previous;
    }, 900);
  }

  // ------------------------------------------------------------------- UI

  function toast(message) {
    const existing = document.getElementById('dvsa-quickfill-toast');
    if (existing) existing.remove();

    const node = document.createElement('div');
    node.id = 'dvsa-quickfill-toast';
    node.textContent = message;
    node.style.cssText = [
      'position:fixed',
      'bottom:16px',
      'right:16px',
      'z-index:2147483647',
      'background:#0b0c0c',
      'color:#fff',
      'padding:10px 14px',
      'border-radius:4px',
      'font:16px/1.3 "GDS Transport", Arial, sans-serif',
      'box-shadow:0 2px 8px rgba(0,0,0,.35)',
    ].join(';');
    document.body.appendChild(node);
    window.setTimeout(function () {
      node.remove();
    }, 2600);
  }

  function openPanel(note) {
    const existing = document.getElementById(PANEL_ID);
    if (existing) existing.remove();

    const details = loadDetails() || { licence: '', theory: '' };
    const locked = Boolean(PRESET.licence || PRESET.theory);

    const panel = document.createElement('div');
    panel.id = PANEL_ID;
    panel.style.cssText = [
      'position:fixed',
      'top:16px',
      'right:16px',
      'z-index:2147483647',
      'width:320px',
      'background:#fff',
      'color:#0b0c0c',
      'border:2px solid #0b0c0c',
      'padding:16px',
      'font:16px/1.4 "GDS Transport", Arial, sans-serif',
      'box-shadow:0 4px 16px rgba(0,0,0,.3)',
    ].join(';');

    const heading = document.createElement('h2');
    heading.textContent = 'DVSA Quick Fill';
    heading.style.cssText = 'margin:0 0 8px;font-size:19px;font-weight:700;';
    panel.appendChild(heading);

    if (note) {
      const noteNode = document.createElement('p');
      noteNode.textContent = note;
      noteNode.style.cssText = 'margin:0 0 12px;color:#505a5f;font-size:14px;';
      panel.appendChild(noteNode);
    }

    const inputs = {};

    FIELDS.forEach(function (spec) {
      const label = document.createElement('label');
      label.textContent = spec.label;
      label.style.cssText = 'display:block;margin:0 0 4px;font-size:14px;font-weight:700;';

      const input = document.createElement('input');
      input.type = 'text';
      input.value = details[spec.key] || '';
      input.disabled = locked;
      input.style.cssText =
        'width:100%;box-sizing:border-box;margin:0 0 12px;padding:6px 8px;border:2px solid #0b0c0c;font:16px "GDS Transport", Arial, sans-serif;';

      inputs[spec.key] = input;
      panel.appendChild(label);
      panel.appendChild(input);
    });

    if (locked) {
      const lockNote = document.createElement('p');
      lockNote.textContent = 'Details are baked into this build of the script. Edit the script to change them.';
      lockNote.style.cssText = 'margin:0 0 12px;color:#505a5f;font-size:13px;';
      panel.appendChild(lockNote);
    }

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:8px;';

    const save = document.createElement('button');
    save.type = 'button';
    save.textContent = locked ? 'Fill now' : 'Save and fill';
    save.style.cssText =
      'flex:1;background:#00703c;color:#fff;border:0;padding:8px 10px;font:16px "GDS Transport", Arial, sans-serif;cursor:pointer;';
    save.addEventListener('click', function () {
      if (!locked) {
        saveDetails({
          licence: inputs.licence.value.trim(),
          theory: inputs.theory.value.trim(),
        });
      }
      panel.remove();
      fill({ force: true, submit: false });
    });

    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = 'Close';
    close.style.cssText =
      'background:#f3f2f1;color:#0b0c0c;border:0;padding:8px 10px;font:16px "GDS Transport", Arial, sans-serif;cursor:pointer;';
    close.addEventListener('click', function () {
      panel.remove();
    });

    row.appendChild(save);
    row.appendChild(close);
    panel.appendChild(row);

    if (!locked) {
      const forget = document.createElement('button');
      forget.type = 'button';
      forget.textContent = 'Forget saved details';
      forget.style.cssText =
        'margin-top:10px;background:none;border:0;padding:0;color:#d4351c;font:14px "GDS Transport", Arial, sans-serif;text-decoration:underline;cursor:pointer;';
      forget.addEventListener('click', function () {
        clearDetails();
        panel.remove();
        toast('Saved details cleared');
      });
      panel.appendChild(forget);
    }

    document.body.appendChild(panel);
    if (!locked) inputs.licence.focus();
  }

  // -------------------------------------------------------------- wiring up

  document.addEventListener(
    'keydown',
    function (event) {
      if (!event.ctrlKey && !event.metaKey) return;

      if (event.shiftKey && (event.key === 'D' || event.key === 'd')) {
        event.preventDefault();
        openPanel('');
        return;
      }

      if (event.key === 'Enter') {
        event.preventDefault();
        fill({ force: true, submit: true });
        return;
      }

      if (event.shiftKey && (event.key === 'F' || event.key === 'f')) {
        event.preventDefault();
        fill({ force: true, submit: false });
      }
    },
    true
  );

  function autofill() {
    const fields = findFields();
    if (!fields.licence && !fields.theory) return;
    if (!loadDetails()) return;
    fill({ force: false, submit: false });
  }

  autofill();

  // The service moves between steps without a full page load, so watch for the
  // form turning up later.
  let pending = null;
  const observer = new MutationObserver(function () {
    window.clearTimeout(pending);
    pending = window.setTimeout(autofill, 300);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
