# BOTB Ticket Placement System — Project Context

## Goal

Build a system that, given a BOTB spot-the-ball image and a ticket budget,
outputs **the set of pixel coordinates to place tickets on** to maximise the
probability of winning. Passion project running on a DGX Spark (GB10, 128 GB
unified memory). Current phase: **data gathering**.

This is NOT a point-prediction project. No model can reliably emit a 5×5 px
region containing the judged pixel — the judges' choice has irreducible
variance at that precision. The system therefore has two components:

1. **Judge model** — a calibrated probability distribution over where the
   judging panel will place the ball (heatmap + covariance, not a point).
2. **Ticket allocator** — decision layer that converts (predictive
   distribution, ticket budget, tie-break rules) into a concrete list of
   pixels to enter. Later refinement: also model the *crowd's* entry
   distribution and weight toward high-judge-probability /
   low-crowd-density pixels, because ties are likely on consensus pixels.

## Confirmed facts — do not re-derive these

All verified against the live site / the 488-record manifest on 2026-07-07.
Trust unless an API call actually fails.

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

### Competitive landscape (computed from the manifest — shapes the whole design)

- **The crowd is already pixel-perfect collectively.** The winning entry is
  the exact judged pixel in 304/488 weeks (62%), within ~1.4 px in 96%,
  never worse than 3 px. Hitting the judged pixel is necessary but likely
  contested — expect ties on consensus pixels.
- **No quantization shortcut.** Judged coordinates are uniform mod 2/5/10 —
  a true continuous target, not snapped to any grid. Every pixel is in play.
- **Precision economics.** A model with Gaussian error σ=30 px puts only
  ~0.4% of its mass in any 25 px² patch — a single 5×5 guess loses
  essentially every week. But at combined (model + judge) σ ≈ 75 px, ~150
  well-placed tickets carry roughly 0.4% weekly win probability — order of
  break-even against a ~£250k prize at ~£6/ticket. Illustrative numbers, not
  gospel: the project lives or dies on calibration and ticket rules, not on
  squeezing σ below judge variance.
- **The edge is calibration relative to the crowd**: profitable weeks are
  the ones where judges land off the crowd consensus and the model followed
  the judges.

### Consolation zones (confirmed rule + open questions)

- **Confirmed by the owner**: a ticket within 10 px of the winner refunds
  100% of its price. In the target scenario of σ ≈ 28 px model error (see
  Phase 4 — no model exists yet), this is worth ~£39/week expected on a
  100-ticket cluster (~6-7% rebate), and ~1 week in 6 returns most of the
  stake. It does NOT change optimal placement — refund probability is
  proportional to the same local mass as win probability, so top-K-by-mass
  stays optimal — but it cuts variance/bleed during live validation.
- **Likely 5-zone structure**: the gamePhoto API component includes
  `hasFiveZoneRadius`, `zone1OverrideValue`..`zone5OverrideValue`, and
  `gameCreditAwarded` — the 10px/100% rule is probably zone 1 of 5. At
  σ ≈ 28 px the model is within 50 px of the judged spot ~79% of weeks, so
  outer-zone partial credits could offset a large fraction of weekly cost.
  **Action: scrape the zone radii and credit values** — from the JSON zone
  fields where present, and by measuring the rendered rings in
  `zonePhotoUrl` overlays otherwise. Fold the full zone schedule into the
  allocator's EV function.
- Whether zone refunds are cash or site credit (credit only compounds if
  you keep playing) — check T&Cs.

### Open questions to resolve from BOTB T&Cs (feed straight into the allocator)

- Maximum tickets per person per week (and per-household rules).
- Tie-break rule when multiple entries hit the same closest pixel
  (earliest entry? re-judging? split?). This determines whether the
  allocator should avoid crowd-consensus pixels.
- Exact prize values per week (varies; affects EV).

### What's already in this directory

- `scrape_botb.py` — working scraper. `python scrape_botb.py manifest`
  rebuilds the manifest from the live API; `python scrape_botb.py images`
  downloads all full-res JPEGs to `data/images/` (~500 MB, 0.5 s delay
  between requests — keep it polite).
- `data/dc_coords.json` — complete 488-record manifest (url, year, guid,
  judged, winner), already built. Refresh it to pick up new weeks.
- `README.md` — findings write-up.

## Phase 1: data-gathering runbook

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
4. **Commit the manifest + verification report** (not the images —
   `data/images/` is gitignored). Keep raw JPEGs untouched on disk;
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

## Phase 2: judge model (for context — starts after data is verified)

- **Do not train from scratch.** Domain familiarity comes from the
  synthetic pretraining stage (supervised domain adaptation on exactly the
  right task), not from training a fresh model on football images — a
  from-scratch model learns weaker features at vastly higher cost. Raw
  4416×3336 resolution is never an input: stage 1 sees a ~1024–1536 px
  downscaled frame, stage 2 sees native-res crops; pixel precision comes
  from the stage-2 crop.
- **Backbone bake-off, not a fixed choice**: candidates DINOv2/DINOv3 ViT-B
  (default favourite — best dense features, works frozen), ViTPose ViT-B
  (heatmap-native, human-pose priors match the judge signal), ConvNeXt
  V2-B (convolutional baseline, cheap at high res). Protocol: identical
  lightweight heatmap decoder on each frozen backbone, fixed short training
  budget on the synthetic corpus, pick by cross-validated out-of-fold error
  on the 488. Start at ViT-B scale; promote to ViT-L / unfreeze only after
  the pipeline and metrics are stable. Skip SAM encoders and VLMs as
  backbones (VLMs may return later as pseudo-judge labellers).
- Pretrain heatmap regression (winning backbone + upsampling head, Gaussian
  target) on the synthetic corpus to recover true ball position; fine-tune
  on the 488 judge-labelled pairs to learn the judge offset (judges place
  the ball where gaze/body shape suggests, not where it was). Coarse
  full-frame pass, then a refinement head on a full-res crop around the
  peak.
- Output must be a **calibrated distribution**, not a point: full-res
  heatmap or peak + covariance. Calibration matters more than peak
  sharpness — the allocator consumes probability mass, not argmax.
- Compute fits the Spark: fine-tune is minutes; synthetic pretraining is an
  overnight-to-couple-of-days run at 512–768 px.

## Phase 3: ticket allocator + backtest (the actual product)

- Allocator: given heatmap + ticket budget K, select the K pixels
  maximising expected value: P(win) × prize + expected zone rebates −
  ticket cost. V1: top-K probability mass (refunds don't change the
  ranking). V2: adjust for tie-breaks and crowd density once T&C questions
  above are answered.
- **Evaluation is a backtest, not a vibe check.** Leave-one-year-out splits
  (panels and photo style drift). For every held-out week score "judged
  pixel ∈ model's top-K set" for K = 25, 150, 1000. With 488 weeks a 2% hit
  rate is credibly measurable. Decision gate: if top-150 hit rate is ~0
  with median error 150+ px, the betting layer isn't live; if it clears
  0.5–1%, it is. Also report median normalised pixel error and 50/90%
  radii for the judge model itself.

## Phase 4: validating a strong result before staking money

Status: **no model exists yet** — data gathering (Phase 1) is still in
progress. This phase defines the success scenario and the gates it must
pass. The working target is "judged pixel within a 10×10 px patch of the
prediction ~2% of held-out weeks" (σ ≈ 28 px) — that is roughly where the
economics turn clearly positive. Expect first fine-tunes to land far worse
(median error in the hundreds of px is normal at first); iterate via the
Phase 3 backtest. If/when a result approaches the target, it must survive
the following before real tickets:

1. **Hit count, not hit rate.** Score every one of the 488 weeks exactly
   once out-of-fold (leave-one-year-out). 2% on a small holdout can be a
   single lucky hit (95% CI ~0.05–10%); 2% over 488 weeks is ~10 hits
   (CI ~1–3.6%), which is informative.
2. **Leakage audit**: no test-week images (or near-duplicates) anywhere in
   pretraining; identical coordinate normalisation at train and eval;
   metric computed against `judgedPosition` (not `winnerPosition`); confirm
   the metric definition (max(|dx|,|dy|)≤5 vs Euclidean ≤5 differ ~27% in
   area). Note: keying on BOTB's inpainting artefacts is NOT leakage — the
   live weekly image is produced the same way, so it's a legal feature.
3. **Calibration curve**: hit rate vs K for K = 25, 50, 100, 150, 500,
   1000 top-probability pixels. The allocator buys top-K mass, not a square
   patch; if hits only appear at large K the 10×10 framing was flattering.
4. **Paper-trade forward** (leakage-proof by construction): each week,
   generate and timestamp the top-100 pixels BEFORE results publish, then
   score against the announced judged position. 8–12 weeks. Zone rebates
   (see consolation zones above) reduce the cost of doing this with real
   tickets. Gate to real staking: out-of-fold hit rate ≥ ~1.5% AND ≥ 1
   top-100 hit in the paper-trade window.

## Ground rules

- Be polite to botb.com: ≤ a few requests/sec, browser UA, no hammering.
  The full image download is ~1,000 requests total — run it once, cache
  everything.
- Don't scrape anything requiring login, and don't automate competition
  entries — BOTB's T&Cs likely prohibit software-assisted entries. The
  system outputs coordinates; a human places the tickets.
- Prior art: https://github.com/DamienLopez1/Spot-the-ball detects the
  inpainting artefacts BOTB leaves behind (U-Net) — predicts the *original*
  ball position, not the judges' choice. Potentially useful auxiliary input.
