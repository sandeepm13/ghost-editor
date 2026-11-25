# Installing ghost-editor on Windows 11

This guide sets up ghost-editor on a Windows 11 PC, step by step. It was written from a real install
(Windows 11, NVIDIA RTX 3050 Laptop GPU with 4 GB, 16 GB RAM). Allow about an hour, most of it downloads.

**Where to type the commands.** Each step says which window to use:

- **PowerShell**: press Start, type `PowerShell`, open "Windows PowerShell".
- **Git Bash**: installed in step 1. Press Start, type `Git Bash`, open it. Use it for every `bash ...` command.
  Never use the `bash` that comes with WSL or the Microsoft Store: ghost-editor needs Git Bash.

**Paths with spaces.** If your Windows user name has a space (like `C:\Users\Jane Doe`), always put paths in quotes:
`"C:\Users\Jane Doe\reels"`. Without quotes the command breaks at the space.

In this guide `D:\edit-pipeline` is where the skill lives and `D:\venvs\ghost-editor` is its Python environment. Any
folder works; if you pick others, change the paths in the commands to match.

---

## 1. The tools (PowerShell)

`winget` is Windows' built-in installer. Run these one at a time and accept the prompts:

```powershell
winget install Git.Git                 # Git + Git Bash
winget install Python.Python.3.12      # the main Python
winget install Python.Python.3.11      # only for the optional tools (step 9)
winget install OpenJS.NodeJS.LTS       # Node 18 or newer (HyperFrames renders with it)
winget install Gyan.FFmpeg             # ffmpeg "full build" (it has libvpx and libass, which the skill needs)
```

Close PowerShell and open a new one so it sees the new programs. Check them:

```powershell
git --version; python --version; node -v; ffmpeg -version
```

Each should print a version. If one says "not recognized", sign out of Windows and back in, then try again.

## 2. The NVIDIA driver (only with an NVIDIA graphics card)

Whisper (speech to text), the person cut-out and the denoiser are much faster on an NVIDIA GPU. Install the current
driver with the **NVIDIA App** (nvidia.com/en-us/software/nvidia-app) or from nvidia.com/drivers. Check it in PowerShell:

```powershell
nvidia-smi
```

It should show your card and a driver version. Without an NVIDIA card everything still works, only slower (on the CPU).

## 3. Two Windows settings (PowerShell)

Make Python read and write text as UTF-8 (emoji and non-English text break without it):

```powershell
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
```

Rendering a reel needs several GB of free space in your TEMP folder (on C: by default). If C: has less than about
15 GB free, point TEMP at another drive:

```powershell
New-Item -ItemType Directory -Force D:\tmp
[Environment]::SetEnvironmentVariable("TEMP", "D:\tmp", "User")
[Environment]::SetEnvironmentVariable("TMP", "D:\tmp", "User")
```

Close and reopen your windows after changing these.

Optional: **Developer Mode** (Settings > System > For developers) lets the skill make real symbolic links. Without it,
it makes hard links or copies instead, which also works.

## 4. Get the skill (PowerShell)

```powershell
git clone https://github.com/<you>/ghost-editor D:\edit-pipeline
```

## 5. The Python environment (PowerShell)

```powershell
py -3.12 -m venv D:\venvs\ghost-editor
D:\venvs\ghost-editor\Scripts\python.exe -m pip install --upgrade pip
D:\venvs\ghost-editor\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu126
D:\venvs\ghost-editor\Scripts\python.exe -m pip install openai-whisper numpy opencv-python google-genai pillow yt-dlp rapidocr-onnxruntime==1.4.4
```

The torch line installs the NVIDIA (CUDA) build. Without an NVIDIA card, leave out `--index-url ...`. Optional, a faster
speech-to-text engine (about 12 times faster, uses less GPU memory):

```powershell
D:\venvs\ghost-editor\Scripts\python.exe -m pip install faster-whisper
```

Now put this environment first on your PATH, so `python` means it everywhere:

```powershell
$p = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "D:\venvs\ghost-editor\Scripts;" + $p, "User")
```

Reopen PowerShell and check: `python -c "import torch; print(torch.cuda.is_available())"` prints `True` on an NVIDIA PC.

## 6. Make Claude Code see the skill (Command Prompt)

Claude Code looks for skills in `%USERPROFILE%\.claude\skills`. Link the folder there. This needs the classic
**Command Prompt** (Start, type `cmd`), because `mklink` only exists there:

```bat
mkdir "%USERPROFILE%\.claude\skills"
mklink /J "%USERPROFILE%\.claude\skills\ghost-editor" "D:\edit-pipeline"
```

(In PowerShell the same is
`New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\ghost-editor" -Target "D:\edit-pipeline"`.)
If Windows says "Access is denied", close VS Code and Claude Code first and try again.

## 7. The Gemini key

The B-roll checks ask Google Gemini (the free tier is enough). Get a key at aistudio.google.com/apikey and put it in a
file named `.env` in `D:\edit-pipeline`:

```
GEMINI_API_KEY=your-key-here
```

`.env` is never uploaded to git.

## 8. One-time setup inside the skill (Git Bash)

```bash
cd /d/edit-pipeline
python scripts/setup_hf_ffmpeg.py      # builds scripts\win-bin\hf_ffmpeg.exe (HyperFrames needs it to render)
python scripts/library_restore.py      # downloads the sound effects, music and animated emoji (not in git)
bash scripts/doctor.sh                 # checks everything
```

`doctor.sh` lists every tool with `ok` or `MISS` and a fix for each `MISS`. It should end with `0 missing`.
(The first run downloads HyperFrames through npx, so it needs internet once.)
If `library_restore.py` changes `library/sfx/manifest.json`, undo that with `git checkout -- library/sfx/manifest.json`
(Windows writes different line endings).

## 9. Optional tools (Git Bash)

These need Python 3.11 (step 1; `uv python install 3.11` works too). Each makes its own environment in
`%USERPROFILE%\.venvs` and installs the NVIDIA build of torch where it uses one:

```bash
bash scripts/setup_matte.sh      # person cut-out: "behind" text, cutout beats (~2.6 GB)
bash scripts/setup_audioqa.sh    # pause detection and voice enhance (~1.2 GB)
bash scripts/setup_looks.sh      # film-look LUTs
bash scripts/setup_captions.sh   # only to add a new caption font
```

The denoiser (`scripts/denoise.sh`) sets itself up the first time you use it.
Run `bash scripts/doctor.sh` again: the optional lines turn from `opt` to `ok`.

## If something goes wrong

| what you see | what to do |
|---|---|
| `bash` opens WSL or says "install a distribution" | use **Git Bash** (step 1), not the `bash` in PowerShell |
| `python` opens the Microsoft Store | step 5's PATH change didn't apply: sign out and in, or turn off the "App execution aliases" for python in Settings > Apps > Advanced app settings |
| a render stops with "no space left" (`ENOSPC`, or ffmpeg exit 4294967268) | free space on C:, or move TEMP (step 3) |
| `hf_ffmpeg.exe missing` | `python scripts/setup_hf_ffmpeg.py` (again after moving the folder or the Python environment) |
| the GPU runs out of memory during transcription | close games and browsers using the GPU, or use `--backend faster` (step 5) |
| a path with a space breaks a command | put the path in quotes |

What changed for Windows, file by file: [WINDOWS-PORT.md](WINDOWS-PORT.md).
