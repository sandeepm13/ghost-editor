// Platform helpers for the Windows port: every platform check lives here (and in its Python twin, scripts/plat.py).
// Off Windows each helper returns exactly what the code used before (bin/python, "npx", "python3", fs.symlinkSync), so
// the macOS path is unchanged; only process.platform === "win32" takes the other branch. Change log: docs/WINDOWS-PORT.md.
//
//   venvPython(venv)        <venv>/bin/python, on Windows <venv>\Scripts\python.exe
//   venvBin(venv, "pip")    <venv>/bin/pip,    on Windows <venv>\Scripts\pip.exe
//   npxCmd("-y", pkg, ...)  ["npx", ...]; on Windows [node, <npm>/bin/npx-cli.js, ...]: const [cmd, ...args] = npxCmd(...)
//                           for execFileSync / spawn without shell:true (Node 18.20+ won't spawn npx.cmd without one)
//   pythonCmd()             $GHOST_PYTHON, else "python3"; on Windows "python" (python3 there is the Microsoft Store stub)
//   linkOrCopy(src, dst)    fs.symlinkSync; on Windows without symlink rights a hard link, else a copy
//   gitBash()               "bash"; on Windows Git for Windows' bash.exe (never WSL's or the WindowsApps one), or null
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

export const IS_WIN = process.platform === "win32";

export const venvBin = (venvDir, name) =>
  IS_WIN ? path.join(venvDir, "Scripts", path.extname(name) ? name : name + ".exe") : path.join(venvDir, "bin", name);
export const venvPython = (venvDir) => venvBin(venvDir, "python");

const isFile = (p) => { try { return fs.statSync(p).isFile(); } catch { return false; } };

function which(name) {
  const exts = IS_WIN && !path.extname(name) ? (process.env.PATHEXT || ".COM;.EXE;.BAT;.CMD").split(";") : [""];
  for (const d of (process.env.PATH || "").split(path.delimiter)) {
    if (!d) continue;
    for (const e of exts) if (isFile(path.join(d, name + e))) return path.join(d, name + e);
  }
  return null;
}

let npxPrefix = null;
export function npxCmd(...args) {
  if (!IS_WIN) return ["npx", ...args];
  if (!npxPrefix) {
    // npm's own npx-cli.js, run by this node: next to node.exe (D:\Node\node_modules\npm\bin), or next to npx.cmd. Same
    // choice as npx.cmd: a newer npm installed globally (in `npm prefix -g`, found by npm-prefix.js) wins over the bundled one.
    const npx = which("npx");
    const npm = [process.execPath, npx].filter(Boolean)
      .map((p) => path.join(path.dirname(fs.realpathSync(p)), "node_modules", "npm", "bin")).find((d) => isFile(path.join(d, "npx-cli.js")));
    let cli = npm && path.join(npm, "npx-cli.js");
    if (npm && isFile(path.join(npm, "npm-prefix.js"))) {
      try {
        const g = path.join(execFileSync(process.execPath, [path.join(npm, "npm-prefix.js")]).toString().trim(), "node_modules", "npm", "bin", "npx-cli.js");
        if (isFile(g)) cli = g;
      } catch { /* keep the bundled one */ }
    }
    npxPrefix = cli ? [process.execPath, cli] : [npx || "npx"];
  }
  return [...npxPrefix, ...args];
}

export const pythonCmd = () => process.env.GHOST_PYTHON || (IS_WIN ? "python" : "python3");

// Windows makes symlinks only with Developer Mode or as admin: there a hard link (a file on the same drive), else a
// copy. A hard link or copy does not follow a later replacement of src. Returns what it made.
export function linkOrCopy(src, dst) {
  if (!IS_WIN) { fs.symlinkSync(src, dst); return "symlink"; }
  const abs = path.resolve(path.dirname(dst), src); // a symlink's src is relative to dst
  const isDir = fs.existsSync(abs) && fs.statSync(abs).isDirectory();
  try { fs.symlinkSync(src, dst, isDir ? "dir" : "file"); return "symlink"; } catch { /* no symlink rights */ }
  if (isDir) { fs.cpSync(abs, dst, { recursive: true }); return "copy"; }
  try { fs.linkSync(abs, dst); return "hardlink"; } catch { fs.copyFileSync(abs, dst); return "copy"; }
}

const wslBash = (p) => {
  const l = p.toLowerCase();
  return l.includes(path.join(process.env.SystemRoot || "C:\\Windows", "System32").toLowerCase()) || l.includes("windowsapps");
};

let gitBashPath;
export function gitBash() {
  if (!IS_WIN) return "bash";
  if (gitBashPath !== undefined) return gitBashPath;
  const cands = [process.env.GIT_BASH];
  const git = which("git");
  if (git) {
    let d = path.dirname(fs.realpathSync(git));
    for (let i = 0; i < 3; i++) { cands.push(path.join(d, "bin", "bash.exe")); d = path.dirname(d); } // <Git>\cmd, <Git>\bin, <Git>\mingw64\bin
  }
  for (const root of [process.env.ProgramW6432, process.env.ProgramFiles, process.env["ProgramFiles(x86)"],
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, "Programs")])
    if (root) cands.push(path.join(root, "Git", "bin", "bash.exe"));
  gitBashPath = cands.find((c) => c && isFile(c) && !wslBash(c)) || null;
  return gitBashPath;
}

// node scripts/lib/plat.mjs: what each helper gives on this machine
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const v = path.join(os.homedir(), ".venvs", "ghost-matte");
  for (const [k, val] of [["IS_WIN", IS_WIN], ["venvPython(~/.venvs/ghost-matte)", venvPython(v)], ["venvBin(~/.venvs/ghost-matte, 'pip')", venvBin(v, "pip")],
    ["npxCmd('--version')", JSON.stringify(npxCmd("--version"))], ["pythonCmd()", pythonCmd()], ["gitBash()", gitBash()]])
    console.log(k.padEnd(40), val);
}
