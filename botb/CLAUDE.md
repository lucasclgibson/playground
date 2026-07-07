# BOTB Spot-the-Ball Prediction — Project Context

## Goal

Train a model that predicts where BOTB's judging panel places the ball in
their weekly spot-the-ball competition photos. Passion project running on a
DGX Spark (GB10, 128 GB unified memory). Current phase: **data gathering**.

## Confirmed facts — do not re-derive these

All of the following was verified against the live site on 2026-07-07.
Trust it unless an API call actually fails.

### The data source

BOTB's winner pages are backed by a public, unauthenticated JSON API
(Umbraco). Requests need a browser User-Agent header (plain curl/urllib
default UA gets 403 on HTML pages; the API itself is permissive but send a
browser UA everywhere anyway).

1. `GET https://www.botb.com/umbraco/surface/WinnersSurface/GetWinners`
   → `data.winnerList[]`, ~2,900 winner entries, all competitions since 2005.
2. Filter entries whose `Url` matches `/winners/dc\d+` — **only Dream Car
   pages have spot-the-ball data**. Slug format `dcWWYY` (week, year).
3. `GET https://www.botb.com/umbraco/botb/winnersresult/getpagecomponents?path=/winners/dcWWYY`
   → `PageComponents[]`; the component with `type == "gamePhoto"` contains:
   - `competitionPictureGuid`
   - `judgedPosition: [x, y]` — the training label
   - `winnerPosition: [x, y]`
4. `GET https://www.botb.com/umbraco/botb/spottheball/getcompetitionpicture/?competitionpictureguid=<guid>&size=RESULT_FULL`
   → full-resolution JPEG (typically 2500–4500 px wide, 0.4–1.2 MB).

### Dataset shape

- **488 samples** with coordinates: weeks 5/2017 → 26/2026, one per week,
  still growing weekly. This is the ceiling for judge-labelled data — midweek
  (`mw`), cash (`ew`/`cp`/`ml`/`xc`/`ls`), and pre-2017 supercar (`sc`)
  result pages contain no `gamePhoto` component. A handful of dc pages
  (dc1124, dc1224, dc1724) legitimately lack it; skip them.
- **Coordinate space**: `judgedPosition` is in the pixel space of the
  `size=RESULT_FULL` image. Verified by diffing the site's crosshair overlay
  (`getcoordinatepicture`, transparent PNG at `size=RESULT`, 736×556) against
  the published coords: overlay centre (375, 233) == [2250, 1396] scaled from
  the 4416×3336 full image, exact to the pixel.
- **Winner-vs-judged distance**: median 0 px, max 3 px across all 488
  results. Someone always hits the exact judged pixel. Pixel-exact output is
  the long-term bar; "within a few px" is the realistic model target.

### What's already in this directory

- `scrape_botb.py` — working scraper. `python scrape_botb.py manifest`
  rebuilds the manifest from the live API; `python scrape_botb.py images`
  downloads all full-res JPEGs to `data/images/` (~500 MB, 0.5 s delay
  between requests — keep it polite).
- `data/dc_coords.json` — complete 488-record manifest (url, year, guid,
  judged, winner), already built. Refresh it to pick up new weeks.
- `README.md` — findings write-up.

## Data-gathering runbook

Work through these in order; each step is idempotent and resumable.

1. **Refresh the manifest**: `python scrape_botb.py manifest`. Expect 488+
   records (grows by ~1/week since this was written). Diff against the
   committed file; new weeks append at the end.
2. **Download all images**: `python scrape_botb.py images`. The script skips
   files that already exist. Verify afterwards: every manifest record should
   have a readable JPEG, and every `judgedPosition` must fall inside its
   image bounds. Write a small `verify.py` that opens each image with PIL,
   checks dimensions vs coords, and reports any corrupt/missing files.
3. **Record image dimensions** into the manifest (add `width`/`height` per
   record) so training code can normalise coordinates without opening files.
4. **Commit the manifest + verification report** (not the images — add
   `data/images/` to `.gitignore`). Keep raw JPEGs untouched on disk;
   derived/resized versions go in separate directories.
5. **Build the synthetic pretraining corpus** (the big one):
   - Source football match photos that *contain* a visible ball. Options to
     evaluate: SoccerNet (research licence, has ball annotations),
     open-licence sports photo datasets, frames extracted from
     freely-licensed match footage. Target 20–100k images.
   - Detect/annotate the ball centre (SoccerNet has labels; otherwise a
     pretrained detector, e.g. a YOLO variant fine-tuned on 'sports ball').
   - Inpaint the ball out (Stable-Diffusion-class inpainting or LaMa — both
     run comfortably in 128 GB unified memory) to produce (ball-removed
     image, true ball centre) pairs mimicking BOTB's editing.
   - Store as: original, inpainted, mask, centre coords. Spot-check a sample
     visually — bad inpainting leaves artefacts that let the model cheat.

## Modelling plan (next phase, for context)

Two-stage: pretrain a heatmap-regression model (pretrained ViT-B/ConvNeXt
backbone + upsampling head, Gaussian target) on the synthetic corpus to
recover true ball position; fine-tune on the 488 judge-labelled pairs to
learn the judge offset (judges place the ball where gaze/body shape suggests,
not where it was). Coarse full-frame pass, then a refinement head on a
full-res crop around the peak for pixel precision. Evaluate leave-one-year-out
(panels and photo style drift); report median normalised pixel error and
50/90% radii. Compute fits the Spark: fine-tune is minutes, synthetic
pretraining is an overnight-to-couple-of-days run at 512–768 px.

## Ground rules

- Be polite to botb.com: ≤ a few requests/sec, browser UA, no hammering.
  The full image download is ~1,000 requests total — run it once, cache
  everything.
- Don't scrape anything requiring login, and don't automate competition
  entries — BOTB's T&Cs likely prohibit software-assisted entries; this
  project stays on the analysis/prediction side.
- Prior art: https://github.com/DamienLopez1/Spot-the-ball detects the
  inpainting artefacts BOTB leaves behind (U-Net) — predicts the *original*
  ball position, not the judges' choice. Potentially useful auxiliary input.
