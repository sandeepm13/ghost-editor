# Windows port: change log

Every Windows change on the `windows-port` branch gets one row here. Rules are in [CLAUDE.md](../CLAUDE.md), the plan and status in [PHASE1-PLAN.md](PHASE1-PLAN.md).

| file | change | why | tested how |
|---|---|---|---|
| CLAUDE.md | added Windows port rules (Phase 1) | one set of rules for every Windows change | n/a (docs) |
| docs/WINDOWS-PORT.md | added this change log | track each Windows change and its test | n/a (docs) |
| scripts/emoji_fetch.py | win32-only `sys.stdout/stderr.reconfigure(encoding="utf-8")`; `encoding="utf-8"` on the manifest read and write | it runs under `python -I`, which ignores PYTHONUTF8: piped stdout was cp1252 and all 64 emoji failed | `python -I scripts/emoji_fetch.py` re-run: 64 emoji (step 1) |
| docs/PHASE1-PLAN.md | the Phase 1 plan, known Windows issues, status | one place for the plan and where it stands | n/a (docs) |

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
