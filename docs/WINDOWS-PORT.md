# Windows port: change log

Every Windows change on the `windows-port` branch gets one row here. Rules are in [CLAUDE.md](../CLAUDE.md), the plan and status in [PHASE1-PLAN.md](PHASE1-PLAN.md).

| file | change | why | tested how |
|---|---|---|---|
| CLAUDE.md | added Windows port rules (Phase 1) | one set of rules for every Windows change | n/a (docs) |
| docs/WINDOWS-PORT.md | added this change log | track each Windows change and its test | n/a (docs) |
| scripts/emoji_fetch.py | win32-only `sys.stdout/stderr.reconfigure(encoding="utf-8")`; `encoding="utf-8"` on the manifest read and write | it runs under `python -I`, which ignores PYTHONUTF8: piped stdout was cp1252 and all 64 emoji failed | `python -I scripts/emoji_fetch.py` re-run: 64 emoji (step 1) |
| docs/PHASE1-PLAN.md | the Phase 1 plan, known Windows issues, status | one place for the plan and where it stands | n/a (docs) |
| scripts/plat.py, scripts/lib/plat.mjs | new: IS_WIN, venv_python/venv_bin, npx_cmd, python_cmd, link_or_copy, git_bash (camelCase in Node). Off Windows each returns what the code used before | one home for every platform check (rule 5) | `python scripts/plat.py`, `node scripts/lib/plat.mjs` print each value; npx through both runs npm 12.2.0 like plain `npx`; link_or_copy gives a hard link here (no Developer Mode); GIT_BASH set to WSL's or the WindowsApps bash is skipped; non-Windows branch asserted equal to the old strings |
| scripts/approval_sheet.py, autocut.py, toolchain.py, brand_kit.py, finals.py, build.mjs; recipes/seoul-list/prep.py, caption-news/captionnews.py, product-page/productpage.py | venv pythons via `venv_python()` / `venvPython()` instead of `<venv>/bin/python` (matte, audioqa, media, ghost-captions) | Windows venvs keep python.exe in `Scripts\`; the hand-made `bin` junctions are no longer needed by this code | each file `--help` / imports; `toolchain.py show` probes the audioqa venv at `Scripts\python.exe`; `autocut.py --vad` on a Windows-TTS speech wav runs vad_pauses.py in the audioqa venv: 3 takes, 1.5 s pause cut; `node --check build.mjs`. finals.py can't import on Windows (`fcntl`, upstream, also before this change) |
| scripts/hf_version.py (`hf()`), scripts/build.mjs (remove-background) | npx via `npx_cmd()` / `npxCmd()` instead of `"npx"` | npx is npx.cmd on Windows: Python can't find it by name, Node won't spawn a .cmd without shell:true | `subprocess.run(hf("--version"))` and Node `execFileSync` with no shell, cwd with a space: hyperframes 0.8.159 (same as plain `npx`, same npm 12.2.0); approval_sheet, framecheck, qa, save_style, seoul-list/snap.py `--help` |
| recipes/seoul-list/build.mjs (transitions spawn), scripts/toolchain.py (`media_py()`) | `pythonCmd()` instead of `"python3"` (Node: `$GHOST_PYTHON`, else `python` on Windows, `python3` elsewhere); toolchain on Windows tries the running python instead of `python3` | `python3` on a Windows PATH may be the Microsoft Store stub, and a stock venv has only python.exe | `toolchain.py show`: media_python = the project venv's python.exe; the exact `python -c` program seoul-list/build.mjs spawns starts and imports transitions (its render then fails inside transitions.py, the same with `python3`: see PHASE1-PLAN.md known issues); `node --check` |

## Setup done on this machine

Not code changes. Kept here so we can write the Windows install guide (INSTALL-WINDOWS.md, step 8) from what actually worked.

| what | how | notes |
|---|---|---|
| Git Bash | Git for Windows 2.48.1 (`C:\Program Files\Git\bin\bash.exe`) | Run every `.sh` with this bash, never WSL's or the WindowsApps one |
| Node | v24.21.0 at `D:\Node` (on PATH) | hyperframes 0.8.159 runs through `npx` (pinned in scripts/HF_VERSION), not installed globally |
| ffmpeg | 9.0.2 gyan.dev full build via winget (`Gyan.FFmpeg`) | doctor: libvpx and libass ok |
| Project venv | `D:\venvs\ghost-editor`, Python 3.12.10, its `Scripts\` first on PATH so `python` is this venv | has whisper, yt-dlp 2026.10.21, numpy, opencv, google-genai, pillow. Covers what `~/.venvs/media` is on a Mac (no `media` venv here) |
| Optional venvs | `~/.venvs` is a junction to `D:\ghost-editor-data\venvs`; ghost-matte, ghost-audioqa, ghost-captions, ghost-looks, venv-df made with uv 0.11.15 (Python 3.11.15) | Each venv has a hand-made `bin` junction to `Scripts`, which is why doctor's `~/.venvs/<name>/bin/python` checks pass. A fresh install won't have these until step 2. ghost-matte has torch 2.14.1+cu126 |
| uv | 0.11.15 at `~/.local/bin/uv` | Python 3.11 lives under `%APPDATA%\uv\python` |
| PYTHONUTF8 | `1` as a user environment variable (was already set) | Not enough on its own: `python -I` ignores it (see PHASE1-PLAN.md, known issues) |
| Gemini key | `GEMINI_API_KEY=...` in `D:\edit-pipeline\.env` | `.env` is gitignored (`.gitignore:13`); doctor's test call works |
| Media library | `python scripts/library_restore.py` | music 23/23, SFX 78/78, memes none (public edition), emoji 64 after the emoji_fetch.py fix. Revert `library/sfx/manifest.json` afterwards (CRLF) |
| Skill visible to Claude Code | Old clone moved to `%USERPROFILE%\.claude\ghost-editor-old-clone`, then in **cmd**: `mklink /J "%USERPROFILE%\.claude\skills\ghost-editor" "D:\edit-pipeline"` | `mklink` is cmd-only. Close VS Code and Claude Code before moving the old folder, or Windows says "Access is denied". PowerShell: `New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\ghost-editor" -Target "D:\edit-pipeline"` |
