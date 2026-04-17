# ═══════════════════════════════════════════════════════════════
#  core/downloader.py — Lógica de download via yt-dlp
# ═══════════════════════════════════════════════════════════════
import os

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
        "ignoreerrors"    : True,
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


def run_download(opts, url):
    """Executa o download de um único vídeo. Retorna o título ou a URL."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return (info.get("title", "") if info else "") or url


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
