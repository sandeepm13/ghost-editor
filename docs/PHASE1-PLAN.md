# Phase 1 plan: ghost-editor on native Windows

## Goal
Make ghost-editor (my fork of kurbaitaev/ghost-editor) run on native Windows 11 exactly as it does on macOS. Phase 1 is ONLY the port: no new styles or features. Later phases (not now): my own video editing skill system on top of this, with more styles (e.g. glassmorphism, neumorphism) and more aspect ratios (e.g. 3:4). So keep the code close to upstream and easy to merge.

## Decisions already made
- Native Windows, not WSL. Bash scripts stay and run in Git Bash.
- All work on the branch windows-port. At the end, a pull request into MY fork's main, never upstream.
- Platform logic goes in scripts/plat.py and scripts/lib/plat.mjs (step 2).
- The Mac code path must behave exactly as before.

## The 8 steps
1. Prepare the workspace: branch, rules, Gemini key, media library, doctor check
2. Shared plumbing: plat.py / plat.mjs, venv paths (Scripts\python.exe), running npx without a shell, python3 calls, symlink fallback
3. HyperFrames on Windows, including the ffmpeg wrapper (HYPERFRAMES_FFMPEG_PATH points at .sh files) and render determinism
4. The core pipeline on a real talking-head video with the clean preset: prep, transcribe, face track, autocut, build, approval sheet, preview, render, QA
5. Whisper on my RTX 3050 (4 GB): add faster-whisper only if turbo doesn't fit, and compare word times first
6. Mac-only features: caption OCR (macOS Vision -> a Windows OCR, measured CAP_RATIO), own-footage folders, sysctl, videotoolbox, CUDA in matte.py, doctor.sh on Windows
7. Optional tools: setup_matte / audioqa / captions / looks, denoise.sh, Python 3.11, CUDA torch
8. One Clean OS reel, a smoke test of every recipe, docs (INSTALL-WINDOWS.md, a short Windows section in SKILL.md), PR to my fork

Phase 1 is done when: doctor.sh ends with "0 missing", the tests in tests/ pass, one clean-preset reel passes finals.py qa, and one Clean OS preview renders.

## Known Windows issues (add new ones here when you find them)
- `python -I` ignores PYTHONUTF8, so scripts started with -I need an explicit encoding="utf-8" on open(). Fix each one as it is found.
- `python -I` also leaves stdout/stderr as cp1252 when they are piped or redirected (not a console), so printing an emoji fails. Fixed in emoji_fetch.py with a win32-only `sys.stdout.reconfigure(encoding="utf-8")`. Other -I scripts may need the same.
- `python -I` removes the script's own folder from sys.path, so a script run with -I cannot `import plat`. Step 2 must handle this (e.g. an explicit sys.path insert, or keep such fixes inline).
- Scripts that rewrite tracked files write CRLF line endings on Windows (seen: library/sfx/manifest.json after library_restore.py). For now, revert those changes. Decide on a proper fix (e.g. newline="\n" when writing tracked files) in a later step, and ask me first.
- npx is npx.cmd on Windows: Python can't find it by name, and Node refuses to spawn .cmd files without shell:true (step 2).
- HYPERFRAMES_FFMPEG_PATH points at .sh wrappers that Node can't start on Windows (step 3).
- matte.py only uses mps or cpu, with no CUDA (step 6).
- Whisper turbo may not fit in 4 GB VRAM (steps 4-5).
- My user folder has a space: C:\Users\Sandeep Mopuri. Quote every path.
- WSL's bash.exe and the WindowsApps bash.exe are also on PATH. Always use Git Bash.
- `mklink` exists only inside cmd.exe, not PowerShell, and PowerShell doesn't expand `%USERPROFILE%`. In PowerShell use `New-Item -ItemType Junction`.
- A folder can't be moved while a running program (VS Code, Claude Code) watches it: Windows says "Access is denied". Close them first.

## When to decide yourself, and when to ask me
Decide yourself, then tell me in the step's report:
- a small fix for a Windows bug, inside the current step, that keeps the Mac behaviour identical and that you have tested (like adding encoding="utf-8")
- reverting changes a script run made to tracked files (generated data, line endings)
- adding log rows and committing with "win: "
Ask me first:
- installing anything, or changing anything outside D:\edit-pipeline
- choosing between two different designs
- changing behaviour, numbers, thresholds or creative output
- a big refactor, or one change across many files
- deleting files
- moving on to the next step

## Status
(update this at the end of every step: step, done / in progress, what's left, open questions)

**Step 1: prepare the workspace: DONE (2026-11-07), waiting for your go to start step 2.**

Done:
- Branch `windows-port` from main; CLAUDE.md port rules; docs/WINDOWS-PORT.md change log.
- Checked the venvs: ghost-matte, ghost-audioqa, ghost-captions and ghost-looks are real (uv Python 3.11.15, packages installed). doctor's "ok" lines are true because each venv has a hand-made `bin` junction to `Scripts` (see WINDOWS-PORT.md, setup section). No `media` venv; the project venv covers it.
- Skills junction `%USERPROFILE%\.claude\skills\ghost-editor` -> `D:\edit-pipeline` created; Claude Code now loads this repo's skill.
- PYTHONUTF8=1 was already set as a user variable.
- GEMINI_API_KEY in .env (gitignored; doctor's test call works).
- library_restore.py: music 23/23, SFX 78/78, memes none (public edition). Emoji first failed 64/64 (cp1252 under `-I`); fixed in emoji_fetch.py, re-run: see WINDOWS-PORT.md.
- Reverted the CRLF + dropped `review` note that the restore made to library/sfx/manifest.json.
- doctor.sh: 23 ok, 0 missing.

Open questions / notes for later:
- CRLF on rewritten tracked files: needs a decision (known issue above).
- sfx_fetch.py drops the `review` field of send-swoosh when it rewrites the manifest. Probably upstream behaviour on Mac too; not a Windows issue, left alone.
- doctor.sh "animated emoji ok" only counts .webm files, not manifest.json, so it said ok while the emoji library was broken. Upstream check; consider in step 6 (doctor.sh on Windows).
- DeepFilterNet shows "not set up": `~/.venvs/venv-df` exists but the repo has no `.venv-df` link to it (the old clone had one). Step 7.
- doctor.sh WARN "x264 threads not pinned" (seoul.py, open_pause.py) is an upstream check, not a Windows issue.
- The `bin` -> `Scripts` junctions in each venv are hand-made; a fresh Windows install won't have them. Step 2 (venv paths in plat.py) should make them unnecessary.
- Old skill clone kept at `%USERPROFILE%\.claude\ghost-editor-old-clone` (163 MB). Delete it when you're happy (your call).
- The Gemini key was pasted into chat; consider rotating it.
