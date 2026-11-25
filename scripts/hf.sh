#!/usr/bin/env bash
# The pinned HyperFrames CLI: `$S/scripts/hf.sh render -o build/reel.mp4` = npx -y hyperframes@<scripts/HF_VERSION> ...
# An HF_VERSION environment variable overrides the file for a one-off test (doctor.sh warns while it is set).
# HyperFrames runs ffmpeg through hf_ffmpeg.sh, which fixes the audio mix's input order (why: hf_mix_order.py).
v="${HF_VERSION:-$(cat "$(dirname "$0")/HF_VERSION")}"
w="$(cd "$(dirname "$0")" && pwd)/hf_ffmpeg.sh"
case "$OSTYPE" in msys* | cygwin*)  # Windows (Git Bash): Node can't start a .sh; the launcher from setup_hf_ffmpeg.py
  w="$(cygpath -w "${w%/*}/win-bin/hf_ffmpeg.exe")"
  [ -n "$HYPERFRAMES_FFMPEG_PATH" ] || [ -f "$w" ] || echo "WARNING $w missing: run python scripts/setup_hf_ffmpeg.py" >&2 ;;
esac
export HYPERFRAMES_FFMPEG_PATH="${HYPERFRAMES_FFMPEG_PATH:-$w}"
exec npx -y "hyperframes@$v" "$@"
