# Under-desk power bank tray

A printable cradle that screws to the underside of a desk. The power bank
slides in end-on from the front, lies flat on two shelves, and clicks in behind
a pair of sprung arms.

![preview](preview.png)

Built for an **83 x 165 x 52.7 mm** power bank, lying flat with its 52.7 x 83
end facing the front of the desk - so the ports and display face out of the
open mouth where you can reach them, and the long axis runs back under the desk.

This is the [mini PC mount](../under-desk-minipc-mount/) re-parameterised: same
tray, same latch idea, same checks. What changed is below.

## Dimensions

| | mm |
| --- | --- |
| Pocket (W x D x H) | 84.6 x 166 x 53.9 |
| Body (W x D x H) | 90.6 x 179.5 x 60.9 |
| Overall, including mounting pads | 118.6 x 179.5 x 60.9 |
| Drop below the desk | 60.9 |
| Screw pattern | 104.6 across x 119.5 along |
| Material | 113 cm3 solid (~100 g as printed) |

Clearance is 0.8 mm each side, 1.2 mm above and 1 mm front-to-back.

## What changed from the mini PC mount

- **Shorter arms need a different spring.** The latch arms sweep in from the
  shelves to the middle of the mouth, and a narrower bay gives them less run.
  Sweeping at 30 degrees instead of 40 buys some length back, and the section
  drops from 16 x 5 to 12 x 3 mm. That lands the click at 0.2-1.0 kgf for the
  pair, at 5-12 MPa at the root - the same margin the mini PC has.
- **Barbs clear a 15 mm corner radius**, declared in the model as
  `MAX_CORNER_R` and enforced by an assert and by the check. A power bank is a
  much squarer brick than a Mac mini, so the real margin is 22 mm.
- **The rear opening is a vent, not a port cutout.** Your ports face forward
  out of the mouth, so the back only needs to breathe: 60 x 34 mm.
- **Barb 3.5 -> 3 mm**, since a power bank's bottom front edge has a much
  smaller radius to bite past than a Mac mini's.

Everything else - the honeycomb vents, the mounting pads, the square barb
faces, the print orientation - is unchanged, and the vent fields resized
themselves from the new box.

## Airflow

A power bank pushing 100 W gets warm. Open bottom, open front, a 60 x 34 mm
rear vent, and the vent lattice through the top plate and both side walls:
49 cells overhead (~6,300 mm2 open) and 23 per side (~3,000 mm2 each).

## Printing

Print `under-desk-powerbank-tray-print.stl` - the same solid rolled onto its
back face, which is what makes it support-free.

| | |
| --- | --- |
| Bed footprint | 118.6 x 60.9 mm, 179.5 mm tall |
| Supports | none |
| Material | PETG or ASA - a power bank under load runs warm |
| Layer height | 0.2 mm |
| Walls | 4 perimeters |
| Infill | 25% |

179.5 mm is a tall print. It is stable on a 118.6 x 60.9 footprint, but if your
printer is fussy about height, this is the part to add a brim to.

## Mounting

Four **#8 or M4 flat-head wood screws**, on a 104.6 x 119.5 mm pattern. Same as
the mini PC mount: pilot 2.5-3 mm, screws no longer than
`6.5 mm + desk thickness - 3 mm`, and use a hand screwdriver or a bit extension
rather than a drill chuck - the screws sit 7 mm out from a wall that hangs
60.9 mm down.

Slide the bank in until the arms click. To take it out, reach under and press
both arms down through the open bottom, then pull.

## Files

| file | what it is |
| --- | --- |
| `under_desk_powerbank_tray.scad` | the model - every dimension is a parameter |
| `under-desk-powerbank-tray-print.stl` | ready to slice, back face on the bed |
| `under-desk-powerbank-tray.stl` | as-designed orientation |
| `build.sh` | render both STLs, then verify and re-render the preview |
| `verify.py` | checks the exported STL against the fit and print rules |
| `render_previews.py` | regenerates `preview.png` |

## Changing it

Edit the parameter block and run `./build.sh`.

```
mesh        watertight, one connected solid, consistent winding
envelope    118.6 x 179.5 x 60.9 mm
fit         seated bank clears the frame, 1.20 mm of headroom
insertion   slide-in path is clear apart from the barbs
latches     barbs stand 3.0 mm proud at x 8-20 mm, 72 mm2 of catch, air to duck
retention   0.9 mm slide-out is free travel, 1.5 mm is stopped
vents       49 top cells, 23 per side wall, 4 screws, 1 port = 100 holes
fasteners   4 bored through, pad solid around each, driver reaches every head
print       sits on z = 0, largest unsupported patch 36 mm2 (a barb face)
```

## Notes and limits

- A 25,000 mAh brick this size runs 600-900 g. The tray is fine with that - it
  was sized for a 2 kg device - but do drive all four screws into something
  solid, not into a 6 mm drawer bottom.
- Give it air. A bank charging at full tilt under a desk with no airflow will
  throttle; the vents help, but do not box it in further.
- If your bank is wedge-shaped or has a rubber foot strip, measure its thickest
  point for `BANK_H`.
