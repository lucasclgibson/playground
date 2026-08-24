#!/usr/bin/env bash
# Render both STLs from the model, then check them.
set -euo pipefail
cd "$(dirname "$0")"

openscad -o under-desk-minipc-mount.stl under_desk_minipc_mount.scad
openscad -o under-desk-minipc-mount-print.stl -D PRINT_ORIENTATION=true \
         under_desk_minipc_mount.scad

python3 verify.py
python3 render_previews.py
