# Under-desk AirPods Pro case holder

A socket that screws to the underside of a desk. Push the case up into it, pull
it down to take it out. One screw, straight up through the ceiling of the
socket - you drive it through the open mouth before the case goes in, so there
is no flange hanging off the side.

![preview](preview.png)

## The case, and what is knowable about it

Apple publishes the AirPods Pro 2 charging case as **45.2 x 60.6 x 21.7 mm**,
50.8 g. It does not publish the radii, and neither does anyone else - the
dimension drawings that exist give the bounding box and nothing more.

The ends look semicircular, which for a 21.7 mm depth would mean r = 10.85 -
the most rounded that bounding box can possibly be. That is exactly why the
pocket is **not** cut to it. A pocket at 10.85 fits only if the case really is
a perfect stadium; a case even slightly squarer is wider at its corners and
jams. Cutting the pocket smaller is the safe direction:

| pocket radius | fits a case whose corners are at least |
| --- | --- |
| 11.45 (stadium) | 10.85 mm - only a perfect stadium |
| 10.0 | 9.40 mm |
| **8.0 (used)** | **7.40 mm** |

At 8 mm the case drops in whether its ends are semicircular or noticeably
squarer, and the extra room at the corners is invisible once it is in.

## Dimensions

| | mm |
| --- | --- |
| Overall | 66.8 x 27.9 x 35 |
| Pocket | 61.8 x 22.9, 30 deep, 8 mm corners |
| Drop below the desk | 35 |
| Case left proud to grab | 15 |
| Material | 21 cm3 (~15 g) |

## How it holds

- **Socket** - swallows the top 30 mm of the case with 0.6 mm of clearance all
  round, so it cannot swing or rattle.
- **Sprung tongue** - a 14 mm tongue cut into the front wall carries a 1.2 mm
  bump that presses the case against the back of the pocket. That is the whole
  grip: about 6 N of push, so roughly 2.4 N of friction against a case that
  weighs 0.5 N - five times its weight. A plain friction fit would need the
  print to land on tolerance; a sprung one does not care, and if the print
  comes out a few tenths loose the bump simply sits further out.
- **One screw** - a #8 or M4 flat head, countersunk flush into the ceiling from
  inside. It sits directly over the case, so pushing the case in pushes
  straight through the screw and there is nothing to twist the holder round.

## Printing

Print `airpods-holder.stl` as it comes - it is exported ceiling-down, which is
how it prints. **Nothing in the part overhangs at all**: the desk face is the
first layer, the walls rise from it, the mouth is the open top, and the
countersink is a cone that opens upward.

| | |
| --- | --- |
| Bed footprint | 66.8 x 27.9 mm, 35 mm tall |
| Supports | none |
| Material | PLA or PETG |
| Layer height | 0.2 mm |
| Walls | 3 perimeters |
| Infill | 20% |

## Mounting

One **#8 or M4 flat-head wood screw**, 20-25 mm.

1. Hold the holder against the desk, mark through the hole, pilot drill 2.5-3 mm.
2. Drive the screw through the ceiling from inside the socket - a driver goes
   in through the open mouth easily.
3. Push the case up until the tongue clicks over it.

Pick a screw no longer than `5 mm + desk thickness - 3 mm`.

## Files

| file | what it is |
| --- | --- |
| `under_desk_airpods_holder.scad` | the model - every dimension is a parameter |
| `airpods-holder.stl` | ready to slice |
| `build.sh` | render, verify, re-render the preview |
| `verify.py` | checks the exported STL against the fit and print rules |
| `render_previews.py` | regenerates `preview.png` |

## Changing it

Edit the parameter block and run `./build.sh`. `GAP` is the clearance, `BUMP`
the grip, `DEPTH` how much of the case is swallowed. `POCKET_R` is the one to
leave alone unless you have measured your own case's corners - the check
`pocket takes the squarest case it claims` tests a case cut to exactly
`POCKET_R - GAP`, so raising the radius quietly narrows what fits.

```
mesh        one watertight solid, on z = 0 ceiling down, 66.8 x 27.9 x 35.0 mm
fit         takes the squarest case it claims and a fully rounded one
grip        tongue cut free either side, bump stands 1.2 mm into the pocket
fastener    hole bored through, ceiling solid around it, driver reaches it
support     nothing in the part overhangs at all
```

## Notes and limits

- Sized for the **2nd gen / USB-C** case. The 1st gen Pro case is 45.2 x 60.6 x
  21.7 as well, so it fits; the standard AirPods case is a different shape and
  will not.
- With a case in a silicone skin, add the skin's thickness to `GAP` - or just
  print it with `GAP = 1.2` and accept a looser hold on the bare case.
- The case hangs mouth-down, so its own lid faces the desk. Nothing falls out
  of it, but the USB-C port ends up at the exposed bottom, which is the right
  way round for charging it in place.
