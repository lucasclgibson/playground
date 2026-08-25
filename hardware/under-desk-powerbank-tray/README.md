# Under-desk power bank tray

A printable cradle that screws to the underside of a desk. The power bank
slides in end-on from the front and lies flat on two shelves. Nothing latches
it: it is a heavy brick in a horizontal tray, so it goes in and out from the
front and that is the whole interaction. The far end is closed off. One side
wall is slotted through so the band on the brick's side can pass.

![preview](preview.png)

Built for an **83 x 165 x 52.7 mm** power bank, lying flat with its 52.7 x 83
end facing the front of the desk - so the ports and display face out of the
open mouth where you can reach them, and the long axis runs back under the desk.

This is the [mini PC mount](../under-desk-minipc-mount/) re-parameterised: same
tray, same shelves, same checks. What changed is below.

## Dimensions

| | mm |
| --- | --- |
| Pocket (W x D x H) | 84.6 x 166 x 53.9 |
| Body (W x D x H) | 90.6 x 172.5 x 60.9 |
| Overall, including mounting pads | 118.6 x 172.5 x 60.9 |
| Drop below the desk | 60.9 |
| Screw pattern | 104.6 across x 112.5 along |
| Band slot | 19.2 mm across x 35.6 mm in from the mouth, left wall |
| Material | 112 cm3 solid (~100 g as printed) |

Clearance is 0.8 mm each side, 1.2 mm above and 1 mm front-to-back, and 0.6 mm
all round the band.

## The band slot

The brick carries a raised band on one side: **18 mm across its 52.7 mm face,
running 32 mm down from the top**. Laid flat in the tray that face is vertical
and the top of the brick points out of the mouth, so the band ends up on a side
wall running back from the opening. The wall is cut clean through there rather
than merely dished - the band stands proud of the brick by an unknown amount,
and leaving any wall outboard of it would just be a guess.

Two things about it are worth knowing:

- **The slot is 35.6 mm deep, not 32.** The 32 mm is measured on the brick, and
  the brick's top face sits 4 mm behind the mouth (`FRONT_LIP` 3 mm plus
  `GAP_BACK` 1 mm). Cutting a literal 32 mm from the mouth would leave the back
  3.4 mm of the band buried under solid wall and the brick would stop short of
  the rear wall. The model works back from the seated brick instead, so
  `BAND_DEPTH = 32` stays the number you measured.
- **It opens into the mouth**, so it is a notch in the front opening rather than
  a hole through a closed wall. The wall closes up again behind it and still
  carries its shelf, the top plate is untouched, and the part is one solid.

`BAND_SIDE = 1` puts it on the **left as you face the open end**. Set it to `-1`
for the right - that is the whole change; the vent field follows it across.
`BAND_W`, `BAND_DEPTH` and `BAND_CLR` are the band's own numbers, and `BAND_OFF`
shifts the slot off the middle of the brick's thickness if the band is not
centred on that face. The asserts will stop you if the slot would break into a
shelf or the top plate.

The banded wall's vent field stops one rib short of the slot, so that wall
carries 18 cells against the other's 20.

## What changed from the mini PC mount

- **No latch.** The sprung arms and barbs are gone. A 600-900 g brick lying in
  a horizontal tray is not going anywhere on its own, and you asked for a pure
  slide in and out - so the check that used to prove the barbs stopped it now
  proves the opposite: the whole travel, in and out, is clear.
- **The far end is closed.** No rear cutout at all. Your ports face forward out
  of the mouth, so the back does not need to open for anything, and a solid
  back wall is a better first layer too.
- **Front lip 10 -> 3 mm.** It only existed to carry the barbs; now it is just
  a margin for the lead-in chamfer. That is 7 mm off the depth.

Everything else - the honeycomb vents, the mounting pads, the shelves, the
print orientation - is unchanged, and the vent fields resized themselves from
the new box.

## Airflow

A power bank pushing 100 W gets warm, and the closed back means it breathes
through the sides and the mouth. Open bottom, open front, and the vent lattice
through the top plate and both side walls: 49 cells overhead (~6,300 mm2 open),
20 in the plain wall and 18 in the banded one (~2,600 and ~2,300 mm2). The band
slot itself is another ~690 mm2 of opening right at the mouth. If yours runs
hot, the back wall is the place to put an opening back - it costs nothing
structurally.

## Printing

Print `under-desk-powerbank-tray-print.stl` - the same solid rolled onto its
back face, which is what makes it support-free.

| | |
| --- | --- |
| Bed footprint | 118.6 x 60.9 mm, 172.5 mm tall |
| Supports | none |
| Material | PETG or ASA - a power bank under load runs warm |
| Layer height | 0.2 mm |
| Walls | 4 perimeters |
| Infill | 25% |

172.5 mm is a tall print. It is stable on a 118.6 x 60.9 footprint, but if your
printer is fussy about height, this is the part to add a brim to.

## Mounting

Four **#8 or M4 flat-head wood screws**, on a 104.6 x 112.5 mm pattern. Same as
the mini PC mount: pilot 2.5-3 mm, screws no longer than
`6.5 mm + desk thickness - 3 mm`, and use a hand screwdriver or a bit extension
rather than a drill chuck - the screws sit 7 mm out from a wall that hangs
60.9 mm down.

Slide the bank in from the front until it meets the back wall, band-side to your
left, the band running down the slot. Pull it out the same way. If your band is
on the other side, flip `BAND_SIDE` and re-run `./build.sh` rather than mounting
the tray upside down - the mounting pads and the shelves are not symmetric top
to bottom.

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
envelope    118.6 x 172.5 x 60.9 mm
fit         seated bank clears the frame, 1.20 mm of headroom
slide       slides the whole way in and out, far end closed, 24 mm of shelf
band        18 x 32 mm band clears seated and all the way out, wall closes
            again 35.6 mm in, slot 16.8 mm clear of the shelf and 18.0 of the top
vents       49 top, 20 plain wall, 18 banded wall, 4 screws, closed = 91 holes
fasteners   4 bored through, pad solid around each, driver reaches every head
print       sits on z = 0, largest unsupported patch 17 mm2 (a screw bore)
```

## Notes and limits

- A 25,000 mAh brick this size runs 600-900 g. The tray is fine with that - it
  was sized for a 2 kg device - but do drive all four screws into something
  solid, not into a 6 mm drawer bottom.
- Give it air. A bank charging at full tilt under a desk with no airflow will
  throttle; the vents help, but with the back closed there is less through-flow
  than there was, so do not box it in further.
- Nothing stops it sliding out but its own weight and the friction of the
  shelves. That is deliberate. If you ever want a stop, the mini PC mount's
  sprung arms drop straight back in - they are the same tray.
- If your bank is wedge-shaped or has a rubber foot strip, measure its thickest
  point for `BANK_H`.
- The band slot is sized from the band, not from how far it sticks out - the cut
  goes right through the wall, so a strap loop, a rubber band or a moulded rib
  all clear it equally. What it will not tolerate is the band sitting off-centre
  on the 52.7 mm face: that is what `BAND_OFF` is for, and a check proves the
  slot still misses the shelf and the top plate wherever you put it.
