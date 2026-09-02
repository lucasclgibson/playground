# UK Property Looker badge — printable

The badge mark from the logo (no wordmark), as printable solids.

![the block](preview_block.png)

## The files

| File | | |
|---|---|---|
| **`ukpl_badge_block_110mm.stl`** | 110 × 95.3 × 20 mm, one piece | the mark extruded thick with **square edges — no bevel anywhere**. The roof is held on by a thin web across the shadow gap, and nothing else. |
| `ukpl_badge_plaque_100mm.stl` | 106.8 × 93.5 × 6 mm, one piece | flat version: the mark raised 3.5 mm on a backing plate that follows its outline. |
| `ukpl_badge_flat_100mm.stl` | 100 × 86.7 × 6 mm, two pieces | the bare mark as two solids in true relative position, for gluing onto something or insetting. |

<p align="center">
  <img src="preview_plaque.png" width="44%"> <img src="preview_flat.png" width="40%">
</p>

The mark is **two disconnected shapes** — a roof chevron floating above a rounded
tag — so something has to join them. The block does it with a **3.5 mm web**
across the gap and nothing more: no plate, no plinth. The web sits against the
**back** face, so from the front the gap reads as a 16.5 mm-deep blind slot with
the silhouette intact, and the block lies flat on its back with nothing
overhanging.

## Printing the block

Flat on its back, as exported — logo face up. **No supports:** measured, not
assumed, there is 0.00 mm² of down-facing surface anywhere but the bed.

Putting the web mid-depth instead would look symmetric from both sides but hangs
580 mm² of it in mid-air, and standing the block on its own bottom edge — which
it will just about do, balancing by 2.4 mm with the mass 47 mm up, so a 3° nudge
tips it — needs 595 mm² of support. Lying flat is the one orientation that needs
none, which is why it is exported that way.

* 0.2 mm layers; about 57 g of PLA at 15 % infill (141 g if you print it solid).
* Every wall is square and vertical, so perimeters stay simple and the edges come
  out crisp.
* The exact geometry is extruded and booleaned rather than sampled on a grid, so
  the edges are truly sharp — a voxel mesher rounds them by half a voxel — and
  the file is 200 kB and 4,084 triangles.

```bash
pip install numpy shapely trimesh mapbox_earcut manifold3d pillow
python3 badge.py --style block --width 130 --thickness 25 --out bigger.stl
python3 badge.py --style block --web 5 --reach 8 --out sturdier.stl
```

`--thickness` sets how deep the block is, `--web` how thick the bridging web is,
`--reach` how wide a gap it closes. Every run reports size, watertightness, body
count and the fraction of the artwork in walls too thin to print, and exits
non-zero if any fail.

## The sculpted variant

`stand.py` is the other approach: the mark rolled over to a bullnose edge with
gently domed faces, standing on a plinth, meshed from a distance field. Not what
the block is for, but the flags are there — `--edge`, `--dome`, `--base none`,
`--web-centred` — if a softer object is ever wanted.

```bash
python3 stand.py --out sculpted.stl
```

## How it works

* `svgpath.py` — a small SVG path reader: tokenises the `d` attribute (including
  nasties like `71.29.03` meaning two numbers) and flattens curves to polylines.
* `shapes.py` — rings to shapely geometry under SVG's **non-zero** fill rule,
  worked out from the containment tree and each ring's winding. That is what
  correctly makes the tag's eyelet a hole while keeping the roof — which winds
  the other way but sits outside the tag — a solid. Also builds the bridging web,
  as a morphological closing of the mark: it fills the shadow gap and leaves the
  silhouette alone.
* `badge.py` — the three extruded styles, with the printability checks.
* `stand.py` — the distance-field route, for the sculpted variant.

`badge.svg` is the mark lifted from the site's icon sprite
(`symbol#ukpl-logo-badge`), cropped to its own bounding box and otherwise
untouched — the printed outline is the logo's own geometry, not a redraw.

Renders were made with the previewer from the sibling `highland-cow/` project:
`python3 ../highland-cow/render.py file.stl out.png --flat`.
