# ═══════════════════════════════════════════════════════════════
#  core/discord.py — Notificações via Discord Webhook
# ═══════════════════════════════════════════════════════════════
import os, ctypes
from datetime import datetime

import requests

from core.config import DISCORD_WEBHOOK, APP_VERSION


def _get_windows_username():
    """Retorna o nome de exibição do usuário do Windows."""
    try:
        GetUserNameW = ctypes.windll.secur32.GetUserNameExW
        NameDisplay  = 3
        size = ctypes.c_ulong(0)
        GetUserNameW(NameDisplay, None, ctypes.byref(size))
        buf = ctypes.create_unicode_buffer(size.value)
        if GetUserNameW(NameDisplay, buf, ctypes.byref(size)):
            name = buf.value.strip()
            if name:
                return name.split("\\")[-1]
    except Exception:
        pass
    try:
        import winreg
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        val, _ = winreg.QueryValueEx(reg, "RegisteredOwner")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "Usuário"


def _post(payload):
    """Envia um payload para o webhook do Discord."""
    resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    resp.raise_for_status()


def _footer():
    return f"OffTube {APP_VERSION}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}"


def send_open():
    """Notifica que o app foi aberto."""
    try:
        username = _get_windows_username()
        _post({"embeds": [{
            "description": f"🚀 **{username}** abriu o **OffTube**\n📦 Versão **{APP_VERSION}**",
            "color": 0x4f8ef7,
            "footer": {"text": _footer()},
        }]})
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook de abertura: {e}")


def send_updated():
    """Notifica que o app foi atualizado."""
    try:
        username = _get_windows_username()
        _post({"embeds": [{
            "description": f"🔄 **{username}** atualizou o **OffTube** para **{APP_VERSION}**",
            "color": 0x22c55e,
            "footer": {"text": _footer()},
        }]})
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook de atualização: {e}")


def send_download(video_count, elapsed_secs, titles, folder,
                  fmt="mp4", qual="Melhor", mp3_qual="192k",
                  thumb=False, thumb_fmt="jpg"):
    """Notifica que um download foi concluído."""
    try:
        username  = _get_windows_username()
        mins      = int(elapsed_secs // 60)
        secs      = int(elapsed_secs % 60)
        tempo_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        emoji_num   = ["1⃣","2⃣","3⃣","4⃣","5⃣","6⃣","7⃣","8⃣","9⃣","🔟"]
        count_emoji = emoji_num[video_count - 1] if 1 <= video_count <= 10 else "🎬"

        if fmt == "mp3":
            fmt_line = f"🎵 **MP3** `{mp3_qual}`"
        else:
            fmt_emoji = {"mp4": "🎬", "mkv": "📼", "webm": "🌐"}.get(fmt, "🎬")
            fmt_line  = f"{fmt_emoji} **{fmt.upper()}**"

        description = (
            f"**{username}** baixou {count_emoji} **{video_count} vídeo{'s' if video_count != 1 else ''}** "
            f"em ⏱️ **{tempo_str}**\n{fmt_line}"
        )
        _post({"embeds": [{
            "description": description,
            "color": 0x4f8ef7,
            "footer": {"text": _footer()},
        }]})
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook: {e}")
