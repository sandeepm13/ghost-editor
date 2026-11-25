"""The one HyperFrames CLI version every script lints, snapshots and renders with.

The version lives in scripts/HF_VERSION (one line). An HF_VERSION environment variable overrides it for a one-off test
(doctor.sh warns while it is set). Unpinned `npx hyperframes` fetches whatever was published last, so two machines,
or one machine on two days, render the same reel differently, and a release whose tarball 404s fails a whole batch.

    from hf_version import VERSION, hf
    subprocess.run(hf("render", "-o", out), cwd=project)       # ["npx", "-y", "hyperframes@<VERSION>", "render", ...]

Importing this also points HyperFrames at scripts/hf_ffmpeg.sh (HYPERFRAMES_FFMPEG_PATH, unless already set), which
fixes the audio mix's input order so the same reel gets the same audio on every render (why: hf_mix_order.py).
"""
import os

from plat import hf_ffmpeg, npx_cmd

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "HF_VERSION")
PINNED = open(FILE).read().strip()
VERSION = os.environ.get("HF_VERSION") or PINNED
if "HYPERFRAMES_FFMPEG_PATH" not in os.environ:
    os.environ["HYPERFRAMES_FFMPEG_PATH"] = hf_ffmpeg()  # scripts/hf_ffmpeg.sh; Windows: win-bin\hf_ffmpeg.exe


def hf(*args):
    return npx_cmd("-y", f"hyperframes@{VERSION}", *args)
