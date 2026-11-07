#!/usr/bin/env bash
# Optional: the audio QA tools -- scripts/vad_pauses.py (silero-vad speech islands) and scripts/voice_enhance.py
# (ClearerVoice MossFormer2 enhance / super-resolution). One venv (~1.2 GB with torch) plus weights in ~/.cache/ghost-audioqa
# (ClearerVoice SE + SR ~0.65 GB, Apache-2.0). Prints the venv's python path on the last line.
#   bash scripts/setup_audioqa.sh [--no-clearvoice]   -> ~/.venvs/ghost-audioqa (AUDIOQA_VENV), ~/.cache/ghost-audioqa (GHOST_AUDIOQA_CACHE)
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
. "$S/scripts/lib/plat.sh"   # VB=bin (Scripts on Windows), py311, torch_cuda
V="${AUDIOQA_VENV:-$HOME/.venvs/ghost-audioqa}"
C="${GHOST_AUDIOQA_CACHE:-$HOME/.cache/ghost-audioqa}"
# pinned to the tested set: clearvoice's resolver otherwise picks torch 2.14 + torchaudio 2.11 (mismatched ABI)
PKGS=("clearvoice==0.1.2" "silero-vad==6.2.3" "torch==2.8.0" "torchaudio==2.8.0" "torchvision==0.23.0" "numpy==1.26.4"
      "pyloudnorm==0.2.0" "matplotlib==3.11.2" "python_speech_features==0.6" "opencv-python==4.10.0.84" "soundfile==0.12.1")
if [ ! -x "$V/$VB/python" ]; then
  PY="${PYTHON311:-$(command -v python3.11 || echo /opt/homebrew/bin/python3.11)}"
  [ -z "$IS_WIN" ] || PY="${PYTHON311:-$(py311)}"
  [ -n "$PY" ] || { echo "needs Python 3.11 -> $W311" >&2; exit 1; }
  if command -v uv >/dev/null; then uv venv -q -p "$PY" "$V"; else "$PY" -m venv "$V"; fi
fi
torch_cuda cu126   # Windows: torch/torchaudio/torchvision 2.8.0+cu126 (NVIDIA); macOS keeps PyPI's
if command -v uv >/dev/null; then VIRTUAL_ENV="$V" uv pip install -q "${PKGS[@]}" >&2
else "$V/$VB/python" -m pip install -q "${PKGS[@]}" >&2; fi
mkdir -p "$C"
[ "${1:-}" = "--no-clearvoice" ] || GHOST_AUDIOQA_MODELS="$C/clearvoice" "$V/$VB/python" "$S/scripts/voice_enhance.py" --fetch-only >&2
"$V/$VB/python" -c "import silero_vad, clearvoice, python_speech_features, cv2" >&2
echo "$V/$VB/python"
