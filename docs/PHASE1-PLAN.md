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
- HYPERFRAMES_FFMPEG_PATH points at .sh wrappers that Node can't start on Windows. FIXED in step 3 (scripts\win-bin\*.exe launchers; run `python scripts/setup_hf_ffmpeg.py` once per machine).
- (step 3) Git Bash garbles some arguments when a native program starts bash.exe with them (`q"uote` and non-ASCII args got merged). Not seen with real ffmpeg args; matters only for .sh scripts started from Python/Node with such args.
- matte.py only uses mps or cpu, with no CUDA. Code FIXED in step 6 (cuda fp16); the real run is step 7.
- Whisper turbo may not fit in 4 GB VRAM (steps 4-5).
- My user folder has a space: C:\Users\Sandeep Mopuri. Quote every path.
- WSL's bash.exe and the WindowsApps bash.exe are also on PATH. Always use Git Bash.
- `mklink` exists only inside cmd.exe, not PowerShell, and PowerShell doesn't expand `%USERPROFILE%`. In PowerShell use `New-Item -ItemType Junction`.
- A folder can't be moved while a running program (VS Code, Claude Code) watches it: Windows says "Access is denied". Close them first.
- (found in step 2) finals.py can't even be imported on Windows: `import fcntl` (line 53) -> `ModuleNotFoundError: No module named 'fcntl'`. Upstream, also before step 2. Blocks `finals.py qa` (step 4).
- (step 2) transitions.py: `render_junction(..., "zoom_blur", ...)` fails on Windows: the window it writes (win_expr: parallel FFV1 chunks joined with the concat demuxer, transitions.py:538-540) is corrupt: `[in#0] Duplicate element ... 0x00 at pos 110 (0x6e) invalid as first byte of an EBML number ... Error opening input file ...\txj-...\w.mkv`. Same with `python3`, so not caused by step 2. Root cause not confirmed yet. Hits build.mjs `transitions` and the Seoul list `tx`.
- (step 2) recipes/seoul-list/seoul.py:103 pastes Windows paths into a `python -c` string inside single quotes: `'C:\Users\...'` is a `\U` escape -> `SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 2-3`. Small fix (pass the paths in sys.argv); step 8 Seoul smoke test, or earlier if you say so.
- (step 2) build.mjs `die()` hints (lines ~283, 300, 334: look.film, look.cutout, transitions) print Mac commands (`python3`, `~/.venvs/ghost-matte/bin/python`, unquoted paths with backslashes) that won't run as-is in Git Bash. Not executed by the code; fix when step 4 hits them.
- (step 2) Symlinks need Developer Mode or admin (`[WinError 1314] A required privilege is not held by the client`). link_or_copy then makes a hard link (or a copy across drives). Unlike a symlink, a hard link no longer follows the source if a tool replaces the file with a new one (write-to-temp + rename); ffmpeg -y rewrites in place, so a hard link still follows that. Turning on Developer Mode gives real symlinks with no code change.
- (step 2) The tests in tests/ are standalone scripts, not pytest tests, and pytest isn't installed. Run them as their docstrings say (test_cutout_fx.py and test_decode_levels.py with the ghost-matte python).
- (step 3) HyperFrames 0.8.159 starts ffmpeg (HYPERFRAMES_FFMPEG_PATH, resolved by findFfBinary) with plain child_process spawn/execFile, no shell, no cross-spawn/execa (7 call sites). Node 24 refuses the .sh (`spawn EFTYPE`) and any .cmd/.bat (`spawn EINVAL`), so the wrapper must be a real .exe.
- (step 3) hf_mix_order.py ends with os.execv. On Windows that doesn't replace the process: it starts ffmpeg and exits at once with code 0, so the caller doesn't wait for ffmpeg and never sees its exit code. FIXED in step 3 (win32 branch).
- (step 4) ffprobe.exe/ffmpeg.exe print CRLF: in Git Bash `$(ffprobe ...)` keeps the `\r`, so numbers compare wrong (`[: 3838: integer expression expected`). FIXED in prep.sh; other .sh scripts that read ffprobe output (rawcut_prep.sh, denoise.sh, seoul-list/proxy.sh, ...) need the same `tr -d '\r'` when they are hit.
- (step 4) GNU tr refuses reversed ranges like `',- '` (BSD tr on macOS doesn't). FIXED in prep.sh; grep other .sh for `tr` sets with a `-` in the middle when they are hit.
- (step 4) A Windows path inside an ffmpeg filter option (`lut3d=file=D:/...`) breaks on the drive colon. FIXED in grade_lib.sdr_vf via plat.ff_filter_path; NOT yet in insert_prep.py:167 and house_look.py:140 (same pattern).
- (step 4) macOS `open` in Python: FIXED in approval_sheet.py via plat.open_path; NOT yet in audition.py:55.
- (step 4) Whisper on a recording joined from several clips smears words across the joins (and into trimmed pauses): words in the audio got no caption. Workaround used: re-transcribe the cut voice (the skill's rough-cut audit) and map it back to original seconds (build/words.cut.json). Not a Windows issue.
- (step 4) Peak VRAM for whisper turbo (openai-whisper CLI, fp32, CUDA): 3883 MiB of 4096 with ~576 MiB used by the desktop. It fits, with ~200 MiB spare; a browser or game on the GPU at the same time could push it out. Triton is missing, so word timing uses the slower non-Triton kernels (a warning, not an error).
- (step 5) faster-whisper 1.2.1's own audio decoding breaks with av 19: `TypeError: open() got an unexpected keyword argument 'metadata_errors'`. transcribe.py's faster path decodes with ffmpeg instead (any av works).
- (step 5) CTranslate2 needs cublas64_12.dll / cuDNN 9 on PATH (os.add_dll_directory is not enough). plat.cuda_dlls() puts torch\lib first on PATH.
- (step 6) C: ran full (0 bytes free) during step 6; tests/ then failed with ffmpeg exit 4294967268 (-28, ENOSPC) in %TEMP%. With TEMP/TMP on D: they pass. Cause of the growth not found (the calibration renders used D:).
- (step 6) grade_lib.guess_kind's provenance regexes (`/stock/`, `/broll_dl/`, `/ai/`) and own_footage.py's file walk use `/`; on Windows paths have `\`, so a stock clip found only by its folder name reads "unknown". Not fixed (not hit yet); own_footage's SKIP is fixed.
- (step 6) Caption OCR (RapidOCR) reads Latin, not Cyrillic: Russian captions and the "Latin text in a Cyrillic reel" check don't work on Windows. A Cyrillic RapidOCR model would need a new install and its own calibration.
- (step 6) NVENC is unusable with this driver: ffmpeg 9 needs NVENC API 13.1 (driver >= 610), the driver has 12.2. Recorded only (toolchain.py); renders never use it.
- (step 7) `py -3.11` finds no Python here: the 3.11 is uv's (cpython-3.11.15, registered with the launcher only as `-V:Astral/CPython3.11.15`). plat.sh's py311 falls back to `python3.11` (uv's shim in ~/.local/bin) and uses its sys.executable (uv can't use the shim path).
- (step 7) PyTorch has no cu126 wheels before torch 2.6; denoise.sh pins `torch<2.6`, so its Windows venv uses cu124 (torch 2.5.1+cu124).
- (step 7) matte.py / cutout_fx.py on the step-4 footage (handheld phone, a fine plaid shirt): almost every frame counts as a "cut" (64x64 thumb diff median 2.8-3.7 vs the 1.5 threshold; matte's decoder and plain ffmpeg agree), so the temporal smoothing resets every frame. Same code and footage on a Mac would do the same: not Windows. Worth a look if mattes shimmer.
- (step 7) cutout_fx.py `bench` calls `os.getloadavg()`, which Windows doesn't have (AttributeError). Not run in step 7; small fix when needed.
- (step 7) Per-process VRAM: nvidia-smi shows `[N/A]` per process on Windows (WDDM); measure GPU totals minus the desktop baseline.
- (step 3) Without the wrapper, x264 picks threads=18 here (12 logical cores); the MP4's x264 settings string shows it (`grep -a threads=`). With the wrapper it must say threads=12.

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

**Step 8: Clean OS, smoke tests, docs, PR: DONE (2026-11-07), except one Phase 1 criterion (below).**

- Clean OS reel D:\reels\cleanos-1 from talk.mp4 (step 4's 27 takes; tight 1.3 upscaled, your choice: no 4K source):
  denoise.sh, assemble.py (--alt), transcribe the cut voice, fetch_fonts, face_track on the plate, reel.py on the builder
  (4 scenes, 2 chest cards, 2 top widgets, Figma x3, pen, hero, QuickType), lint 0 errors, snap.py beats, finals.py preview:
  `D:\reels\cleanos-1\finals\C1 - Clean OS (preview).mp4` (629 s, 720x1280, 55.3 s, -14.1 LUFS, TP -1.6). One Windows-run fix:
  assemble.py's frame count (`'1646,'`, upstream ffprobe quirk). components.py add/record not run (it edits catalog.json;
  a test reel shouldn't enter the style's history).
- Recipes: all 14 builders start (7 print their --api, 7 are library modules that import cleanly; seoul build.mjs needs a
  project). explainer-vector, pov-montage, stan-style have no builder (core scripts only).
- tests/ 3 of 3 pass; doctor.sh 26 ok, 0 missing.
- Docs: INSTALL-WINDOWS.md (new), SKILL.md "0b. On Windows", WINDOWS-PORT.md summary.
- Commits made by Claude this once (you asked), pushed, PR into the fork's main.

Phase 1 checklist:
- [x] doctor.sh ends with "0 missing" (26 ok)
- [x] the tests in tests/ pass (3 of 3)
- [ ] one clean-preset reel passes finals.py qa: NOT YET. Step 4's reel renders and qa runs, but fails on that reel's creative
      budgets (speaker 63.9 %, inserts 5.4/min, a face in the footage, an animation hold, a VFR plate). Waiting for your call
      on the animations (step 4 open questions).
- [x] one Clean OS preview renders

**Step 7: optional tools: DONE (2026-11-07).**

Built (8 WINDOWS-PORT.md rows; not committed, you commit): scripts/lib/plat.sh (new, bash twin of plat.py), setup_matte / setup_audioqa / setup_captions / setup_looks / denoise.sh on it, cutout_fx.py cuda (it had its own mps-or-cpu device), gen_luts.py `as_posix` (looks.json got `split\...` on Windows).
Python 3.11: you chose uv's 3.11.15 (no install); `py -3.11` finds none, py311 falls back to python3.11. torch: matte + audioqa cu126, denoise cu124 (pin `torch<2.6`). Requirement files unchanged.
All tested in fresh venvs under D:\ghost-editor-data\venvs-test (your ~/.venvs untouched):

| tool | works | speed | notes |
|---|---|---|---|
| setup_matte.sh | yes | 9 min 6 s (fresh, torch download) | torch 2.14.1+cu126 |
| matte.py lite | yes, cuda fp16 | 0.265 s/frame infer, 84 s for 3 s | peak GPU 2252 MiB (698 desktop) |
| matte.py portrait | yes, cuda fp16 | 0.64 s/frame infer, 116 s for 3 s | peak GPU 3354 / 4096 MiB (777 desktop): fits, default unchanged |
| cutout_fx.py bg-blur | yes, cuda (after the fix) | 1 min 46 s for 3 s | peak 2261 MiB |
| setup_audioqa.sh | yes (after the py311 fix) | 3 min 47 s | torch 2.8.0+cu126 |
| vad_pauses.py | yes | 15-20x real time (CPU, 1 thread, as on Mac) | same JSON as the CPU-torch venv |
| setup_captions.sh | yes | 53 s | font_metrics.py widths match |
| setup_looks.sh | yes | 2 min 37 s | 24 LUTs; looks.json = tracked except CRLF |
| film_look.py still | yes | 0.5 s | grain via spectral_film_lut with the looks venv |
| denoise.sh | yes, cuda | first run 2 min 46 s (builds the venv), then 15 s for 76 s | repeatable; floor -61.2 -> -64.0 dB |

Open questions:
- Swap the real ~/.venvs/* for the tested ones (or re-run the scripts into ~/.venvs)? ghost-audioqa and venv-df there still have CPU torch; the hand-made `bin` junctions are no longer needed by any code. Your call (deleting/replacing venvs).
- denoise.sh's default venv is `<repo>\.venv-df`; on this PC the old one lives in ~/.venvs/venv-df (doctor: "not set up" unless DF_VENV is set). Set DF_VENV permanently, or let the first run build .venv-df?
- CRLF in tracked files written by scripts (looks.json now too): still waiting for your decision (step 1).
- Earlier open questions (steps 4-6) unchanged.

**Step 6: Mac-only features: DONE (2026-11-07), except matte.py's CUDA run (step 7, as planned).**

Built (6 WINDOWS-PORT.md rows + 1 setup row; not committed, you commit):
1. Caption OCR: scripts/ocr_text_rapid.py (RapidOCR, same output as ocr_text.js), `plat.ocr_cmd()`, broll_qa.py `CAP_RATIO_RAPID = 1.06` (your choice). rapidocr-onnxruntime 1.4.4 in the project venv (you approved).
   Calibration (15 renders in D:\reels\ocr-calib, 271 caption events; box height / CSS size, events at 48-54 px):

   | font (style) | 48 px | 54 px | 64 px | 92 px | 120 px |
   |---|---|---|---|---|---|
   | Geist (clean) | 1.062 | 1.056 | 1.062 | 0.973 | 0.958 |
   | Montserrat (clean) | 1.167 | 1.130 | 1.141 | 1.082 | 1.008 |
   | Arial (house, stroke) | 1.292 | 1.204 | 1.195 | 1.142 | 1.058 |

   Pooled near the threshold 1.13. Spread inside a font comes from the letters: lines with ascenders and descenders ~1.13, ascenders only ~0.92, x-height only ~0.73. With 1.06 no caption >= 54 px reads small in any of the three fonts; too-small Arial (~40-47 px) / Montserrat (~44-47 px) could pass. W1 - clean.mp4: captions skip -> warn (median 63 px for 64 px Montserrat).
2. Own footage: `plat.own_footage_roots()` (here ~\Videos and ~\OneDrive\Pictures; `OWN_FOOTAGE_ROOTS` overrides), SKIP on `\` paths.
3. cutout_fx.platform_name(): `AMD Ryzen 5 5600H with Radeon Graphics, 16 GB, NVIDIA GeForce RTX 3050 Laptop GPU`.
4. toolchain.py: `ffmpeg.h264_nvenc` = false here (driver too old for ffmpeg 9's NVENC; recorded only).
5. matte.py: cuda fp16 between mps and cpu. Compiles; the real run is step 7.
6. doctor.sh: Windows-aware; Mac path checked line for line against the old output; here 25 ok, 0 missing.
7. brew messages: only doctor.sh's are seen in normal use on Windows (done in 6). Left: setup_matte/looks/audioqa.sh, denoise.sh (step 7), hf_ffmpeg.sh (not used on Windows).
tests/: 3 pass (assemble_sync and decode_levels needed TEMP on D:, C: was full).

Open questions:
- C: is full (see known issues). Free space there, or set TEMP/TMP to D: permanently? (Same question as step 4.)
- OCR speed: ~1.7 s per frame on the CPU (~4 min for a 56 s reel). onnxruntime-gpu would be faster but is another install (and must not clash with faster-whisper's onnxruntime). Worth it?
- Per-font CAP_RATIO (broll_qa reading the caption font from index.html) would remove the font spread; a design change, not done.
- Docs that still say captions need macOS (SKILL.md:453, references/broll.md:315, docs/THIRD_PARTY/runtime.md:14): step 8.
- Step 5's `faster` default and step 4's round 2 are still waiting for you.

**Step 5: Whisper on the RTX 3050: BUILT (2026-11-07), waiting for your yes/no on making `faster` the Windows default.**

Step 4 said: openai-whisper turbo fits (peak 3883 / 4096 MiB) but with ~200 MiB spare and at 0.57x real time, so route 2 (you approved the install).
- `--backend faster` (transcribe.py) and `GHOST_ASR=faster` (asr(): islands_tx.py, subcheck.py): faster-whisper 1.2.1 turbo, CUDA int8_float16, ANTI_MERGE settings, seeded, the openai json shape. NOT the default.
- toolchain.py records it (`faster-whisper 1.2.1 (ctranslate2 4.8.5)` when GHOST_ASR=faster).
- On D:\reels\win-test-1\assets\talk.mp4 (76 s, 2 speakers, 7 joined clips):

| | openai-whisper (CLI, fp32, CUDA) | faster (int8_float16, CUDA) |
|---|---|---|
| time | 133 s | 10.6 s |
| peak VRAM (desktop ~550 MiB included) | 3883 MiB | 1663 MiB |
| words | 189 | 198 (+10: an off-script remark openai dropped) |
| matched words | 185 of 189 | |
| start time \|diff\| | mean 18 ms, median 0, p90 20 ms, max 400 ms; signed +10 ms; 12 words > 100 ms, 4 > 200 ms | |
| at take edges (86 words) | mean 24 ms, max 400 ms | |
| sentences that differ (of 16) | "place your prompt" (wrong), "Windows H for voice typing", "in a weekend" | "paste" (right), "Windows, H4, voice typing" (wrong), "in a beacon" (wrong) |
| repeatable | CLI can't be seeded | two runs identical |

The biggest time differences sit where a clip starts right on a word after a join (both models smear into the 0.6 s pad; neither is consistently closer) and on "like" (55.68 vs 56.08).

Open questions:
- Make `faster` the Windows default? My recommendation: yes on Windows only, after one check on a raw multi-take recording (this video was pre-trimmed clips, so it barely tests the anti-merge / retake behaviour take selection depends on).
- Step 4's round-2 fixes and your call on the animations are still pending (below).

**Step 4: core pipeline on a real video: IN PROGRESS (2026-11-07). Every stage runs on Windows; finals.py qa FAILS (round 1), waiting for your decision.**

Project D:\reels\win-test-1: 7 of the 8 clips in D:\drive-download-20261106T212218Z-1-001 (Teja + Sandeep), joined in script order (assemble_order.sh; IMG_0549 left out, an earlier partial take), clean preset, 27 autocut takes, 56.0 s. Five Prompt Master animations in brag.mp4's look (anim/make_anim.py -> assets/anim-*.mp4, full-screen broll beats with captions: false), a purple-dot logo beat, a thinking emoji, a "1 weekend" card.

Stages (fixes: 5 WINDOWS-PORT.md rows; not committed, you commit):
- prep.sh: FIXED (GNU tr range, ffprobe CRLF; grade_lib LUT path via plat.ff_filter_path). 1080x1920, 30 fps, -16.1 LUFS.
- transcribe.py: as-is. CUDA, peak VRAM 3883 / 4096 MiB (baseline 576), turbo fits (~200 MiB spare), no OOM, no CPU fallback, 133 s for 76 s.
- face_track.py: as-is (face in 355/380 samples; misses = snooker turn + cut chatter).
- autocut.py --noise -30: as-is (31 takes; 4 dropped by hand: the first "Why now?", off-script talk, a breath).
- reel.json / build.mjs: as-is, plus the broll `captions: false` feature (you asked for it).
- approval_sheet.py --open: FIXED (plat.open_path); you approved build 77104aa104 from the page.
- finals.py: FIXED (fcntl -> plat.lock_nb/unlock). preview 236 s, render 335 s. Both need TEMP/TMP on D: (C: has ~8 GB free; HyperFrames' frame folder is os.tmpdir(): ENOSPC on C:).
- qa.py: all checks passed.
- finals.py qa: FAIL: bq_speaker 63.9 % (>= 65), bq_inserts 5.4/min (<= 3), bq_faces (a passer-by behind the frosted glass in IMG_0552, footage), bq_freeze (anim-messy 0.23 s hold: mine), bq_keyframes (talk.mp4 is VFR, 29.93 fps: my concat in assemble_order.sh, not Windows).

Left: fix the plate (fps=30 in assemble_order.sh) and the messy hold; your call on the 5 animations vs the talking-head budgets; rebuild, approval, preview, render, qa (round 2). Then step 4 is done.

Open questions:
- Speaker/inserts budgets vs the five full-screen animations (trim one, drop some, or QA with the "tutorial" profile).
- HyperFrames still warns "sparse keyframes" for the re-encoded animations although ffprobe shows a keyframe every 1 s; the render shows no freeze. Not understood yet.
- build.mjs writes asset paths with backslashes on Windows (`src="assets\anim-better.mp4"`, path.join). Chrome accepts them and the render is right; consider forward slashes in step 8.
- Set TEMP/TMP to D: for renders permanently (user env var), or free space on C:? Your call.

**Step 3: HyperFrames + ffmpeg wrapper: DONE (2026-11-07).**

Built (3 WINDOWS-PORT.md rows; not committed, you commit):
- Launcher: pip's own t64.exe (you said go ahead with it; no PyInstaller). `python scripts/setup_hf_ffmpeg.py` builds scripts\win-bin\hf_ffmpeg.exe + hf_mix_pcm.exe (gitignored).
- hf_ffmpeg.py / hf_mix_pcm.py: same behaviour as the .sh (13-case comparison), real ffmpeg in a kill-on-close job object. hf_mix_order.py: win32 branch instead of os.execv.
- hf.sh, hf_version.py, finals.py pick the .exe only on Windows (plat.hf_ffmpeg; hf.sh its own $OSTYPE case). macOS values checked unchanged.
- Proof: two wrapper renders of D:\reels\hf-test (voice + 2 SFX) have the same sha256; MP4 says threads=12 (18 without); mix-order log shows the sorted inputs; hf_mix_pcm.exe writes the PCM mix.
- Cost: ~130 ms per ffmpeg call (venv python redirector + base python + imports). 11 calls in the 6 s test render (~1.4 s of ~30-40 s); more calls with more audio tracks (one prep per track, run in parallel).

Open questions:
- Speed-up if wanted: point the launcher at the base python (sys._base_executable, ~15 ms less) and skip the `subprocess` import (~25 ms). Not done: small gain, more code.
- doctor.sh still checks hf_ffmpeg.sh's -threads with `HF_REAL_FFMPEG=echo` (works in Git Bash) but not the .exe or whether win-bin exists: step 6 (doctor.sh on Windows).
- finals.py nomusic end to end still blocked by `fcntl` (step 4); hf_mix_pcm.exe itself is tested.

Done:
- Read how HyperFrames 0.8.159 starts ffmpeg (known issues above): .cmd is impossible, needs a real .exe.
- Test project D:\reels\hf-test (5 s testsrc2 + 440 Hz sine, 1080x1920, 30 fps; hand-written words json; clean.reel.json cut to one 0-5 s take). build.mjs, lint (0 errors), snapshot (4 frames, captions correct) and render through hf.sh with HYPERFRAMES_FFMPEG_PATH = real ffmpeg.exe all work: 6.2 s, 7.2 MB in 38 s.
- Determinism without the wrapper (same machine): 4 renders, same sha256 (7c0db6ec...).
- Background renders: finals.py has no background code; "tracked background job" is an instruction to the agent. A Claude Code background job render works. A `nohup ... &` render also survives its tool shell exiting on Windows (unlike macOS): a Git Bash `&` job's Windows parent chain doesn't include the starting shell, so HyperFrames' watchdog (ancestor PIDs via PowerShell Get-CimInstance, polled every 2 s) only sees the bash processes that live as long as the render.

Left: build the Windows wrapper (exe launcher + hf_ffmpeg.py / hf_mix_pcm.py), switch hf.sh / hf_version.py / finals.py to it on win32 only, measure per-call overhead, two wrapper renders with equal hashes and threads=12 in the MP4, a reel with 3+ audio tracks to exercise hf_mix_order.

**Step 2: shared plumbing: DONE (2026-11-07).**

Done (commits 0e3d5c7..02e8bf0; one row each in WINDOWS-PORT.md):
- scripts/plat.py + scripts/lib/plat.mjs: IS_WIN, venv_python/venv_bin, npx_cmd, python_cmd, link_or_copy, git_bash (camelCase in Node). Off Windows each returns the old value. `python scripts/plat.py` / `node scripts/lib/plat.mjs` print them.
- npx_cmd uses the same npx-cli.js that npx.cmd would: the global npm in `npm prefix -g` (here npm 12.2.0 in %APPDATA%\npm) before the one bundled next to node.exe (11.19.0). So Python, Node and Git Bash's `npx` all run the same npm.
- venv pythons (9 files), npx (hf_version.hf, build.mjs remove-background), python3 (seoul-list build.mjs, toolchain media_py), os.symlink (save_style, facereel, seoul) now go through plat.
- tests/: all 3 pass before and after (assemble_sync, cutout_fx, decode_levels).
- Step 1's leftovers committed first (815f8c6).

Left alone on purpose:
- mlxw paths (transcribe.py, toolchain.py): mlx-whisper is Apple-Silicon-only.
- `bin/python` / `python3` in docstrings and usage text (docs: step 8), build.mjs die() hints (known issue above), bash scripts and hf_ffmpeg.sh (steps 3, 6, 7).

Open questions:
- Developer Mode on? Then link_or_copy makes real symlinks like the Mac (no code change). Your call; it's a Windows setting.
- The `bin` -> `Scripts` junctions in each venv: the Python/Node code no longer needs them, but doctor.sh and setup_*.sh still use `$V/bin/python`. Keep them until those are ported (steps 6-7).
- Install pytest into the project venv? Not needed to run tests/ (they're scripts).
- New issues to schedule: finals.py `fcntl` (step 4 needs it), transitions.py corrupt window, seoul.py:103 path escape (known issues above).

**Step 1: prepare the workspace: DONE (2026-11-07).**

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
