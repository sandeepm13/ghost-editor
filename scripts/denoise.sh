#!/usr/bin/env bash
# Speech denoise for outdoor takes (crickets, hum, wind): DeepFilterNet3, attenuation capped at 20 dB.
#   bash $S/scripts/denoise.sh <video-or-audio> <out.wav> [atten_db=20]
# Full strength removes the noise but leaves a thin, "watery" voice (A/B checked on reel-c007);
# 20 dB + a little low-mid warmth (done later in the cut) sounds natural.
# First run creates a Python 3.11 venv at <skill>/.venv-df (no py3.13 wheel exists; building needs Rust).
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
. "$S/scripts/lib/plat.sh"   # VB=bin (Scripts on Windows), py311, torch_cuda
IN="$1"; OUT="$2"; ATT="${3:-20}"
V="${DF_VENV:-$S/.venv-df}"
if [ ! -x "$V/$VB/deepFilter" ]; then
  PY=$(command -v python3.11 || echo /opt/homebrew/bin/python3.11)
  [ -z "$IS_WIN" ] || PY=$(py311)
  [ -x "$PY" ] || { echo "needs python3.11 ($([ -n "$IS_WIN" ] && echo "$W311" || echo "brew install python@3.11"))"; exit 1; }
  command -v uv >/dev/null || { echo "needs uv (pip install uv)"; exit 1; }
  echo "setting up DeepFilterNet in $V (one time, ~1 GB with torch)..."
  uv venv -q -p "$PY" "$V"
  torch_cuda cu124   # Windows: torch 2.5.1+cu124 (NVIDIA); PyTorch has no cu126 wheels before 2.6 (the pin below)
  VIRTUAL_ENV="$V" uv pip install -q deepfilternet "torch<2.6" "torchaudio<2.6" soundfile
fi
TMP=$(mktemp -d)
ffmpeg -v error -y -i "$IN" -vn -ac 1 -ar 48000 "$TMP/in.wav"
"$V/$VB/deepFilter" "$TMP/in.wav" --atten-lim "$ATT" -o "$TMP/out" >/dev/null 2>&1
mv "$TMP"/out/*.wav "$OUT"
rm -rf "$TMP"
for f in "$IN" "$OUT"; do printf "%s: " "$(basename "$f")"; ffmpeg -hide_banner -nostats -i "$f" -af volumedetect -f null - 2>&1 | grep -o "mean_volume: [-0-9.]* dB"; done
echo "-> $OUT"
