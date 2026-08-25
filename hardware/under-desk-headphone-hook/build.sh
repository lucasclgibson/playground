#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
openscad -o headphone-hook.stl under_desk_headphone_hook.scad
python3 verify.py
python3 render_previews.py
