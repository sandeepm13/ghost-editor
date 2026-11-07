#!/usr/bin/env bash
# Check everything ghost-editor needs on this machine, and say how to fix what's missing.
#   bash scripts/doctor.sh
S="$(cd "$(dirname "$0")/.." && pwd)"
ok=0; bad=0
pass() { echo "  ok    $1"; ok=$((ok+1)); }
fail() { echo "  MISS  $1  ->  $2"; bad=$((bad+1)); }
# Windows (Git Bash): venv programs live in Scripts\ (not bin/), python is `python`, fixes come from winget (not brew)
VB=bin; P3=python3; WIN=
case "$OSTYPE" in msys* | cygwin*) WIN=1; VB=Scripts; P3=python ;; esac
fix() { if [ -n "$WIN" ]; then echo "$2"; else echo "$1"; fi; }   # fix "<macOS hint>" "<Windows hint>"

# numpy/opencv/google-genai may live in a separate venv (MEDIA_PY, or ~/.venvs/media) on machines whose python3 has none
PY=${MEDIA_PY:-$P3}; "$PY" -c "import numpy" 2>/dev/null || { [ -x "$HOME/.venvs/media/$VB/python" ] && PY="$HOME/.venvs/media/$VB/python"; }

echo "tools"
command -v ffmpeg >/dev/null && pass "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || fail ffmpeg "$(fix "brew install ffmpeg" "winget install Gyan.FFmpeg")"
ffmpeg -hide_banner -buildconf 2>/dev/null | grep -q enable-libvpx && pass "ffmpeg libvpx (alpha WebM memes)" || fail "ffmpeg libvpx" "$(fix "brew reinstall ffmpeg" "winget install Gyan.FFmpeg (the gyan.dev full build has it)")"
ffmpeg -hide_banner -buildconf 2>/dev/null | grep -q enable-libass && pass "ffmpeg libass" || fail "ffmpeg libass" "$(fix "brew reinstall ffmpeg" "winget install Gyan.FFmpeg (the gyan.dev full build has it)")"
command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ] && pass "node $(node -v)" || fail "node >= 18" "$(fix "brew install node" "winget install OpenJS.NodeJS.LTS")"
if [ -n "$WIN" ]; then  # .sh scripts need Git for Windows' bash, never WSL's System32\bash.exe (python/node find it via plat)
  gb=$("$PY" -c "import sys; sys.path.insert(0, sys.argv[1]); import plat; print(plat.git_bash() or '')" "$S/scripts" 2>/dev/null | tr -d '\r')
  [ "$OSTYPE" = msys ] && [ -n "$gb" ] && pass "Git Bash ($gb)" || fail "Git Bash (Git for Windows; this shell: ${BASH:-?}, found by scripts: ${gb:-none})" "winget install Git.Git, then run bash scripts/doctor.sh from Git Bash"
fi
# HyperFrames is pinned in ONE place (scripts/HF_VERSION), read by hf.sh, hf_version.py and build.mjs
hv=$(cat "$S/scripts/HF_VERSION" 2>/dev/null)
v=$(bash "$S/scripts/hf.sh" --version 2>/dev/null | tail -1)
[ -n "$v" ] && [ "$v" = "${HF_VERSION:-$hv}" ] && pass "hyperframes $v (pinned in scripts/HF_VERSION)" || fail "hyperframes $hv (scripts/HF_VERSION)" "bash $S/scripts/hf.sh --version (needs network once)"
[ -n "$HF_VERSION" ] && [ "$HF_VERSION" != "$hv" ] && echo "  WARN  HF_VERSION=$HF_VERSION overrides scripts/HF_VERSION ($hv): renders here differ from the other machine; unset it after the test"
un=$(grep -rnE 'npx (-y )?hyperframes([^@]|$)|"npx", "hyperframes"' "$S" --include='*.md' --include='*.py' --include='*.sh' --include='*.mjs' --include='*.js' 2>/dev/null | grep -v -e '/public/' -e node_modules | grep -iv -e unpinned -e 'instead of')
[ -z "$un" ] && pass "no unpinned hyperframes calls in the skill" || { echo "  WARN  unpinned hyperframes calls (use \$S/scripts/hf.sh, or hf() from scripts/hf_version.py):"; echo "$un" | sed 's/^/          /'; }
# x264's thread count is pinned in ONE place (scripts/X264_THREADS): on automatic threads it follows the core count and
# each Mac writes different bytes. Every libx264 encode passes it right after libx264; HyperFrames' get it from hf_ffmpeg.sh.
# VideoToolbox's encoder gives different bytes on every run, so no script may use it.
xt=$(cat "$S/scripts/X264_THREADS" 2>/dev/null)
ux=$(grep -rnIE --include='*.py' --include='*.sh' --include='*.mjs' --include='*.js' -- "(-c:v|-vcodec|-codec:v)[\"', ]*(libx264|h264_videotoolbox|hevc_videotoolbox)" "$S" 2>/dev/null \
  | grep -v -e node_modules -e '/\.venv' -e '/scripts/doctor.sh:' | grep -vE -- "libx264[\"', ]*-threads.{0,60}X264_THREADS")


w=${WHISPER:-$(command -v whisper)}; [ -n "$w" ] && pass "whisper ($w)" || fail whisper "pip install openai-whisper (or set WHISPER=/path)"
command -v yt-dlp >/dev/null && pass "yt-dlp $(yt-dlp --version)" || echo "  opt   yt-dlp not installed: only needed to pull a reference video from a link -> $(fix "brew install yt-dlp" "$P3 -m pip install yt-dlp")"
"$PY" -c "import numpy" 2>/dev/null && pass "python numpy ($PY)" || fail numpy "pip install numpy"
"$PY" -c "import cv2; cv2.FaceDetectorYN" 2>/dev/null && pass "python opencv (face tracking)" || fail opencv "pip install opencv-python"
"$PY" -c "import google.genai" 2>/dev/null && pass "python google-genai" || fail "python google-genai (B-roll people/line checks, QA)" "$PY -m pip install google-genai"
"$PY" -c "import PIL" 2>/dev/null && pass "python pillow" || fail pillow "$PY -m pip install pillow"

echo "keys"
# required: insert_prep.py, broll_vision.py and broll_qa.py's people / match checks ask Gemini, and an unchecked shot FAILS
# the render's QA. One cheap call proves the key works (a set but revoked key looks fine until the batch).
if [ -n "$GEMINI_API_KEY" ] || grep -qs '^GEMINI_API_KEY=' "$S/.env"; then
  r=$(S="$S" "$PY" - 2>&1 <<'PYEOF'
import os, re
from google import genai
from google.genai import types
k = os.environ.get("GEMINI_API_KEY")
if not k:
    m = re.search(r"GEMINI_API_KEY\s*=\s*['\"]?([^'\"\n]+)", open(os.path.join(os.environ["S"], ".env")).read())
    k = m.group(1).strip()
c = genai.Client(api_key=k, http_options=types.HttpOptions(timeout=30000))
print((c.models.generate_content(model="gemini-2.5-flash", contents="Reply with the single word ok.").text or "").strip()[:20])
PYEOF
)
  case "$r" in [Oo]k*) pass "GEMINI_API_KEY works (one test call)";;
    *) r=${r##*$'\n'}; fail "GEMINI_API_KEY is set but the test call failed: ${r:0:140}" "check the key at aistudio.google.com/apikey (env or $S/.env)";; esac
else fail "GEMINI_API_KEY (insert_prep.py, broll_vision.py, broll_qa.py people/match: unchecked shots fail)" "export GEMINI_API_KEY=... or put GEMINI_API_KEY=... in $S/.env (free key: aistudio.google.com/apikey)"; fi

if [ -n "$ELEVENLABS_API_KEY" ] || grep -qs '^ELEVENLABS_API_KEY=' "$S/.env"; then pass "ELEVENLABS_API_KEY (narrated explainers)"; else echo "  opt   ELEVENLABS_API_KEY not set: only scripts/tts_elevenlabs.py (explainer voiceover) needs it -> $S/.env"; fi
[ -x "${DF_VENV:-$S/.venv-df}/$VB/deepFilter" ] && pass "DeepFilterNet (scripts/denoise.sh)" || echo "  opt   DeepFilterNet not set up: scripts/denoise.sh installs it on first use (needs python3.11 + uv)"

echo "optional tools (the core skill works without them)"
[ -f "$S/templates/vendor/hf-paper.js" ] && pass "Paper Shaders bundle (templates/vendor/hf-paper.js)" || fail "templates/vendor/hf-paper.js (shader looks)" "git checkout templates/vendor, or rebuild: cd $S/tools/paper && npm install && node build-vendor.mjs"
e=$(ls "$S"/library/emoji/*.webm 2>/dev/null | wc -l | tr -d ' ')
[ "$e" -ge 30 ] && pass "animated emoji ($e Fluent webm)" || echo "  opt   animated emoji not fetched: emoji beats fall back to the font glyph -> $P3 -I $S/scripts/emoji_fetch.py (needs ffmpeg libvpx-vp9)"
l=$(ls "$S"/library/luts/*.cube 2>/dev/null | wc -l | tr -d ' ')
[ "$l" -ge 6 ] && pass "film-look LUTs ($l in library/luts)" || echo "  opt   film-look LUTs not generated: only look.film needs them -> bash $S/scripts/setup_looks.sh (venv ~/.venvs/ghost-looks)"
[ -x "${MATTE_VENV:-$HOME/.venvs/ghost-matte}/$VB/python" ] && pass "BiRefNet matte (behind beats, cutout beats)" || echo "  opt   BiRefNet matte not set up: behind beats fall back to hyperframes remove-background (u2net), cutout beats need it -> bash $S/scripts/setup_matte.sh (~2.6 GB with weights)"
mc="${CUTOUT_FX_CACHE:-${GHOST_MATTE_CACHE:-$HOME/.cache/ghost-matte}}"
[ -x "${MATTE_VENV:-$HOME/.venvs/ghost-matte}/$VB/python" ] && [ ! -f "$mc/hf/BiRefNet_lite/model.safetensors" ] && echo "  opt   BiRefNet_lite weights not cached: cutout beats will download them (176 MB) on first use -> bash $S/scripts/setup_matte.sh"
[ -x "${AUDIOQA_VENV:-$HOME/.venvs/ghost-audioqa}/$VB/python" ] && pass "audio QA venv (vad_pauses, voice_enhance)" || echo "  opt   audio QA venv not set up: only autocut --vad, vad_pauses.py and voice_enhance.py need it -> bash $S/scripts/setup_audioqa.sh"
[ -x "${CAPTIONS_VENV:-$HOME/.venvs/ghost-captions}/$VB/python" ] && pass "caption metrics venv (scripts/font_metrics.py)" || echo "  opt   caption metrics venv not set up: only needed to add a font to the caption templates -> bash $S/scripts/setup_captions.sh"

if [ -n "$WIN" ]; then  # macOS reads captions with Vision (part of the OS); Windows needs RapidOCR in the project python
  "$PY" -c "import rapidocr_onnxruntime" 2>/dev/null && pass "caption OCR (RapidOCR: broll_qa.py caption size/contrast)" || echo "  opt   caption OCR not installed: broll_qa.py skips the caption size/contrast check -> $PY -m pip install rapidocr-onnxruntime==1.4.4"
fi

echo "recipes"
ls "$S"/templates/fonts/inter-tight-cyrillic.woff2 "$S"/templates/fonts/playfair-display-italic-cyrillic.woff2 >/dev/null 2>&1 && pass "Seoul list / RESULT fonts (Inter Tight, Playfair Display, OFL)" || fail "templates/fonts/inter-tight-*.woff2" "git -C $S checkout templates/fonts"
miss=""; for e in waving-hand hand-splayed point-right running yum eyes fire; do [ -f "$S/library/emoji/$e.webm" ] || miss="$miss,$e"; done
[ -z "$miss" ] && pass "Seoul list emoji (hands, eyes, runner, yum, fire)" || echo "  opt   Seoul list emoji missing (${miss#,}) -> $P3 -I $S/scripts/emoji_fetch.py --only ${miss#,}"
[ -f "$S/library/sfx/send-swoosh.wav" ] && pass "Seoul list send sound (send-swoosh)" || echo "  opt   send-swoosh not fetched (Seoul list outro) -> $P3 $S/scripts/sfx_fetch.py --only send-swoosh"

echo "library"
n=$(ls "$S"/library/sfx/*.wav 2>/dev/null | wc -l | tr -d ' ')
[ "$n" -ge 30 ] && pass "sfx kit ($n files)" || fail "sfx kit ($n files)" "$P3 $S/scripts/library_restore.py --sfx-only"
m=$(ls "$S"/library/memes/*/clip.webm "$S"/library/memes/*/image.png 2>/dev/null | wc -l | tr -d ' ')
if [ "$m" -ge 1 ]; then pass "memes ($m)"
elif [ -f "$S/.public-edition" ]; then echo "  opt   memes: none (public edition; add clips you have rights to with scripts/meme_add.py)"
else fail "memes" "$P3 $S/scripts/library_restore.py --memes-only"; fi
ls "$S"/library/music/*.mp3 >/dev/null 2>&1 && pass "music beds" || fail "music beds" "$P3 $S/scripts/library_restore.py --music-only"

echo "toolchain vs the other machine (scripts/toolchain.py: records this one in library/toolchain/, compares)"
tc=$("$P3" "$S/scripts/toolchain.py" compare 2>&1); tcr=$?
echo "$tc" | sed -e 's/^  DIFF /  WARN  /' -e 's/^  info /  info  /' -e 's/^vs /  /' -e 's/^no other/  opt   no other/'
[ "$tcr" -ne 0 ] && echo "        the WARN lines change the edit (cut, mix or render); align them (docs/SYNC.md, Toolchain parity)"

echo; echo "$ok ok, $bad missing"
[ "$bad" -eq 0 ]
