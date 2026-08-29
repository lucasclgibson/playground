# Princess tiara comb

A fine arched tiara that stands on its own comb, curved to sit on a head, and
printable in one piece with no supports.

![the tiara](preview_3d.png)

**`tiara_comb_94mm.stl`** — 95.0 mm wide × 30.0 mm tall × 29.2 mm front to back,
watertight, one body, about 4 g of filament.

The face is a **flat 2.0 mm wall** with square edges — no bevel or rolled-over
section on the strands, which keeps the perimeters simple to slice. The comb
**tapers from 2.0 mm where it meets the band down to 1.2 mm at the tooth tips**,
so the teeth end thin and springy while keeping their full section where they
carry the tiara; the underside stays flat on the bed.

The face is wrapped onto a **110 mm radius**, so it curves around the head as it
comes off the printer — no heat-forming needed. The comb sits at right angles to
it, teeth running backwards into the hair, the way a real tiara comb does.

## Printing

**Standing up, exactly as exported** — comb flat on the bed, crown in the air,
which is also how it is worn. **No supports.** The build checks this properly:
every layer is tested for material that starts with nothing under it, treating
bridges as fine (they are anchored at both ends and slicers handle them) and
counting only true floating starts. There are 0.19 mm² of those, which is a
voxel or two of rounding — nothing a slicer would even build support for.

* 0.15–0.2 mm layers. The comb gives a 94 × 29 mm footprint on the bed, so
  adhesion is not a worry; a brim is optional.
* **PETG or PLA+ rather than plain PLA.** The teeth are 2.6 mm thick and 22 mm
  long, and printed in this orientation the layers run across a tooth, which is
  the strong way.
* The crown is deliberately fine: strands are 1.6–1.8 mm wide in a 2.0 mm wall,
  which is four or five passes of a 0.4 mm nozzle.
* The arches print as bridges between the leaf tips — short spans over the
  openings, which come out clean.

Silver or chrome filament reads best. A dab of clear gloss or coloured nail
polish on each pin head gives a sparkle; the heads are raised, not sockets, so
there is nowhere to glue a real stone in.

## The design

The face: a lens between two arcs — a slim band below and a rim arching over —
filled with five pointed leaves whose tips meet the rim, a ball-tipped pin
standing in each gap, a small curl at either end and a finial at the crown.
Below it, a nine-tooth comb at right angles.

Leaves widen with their own height, so the short outer ones stay as slender as
the tall middle ones instead of turning into circles. Each end curl stops short
of the top of its sweep: carry it to the apex and the last stretch runs near
horizontal, which starts in mid-air when the piece is printed standing.

Every strand is stroked with a round pen along a Bézier or a spiral; unioning
strokes can only *add* material, so the narrowest pen a design asks for is a hard
floor on its feature size — the same trick as the snowflakes in this repo.

The face is drawn flat and then wrapped: a point in space is turned into an arc
length along the head curve and a height, and the flat drawing's distance field
is sampled there. The wall is one thickness throughout with square edges — a
bevel running along every strand buys very little on a piece this fine and costs
a lot of slicing. The comb is built separately in the horizontal plane, its
thickness driven by how far back it sits from the band, and blended into the face
with a fillet so the T-joint has some meat in it.

```bash
pip install numpy shapely trimesh scikit-image pillow
python3 tiara.py --curve 85 --out tighter.stl     # a stronger curve
python3 tiara.py --scale 0.9 --out smaller.stl    # 85 mm wide
python3 preview.py                                # flat drawing and comb plan
```

`--curve` is the radius the face wraps on; smaller curls it more tightly round
the head. `--scale` resizes the face drawing only — thicknesses stay in
millimetres, since they are set by what the printer can do rather than by how big
the tiara is. Because the strands are already close to the floor there is not
much room below full size: **0.9 (85 mm) passes, 0.85 does not**, and the run
fails rather than handing you something that prints as lace.

Every run reports size, watertightness, body count, the narrowest wall in the
drawing, whether the centre of mass sits over the footprint, and the unsupported
area per layer. It exits non-zero if any of those fail.

Files: `curves.py` (Bézier, arc, spiral, stroking), `design.py` (the face and the
comb plan, all coordinates and widths in one place), `tiara.py` (wrapping, height
field, marching cubes, checks), `preview.py` (flat PNGs).

Renders were made with the previewer from the sibling `highland-cow/` project.
