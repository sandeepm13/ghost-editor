"""Platform helpers for the Windows port: every platform check lives here (and in its Node twin, scripts/lib/plat.mjs).

Off Windows each helper returns exactly what the code used before (bin/python, "npx", os.symlink), so the macOS path
is unchanged; only sys.platform == "win32" takes the other branch. Change log: docs/WINDOWS-PORT.md.

    sys.path.append(os.path.join(SKILL, "scripts"))   # only where scripts/ is not on sys.path yet (and under python -I)
    from plat import IS_WIN, venv_python, npx_cmd, link_or_copy

    venv_python(venv)          <venv>/bin/python, on Windows <venv>\\Scripts\\python.exe
    venv_bin(venv, "pip")      <venv>/bin/pip,    on Windows <venv>\\Scripts\\pip.exe
    npx_cmd("-y", pkg, ...)    ["npx", ...]; on Windows [node, <npm>/bin/npx-cli.js, ...] (no shell, paths with spaces ok)
    python_cmd()               the running interpreter (sys.executable)
    link_or_copy(src, dst)     os.symlink; on Windows without symlink rights a hard link, else a copy
    git_bash()                 "bash"; on Windows Git for Windows' bash.exe (never WSL's or the WindowsApps one), or None
    hf_ffmpeg("hf_mix_pcm")    scripts/hf_mix_pcm.sh; on Windows scripts\\win-bin\\hf_mix_pcm.exe (setup_hf_ffmpeg.py)
    ff_filter_path(p)          p; on Windows 'D\\:/x/y.cube' for an ffmpeg filter option
    open_path(p)               `open p` (default app / browser); on Windows os.startfile
    ocr_cmd()                  osascript + ocr_text.js (macOS Vision); on Windows python ocr_text_rapid.py (RapidOCR)
    own_footage_roots(roots)   roots; on Windows $OWN_FOOTAGE_ROOTS or the existing Pictures / Videos / Camera Roll
    machine_name()             (Windows only) "CPU, RAM GB, NVIDIA GPU" for cutout_fx.platform_name()
    lock_nb(f) / unlock(f)     fcntl.flock LOCK_EX|LOCK_NB / LOCK_UN; on Windows msvcrt.locking (no fcntl there)
    cuda_dlls()                None; on Windows torch\\lib (CUDA 12 + cuDNN 9 DLLs) first on PATH for faster-whisper
"""
import functools
import os
import shutil
import subprocess
import sys

IS_WIN = sys.platform == "win32"


def venv_bin(venv_dir, name):
    """a program in a venv: <venv>/bin/<name>, on Windows <venv>\\Scripts\\<name>.exe"""
    if IS_WIN:
        return os.path.join(venv_dir, "Scripts", name if os.path.splitext(name)[1] else name + ".exe")
    return os.path.join(venv_dir, "bin", name)


def venv_python(venv_dir):
    return venv_bin(venv_dir, "python")


@functools.lru_cache(maxsize=None)
def _npx_prefix():
    # npx is npx.cmd on Windows: subprocess can't find it by name, and a .cmd needs a shell. npm's own npx-cli.js run by
    # node needs neither. It sits next to node.exe (D:\Node\node_modules\npm\bin), or next to npx.cmd. Same choice as
    # npx.cmd: a newer npm installed globally (in `npm prefix -g`, found by npm-prefix.js) wins over the bundled one.
    node, npx = shutil.which("node"), shutil.which("npx")
    for d in (node, npx):
        if node and d:
            npm = os.path.join(os.path.dirname(os.path.realpath(d)), "node_modules", "npm", "bin")
            if os.path.isfile(os.path.join(npm, "npx-cli.js")):
                cli = os.path.join(npm, "npx-cli.js")
                if os.path.isfile(os.path.join(npm, "npm-prefix.js")):
                    r = subprocess.run([node, os.path.join(npm, "npm-prefix.js")], capture_output=True, text=True)
                    g = os.path.join(r.stdout.strip(), "node_modules", "npm", "bin", "npx-cli.js")
                    if r.returncode == 0 and r.stdout.strip() and os.path.isfile(g):
                        cli = g
                return (node, cli)
    return (npx or "npx",)


def npx_cmd(*args):
    """a command list that runs npx without a shell: ["npx", *args], on Windows [node, npx-cli.js, *args]"""
    if not IS_WIN:
        return ["npx", *args]
    return [*_npx_prefix(), *args]


def python_cmd():
    """the python to run a helper script with: the running interpreter"""
    return sys.executable


def link_or_copy(src, dst):
    """os.symlink(src, dst). Windows makes symlinks only with Developer Mode or as admin: there a hard link (a file on
    the same drive), else a copy. A hard link or copy does not follow a later replacement of src. Returns what it made."""
    if not IS_WIN:
        os.symlink(src, dst)
        return "symlink"
    is_dir = os.path.isdir(src if os.path.isabs(src) else os.path.join(os.path.dirname(dst), src))
    try:
        os.symlink(src, dst, target_is_directory=is_dir)
        return "symlink"
    except OSError:
        pass
    src = src if os.path.isabs(src) else os.path.join(os.path.dirname(dst), src)  # a symlink's src is relative to dst
    if is_dir:
        shutil.copytree(src, dst)
        return "copy"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def hf_ffmpeg(name="hf_ffmpeg"):
    """the ffmpeg wrapper HyperFrames runs (HYPERFRAMES_FFMPEG_PATH): scripts/<name>.sh; on Windows the launcher
    scripts\\win-bin\\<name>.exe that setup_hf_ffmpeg.py builds (Node starts ffmpeg without a shell: no .sh, no .cmd)"""
    here = os.path.dirname(os.path.abspath(__file__))
    if not IS_WIN:
        return os.path.join(here, name + ".sh")
    exe = os.path.join(here, "win-bin", name + ".exe")
    if not os.path.isfile(exe) and os.path.basename(sys.argv[0]) != "setup_hf_ffmpeg.py":
        print(f"WARNING {exe} missing: run python scripts/setup_hf_ffmpeg.py (HyperFrames renders will fail)", file=sys.stderr)
    return exe


def lock_nb(f):
    """exclusive non-blocking lock on an open file: fcntl.flock(f, LOCK_EX | LOCK_NB), BlockingIOError while another
    process holds it; on Windows (no fcntl) msvcrt.locking on the file's first byte, same exception"""
    if not IS_WIN:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    import msvcrt
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as e:
        raise BlockingIOError(*e.args) from e


def unlock(f):
    """release lock_nb: fcntl.flock(f, LOCK_UN); on Windows msvcrt.locking LK_UNLCK on the first byte"""
    if not IS_WIN:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)
        return
    import msvcrt
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def cuda_dlls():
    """the CUDA 12 / cuDNN 9 DLLs CTranslate2 (faster-whisper) needs: nothing to do off Windows (None); on Windows
    torch's own copies (torch\\lib of the cu126 wheel) go first on PATH for this process. CTranslate2 loads
    cublas64_12.dll lazily with a bare LoadLibrary, which searches PATH and ignores os.add_dll_directory alone.
    Returns the folder, or None when torch has no CUDA DLLs (faster-whisper then runs on the CPU)."""
    if not IS_WIN:
        return None
    import importlib.util
    spec = importlib.util.find_spec("torch")
    if not spec or not spec.submodule_search_locations:
        return None
    lib = os.path.join(list(spec.submodule_search_locations)[0], "lib")
    if not os.path.isfile(os.path.join(lib, "cublas64_12.dll")):
        return None
    if lib not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = lib + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(lib)
    return lib


def ocr_cmd():
    """the caption OCR command (broll_qa.py appends the frame paths; one JSON line per image back): macOS Vision through
    `osascript -l JavaScript ocr_text.js`, None off macOS or without osascript; on Windows RapidOCR through
    ocr_text_rapid.py (same output), None when rapidocr-onnxruntime is not installed"""
    here = os.path.dirname(os.path.abspath(__file__))
    if not IS_WIN:
        if sys.platform != "darwin" or not shutil.which("osascript"):
            return None
        return ["osascript", "-l", "JavaScript", os.path.join(here, "ocr_text.js")]
    import importlib.util
    if importlib.util.find_spec("rapidocr_onnxruntime") is None:
        return None
    return [sys.executable, os.path.join(here, "ocr_text_rapid.py")]


_KNOWN_FOLDERS = {"Pictures": "{33E28130-4E1E-4676-835A-98395C3BC3BB}", "Videos": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}",
                  "CameraRoll": "{AB5FB87B-7CE2-4F83-915D-550846C9DC3A}"}


def _known_folder(name):
    """a Windows known folder's real path (Pictures / Videos may be redirected into OneDrive), or None"""
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]

    g = GUID()
    if ctypes.oledll.ole32.CLSIDFromString(_KNOWN_FOLDERS[name], ctypes.byref(g)) != 0:
        return None
    p = ctypes.c_wchar_p()
    try:
        ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(p))
        return p.value
    except OSError:
        return None
    finally:
        ctypes.windll.ole32.CoTaskMemFree(p)


def own_footage_roots(roots):
    """the folders the user's own footage lives in: `roots` (the macOS list) as given; on Windows $OWN_FOOTAGE_ROOTS
    (folders separated by ';') when set, else whichever of ~/Pictures, ~/Videos, the Pictures / Videos / Camera Roll
    known folders (often redirected into OneDrive) and ~/OneDrive/Pictures/Camera Roll exist"""
    if not IS_WIN:
        return roots
    env = os.environ.get("OWN_FOOTAGE_ROOTS")
    if env:
        return [os.path.abspath(os.path.expanduser(r.strip())) for r in env.split(os.pathsep) if r.strip()]
    cands = [os.path.expanduser(os.path.join("~", "Pictures")), os.path.expanduser(os.path.join("~", "Videos"))]
    cands += [_known_folder(k) for k in ("Pictures", "Videos", "CameraRoll")]
    cands.append(os.path.expanduser(os.path.join("~", "OneDrive", "Pictures", "Camera Roll")))
    out = []
    for c in cands:
        if c and os.path.isdir(c) and os.path.normcase(os.path.abspath(c)) not in [os.path.normcase(o) for o in out]:
            out.append(os.path.abspath(c))
    return out


def machine_name():
    """Windows: "<CPU name>, <RAM> GB[, <NVIDIA GPU>]" (the Windows twin of cutout_fx.platform_name's sysctl line);
    the GPU part only when nvidia-smi answers"""
    import ctypes
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
        cpu = " ".join(str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).split())
    kb = ctypes.c_ulonglong()   # installed RAM, like the Mac's hw.memsize (not the smaller usable amount)
    ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(kb))
    out = f"{cpu}, {kb.value / 2**20:.0f} GB"
    if shutil.which("nvidia-smi"):
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=10)
            gpus = [g.strip() for g in r.stdout.splitlines() if g.strip()] if r.returncode == 0 else []
            if gpus:
                out += ", " + " + ".join(gpus)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return out


def open_path(p):
    """show a file in its default app (an .html page in the browser): `open p`; on Windows os.startfile (like `start`)"""
    if not IS_WIN:
        subprocess.run(["open", p])
        return
    os.startfile(os.path.abspath(p))


def ff_filter_path(p):
    """a file path inside an ffmpeg filter option (lut3d=file=...): p as is; on Windows quoted with forward slashes and
    the drive colon escaped ('D\\:/x/y.cube'), since a bare 'D:' ends the option"""
    if not IS_WIN:
        return p
    return "'" + str(p).replace("\\", "/").replace(":", "\\:") + "'"


def _wsl_bash(p):
    p = os.path.normcase(p)
    return os.path.normcase(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")) in p or "windowsapps" in p


@functools.lru_cache(maxsize=None)
def git_bash():
    """the bash to run the skill's .sh scripts with: "bash"; on Windows Git for Windows' bin\\bash.exe ($GIT_BASH
    overrides), never WSL's System32\\bash.exe or the WindowsApps one. None when Git for Windows is not found."""
    if not IS_WIN:
        return "bash"
    cands = [os.environ.get("GIT_BASH")]
    git = shutil.which("git")
    if git:
        d = os.path.dirname(os.path.realpath(git))
        for _ in range(3):  # <Git>\cmd\git.exe, <Git>\bin\git.exe, <Git>\mingw64\bin\git.exe
            cands.append(os.path.join(d, "bin", "bash.exe"))
            d = os.path.dirname(d)
    for root in (os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if root:
            cands.append(os.path.join(root, "Git", "bin", "bash.exe"))
    return next((c for c in cands if c and os.path.isfile(c) and not _wsl_bash(c)), None)


if __name__ == "__main__":  # python scripts/plat.py: what each helper gives on this machine
    v = os.path.expanduser(os.path.join("~", ".venvs", "ghost-matte"))
    for k, val in [("IS_WIN", IS_WIN), ("venv_python(~/.venvs/ghost-matte)", venv_python(v)),
                   ("venv_bin(~/.venvs/ghost-matte, 'pip')", venv_bin(v, "pip")), ("npx_cmd('--version')", npx_cmd("--version")),
                   ("python_cmd()", python_cmd()), ("git_bash()", git_bash()), ("hf_ffmpeg()", hf_ffmpeg()),
                   ("hf_ffmpeg('hf_mix_pcm')", hf_ffmpeg("hf_mix_pcm"))]:
        print(f"{k:40} {val}")
