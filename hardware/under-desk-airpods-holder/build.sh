#!/usr/bin/env bash
# Render the holder, then check it.
set -euo pipefail
cd "$(dirname "$0")"
openscad -o airpods-holder.stl under_desk_airpods_holder.scad
python3 verify.py
python3 render_previews.py
