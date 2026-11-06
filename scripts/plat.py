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
                   ("python_cmd()", python_cmd()), ("git_bash()", git_bash())]:
        print(f"{k:40} {val}")
