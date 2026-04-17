# ═══════════════════════════════════════════════════════════════
#  ui/preview.py — Mixin de preview de vídeo/playlist
#  ► Para mudar como o preview funciona, edite apenas este arquivo
# ═══════════════════════════════════════════════════════════════
import io, threading, urllib.request

import customtkinter as ctk
from PIL import Image

from core.downloader import fetch_info, FFMPEG
from ui.theme        import TEXT, MUTED


class PreviewMixin:
    """
    Mixin que adiciona lógica de preview (info + thumbnail) à App.
    Depende de: url_v, title_lbl, meta_lbl, thumb_lbl, _pl_banner,
                _pl_entries, _is_playlist, _pl_title, _th_t, _img_ref
    """

    def _url_changed(self, *_):
        url = self.url_v.get().strip()
        self._is_playlist = False
        self._pl_entries  = []
        self.after(0, lambda: (
            self.title_lbl.configure(text="Cole um link para começar", text_color=MUTED),
            self.meta_lbl.configure(text=""),
            self.thumb_lbl.configure(image=None, text="🎬"),
            self._pl_banner.grid_remove(),
        ))
        self._img_ref = None
        if len(url) < 16:
            return
        if hasattr(self, "_preview_after"):
            self.after_cancel(self._preview_after)
        self._preview_after = self.after(700, lambda: self._trigger_preview(url))

    def _trigger_preview(self, url):
        if url != self.url_v.get().strip():
            return
        if self._th_t and self._th_t.is_alive():
            self.after(800, lambda: self._trigger_preview(url))
            return
        self._last_url = url
        self._th_t = threading.Thread(target=self._load_preview, args=(url,), daemon=True)
        self._th_t.start()

    def _load_preview(self, url):
        if url != self.url_v.get().strip():
            return
        self.after(0, lambda: (
            self.title_lbl.configure(text="Carregando...", text_color=MUTED),
            self.meta_lbl.configure(text=""),
        ))
        try:
            info = fetch_info(url, FFMPEG)
            if url != self.url_v.get().strip():
                return
            if not info:
                raise Exception("sem info")

            is_playlist = info.get("_type") == "playlist" or "entries" in info

            if is_playlist:
                short, meta, thumb = self._parse_playlist_info(info)
                self.after(0, lambda: self._pl_banner.grid())
            else:
                short, meta, thumb = self._parse_video_info(info)
                self.after(0, lambda: self._pl_banner.grid_remove())

            self.after(0, lambda s=short, m=meta: (
                self.title_lbl.configure(text=s, text_color=TEXT),
                self.meta_lbl.configure(text=m, text_color=MUTED),
            ))
            if thumb:
                self._load_thumbnail(thumb)

        except Exception:
            self.after(0, lambda: self.title_lbl.configure(
                text="Não foi possível carregar o preview.", text_color=MUTED))

    def _parse_playlist_info(self, info):
        entries  = list(info.get("entries") or [])
        count    = len(entries)
        pl_title = info.get("title", "Playlist")
        ch       = info.get("uploader") or info.get("channel", "")
        short    = pl_title[:70] + ("…" if len(pl_title) > 70 else "")
        meta     = f"📋 Playlist  ·  {count} vídeo{'s' if count != 1 else ''}   📺 {ch[:30]}"
        thumb    = info.get("thumbnail", "")
        if not thumb and entries:
            thumb = entries[0].get("thumbnail", "") if entries[0] else ""
        self._pl_entries  = entries
        self._is_playlist = True
        self._pl_title    = pl_title
        return short, meta, thumb

    def _parse_video_info(self, info):
        self._is_playlist = False
        self._pl_entries  = []
        title = info.get("title", "")
        dur   = int(info.get("duration", 0) or 0)
        views = info.get("view_count", 0) or 0
        ch    = info.get("uploader") or info.get("channel", "")
        thumb = info.get("thumbnail", "")
        m, s  = divmod(dur, 60)
        meta  = f"⏱ {m}:{s:02d}   👁 {f'{views:,}'.replace(',', '.')}   📺 {ch[:30]}"
        short = title[:70] + ("…" if len(title) > 70 else "")
        return short, meta, thumb

    def _load_thumbnail(self, thumb_url):
        try:
            req  = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()
            img  = Image.open(io.BytesIO(data)).convert("RGB").resize((200, 113), Image.LANCZOS)
            cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 113))
            self._img_ref = cimg
            self.after(0, lambda i=cimg: self.thumb_lbl.configure(image=i, text=""))
        except Exception:
            pass
