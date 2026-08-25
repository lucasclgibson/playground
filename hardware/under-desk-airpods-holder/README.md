# Under-desk AirPods Pro case tray

A shallow open-front tray that screws to the underside of a desk. The case lies
flat, big face to the desk, and slides in and out from the front. A thumb slot
runs up the middle of the floor so you can hook a thumb under the case and drag
it out.

![preview](preview.png)

## Dimensions

| | mm |
| --- | --- |
| Overall, including mounting pads | 92.4 x 50.3 x 27.7 |
| Pocket | 61.4 wide x 45.8 deep x 22.2 |
| Drop below the desk | 27.7 |
| Screw centres | 79.4 apart |
| Material | 32 cm3 (~20 g) |

Clearance is **0.4 mm each side, 0.5 mm above and 0.6 mm front-to-back** - a
snug slip fit. The case is a known size, so there is no reason to leave slop;
if your printer runs tight, `GAP_SIDE` is the one to open up.

## The thumb slot

A 24 x 34 mm channel up the middle of the floor, open at the mouth. It reaches
34 mm back into a 45 mm case, so a thumb goes in at the mouth, gets behind the
middle of the case and drags it forward.

It is cut against the floor's other job. The case's section is a stadium, so
the face it lies on is flat only across its middle 38.9 mm, and the slot eats
24 of that:

| slot width | flat floor each side |
| --- | --- |
| 20 mm | 9.45 mm |
| **24 mm (used)** | **7.45 mm** |
| 28 mm | 5.45 mm |
| 32 mm | 3.45 mm - resting on an edge |

24 mm admits a thumb and still leaves the case sitting on two 7.5 mm strips of
flat floor rather than balancing on the curve. Behind the slot the floor is
solid. The check measures both, and asserts each strip is at least 4 mm.

## The case, and what is knowable about it

Apple publishes the AirPods Pro 2 charging case as **45.2 x 60.6 x 21.7 mm**,
50.8 g. It does not publish the radii, and neither does anyone else.

Lying flat, that barely matters - a square pocket takes the case whatever its
corners do. It shows up in exactly one place, and the section above is it: the case's
cross-section is a stadium, so it only rests on the flat middle 38.9 mm of its
face. That is what sets how wide the thumb slot can be, and why the floor is a
floor rather than a pair of shelves at the edges - shelves would meet the case
out on the curve, on two lines, and let it rock.

## Why flat rather than on end

Stood on end the case has to be held up against gravity, which needs a snap,
and a socket that shallow has no wall length to spring with - a 14 mm wall is
some 30 N/mm, so a 1 mm catch would take more force to fit than the case can
survive. Lying flat, the floor does the work and there is nothing to latch.

## Printing

Print `airpods-holder.stl` as it comes - it is exported on its back face, which
is how it prints. Everything is walls running along the build direction; the
only thing left facing down is the top of each screw bore, a 5 mm hole printed
on its side. 22 mm2 of the part, and nothing anywhere else.

| | |
| --- | --- |
| Bed footprint | 92.4 x 27.7 mm, 50.3 mm tall |
| Supports | none |
| Material | PLA or PETG |
| Layer height | 0.2 mm |
| Walls | 3 perimeters |
| Infill | 20% |

## Mounting

Two **#8 or M4 flat-head wood screws** on a 79.4 mm pattern, countersunk flush
into the side pads. Pilot 2.5-3 mm; screws no longer than
`5 mm + desk thickness - 3 mm`. The pads are outboard so a driver reaches the
screws from below without going into the tray.

## Files

| file | what it is |
| --- | --- |
| `under_desk_airpods_holder.scad` | the model - every dimension is a parameter |
| `airpods-holder.stl` | ready to slice |
| `build.sh` | render, verify, re-render the preview |
| `verify.py` | checks the exported STL against the fit and print rules |
| `render_previews.py` | regenerates `preview.png` |

## Changing it

Edit the parameter block and run `./build.sh`.

```
mesh        one watertight solid, on z = 0 on its back, 92.4 x 27.7 x 50.3 mm
slide       slides the whole way in and out, 0.5 mm clear, far end closed
support     14.9 mm of flat floor either side of the slot, solid behind it
            slot open all 34 mm from the mouth, past the middle of the case
fasteners   2 holes bored through, pads solid, driver reaches both heads
print       the screw bores are the only overhang
```

## Notes and limits

- Sized for the **2nd gen / USB-C** case. The 1st gen Pro case is the same
  size. The standard AirPods case is a different shape and will not fit.
- With the case in a silicone skin, add the skin's thickness to `GAP_SIDE` and
  `GAP_TOP`. The fit is snug enough now that a skin will not go in on top of it.
- Nothing latches it. The tray is horizontal, so gravity is not trying to pull
  the case out - only a knock from the front would, and the case is 50 g.
