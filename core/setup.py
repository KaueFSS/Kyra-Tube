# ═══════════════════════════════════════════════════════════════
#  core/setup.py — Auto-instalação de dependências e setup inicial
# ═══════════════════════════════════════════════════════════════
import sys, os, subprocess, re
from pathlib import Path

IS_FROZEN = getattr(sys, "frozen", False)
THIS_FILE  = Path(sys.executable if IS_FROZEN else os.path.abspath(__file__)).parent.parent
# THIS_FILE aponta para a pasta raiz do projeto (onde está OffTube.py)
THIS_EXE   = Path(sys.executable if IS_FROZEN else os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'OffTube.py')))


def _pip(*pkgs):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *pkgs])


def ensure_dependencies():
    """Instala dependências ausentes quando rodando em modo dev (não frozen)."""
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
