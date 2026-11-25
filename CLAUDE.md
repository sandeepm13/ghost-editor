## Windows port rules (Phase 1)
Read docs/PHASE1-PLAN.md at the start of every session, and update its Status section at the end of every step.
Goal: this skill runs on native Windows 11 the same as on macOS.
Machine: Windows 11, Git Bash, Python 3.12 venv at D:\venvs\ghost-editor, Node 24 at D:\Node, ffmpeg 9 (gyan.dev full build), RTX 3050 Laptop GPU with 4 GB VRAM, 16 GB RAM.
The Windows user folder has a SPACE in it (C:\Users\Sandeep Mopuri). Quote every path, in bash and in code.

1. Never break macOS. Every Windows change is either a branch on `sys.platform == "win32"` (Python) / `process.platform === "win32"` (Node), or works the same on both. The Mac code path must behave exactly as before.
2. Change as little as possible. Don't refactor, reformat or rename upstream code. Small diffs keep future merges from upstream (kurbaitaev/ghost-editor) easy.
3. Never change creative or numeric behaviour: styles, timings, sizes, loudness targets, QA thresholds, take selection. Exception: a value measured by a Mac-only tool (e.g. CAP_RATIO for macOS Vision OCR) gets a separate Windows value that is MEASURED, never guessed.
4. Keep the bash scripts. Run them with Git Bash (C:\Program Files\Git\bin\bash.exe). Never use C:\Windows\System32\bash.exe (WSL) or the WindowsApps bash.exe.
5. All platform logic lives in scripts/plat.py (Python) and scripts/lib/plat.mjs (Node): venv python path, running npx, finding Git Bash, symlink fallback. Use them. Don't copy platform checks into many files.
6. Python venvs keep the repo's names (~/.venvs/ghost-matte, ghost-audioqa, ghost-captions, ghost-looks, media). On Windows their programs are in Scripts\ (python.exe, pip.exe), not bin/.
7. Don't install anything globally or outside a venv without asking me first.
8. After every change: run that step's test, add a row to docs/WINDOWS-PORT.md, and commit with a message starting "win: ". One commit per logical change.
9. When something fails, show me the exact error before trying a big fix.
