# ═══════════════════════════════════════════════════════════════
#  core/updater.py — Auto-atualização via GitHub Releases
# ═══════════════════════════════════════════════════════════════
import os, subprocess
from pathlib import Path

import requests

from core.config import GITHUB_USER, GITHUB_REPO, GITHUB_ASSET, APP_VERSION
from core.setup  import IS_FROZEN, THIS_EXE

_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


def _version_tuple(v):
    try:
        return tuple(int(x) for x in v.lstrip("v").strip().split("."))
    except Exception:
        return (0,)


def fetch_release():
    """Busca a última release no GitHub. Retorna (dl_url, tag, body) ou (None, None, '')."""
    try:
        r = requests.get(_RELEASE_API, timeout=15, headers={
            "Accept":      "application/vnd.github+json",
            "User-Agent":  f"OffTube-updater/{APP_VERSION}",
        })
        if r.status_code == 404:
            return None, None, ""
        r.raise_for_status()
        data    = r.json()
        tag     = (data.get("tag_name") or "").strip()
        body    = (data.get("body") or "").splitlines()[0][:60] if data.get("body") else ""
        dl_url  = next(
            (a["browser_download_url"] for a in data.get("assets", [])
             if a["name"].lower() == GITHUB_ASSET.lower()), None)
        return dl_url, tag, body
    except Exception:
        return None, None, ""


def download_exe(url, progress_cb=None):
    """Baixa o executável da URL dada. Retorna bytes ou None em caso de falha."""
    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        total, chunks, done = int(r.headers.get("content-length", 0)), [], 0
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                chunks.append(chunk)
                done += len(chunk)
                if progress_cb and total:
                    try:
                        progress_cb(done / total)
                    except Exception:
                        pass
        return b"".join(chunks)
    except Exception:
        return None


def apply_update(content):
    """Substitui o executável atual pelo novo conteúdo via .bat."""
    new_exe = THIS_EXE.with_name(THIS_EXE.stem + ".new.exe")
    bat     = THIS_EXE.with_name("_offtube_upd.bat")
    pid     = os.getpid()
    try:
        new_exe.write_bytes(content)
        bat_lines = [
            "@echo off", "setlocal",
            "title OffTube - Atualizando...", "",
            "echo Atualizando, aguarde...", "",
            f"taskkill /PID {pid} /F >NUL 2>&1",
            "ping 127.0.0.1 -n 6 >NUL 2>&1", "",
            f"move /Y \"{new_exe}\" \"{THIS_EXE}\" >NUL 2>&1",
            "ping 127.0.0.1 -n 3 >NUL 2>&1",
            f"move /Y \"{new_exe}\" \"{THIS_EXE}\" >NUL 2>&1",
            "ping 127.0.0.1 -n 4 >NUL 2>&1",
            f"move /Y \"{new_exe}\" \"{THIS_EXE}\" >NUL 2>&1", "",
            "mshta.exe \"vbscript:Execute(\"\"MsgBox \"\"\"\"Atualizado: Reabra o OffTube\"\"\"\",64,\"\"\"\"OffTube\"\"\"\"):close\"\"\"",
            "", 'del "%~f0"',
        ]
        bat.write_text("\r\n".join(bat_lines), encoding="mbcs")
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat)],
            creationflags=subprocess.DETACHED_PROCESS,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os._exit(0)
    except Exception:
        for f in (new_exe, bat):
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass


def is_newer(remote_tag):
    """Retorna True se a tag remota for mais nova que APP_VERSION."""
    return _version_tuple(remote_tag) > _version_tuple(APP_VERSION)
