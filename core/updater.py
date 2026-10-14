# ═══════════════════════════════════════════════════════════════
#  core/updater.py — Atualização pelo GitHub Releases
#
#  Fluxo: o app consulta a última release → mostra um aviso →
#  (se a pessoa quiser) baixa o instalador, confere o SHA-256 →
#  roda o instalador em modo silencioso, que fecha o app, troca os
#  arquivos e abre o Kyra Tube de novo. Sem janela de terminal.
# ═══════════════════════════════════════════════════════════════
import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests

from core.config import APP_VERSION, GITHUB_REPO, GITHUB_USER, INSTALLER_ASSET

_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


class UpdateError(Exception):
    """Algo deu errado ao baixar ou conferir a atualização."""


@dataclass(frozen=True)
class Release:
    version: str          # "3.1.0"
    notes: list           # frases curtas das novidades
    url: str              # endereço do instalador
    size: int             # bytes (0 se desconhecido)
    sha256: str | None    # hash esperado, se o GitHub informou


def parse_version(value):
    """'v3.1.0' → (3, 1, 0). Valor inválido vira (0,)."""
    try:
        return tuple(int(part) for part in value.strip().lstrip("vV").split("."))
    except Exception:
        return (0,)


def is_newer(remote, local=APP_VERSION):
    """True se a versão remota for maior que a instalada."""
    return parse_version(remote) > parse_version(local)


def parse_notes(body, limit=3):
    """Pega as primeiras linhas com marcador ('- algo') do texto da release."""
    lines = []
    for raw in (body or "").splitlines():
        match = re.match(r"^\s*[-*•]\s+(.*\S)\s*$", raw)
        if match:
            lines.append(match.group(1))
        if len(lines) >= limit:
            break
    return lines


def fetch_latest():
    """Última release publicada, ou None (sem internet, sem release, erro)."""
    try:
        reply = requests.get(
            _RELEASE_API,
            timeout=15,
            headers={"Accept": "application/vnd.github+json", "User-Agent": f"KyraTube/{APP_VERSION}"},
        )
        if reply.status_code != 200:
            return None
        data = reply.json()
        asset = next((a for a in data.get("assets", []) if a.get("name", "").lower() == INSTALLER_ASSET.lower()), None)
        if not asset:
            return None
        digest = (asset.get("digest") or "")
        return Release(
            version=(data.get("tag_name") or "").strip().lstrip("vV"),
            notes=parse_notes(data.get("body")),
            url=asset["browser_download_url"],
            size=int(asset.get("size") or 0),
            sha256=digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else None,
        )
    except Exception:
        return None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify(path, expected):
    """Confere o hash do arquivo baixado (quando o GitHub informou um)."""
    if expected and _sha256(path) != expected.lower():
        raise UpdateError("O arquivo baixado não passou na verificação e foi descartado.")


def download(release, progress=None):
    """Baixa o instalador para a pasta temporária e devolve o caminho."""
    target_dir = Path(tempfile.gettempdir()) / "KyraTube-update"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / INSTALLER_ASSET
    try:
        with requests.get(release.url, stream=True, timeout=30) as reply:
            reply.raise_for_status()
            total = int(reply.headers.get("content-length") or release.size or 0)
            done = 0
            with open(target, "wb") as out:
                for chunk in reply.iter_content(chunk_size=256 * 1024):
                    if not chunk:
                        continue
                    out.write(chunk)
                    done += len(chunk)
                    if progress and total:
                        progress(min(done / total, 1.0))
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise UpdateError("Não foi possível baixar a atualização. Verifique a internet.") from exc
    try:
        verify(target, release.sha256)
    except UpdateError:
        target.unlink(missing_ok=True)
        raise
    return target


def launch_installer(path):
    """Inicia o instalador em modo silencioso e solta o processo.

    /SILENT mostra só a barra de progresso do instalador; ele fecha o app,
    troca os arquivos e abre o Kyra Tube de novo (veja installer/kyra-tube.iss).
    """
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
        creationflags=flags,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def exit_now():
    """Sai na hora, para o instalador poder trocar os arquivos."""
    os._exit(0)
