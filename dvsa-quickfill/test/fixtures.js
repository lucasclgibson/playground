// Two mocks of the DVSA sign-in step. The first mirrors the markup as it looks
// today; the second strips the helpful ids so only the visible labels are left,
// which is roughly what happens whenever the service is rebuilt.
const LABELLED = `
  <div class="govuk-form-group">
    <label class="govuk-label" for="driving-licence-number">Driving licence number</label>
    <span id="dln-hint" class="govuk-hint">Enter the 16 characters shown on your licence</span>
    <input class="govuk-input" id="driving-licence-number" name="username" type="text" aria-describedby="dln-hint">
  </div>
  <div class="govuk-form-group">
    <label class="govuk-label" for="application-reference-number">Theory test pass number or booking reference</label>
    <input class="govuk-input" id="application-reference-number" name="password" type="text">
  </div>
  <button class="govuk-button" type="submit">Continue</button>
`;

const ANONYMOUS = `
  <div class="govuk-form-group">
    <label class="govuk-label" for="field-a">Driving licence number</label>
    <input class="govuk-input" id="field-a" name="f1" type="text">
  </div>
  <div class="govuk-form-group">
    <label class="govuk-label" for="field-b">Theory test pass number</label>
    <input class="govuk-input" id="field-b" name="f2" type="text">
  </div>
  <div class="govuk-form-group">
    <label class="govuk-label" for="field-c">Postcode</label>
    <input class="govuk-input" id="field-c" name="f3" type="text">
  </div>
  <button class="govuk-button" type="submit">Sign in</button>
`;

function page(body) {
  // The viewport meta matters: every GOV.UK page ships one, and without it a
  // mobile browser lays out at 980px and scales down, which would make any
  // on-screen position assertion meaningless.
  return `<!doctype html><html><head><meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Change your driving test</title></head>
  <body><h1>Change your driving test</h1><form onsubmit="event.preventDefault();document.body.dataset.submitted='yes'">${body}</form></body></html>`;
}

// A page on the same site with nothing to fill — the floating button should
// stay out of the way here.
const UNRELATED = `
  <p>Your driving test is booked for 14 March.</p>
  <a class="govuk-link" href="/change">Change your test</a>
`;

module.exports = {
  LABELLED: page(LABELLED),
  ANONYMOUS: page(ANONYMOUS),
  UNRELATED: page(UNRELATED),
};
