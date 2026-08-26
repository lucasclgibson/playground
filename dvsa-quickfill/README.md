# DVSA Quick Fill

A userscript that types the two numbers you need for the DVSA driving test
service so you don't have to. When the sign-in page loads it fills in the
driving licence number and theory test pass number and puts the cursor on
**Continue** — so signing in is one keypress.

It only fills the form in front of you. It doesn't check for slots, poll the
service, or book anything.

## Install

1. Install a userscript manager: [Violentmonkey](https://violentmonkey.github.io/)
   or [Tampermonkey](https://www.tampermonkey.net/). Both are free and available
   for Chrome, Edge, Firefox and Safari.
2. Open `dvsa-quickfill.user.js`, copy the contents into a new script in the
   manager, and save.
3. Open the DVSA page. A panel appears asking for the two numbers. Enter them
   once and they're saved in your browser.

## Using it

| Action | What happens |
| --- | --- |
| Load the sign-in page | Both fields fill automatically, **Continue** gets focus, so `Enter` signs you in |
| `Ctrl` + `Enter` | Fill and submit in one go |
| `Ctrl` + `Shift` + `F` | Re-fill, overwriting anything already typed |
| `Ctrl` + `Shift` + `D` | Open the panel to change or clear the saved numbers |

On a Mac, `Cmd` works in place of `Ctrl`.

## Skipping the setup step

If you'd rather have the numbers already in the script:

```sh
./make-personal.sh <driving-licence-number> <theory-test-pass-number>
```

That writes `dvsa-quickfill.personal.user.js` — install that instead and it
works immediately, no panel. The file is gitignored, and should stay that way:
a driving licence number is personal data and doesn't belong in a repository.
The same goes for the browser-saved version — it lives in that browser profile
only, so use a device you control, not a shared one.

## Keeping it working

The DVSA markup changes now and again. Rather than pinning to one element id,
the script scores every text input on the page against its id, name,
placeholder, `aria-label` and visible label, and fills the two best matches. If
a redesign ever breaks it, the fix is usually a new keyword in the `FIELDS`
list at the top of the script.

## Tests

```sh
node test/run.js
```

Runs the script against mock sign-in pages in a real browser (Playwright,
Chromium) and checks the field matching, the fill, the focus and the keyboard
shortcuts. Requires Playwright — it's already on this machine at
`/opt/node22/lib/node_modules/playwright`.
