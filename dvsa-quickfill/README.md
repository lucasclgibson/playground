# DVSA Quick Fill

A userscript that types the two numbers the DVSA driving test service asks for,
so you don't have to. Built for iPhone Safari first: the sign-in fields fill
themselves when the page loads, and a floating **Fill & sign in** button puts
the whole thing one thumb-tap away.

It only fills the form in front of you. It doesn't check for slots, poll the
service, or book anything.

## Install on iPhone

Safari on iOS supports extensions, so a userscript manager works — it's just a
different app from the desktop ones.

1. Install **[Userscripts](https://apps.apple.com/app/userscripts/id1463298887)**
   from the App Store (free, open source). Tampermonkey and Violentmonkey are
   not available for iOS Safari.
2. Open the Userscripts app once and pick a folder when it asks — iCloud Drive
   or On My iPhone, either is fine. That's where your scripts live.
3. Turn the extension on: **Settings → Apps → Safari → Extensions → Userscripts
   → On**, and set **dvsa.gov.uk** to **Allow**. Choosing *Always Allow* stops
   Safari asking again each visit. This step is the one people miss — without
   it the script never runs.
4. In Safari, open the DVSA page, tap the **puzzle-piece icon** in the address
   bar, choose **Userscripts → New → New Script**, then paste in the contents
   of `dvsa-quickfill.user.js` and save.

Then load the sign-in page. Both fields fill on their own.

## Using it

| Action | What happens |
| --- | --- |
| Open the sign-in page | Both fields fill automatically |
| Tap **Fill & sign in** | Fills and submits in one go |
| Press and hold the button | Opens the panel to change or clear the saved numbers |

The button only appears on pages that actually have the sign-in fields, so it
stays out of the way everywhere else.

On a desktop browser (Chrome, Firefox, Edge, Safari with Tampermonkey or
Violentmonkey) the same script gives you `Ctrl`/`Cmd` + `Enter` to fill and
submit, `Ctrl` + `Shift` + `F` to re-fill, and `Ctrl` + `Shift` + `D` for the
settings panel.

## Skipping the setup step

```sh
./make-personal.sh <driving-licence-number> <theory-test-pass-number>
```

That writes `dvsa-quickfill.personal.user.js` with the numbers already in it —
install that and there's nothing to type. The file is gitignored and should
stay that way: a driving licence number is personal data and doesn't belong in
a repository. The same goes for the browser-saved version, which lives in that
Safari profile only. Use a device you control, with a passcode on it.

## If you'd rather not install an extension

Two native fallbacks, in order of how well they work:

- **Text Replacement.** Settings → General → Keyboard → Text Replacement. Add
  the licence number with shortcut `zdl`, and the theory number with `ztp`.
  Typing the shortcut expands it. Works in every app, nothing to install, and
  syncs across your devices via iCloud.
- **Paste from Notes.** Slower, but fine as a stopgap.

Neither gives you the one-tap sign-in, but the Text Replacement trick removes
most of the typing and takes about a minute to set up.

## Keeping it working

The DVSA markup changes now and again. Rather than pinning to specific element
ids, the script scores every text input on the page against its id, name,
placeholder, `aria-label` and visible label, and fills the two best matches. If
a redesign ever breaks it, the fix is usually one new keyword in the `FIELDS`
list at the top of the script.

## Tests

```sh
node test/run.js
```

Runs the script against mock sign-in pages in a real browser (Playwright,
Chromium) under iPhone emulation: autofill, the tap and press-and-hold
gestures, tap-target size, the panel fitting a phone screen, the button hiding
itself on unrelated pages, plus the field matching and desktop shortcuts.
Playwright is already on this machine at
`/opt/node22/lib/node_modules/playwright`.
