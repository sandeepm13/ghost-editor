# Platform helpers for the .sh scripts: the bash twin of scripts/plat.py and scripts/lib/plat.mjs (bash can't import
# those). Off Windows every value is what the scripts used before, so macOS behaves exactly as without this file.
#   . "$(dirname "$0")/lib/plat.sh"
#   IS_WIN        1 under Git Bash (MSYS / Cygwin) on Windows, else empty
#   VB            a venv's program folder: bin; on Windows Scripts (python.exe, pip.exe, deepFilter.exe)
#   py311         (Windows) prints the Python 3.11 to build venvs with: `py -3.11`, else python3.11 on PATH (e.g. uv's
#                 shim in ~/.local/bin); prints nothing when there is none
#   torch_cuda T  (Windows) torch / torchvision / torchaudio from PyTorch's CUDA index T (cu126, ...): pip gets it as an
#                 extra index (its +cuXXX wheel outranks PyPI's CPU-only one), uv as --torch-backend. No-op elsewhere
#   W311          the install hint for a missing Python 3.11 on Windows
IS_WIN=; VB=bin
case "$OSTYPE" in msys* | cygwin*) IS_WIN=1; VB=Scripts ;; esac
W311="winget install Python.Python.3.11 (or: uv python install 3.11)"

py311() {
  local p
  p=$(py -3.11 -c "import sys; print(sys.executable)" 2>/dev/null | tr -d '\r') || p=
  # the interpreter's own path (python.exe), not the name on PATH: `uv venv -p` needs the real file
  [ -n "$p" ] || p=$(python3.11 -c "import sys; print(sys.executable)" 2>/dev/null | tr -d '\r') || p=
  echo "$p"
}

torch_cuda() {
  [ -n "$IS_WIN" ] || return 0
  export PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/$1" UV_TORCH_BACKEND="$1"
}
