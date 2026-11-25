"""Windows only: build the launchers HyperFrames can start as its ffmpeg (HYPERFRAMES_FFMPEG_PATH):
scripts\\win-bin\\hf_ffmpeg.exe (runs hf_ffmpeg.py) and hf_mix_pcm.exe (runs hf_mix_pcm.py). win-bin is gitignored.

HyperFrames starts ffmpeg with Node's child_process.spawn and no shell, which on Windows can start neither hf_ffmpeg.sh
nor a .cmd. Each launcher is pip's own console-script launcher (t64.exe from pip's vendored distlib, the same program as
Scripts\\pip.exe) + a shebang naming this python (-I) + a zip whose __main__.py runs the script. Nothing is installed.
The launcher waits for python and passes its exit code and stdin/stdout/stderr through; killing it kills python.
Re-run after moving the repo or this python.

    python scripts/setup_hf_ffmpeg.py
"""
import io
import os
import platform
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "win-bin")
sys.path.insert(0, HERE)
from plat import IS_WIN, hf_ffmpeg, python_cmd  # noqa: E402


def launcher_stub():
    import pip._vendor.distlib as distlib
    name = "t64-arm.exe" if platform.machine().upper() == "ARM64" else "t64.exe"
    return open(os.path.join(os.path.dirname(distlib.__file__), name), "rb").read()


def build(name, stub, python):
    script = os.path.join(HERE, name + ".py")
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("__main__.py", f"import runpy, sys\nsys.argv[0] = {script!r}\nrunpy.run_path(sys.argv[0], run_name='__main__')\n")
    exe = hf_ffmpeg(name)
    tmp = exe + ".tmp"
    with open(tmp, "wb") as f:
        f.write(stub + f'#!"{python}" -I\n'.encode("utf-8") + z.getvalue())
    os.replace(tmp, exe)
    return exe


def main():
    if not IS_WIN:
        sys.exit("setup_hf_ffmpeg.py is for Windows; on macOS HyperFrames runs scripts/hf_ffmpeg.sh directly")
    os.makedirs(OUT, exist_ok=True)
    stub, python = launcher_stub(), python_cmd()
    ok = True
    for name in ("hf_ffmpeg", "hf_mix_pcm"):
        exe = build(name, stub, python)
        r = subprocess.run([exe, "-hide_banner", "-version"], capture_output=True, text=True)
        good = r.returncode == 0 and r.stdout.startswith("ffmpeg version")
        ok &= good
        print(f"{'ok  ' if good else 'FAIL'} {exe}  (python {python})" + ("" if good else f"\n     rc={r.returncode} {r.stderr.strip()[-300:]}"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
