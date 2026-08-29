# Princess tiara comb

A fine arched tiara on a hair comb, built to print in one piece.

![the tiara](preview_3d.png)

![the drawing](preview.png)

**`tiara_comb_97mm.stl`** — 97.2 mm wide × 52.9 mm tall × 3.6 mm deep, watertight,
one body, about 5 g of filament.

## Printing

Face up, flat back on the bed, exactly as exported. **No supports.** The whole
piece is a height field over a flat base — every surface either rises straight
off the bed or curves over the top — and the build measures that rather than
assuming it: of the down-facing area, everything bar a fraction of a square
millimetre of decimation slivers is the flat back itself.

* 0.15–0.2 mm layers. A **brim** is worth it: the crown meets the bed as a lot of
  separate thin strands.
* **PETG or PLA+ rather than plain PLA.** The teeth are 2.6 mm thick and 22 mm
  long; brittle PLA can snap one if it is forced into thick hair. Printed flat
  like this the layers run the strong way across a tooth, which is the main thing.
* The crown is deliberately fine — strands are 1.6–1.8 mm wide and about 2 mm in
  section. That is three or four passes of a 0.4 mm nozzle, and it is the whole
  point of the look, but it does mean this is not a piece to sit on.

**It prints flat, and heads are not.** To curve it, dip the band and comb in
water at about 70 °C for twenty seconds and bend gently over something round —
PLA and PETG both soften enough to take a set and hold it once cool. Do this
before painting.

Silver or chrome filament reads best. A dab of clear gloss or coloured nail
polish on each pin head gives a convincing sparkle; the heads are raised, not
sockets, so there is nowhere to glue a real stone in.

## The design

A lens between two arcs — a slim band below, a rim arching over — filled with
five pointed leaves whose tips meet the rim, a ball-tipped pin standing in each
gap, a small curl at either end and a finial at the crown. Below the band, a
nine-tooth comb.

Leaves widen with their own height, so the short outer ones stay as slender as
the tall middle ones instead of turning into circles. Every strand is stroked
with a round pen along a Bézier or a spiral; unioning strokes can only *add*
material, so the narrowest pen a design asks for is a hard floor on its feature
size — the same trick as the snowflakes in this repo.

The third dimension comes from a height field rather than a flat extrusion:
strands roll over to their own half width so they come out round like wire, the
band gets a gentler roll so it reads as polished metal, each pin head is a
hemisphere of the radius it was drawn with, and the comb stays a flat section
because teeth want their full thickness.

```bash
pip install numpy shapely trimesh scikit-image pillow
python3 tiara.py --scale 0.9 --out smaller.stl        # 87.5 mm wide
python3 preview.py                                    # flat drawing, to check the art
```

`--scale` resizes the drawing only — thicknesses stay in millimetres, since they
are set by what the printer can do rather than by how big the tiara is. Because
the strands are already close to the floor, there is not much room below full
size: **0.9 (87.5 mm) passes, 0.85 (82.7 mm) does not**, and the run fails rather
than handing you something that prints as lace. Scaling up is unbounded.

Files: `curves.py` (Bézier, arc, spiral, stroking), `design.py` (the tiara
itself, all coordinates and widths in one place), `tiara.py` (height field,
marching cubes, checks), `preview.py` (flat PNG).

Renders were made with the previewer from the sibling `highland-cow/` project.
