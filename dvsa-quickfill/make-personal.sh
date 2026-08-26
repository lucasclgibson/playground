#!/usr/bin/env bash
# Produces a copy of the userscript with the details already baked in, so it
# works the moment it is installed — no first-run typing.
#
#   ./make-personal.sh <driving-licence-number> <theory-test-pass-number>
#
# The output file is gitignored. Keep it out of version control: it contains
# someone's licence number.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <driving-licence-number> <theory-test-pass-number>" >&2
  exit 1
fi

here="$(cd "$(dirname "$0")" && pwd)"
source_file="$here/dvsa-quickfill.user.js"
output_file="$here/dvsa-quickfill.personal.user.js"

LICENCE="$1" THEORY="$2" SRC="$source_file" OUT="$output_file" node <<'NODE'
const fs = require('fs');

const source = fs.readFileSync(process.env.SRC, 'utf8');
const licence = JSON.stringify(process.env.LICENCE);
const theory = JSON.stringify(process.env.THEORY);

const replaced = source.replace(
  /const PRESET = \{\s*licence: '',\s*theory: '',\s*\};/,
  `const PRESET = {\n    licence: ${licence},\n    theory: ${theory},\n  };`
);

if (replaced === source) {
  console.error('Could not find the PRESET block to fill in — has the script changed?');
  process.exit(1);
}

fs.writeFileSync(process.env.OUT, replaced.replace('@name         DVSA Quick Fill', '@name         DVSA Quick Fill (personal)'));
NODE

chmod 600 "$output_file"
echo "Wrote $output_file"
