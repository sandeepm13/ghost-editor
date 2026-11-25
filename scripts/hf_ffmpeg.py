"""Windows twin of hf_ffmpeg.sh: the ffmpeg HyperFrames runs on Windows (stdlib only; macOS keeps hf_ffmpeg.sh).

HyperFrames starts HYPERFRAMES_FFMPEG_PATH with child_process.spawn and no shell, and on Windows Node can start neither a
.sh (spawn EFTYPE) nor a .cmd (spawn EINVAL). So there HYPERFRAMES_FFMPEG_PATH is scripts\\win-bin\\hf_ffmpeg.exe, a
launcher built by setup_hf_ffmpeg.py that runs this file. Same behaviour as hf_ffmpeg.sh (why: there):
  - -threads from scripts/X264_THREADS goes in after every libx264
  - HyperFrames' audio mix (-/filter_complex or -filter_complex_script) runs through hf_mix_order.py
  - every other call goes straight to the real ffmpeg ($HF_REAL_FFMPEG, else ffmpeg on PATH)
The real ffmpeg runs in a job object that dies with this process: HyperFrames stops a cancelled ffmpeg by killing the
wrapper, which on Windows would otherwise leave the real ffmpeg running.

    hf_ffmpeg.py <ffmpeg args...>
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MIX = ("-/filter_complex", "-filter_complex_script")
_job = None


def with_threads(args):
    t = open(os.path.join(HERE, "X264_THREADS")).read().strip()
    a, prev = [], ""
    for x in args:
        a.append(x)
        if (prev.startswith(("-c:v", "-codec:v")) or prev in ("-vcodec", "-c", "-codec")) and x == "libx264":
            a += ["-threads", t]
        prev = x
    return a


def _contain(p):
    """put p in a job object with KILL_ON_JOB_CLOSE (its children join it too): when this wrapper dies, so do they"""
    global _job
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", ctypes.c_uint64 * 6),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    if _job is None:
        job = k32.CreateJobObjectW(None, None)
        info = Extended()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not job or not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):  # 9: extended limits
            return
        _job = job                                       # never closed: the handle closes when this process ends
    k32.AssignProcessToJobObject(_job, int(p._handle))


def run(args, **popen):
    """one HyperFrames ffmpeg call, the way hf_ffmpeg.sh runs it; returns the exit code"""
    args = with_threads(args)
    real = os.environ.get("HF_REAL_FFMPEG") or shutil.which("ffmpeg")
    if not real:
        print("hf_ffmpeg.py: ffmpeg not found on PATH (winget install Gyan.FFmpeg)", file=sys.stderr)
        return 127
    cmd = [real, *args]
    if any(x in MIX for x in args):
        cmd = [sys.executable, "-I", os.path.join(HERE, "hf_mix_order.py"), real, *args]
    p = subprocess.Popen(cmd, **popen)
    _contain(p)
    return p.wait()


def exit_code(rc):
    """a Windows exit code (unsigned 32-bit, e.g. 0xC0000135) as the signed int sys.exit accepts: same 32 bits"""
    return rc - 2**32 if rc >= 2**31 else rc


if __name__ == "__main__":
    sys.exit(exit_code(run(sys.argv[1:])))
