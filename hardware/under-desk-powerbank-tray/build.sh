#!/usr/bin/env bash
# Render both STLs from the model, then check them.
set -euo pipefail
cd "$(dirname "$0")"

openscad -o under-desk-powerbank-tray.stl under_desk_powerbank_tray.scad
openscad -o under-desk-powerbank-tray-print.stl -D PRINT_ORIENTATION=true \
         under_desk_powerbank_tray.scad

python3 verify.py
python3 render_previews.py
