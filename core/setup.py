# ═══════════════════════════════════════════════════════════════
#  core/setup.py — Dependências, caminhos e utilidades de arranque
# ═══════════════════════════════════════════════════════════════
import sys, os, subprocess, re
from pathlib import Path

IS_FROZEN = getattr(sys, "frozen", False)
# Pasta raiz do projeto (onde está main.py) ou a pasta do executável.
ROOT = Path(sys.executable).parent if IS_FROZEN else Path(os.path.abspath(__file__)).parent.parent


def resource_path(relative):
    """Caminho de um arquivo do projeto (ícones etc.), no código-fonte ou no executável."""
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    return base / relative


def _pip(*pkgs):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *pkgs])


def ensure_dependencies():
    """Instala dependências ausentes quando rodando pelo código (não no executável)."""
    if IS_FROZEN:
        return
    for _pkg, _imp in [
        ("customtkinter", "customtkinter"),
        ("Pillow",         "PIL"),
        ("imageio-ffmpeg", "imageio_ffmpeg"),
        ("yt-dlp",         "yt_dlp"),
        ("requests",       "requests"),
    ]:
        try:
            __import__(_imp)
        except ImportError:
            print(f"[setup] Instalando {_pkg}...")
            _pip(_pkg)


def get_ffmpeg():
    """Retorna o caminho do executável ffmpeg embutido."""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


STRIP_ANSI = re.compile(r'\x1b\[[0-9;]*[mGKH]')

def clean(s):
    """Remove códigos ANSI de uma string."""
    return STRIP_ANSI.sub("", s or "").strip()
