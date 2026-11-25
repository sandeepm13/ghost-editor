#!/usr/bin/env bash
# Optional: the small venv for scripts/font_metrics.py, which regenerates scripts/lib/metrics.json (the glyph widths the
# caption templates lay out with) after a font is added to templates/fonts. The caption templates themselves need nothing.
#   bash scripts/setup_captions.sh            -> ~/.venvs/ghost-captions (override with CAPTIONS_VENV=/path)
set -euo pipefail
. "$(dirname "$0")/lib/plat.sh"   # VB=bin (Scripts on Windows), py311
V="${CAPTIONS_VENV:-$HOME/.venvs/ghost-captions}"
PY="${PYTHON311:-$(command -v python3.11 || command -v python3)}"
[ -z "$IS_WIN" ] || { PY="${PYTHON311:-$(py311)}"; [ -n "$PY" ] || PY=$(command -v python); }   # Windows: no python3
[ -x "$V/$VB/python" ] || "$PY" -m venv "$V"
"$V/$VB/python" -m pip install -q --upgrade pip
"$V/$VB/pip" install -q "fonttools==4.66.1" "brotli==1.2.0"
"$V/$VB/python" -c "import fontTools, brotli" && echo "captions venv ready: $V"
