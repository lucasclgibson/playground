// ==UserScript==
// @name         DVSA Quick Fill
// @namespace    https://github.com/lucasclgibson/playground
// @version      2.0.0
// @description  Fills the DVSA driving test sign-in form from details saved on your device. Built for iPhone Safari, works on desktop too.
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
  const PROMPTED_KEY = 'dvsa-quickfill:prompted';
  const PANEL_ID = 'dvsa-quickfill-panel';
  const BUTTON_ID = 'dvsa-quickfill-button';
  const TOAST_ID = 'dvsa-quickfill-toast';
  const LONG_PRESS_MS = 550;

  const FIELDS = [
    {
      key: 'licence',
      label: 'Driving licence number',
      hints: ['driving-licence', 'drivinglicence', 'driving licence', 'licence', 'license', 'dln'],
      penalties: ['instructor', 'trainer'],
    },
    {
      key: 'theory',
      label: 'Theory pass number or booking reference',
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
      if (button.disabled || button.id === BUTTON_ID || button.closest('#' + PANEL_ID)) continue;
      const text = (button.textContent || button.value || '').toLowerCase();
      for (let j = 0; j < wanted.length; j += 1) {
        if (text.indexOf(wanted[j]) !== -1) return button;
      }
    }

    return (
      buttons.find(function (button) {
        return !button.disabled && button.type === 'submit' && button.id !== BUTTON_ID;
      }) || null
    );
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
      openPanel('Enter the two numbers once. They stay on this device.');
      return 0;
    }

    const fields = findFields();
    let filled = 0;

    FIELDS.forEach(function (spec) {
      const input = fields[spec.key];
      const value = details[spec.key];
      if (!input || !value) return;
      // Don't clobber something already typed unless we were asked to.
      if (input.value && !options.force) return;
      setValue(input, value);
      flash(input);
      filled += 1;
    });

    const alreadyComplete =
      filled === 0 &&
      FIELDS.every(function (spec) {
        return !fields[spec.key] || fields[spec.key].value;
      }) &&
      Boolean(fields.licence || fields.theory);

    if (filled === 0 && !alreadyComplete) {
      toast('Nothing to fill on this page');
      return 0;
    }

    const submit = findSubmit();
    if (submit && options.submit) {
      toast('Signing in');
      submit.click();
      return filled;
    }

    if (submit) submit.focus();
    // Name the real button rather than guessing: the service calls it
    // "Continue" on some steps and "Sign in" on others.
    const buttonLabel = submit ? (submit.textContent || submit.value || '').trim().split('\n')[0] : '';
    toast(filled ? (buttonLabel ? 'Filled — tap ' + buttonLabel : 'Filled') : 'Already filled in');
    return filled;
  }

  function flash(input) {
    const previous = input.style.boxShadow;
    input.style.boxShadow = '0 0 0 3px #00703c';
    window.setTimeout(function () {
      input.style.boxShadow = previous;
    }, 900);
  }

  // -------------------------------------------------------- the tap target

  // iPhone has no keyboard shortcuts to lean on, so the floating button is the
  // primary control: tap to fill and sign in, hold to edit the saved details.
  // It only appears on pages that actually have the sign-in fields.
  function ensureButton(shouldShow) {
    const existing = document.getElementById(BUTTON_ID);

    if (!shouldShow) {
      if (existing) existing.remove();
      return;
    }
    if (existing) return;

    const button = document.createElement('button');
    button.id = BUTTON_ID;
    button.type = 'button';
    button.setAttribute('aria-label', 'Fill DVSA sign-in details and sign in. Press and hold to edit them.');
    button.style.cssText = [
      'position:fixed',
      'right:16px',
      'bottom:calc(16px + env(safe-area-inset-bottom, 0px))',
      'z-index:2147483646',
      'min-height:56px',
      'padding:10px 20px',
      'background:#00703c',
      'color:#fff',
      'border:0',
      'border-radius:28px',
      'box-shadow:0 4px 14px rgba(0,0,0,.35)',
      'font:600 17px/1.2 -apple-system, "GDS Transport", Arial, sans-serif',
      'text-align:center',
      'cursor:pointer',
      '-webkit-touch-callout:none',
      '-webkit-user-select:none',
      'user-select:none',
      '-webkit-tap-highlight-color:transparent',
      'touch-action:manipulation',
    ].join(';');

    const main = document.createElement('span');
    main.textContent = 'Fill & sign in';
    main.style.cssText = 'display:block;';

    const hint = document.createElement('span');
    hint.textContent = 'hold to edit';
    hint.style.cssText = 'display:block;font-size:12px;font-weight:400;opacity:.85;margin-top:2px;';

    button.appendChild(main);
    button.appendChild(hint);

    let timer = null;
    let handledAsLongPress = false;

    function startPress() {
      handledAsLongPress = false;
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        handledAsLongPress = true;
        button.style.transform = 'scale(.96)';
        openPanel('');
      }, LONG_PRESS_MS);
    }

    function endPress(activate) {
      window.clearTimeout(timer);
      button.style.transform = '';
      if (activate && !handledAsLongPress) {
        fill({ force: true, submit: true });
      }
    }

    button.addEventListener('pointerdown', function (event) {
      event.preventDefault();
      startPress();
    });
    button.addEventListener('pointerup', function (event) {
      event.preventDefault();
      endPress(true);
    });
    button.addEventListener('pointercancel', function () {
      endPress(false);
    });
    button.addEventListener('pointerleave', function () {
      endPress(false);
    });
    // Belt and braces for anything that reports no pointer events at all.
    button.addEventListener('click', function (event) {
      event.preventDefault();
      if (!window.PointerEvent) fill({ force: true, submit: true });
    });

    document.body.appendChild(button);
  }

  // ------------------------------------------------------------------- UI

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
      'bottom:calc(88px + env(safe-area-inset-bottom, 0px))',
      'z-index:2147483647',
      'max-width:calc(100vw - 32px)',
      'background:#0b0c0c',
      'color:#fff',
      'padding:10px 16px',
      'border-radius:20px',
      'font:16px/1.3 -apple-system, "GDS Transport", Arial, sans-serif',
      'text-align:center',
      'box-shadow:0 2px 8px rgba(0,0,0,.35)',
      'pointer-events:none',
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
      'left:50%',
      'transform:translateX(-50%)',
      'top:calc(16px + env(safe-area-inset-top, 0px))',
      'z-index:2147483647',
      'width:min(360px, calc(100vw - 24px))',
      'box-sizing:border-box',
      'background:#fff',
      'color:#0b0c0c',
      'border:2px solid #0b0c0c',
      'border-radius:8px',
      'padding:16px',
      'font:16px/1.4 -apple-system, "GDS Transport", Arial, sans-serif',
      'box-shadow:0 8px 24px rgba(0,0,0,.35)',
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
      input.autocapitalize = 'characters';
      input.autocorrect = 'off';
      input.spellcheck = false;
      // 16px keeps iOS Safari from zooming the page when the field is focused.
      input.style.cssText =
        'width:100%;box-sizing:border-box;margin:0 0 12px;padding:10px;border:2px solid #0b0c0c;border-radius:4px;font:16px -apple-system, "GDS Transport", Arial, sans-serif;';

      inputs[spec.key] = input;
      panel.appendChild(label);
      panel.appendChild(input);
    });

    if (locked) {
      const lockNote = document.createElement('p');
      lockNote.textContent = 'These are baked into this build of the script. Edit the script to change them.';
      lockNote.style.cssText = 'margin:0 0 12px;color:#505a5f;font-size:13px;';
      panel.appendChild(lockNote);
    }

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:8px;';

    const buttonStyle =
      'min-height:44px;border:0;border-radius:4px;padding:10px 14px;font:600 16px -apple-system, "GDS Transport", Arial, sans-serif;cursor:pointer;';

    const save = document.createElement('button');
    save.type = 'button';
    save.textContent = locked ? 'Fill now' : 'Save and fill';
    save.style.cssText = buttonStyle + 'flex:1;background:#00703c;color:#fff;';
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
    close.style.cssText = buttonStyle + 'background:#f3f2f1;color:#0b0c0c;';
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
        'margin-top:12px;min-height:44px;width:100%;background:none;border:0;padding:0;color:#d4351c;font:14px -apple-system, "GDS Transport", Arial, sans-serif;text-decoration:underline;cursor:pointer;';
      forget.addEventListener('click', function () {
        clearDetails();
        panel.remove();
        toast('Saved details cleared');
      });
      panel.appendChild(forget);
    }

    document.body.appendChild(panel);
  }

  // -------------------------------------------------------------- wiring up

  // Desktop convenience. On iPhone the floating button does all of this.
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

  function refresh() {
    const fields = findFields();
    const onSignInPage = Boolean(fields.licence || fields.theory);

    ensureButton(onSignInPage);
    if (!onSignInPage) return;

    if (!loadDetails()) {
      let prompted = null;
      try {
        prompted = window.sessionStorage.getItem(PROMPTED_KEY);
        window.sessionStorage.setItem(PROMPTED_KEY, '1');
      } catch (err) {
        prompted = '1';
      }
      if (!prompted && !document.getElementById(PANEL_ID)) {
        openPanel('Enter the two numbers once. They stay on this device.');
      }
      return;
    }

    fill({ force: false, submit: false });
  }

  refresh();

  // The service moves between steps without a full page load, so watch for the
  // form turning up later.
  let pending = null;
  const observer = new MutationObserver(function (records) {
    const ours = records.every(function (record) {
      return (
        record.target.id === BUTTON_ID ||
        record.target.id === TOAST_ID ||
        (record.target.closest && record.target.closest('#' + PANEL_ID))
      );
    });
    if (ours) return;
    window.clearTimeout(pending);
    pending = window.setTimeout(refresh, 300);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
