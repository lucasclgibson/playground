# Under-desk mini PC mount

A printable cradle that screws to the underside of a desk. The mini PC slides
straight in from the front, sits on two shelves, and clicks in behind a pair of
sprung latches. No brackets, no straps, no fasteners into the PC itself.

![preview](preview.png)

Built for a **129 x 129 x 45.5 mm** mini PC. Any other size is a three-number
edit at the top of the `.scad` file.

## Dimensions

| | mm |
| --- | --- |
| Pocket (W x D x H) | 131 x 130.5 x 47.5 |
| Body (W x D x H) | 137 x 142 x 54.5 |
| Overall, including mounting pads | 165 x 142 x 54.5 |
| Drop below the desk | 54.5 |
| Screw pattern | 151 across x 82 along |
| Material | 99 cm3 solid (~89 g as printed) |

Clearance is 1 mm each side, 2 mm above and 1.5 mm front-to-back, so a device
that measures a little over its spec still goes in.

## How it holds the PC

- **Bottom shelves** - two 12 mm lips carry the weight; the middle of the
  underside is open, so the intake fan is not covered.
- **Rear wall** - depth stop, with a 113 x 37 mm cutout so the rear ports and
  cables stay accessible.
- **Latches** - a cantilever tab cut into each side wall, 40 x 10 mm, rooted at
  the back and free at the mouth. The PC's own side face pushes each tab 1.6 mm
  outward as it goes in; once the front face clears the barb the tabs snap back
  and you hear it. About 0.7 kgf to push in. Coming back the other way the barb
  presents a 70 degree face instead of a ramp, which needs somewhere between 5
  and 12 kgf depending on friction - so it does not back out. Press the two
  flares at the front corners to let it go.
- **Retention nubs** - a bump on each shelf just ahead of the PC, a backstop
  under the latches. Pushing the PC in lifts it 1.5 mm over a shallow 23 degree
  ramp (there is 2 mm of headroom, so nothing has to flex) and it drops back
  down behind them - that drop is what tells you it is home.
- **Mounting pads** - four tabs rather than full-length flanges, 48 mm long on
  a 151 x 82 mm pattern, tapered at both ends so they still print unsupported.
  They are a uniform 6.5 mm rather than thin-with-a-gusset: a gusset at the
  root reaches in under the screw head and fouls the driver. Every head has a
  clear 6.8 mm radius below it.
- **Airflow** - open bottom, open front, a 113 x 37 mm rear cutout, and a
  12 x 26 mm vent lattice through the top plate and both side walls: 66 cells
  overhead (~8,500 mm2 open) and 10 per side (~1,300 mm2 each, plus 160 mm2 of
  latch slot). The side field stops short of the latch beams.

## Printing

Print `under-desk-minipc-mount-print.stl`. It is the same solid rolled onto
its back face, which is what makes the part support-free: every wall runs
along the build direction, and the vent cells are hexagons stretched to a
point at each end, the points along that direction. A cell closes at 60
degrees from horizontal rather than bridging flat across its width, so the
lattice needs no bridging at all. The latch slots run out of the front face,
so they open at the top of the print rather than closing over one. What is
left is 0.2% of the surface: the four horizontal screw bores, and the 2.6 mm
ledge behind each barb - a latch that resists pulling has to face the way the
PC travels, which is the build direction, and there is no way around that.

| | |
| --- | --- |
| Bed footprint | 165 x 54.5 mm, 142 mm tall |
| Supports | none |
| Material | PETG or ASA (a mini PC exhausts warm air; PLA softens) |
| Layer height | 0.2 mm |
| Walls | 4 perimeters |
| Infill | 25%, gyroid or grid |

`under-desk-minipc-mount.stl` is the same part in its as-designed orientation
(desk surface at the top) if you would rather rotate it yourself.

## Mounting

Four **#8 or M4 flat-head wood screws**. The 5 mm clearance holes leave room to
shuffle the mount a little if a pilot hole wanders. The pads are 6.5 mm thick
with 90 degree countersinks, so the heads finish flush. Nothing crowds them, but they
sit 7 mm out from a wall that hangs 54.5 mm down, so use a hand screwdriver or
a bit extension rather than a drill chuck.

1. Hold the mount against the underside of the desk and mark the four holes.
2. Pilot drill 2.5-3 mm, **no deeper than the desk is thick minus 3 mm**.
3. Pick screws no longer than `6.5 mm + desk thickness - 3 mm` - on an 18 mm
   desk top that is a 20 mm screw at most.
4. Drive all four, then slide the PC in until the latches click.

To take the PC out, press both release flares at the front corners outward and
pull. Pulling without pressing will not do it, which is the point.

Solid wood, plywood and particle board all take screws fine. On a glass or
metal desk, the pads are flat and take 20 mm wide VHB tape instead.

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
envelope    165.0 x 142.0 x 54.5 mm
fit         seated PC clears the frame, 2.00 mm of headroom
insertion   path clear apart from the latches, 0.50 mm clear while on the nubs
latches     beams cut free, barb reaches 2.6 mm, 47 mm2 of catch across the face
retention   1.4 mm slide-out is free travel, 2.0 mm is stopped
vents       66 top cells, 10 per side wall, 4 screws, 1 port = 91 holes
fasteners   4 bored through, pad solid around each, driver reaches every head
print       sits on z = 0, largest unsupported patch 28 mm2 (a barb ledge)
```

So if you retune the fit for a different device, it will tell you whether the
PC still goes in, still stays in, and still prints without supports. The vent
check counts the through-holes in the mesh against the cell count the
parameters imply, which is what catches a vent field that quietly came
out empty rather than just a heavier part.

`LATCH_LEN` is the lever that sets how hard the click is: at 40 mm the beam
takes 3.4 N to flex and sees 9 MPa at its root, a third of what PETG manages
across layer lines. Shorten it and both numbers climb fast - 25 mm would be
14 N and 23 MPa. `LATCH_BARB` sets how far the tab reaches past the PC (it
flexes that minus `GAP_SIDE`), and `LATCH_HOOK` how steeply it refuses to come
back out; 90 would be a dead stop that only releases by pressing.

`VENT_W`, `VENT_LEN` and `VENT_RIB` set the cell size and the web between
cells, and `VENT_ANGLE` sets how steeply each cell closes - drop it towards 45
for rounder cells, raise it for more margin over the overhang limit. The rows
interlock the way a honeycomb does, which holds for any cell proportion, and
each cell is the tile shrunk by half a rib, so the web comes out even
everywhere including at the points. `TOP_VENT_BORDER`, `SIDE_VENT_BORDER` and
`SIDE_VENT_MARGIN` set the solid margins around each field; cells that would
hang over a border are dropped whole, so the edges never end in slivers.

## Notes and limits

- The pocket is a slip fit, not a clamp. The PC rests on the shelves under its
  own weight and the latches stop it sliding forward. Mount it under a
  horizontal surface, not on a wall.
- The barbs catch the left and right edges of the PC's front face, 1.6 mm in
  and 10 mm tall, around mid height. If your machine has a deep chamfer or a
  soft rubber bezel there, raise `LATCH_BARB` so there is more to bite on.
- The top plate beds directly against the desk, so the 2 mm above the PC is a
  dead gap, not a cooling path. Heat leaves through the open bottom, front,
  rear cutout and side vents.
- The top plate is a third of the material and does no structural work beyond
  tying the two side walls together and keeping the desk off the PC. Dropping
  it (`TOP_T` down to nothing) would save another ~33 cm3, at the cost of
  the top grid and a floppier mouth until the mount is screwed down.
- Sized for a device up to about 2 kg. Beyond that, add a value to `SCREW_YS`
  for a third pair of pads and go to 6 perimeters (`verify.py` expects four
  screws, so bump that too).
- The rear cutout assumes ports across the back panel. If yours are on a side,
  turn the PC around and let the cables come out of the open front instead.
