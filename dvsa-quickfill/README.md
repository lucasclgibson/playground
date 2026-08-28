# Jacks Spicy Test Booker

Two ways into the same job: getting through the DVSA driving test service
without typing a licence number, a theory pass number and a card number by hand
every single time.

| | What it is | Where it runs |
| --- | --- | --- |
| `extension/` | Chrome extension with a full-height side panel and one-click copy | Desktop Chrome and Edge |
| `dvsa-quickfill.user.js` | Userscript that fills the sign-in form | iPhone Safari, and desktop browsers with a userscript manager |

Neither one checks for slots or books anything. They fill and copy — the
booking is still yours to do.

> **Chrome extensions do not run on iPhone.** Chrome for iOS has no extension
> support at all, and Safari's extensions have to be compiled and shipped
> through the App Store with Xcode. So the side panel is a desktop tool. On the
> phone, the userscript is still the answer, and it still handles the licence
> and theory numbers. See [On the phone](#on-the-phone) below.

## The Chrome extension

A side panel pinned to the right of the browser, full height, listing every
detail with one click to copy:

- Driving licence number
- Theory test pass number
- Name on card, card number, expiry date, security code

Card details are entered in the extension's settings and stored on that
computer.

### Install

1. Open `chrome://extensions` and turn on **Developer mode** (top right).
2. Click **Load unpacked** and choose the `extension/` folder.
3. Click the chilli icon in the toolbar, then **Add details**, and fill in the
   settings page.

### Using it

Go to <https://driverpracticaltest.dvsa.gov.uk/application>. The panel becomes
available on any DVSA page; open it with the toolbar icon, with
**Ctrl/Cmd + Shift + Y**, or with the **Test Booker** button the extension puts
on the page. Once open it stays open as you move through the booking.

- **Click any row** to copy that value.
- **Press 1 to 6** to copy the row with that number — quickest of the lot.
- Card number and security code are **masked** until you click the eye, so the
  panel can sit open next to the form without a card number on display.
- **Clear clipboard** wipes it once you're done.

The licence and theory numbers also fill themselves into the sign-in form, as
before.

What gets copied is the value the form wants, not what's on screen: the card
number copies as bare digits, without the spaces that make it readable in the
panel.

### Where the details live

`chrome.storage.local`, on that machine, in that browser profile. Deliberately
not `chrome.storage.sync`, which would push a card number through a Google
account and onto every computer signed into it.

Two things worth knowing before putting a card in:

- **Anyone who can use that browser profile can read the card back.** There is
  no master password. It is roughly as safe as the machine and its login are.
- Chrome's own saved-cards feature and a password manager both do this job with
  encryption at rest. This extension exists because it puts everything in one
  place next to the form, not because it protects the card better.

The card details never enter the DVSA page. The side panel runs on the
extension's own origin, so the numbers live somewhere the website cannot reach;
the content script that touches the page only ever reads the licence and theory
numbers. That separation is deliberate — a test asserts the page script doesn't
so much as name a card field.

The extension asks for two permissions, `storage` and `sidePanel`, and access
to `dvsa.gov.uk` and nothing else. Extension pages are barred from making
network requests at all (`connect-src 'none'`), so nothing can be sent anywhere
even by accident.

## On the phone

Install the userscript with the **[Userscripts](https://apps.apple.com/app/userscripts/id1463298887)**
app (free) — Tampermonkey and Violentmonkey don't exist for iOS Safari. Then
**Settings → Apps → Safari → Extensions → Userscripts → On**, and set
**dvsa.gov.uk** to **Always Allow**. Missing that last step is why it looks
broken when it isn't.

In Safari, tap the puzzle-piece icon → **Userscripts → New → New Script**, and
paste in `dvsa-quickfill.user.js`.

The sign-in fields then fill on load. A floating button fills and signs in on a
tap, and press-and-hold opens the panel to change the saved numbers.

To skip the setup:

```sh
./make-personal.sh <driving-licence-number> <theory-test-pass-number>
```

That writes `dvsa-quickfill.personal.user.js` with the numbers already in it.
It's gitignored and should stay that way — a licence number is personal data
and doesn't belong in a repository. There is deliberately no card equivalent:
on the phone a script's values sit in the page's own context, which is exactly
where card details shouldn't be.

## Tests

```sh
node test/extension.js   # Chrome extension, loaded into a real browser profile
node test/run.js         # userscript, under iPhone emulation
```

`test/extension.js` drives the options page and the side panel: validation,
masking, what lands on the clipboard, the permission surface, and that the
content script never reaches for a card field. `test/run.js` covers the
userscript's autofill, gestures and field matching.

Both need Playwright, already on this machine at
`/opt/node22/lib/node_modules/playwright`. The extension tests use
`channel: 'chromium'` because extensions don't load in the headless shell.

## Keeping it working

The DVSA markup changes now and again. Rather than pinning to element ids, the
matcher (`extension/fields.js`, mirrored in the userscript) scores every text
input against its id, name, placeholder, `aria-label` and visible label, and
takes the two best. A redesign is usually a one-keyword fix.

Icons are generated: edit `extension/icons/icon.svg` (and `icon-small.svg`,
a simplified version for 16 and 32px, where the detailed one turns to mush) and
run `node extension/icons/render.js`.
