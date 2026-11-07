#!/usr/bin/env bash
# Optional: film-stock looks. Creates the venv with Spectral Film LUT (MIT) and generates the LUTs into library/luts/
# (6 looks: full LUTs + split negative/grain/print LUTs for the grain, ~25 MB, gitignored like the rest of library/).
# Applying a look afterwards needs only ffmpeg (scripts/film_look.py). Transitions (scripts/transitions.py) need no setup.
#   bash scripts/setup_looks.sh            -> ~/.venvs/ghost-looks (override with LOOKS_VENV=/path), library/luts/*.cube
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
. "$S/scripts/lib/plat.sh"   # VB=bin (Scripts on Windows), py311
V="${LOOKS_VENV:-$HOME/.venvs/ghost-looks}"
PY="${PYTHON311:-$(command -v python3.11 || echo /opt/homebrew/bin/python3.11)}"
[ -z "$IS_WIN" ] || PY="${PYTHON311:-$(py311)}"
[ -x "$V/$VB/python" ] || { [ -n "$PY" ] || { echo "needs Python 3.11 -> $W311" >&2; exit 1; }; "$PY" -m venv "$V"; }
"$V/$VB/python" -m pip install -q --upgrade pip
"$V/$VB/pip" install -q "spectral_film_lut==0.18.12"
"$V/$VB/python" "$S/scripts/gen_luts.py" "$@"
n=$(ls "$S"/library/luts/*.cube 2>/dev/null | wc -l | tr -d ' ')
echo "film looks ready: $n LUTs in $S/library/luts (venv $V)"
