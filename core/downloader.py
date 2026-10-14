# ═══════════════════════════════════════════════════════════════
#  core/downloader.py — Lógica de download via yt-dlp
# ═══════════════════════════════════════════════════════════════
import os
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from core.setup import get_ffmpeg

FFMPEG = get_ffmpeg()


def build_opts(folder, fmt, qual, mp3_qual, sub, thumb, thumb_fmt, hook):
    """
    Monta o dicionário de opções do yt-dlp.
    ► Para adicionar novas opções de download, edite apenas esta função.
    """
    o = {
        "progress_hooks"  : [hook],
        "outtmpl"         : os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist"      : True,
        "writethumbnail"  : thumb,
        "ignoreerrors"    : False,   # falha de verdade aparece (antes era engolida e virava "baixado em 0s")
        "retries"         : 5,
        "fragment_retries": 10,
        "socket_timeout"  : 30,
        "ffmpeg_location" : FFMPEG,
        "keepvideo"       : False,
    }

    # Thumbnail converter
    if thumb:
        o["postprocessors"] = o.get("postprocessors", []) + [{
            "key"   : "FFmpegThumbnailsConvertor",
            "format": thumb_fmt,
            "when"  : "before_dl",
        }]

    # Legendas
    if sub:
        o.update({
            "writesubtitles"   : True,
            "subtitleslangs"   : ["pt", "en"],
            "writeautomaticsub": True,
        })

    # MP3
    if fmt == "mp3":
        quality = mp3_qual.replace("k", "")
        o["format"]         = "bestaudio/best"
        o["postprocessors"] = o.get("postprocessors", []) + [{
            "key"             : "FFmpegExtractAudio",
            "preferredcodec"  : "mp3",
            "preferredquality": quality,
        }]
        return o

    # Mapa qualidade → altura máxima
    h = {"360p":"360","480p":"480","720p":"720","1080p":"1080","4K":"2160","Melhor":None}.get(qual)

    if fmt == "mp4":
        f = (
            f"bestvideo[height<={h}][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={h}]+bestaudio/best"
        ) if h else (
            "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        )
    else:
        f = (
            f"bestvideo[height<={h}][ext={fmt}]+bestaudio/bestvideo[height<={h}]+bestaudio/best"
            if h else
            f"bestvideo[ext={fmt}]+bestaudio/bestvideo+bestaudio/best"
        )

    o["format"]              = f
    o["merge_output_format"] = fmt
    return o


@dataclass(frozen=True)
class Result:
    title: str
    already: bool = False     # True: o arquivo já estava na pasta, nada foi baixado
    path: str = ""


class _Watcher:
    """Logger do yt-dlp que só repara no que importa (arquivo que já existia)."""

    def __init__(self):
        self.already = False

    def _look(self, msg):
        if "has already been downloaded" in str(msg):
            self.already = True

    debug = info = _look

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def final_path(ydl, info, fmt):
    """Onde o arquivo vai ficar depois de juntar/converter (a extensão final é a do formato escolhido)."""
    return Path(ydl.prepare_filename(info)).with_suffix("." + fmt)


def run_download(opts, url, fmt="mp4"):
    """
    Baixa um único vídeo. Retorna Result; erros do yt-dlp sobem como exceção
    (a interface os traduz com core.errors.explain).
    Se o arquivo final já existe na pasta, não baixa de novo: Result(already=True).
    """
    watcher = _Watcher()
    with yt_dlp.YoutubeDL({**opts, "logger": watcher}) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise yt_dlp.utils.DownloadError("Video unavailable")
        title = info.get("title") or url
        target = final_path(ydl, info, fmt)
        if target.exists() and target.stat().st_size > 0:
            return Result(title, already=True, path=str(target))
        info = ydl.process_ie_result(info, download=True) or info
    return Result(title, already=watcher.already, path=str(target))


def fetch_info(url, ffmpeg):
    """
    Busca metadados de um vídeo ou playlist (sem baixar).
    Retorna o dict de info do yt-dlp.
    """
    ydl_opts = {
        "quiet"          : True,
        "no_warnings"    : True,
        "skip_download"  : True,
        "extract_flat"   : "in_playlist",
        "ffmpeg_location": ffmpeg,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)
