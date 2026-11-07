"""Windows twin of hf_mix_pcm.sh (finals.py nomusic() only; why: there; stdlib only; macOS keeps hf_mix_pcm.sh).

The ffmpeg HyperFrames runs for the no-music render (HYPERFRAMES_FFMPEG_PATH = scripts\\win-bin\\hf_mix_pcm.exe, a
launcher built by setup_hf_ffmpeg.py): hf_ffmpeg.py unchanged, plus, once HyperFrames' audio mix has succeeded, the same
mix again to 32-bit float PCM at $HF_MIX_PCM.

    hf_mix_pcm.py <ffmpeg args...>
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I leaves this folder off sys.path
import hf_ffmpeg  # noqa: E402


def main(args):
    if not any(x in hf_ffmpeg.MIX for x in args):
        return hf_ffmpeg.run(args)
    rc = hf_ffmpeg.run(args)
    pcm = os.environ.get("HF_MIX_PCM")
    if rc == 0 and pcm and not os.path.isfile(pcm):
        a, skip = [], False
        for i, x in enumerate(args):
            if skip:
                skip = False
                continue
            if x in ("-acodec", "-c:a", "-b:a"):
                skip = True
                continue
            if i == len(args) - 1:                       # HyperFrames' own output (the last argument)
                continue
            a.append(x)
        if hf_ffmpeg.run(a + ["-acodec", "pcm_f32le", pcm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            if os.path.exists(pcm):
                os.remove(pcm)
    return rc


if __name__ == "__main__":
    sys.exit(hf_ffmpeg.exit_code(main(sys.argv[1:])))
