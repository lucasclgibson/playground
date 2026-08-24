# Under-desk mini PC mount

A printable cradle that screws to the underside of a desk. The mini PC slides
straight in from the front, sits on two shelves, and is held in by a pair of
ramped nubs. No brackets, no straps, no fasteners into the PC itself.

![preview](preview.png)

Built for a **129 x 129 x 45.5 mm** mini PC. Any other size is a three-number
edit at the top of the `.scad` file.

## Dimensions

| | mm |
| --- | --- |
| Pocket (W x D x H) | 131 x 130.5 x 47.5 |
| Body (W x D x H) | 137 x 144 x 56.5 |
| Overall, including mounting flanges | 177 x 144 x 56.5 |
| Drop below the desk | 56.5 |
| Screw pattern | 157 across x 80 along |
| Material | 154 cm3 solid (~115 g at 25% infill) |

Clearance is 1 mm each side, 2 mm above and 1.5 mm front-to-back, so a device
that measures a little over its spec still goes in.

## How it holds the PC

- **Bottom shelves** - two 12 mm lips carry the weight; the middle of the
  underside is open, so the intake fan is not covered.
- **Rear wall** - depth stop, with a 107 x 33 mm cutout so the rear ports and
  cables stay accessible.
- **Retention nubs** - a bump on each shelf just ahead of the PC. Pushing the
  PC in lifts it 1.5 mm over a shallow 21 degree ramp (there is 2 mm of
  headroom, so nothing has to flex) and it drops back down behind them. The
  back of each nub is a steeper 31 degree ramp: a firm pull gets the PC out,
  a knock or a tugged cable does not.
- **Airflow** - open bottom, open front, a 107 x 33 mm rear cutout, and an
  11 mm honeycomb through the top plate and both side walls: 77 cells
  overhead (~8,000 mm2 open) and 23 per side (~2,400 mm2 each).

## Printing

Print `under-desk-minipc-mount-print.stl`. It is the same solid rolled onto
its back face, which is what makes the part support-free: every wall runs
along the build direction, and the honeycomb is laid out flat-side-up, so each
cell closes with a 6.4 mm bridge - one hexagon side - instead of the 30 degree
overhang a point-up cell would give. Nothing in the part needs support.

| | |
| --- | --- |
| Bed footprint | 177 x 56.5 mm, 144 mm tall |
| Supports | none |
| Material | PETG or ASA (a mini PC exhausts warm air; PLA softens) |
| Layer height | 0.2 mm |
| Walls | 4 perimeters |
| Infill | 25%, gyroid or grid |

`under-desk-minipc-mount.stl` is the same part in its as-designed orientation
(desk surface at the top) if you would rather rotate it yourself.

## Mounting

Four **#8 or M4 flat-head wood screws**. The flanges are 6 mm thick with 90
degree countersinks, so the heads finish flush.

1. Hold the mount against the underside of the desk and mark the four holes.
2. Pilot drill 2.5-3 mm, **no deeper than the desk is thick minus 3 mm**.
3. Pick screws no longer than `6 mm + desk thickness - 3 mm` - on an 18 mm
   desk top that is a 20 mm screw at most.
4. Drive all four, then slide the PC in until it clicks past the nubs.

Solid wood, plywood and particle board all take screws fine. On a glass or
metal desk, the flange pads are flat and take 20 mm wide VHB tape instead.

## Files

| file | what it is |
| --- | --- |
| `under_desk_minipc_mount.scad` | the model - every dimension is a parameter |
| `under-desk-minipc-mount-print.stl` | ready to slice, back face on the bed |
| `under-desk-minipc-mount.stl` | as-designed orientation |
| `build.sh` | render both STLs, then verify and re-render the preview |
| `verify.py` | checks the exported STL against the fit and print rules |
| `render_previews.py` | regenerates `preview.png` from the STL |

## Changing it

Edit the parameter block in the `.scad` and run `./build.sh` (needs
`openscad`, plus `trimesh`, `numpy`, `manifold3d`, `scipy` and `matplotlib`
for the checks and preview). Set `SHOW_PC = true` to see the device ghosted in
place while you work in the OpenSCAD GUI.

`verify.py` is the useful part of that loop. It reads the parameters back out
of the `.scad` and checks the exported mesh against them:

```
mesh        watertight, one connected solid, consistent winding
envelope    177.0 x 144.0 x 56.5 mm
fit         seated PC clears the frame, 2.00 mm of headroom
insertion   slide-in path clear the whole way, 0.50 mm clear while on the nubs
retention   1.4 mm slide-out is free travel, 2.0 mm is stopped by the nubs
vents       77 top cells, 23 per side wall, 4 screws, 1 port = 128 holes
fasteners   4 screw holes bored through, flange solid around every hole
print       sits on z = 0, largest unsupported patch 32 mm2 (one cell top)
```

So if you retune the fit for a different device, it will tell you whether the
PC still goes in, still stays in, and still prints without supports. The vent
check counts the through-holes in the mesh against the cell count the
parameters imply, which is what catches a honeycomb field that quietly came
out empty rather than just a heavier part.

`VENT_AF` and `VENT_RIB` set the cell size and the material between cells;
`TOP_VENT_BORDER`, `SIDE_VENT_BORDER` and `SIDE_VENT_MARGIN` set the solid
margins around each field. Cells that would hang over a border are dropped
whole, so the edges never end in slivers.

## Notes and limits

- The pocket is a slip fit, not a clamp. The PC rests on the shelves under its
  own weight; the nubs only stop it sliding forward. Mount it under a
  horizontal surface, not on a wall.
- The top plate beds directly against the desk, so the 2 mm above the PC is a
  dead gap, not a cooling path. Heat leaves through the open bottom, front,
  rear cutout and side vents.
- Sized for a device up to about 2 kg. Beyond that, use six screws (add a
  third pair by editing `SCREW_INSET` into a list) and go to 6 perimeters.
- The rear cutout assumes ports across the back panel. If yours are on a side,
  turn the PC around and let the cables come out of the open front instead.
