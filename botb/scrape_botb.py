#!/usr/bin/env python3
"""Scrape BOTB Dream Car spot-the-ball results: images + judged coordinates.

BOTB publishes every weekly Dream Car result since week 5 of 2017. Each result
page is backed by a public JSON API that exposes the competition picture GUID
and the judges' chosen ball position. The coordinates are in the pixel space of
the full-resolution image served at size=RESULT_FULL (verified by diffing the
crosshair overlay the site renders at size=RESULT against the published
coordinates — they match exactly after scaling).

Pipeline:
  1. GET /umbraco/surface/WinnersSurface/GetWinners        -> all winner pages
  2. filter Url matching /winners/dc\\d+                    -> Dream Car results
  3. GET /umbraco/botb/winnersresult/getpagecomponents     -> gamePhoto component
     ?path=/winners/dcWWYY                                    (guid + judgedPosition)
  4. GET /umbraco/botb/spottheball/getcompetitionpicture/  -> full-res JPEG
     ?competitionpictureguid=<guid>&size=RESULT_FULL

Usage:
  python scrape_botb.py manifest              # write data/dc_coords.json
  python scrape_botb.py images [--limit N]    # download JPEGs to data/images/

Only Dream Car (dc) pages expose coordinates. Midweek (mw), cash (ew/cp/ml/xc/ls),
supercar-era (sc, back to 2005) and other result pages do not include the
gamePhoto component, so they cannot be used as training samples.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://www.botb.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
DATA_DIR = Path(__file__).parent / "data"
MANIFEST = DATA_DIR / "dc_coords.json"


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def get_json(url: str):
    body = get(url)
    return json.loads(body) if body else None


def list_dream_car_slugs() -> list[dict]:
    winners = get_json(f"{BASE}/umbraco/surface/WinnersSurface/GetWinners")
    out = []
    for w in winners["data"]["winnerList"]:
        url = w.get("Url") or ""
        if re.match(r"/winners/dc\d", url):
            out.append({"url": url, "year": w["Date"]["Year"],
                        "dateRange": w.get("CompetitionDateRange")})
    return out


def fetch_result(entry: dict, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            page = get_json(f"{BASE}/umbraco/botb/winnersresult/getpagecomponents"
                            f"?path={entry['url']}")
            if not page:
                return None
            game = next((c["data"] for c in page.get("PageComponents", [])
                         if c["type"] == "gamePhoto"), None)
            if not game:
                return None
            return {**entry,
                    "guid": game["competitionPictureGuid"],
                    "judged": game["judgedPosition"],
                    "winner": game["winnerPosition"]}
        except Exception:
            if attempt == retries - 1:
                print(f"failed: {entry['url']}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)


def build_manifest() -> None:
    slugs = list_dream_car_slugs()
    print(f"{len(slugs)} Dream Car result pages")
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = [r for r in ex.map(fetch_result, slugs) if r]
    results.sort(key=lambda r: (r["year"], r["url"]))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(results, indent=1))
    print(f"{len(results)} results with judged coordinates -> {MANIFEST}")


def download_images(limit: int | None) -> None:
    records = json.loads(MANIFEST.read_text())
    if limit:
        records = records[:limit]
    img_dir = DATA_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(records):
        slug = r["url"].rsplit("/", 1)[-1]
        dest = img_dir / f"{slug}.jpg"
        if dest.exists():
            continue
        body = get(f"{BASE}/umbraco/botb/spottheball/getcompetitionpicture/"
                   f"?competitionpictureguid={r['guid']}&size=RESULT_FULL",
                   timeout=120)
        dest.write_bytes(body)
        print(f"{i + 1}/{len(records)} {slug} {len(body) // 1024}KB")
        time.sleep(0.5)  # stay polite; ~500MB total at full pace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["manifest", "images"])
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.command == "manifest":
        build_manifest()
    else:
        download_images(args.limit)


if __name__ == "__main__":
    main()
