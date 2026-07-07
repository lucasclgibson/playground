# BOTB ticket placement system

Given a BOTB spot-the-ball image and a ticket budget, output the set of
pixels to place tickets on. Two components: a **judge model** (calibrated
probability distribution over where the judging panel will place the ball)
and a **ticket allocator** (turns that distribution plus ticket budget and
tie-break rules into concrete entries). Point prediction is explicitly a
non-goal — the judges' choice has irreducible variance below ~tens of
pixels, so winning is a coverage-and-calibration game, not an accuracy one.

This directory holds the data-collection groundwork: a validated scraper and
the full manifest of every published result with coordinates. `CLAUDE.md` is
the live project brief and runbook.

## What BOTB publishes (confirmed 2026-07-07)

Every weekly **Dream Car** result page since **week 5 of 2017** is backed by a
public JSON API that exposes:

- `competitionPictureGuid` — key to the full-resolution game photo (JPEG,
  typically 2500–4500 px wide, no auth required)
- `judgedPosition` — the judges' chosen ball centre, `[x, y]`
- `winnerPosition` — the winning entry's coordinates

**Dataset size: 488 samples** (weeks 5/2017 → 26/2026), growing by one per
week. Winners pages exist back to 2005, but only the Dream Car template
includes the `gamePhoto` component — midweek, cash, and pre-2017 supercar
results publish no coordinates, so 488 is the ceiling for judge-labelled data.

`data/dc_coords.json` is the complete manifest. Images are downloaded
separately (`python scrape_botb.py images`, ~500 MB total).

### Coordinate space

`judgedPosition` is in the pixel space of the image served at
`size=RESULT_FULL`. Verified by diffing the site's crosshair overlay
(`getcoordinatepicture`, a transparent PNG at `size=RESULT`) against the
published coordinates: overlay centre (375, 233) on a 736×556 render matches
`[2250, 1396]` on the 4416×3336 full image exactly after scaling.

## Key numbers for modelling

- **488** (image, judged-position) pairs; ~52 new per year.
- The winning entry is the **exact judged pixel in 304/488 weeks (62%)**,
  within ~1.4 px in 96%, never worse than 3 px. The crowd collectively
  saturates the neighbourhood every week — hitting the judged pixel is
  necessary but likely contested (ties on consensus pixels).
- **No quantization shortcut**: judged coordinates are uniform mod 2/5/10 —
  a true continuous target, every pixel in play.
- Judges are instructed to place the ball where play suggests it should be
  (gaze direction, body shape), not where it physically was — so the label is
  a human-judgement distribution, which is exactly what makes this learnable.
- Precision economics: a model with Gaussian error σ=30 px puts only ~0.4%
  of its mass in any 25 px² patch, so a single tight guess loses essentially
  every week. But at combined (model + judge) σ ≈ 75 px, ~150 well-placed
  tickets carry roughly 0.4% weekly win probability — order of break-even
  against a ~£250k prize at ~£6/ticket. Calibration and ticket rules decide
  this, not raw accuracy.

## System design

488 samples is too few to train from scratch but fine for fine-tuning:

1. **Pretrain on synthetic spot-the-ball**: take any large corpus of football
   match photos that contain the ball, inpaint the ball out, and train a
   heatmap-regression model (pose-estimation-style: pretrained ViT/ConvNeXt
   backbone + upsampling head, Gaussian target around the true ball centre)
   to recover the true position. This gives effectively unlimited pretraining
   data for the underlying "read the play" skill.
2. **Fine-tune on the 488 judge-labelled samples** so the model learns the
   systematic offset between physical truth and judge consensus. Output is a
   calibrated distribution (heatmap/covariance), not an argmax.
3. **Ticket allocator**: converts (distribution, ticket budget K) into the K
   pixels maximising win probability; later versions adjust for tie-break
   rules and crowd density (prefer high-judge-probability,
   low-crowd-density pixels).
4. **Backtest, don't vibe-check**: leave-one-year-out splits (judge panels
   and photo style drift); for each held-out week score whether the judged
   pixel falls in the model's top-K set (K = 25, 150, 1000), plus median
   normalised pixel error and 50/90% radii. Top-150 hit rate ≈ 0 → betting
   layer isn't live; ≥ 0.5–1% → it is.

## Caveats

- Check BOTB's T&Cs before entering competitively: scraping public result
  pages is one thing, but automated or software-assisted *entries* may be
  prohibited, and entry counts per person are capped.
- Prior art: [DamienLopez1/Spot-the-ball](https://github.com/DamienLopez1/Spot-the-ball)
  detects inpainting artefacts (where the ball was removed) with a U-Net —
  that predicts the *original* position, not the judges' choice, but could be
  a useful auxiliary input.

## Usage

```bash
python scrape_botb.py manifest   # rebuild data/dc_coords.json from the live API
python scrape_botb.py images     # download all full-res JPEGs to data/images/
```
