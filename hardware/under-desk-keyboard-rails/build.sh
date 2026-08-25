#!/usr/bin/env bash
# Render both rails from the one model, then check them.
set -euo pipefail
cd "$(dirname "$0")"

openscad -o keyboard-rail-right.stl under_desk_keyboard_rail.scad
openscad -o keyboard-rail-left.stl -D MIRROR=true under_desk_keyboard_rail.scad

python3 verify.py
python3 render_previews.py
