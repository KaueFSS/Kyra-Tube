# python -m PyInstaller --onefile --windowed --name OffTube OffTube.py
# py -m PyInstaller --clean OffTube.spec

GITHUB_USER  = "KaueFSS"
GITHUB_REPO  = "OffTube"
GITHUB_ASSET = "OffTube.exe"
APP_VERSION  = "v2.0.0"

_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1470857513669759128/K0nMpz3uKEXqTN1YNaLc-i0kU-PJs3v6YNQHrEBAqVJGM4nxvfg3ta0nrDFqiyboCdGu"
DISCORD_CHANNEL_ID = "756707561255731290"

import sys, os, subprocess, threading, time, io, re, json, webbrowser, urllib.request
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox

IS_FROZEN = getattr(sys, "frozen", False)
THIS_FILE  = Path(sys.executable if IS_FROZEN else os.path.abspath(__file__))

def _pip(*pkgs):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *pkgs])

if not IS_FROZEN:
    for _pkg, _imp in [
        ("customtkinter", "customtkinter"), ("Pillow", "PIL"),
        ("imageio-ffmpeg", "imageio_ffmpeg"), ("yt-dlp", "yt_dlp"), ("requests", "requests"),
    ]:
        try: __import__(_imp)
        except ImportError:
            print(f"[setup] Instalando {_pkg}...")
            _pip(_pkg)

import requests, customtkinter as ctk, imageio_ffmpeg, yt_dlp
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
UPDATE_CHECK_INTERVAL = 300

# ── Pega nome do usuário do Windows ─────────────────────────────
def _get_windows_username():
    try:
        import ctypes
        GetUserNameW = ctypes.windll.secur32.GetUserNameExW
        NameDisplay = 3
        size = ctypes.c_ulong(0)
        GetUserNameW(NameDisplay, None, ctypes.byref(size))
        buf = ctypes.create_unicode_buffer(size.value)
        if GetUserNameW(NameDisplay, buf, ctypes.byref(size)):
            name = buf.value.strip()
            if name: return name.split("\\")[-1]
    except Exception:
        pass
    try:
        import winreg
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        val, _ = winreg.QueryValueEx(reg, "RegisteredOwner")
        if val: return val
    except Exception:
        pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "Usuário"

# ── Discord Webhook ─────────────────────────────────────────────
def _send_discord(video_count, elapsed_secs, titles, folder,
                  fmt="mp4", qual="Melhor", mp3_qual="192k",
                  thumb=False, thumb_fmt="jpg"):
    try:
        username = _get_windows_username()
        mins  = int(elapsed_secs // 60)
        secs  = int(elapsed_secs % 60)
        tempo_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        emoji_num = ["1⃣","2⃣","3⃣","4⃣","5⃣","6⃣","7⃣","8⃣","9⃣","🔟"]
        count_emoji = emoji_num[video_count-1] if 1 <= video_count <= 10 else "🎬"

        if fmt == "mp3":
            fmt_line = f"🎵 **MP3** `{mp3_qual}`"
        else:
            fmt_emoji = {"mp4": "🎬", "mkv": "📼", "webm": "🌐"}.get(fmt, "🎬")
            fmt_line = f"{fmt_emoji} **{fmt.upper()}**"

        description = (
            f"**{username}** baixou {count_emoji} **{video_count} vídeo{'s' if video_count!=1 else ''}** "
            f"em ⏱️ **{tempo_str}**\n"
            f"{fmt_line}"
        )

        payload = {
            "embeds": [{
                "description": description,
                "color": 0x4f8ef7,
                "footer": {
                    "text": f"OffTube {APP_VERSION}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                },
            }]
        }

        resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook: {e}")


def _send_discord_open():
    """Envia webhook quando o app é aberto."""
    try:
        username = _get_windows_username()
        payload = {
            "embeds": [{
                "description": f"🚀 **{username}** abriu o **OffTube**\n📦 Versão **{APP_VERSION}**",
                "color": 0x4f8ef7,
                "footer": {
                    "text": f"OffTube {APP_VERSION}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                },
            }]
        }
        resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook de abertura: {e}")


def _send_discord_updated():
    """Envia webhook quando o app é atualizado."""
    try:
        username = _get_windows_username()
        payload = {
            "embeds": [{
                "description": f"🔄 **{username}** atualizou o **OffTube** para **{APP_VERSION}**",
                "color": 0x22c55e,
                "footer": {
                    "text": f"OffTube {APP_VERSION}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                },
            }]
        }
        resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Discord] Erro ao enviar webhook de atualização: {e}")



    try: return tuple(int(x) for x in v.lstrip("v").strip().split("."))
    except Exception: return (0,)

def _fetch_release():
    try:
        r = requests.get(_RELEASE_API, timeout=15, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"OffTube-updater/{APP_VERSION}",
        })
        if r.status_code == 404: return None, None, ""
        r.raise_for_status()
        data = r.json()
        tag  = (data.get("tag_name") or "").strip()
        body = (data.get("body") or "").splitlines()[0][:60] if data.get("body") else ""
        dl_url = next(
            (a["browser_download_url"] for a in data.get("assets", [])
             if a["name"].lower() == GITHUB_ASSET.lower()), None)
        return dl_url, tag, body
    except Exception: return None, None, ""

def _download_exe(url, progress_cb=None):
    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        total, chunks, done = int(r.headers.get("content-length", 0)), [], 0
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                chunks.append(chunk)
                done += len(chunk)
                if progress_cb and total:
                    try: progress_cb(done / total)
                    except Exception: pass
        return b"".join(chunks)
    except Exception: return None

def _apply_update(content):
    new_exe = THIS_FILE.with_name(THIS_FILE.stem + ".new.exe")
    bat     = THIS_FILE.with_name("_offtube_upd.bat")
    pid     = os.getpid()
    try:
        new_exe.write_bytes(content)
        bat_lines = [
            "@echo off", "setlocal",
            "title OffTube - Atualizando...", "",
            "echo Atualizando, aguarde...", "",
            f"taskkill /PID {pid} /F >NUL 2>&1",
            "ping 127.0.0.1 -n 6 >NUL 2>&1", "",
            f"move /Y \"{new_exe}\" \"{THIS_FILE}\" >NUL 2>&1",
            "ping 127.0.0.1 -n 3 >NUL 2>&1",
            f"move /Y \"{new_exe}\" \"{THIS_FILE}\" >NUL 2>&1",
            "ping 127.0.0.1 -n 4 >NUL 2>&1",
            f"move /Y \"{new_exe}\" \"{THIS_FILE}\" >NUL 2>&1", "",
            "mshta.exe \"vbscript:Execute(\"\"MsgBox \"\"\"\"Atualizado: Reabra o OffTube\"\"\"\",64,\"\"\"\"OffTube\"\"\"\"):close\"\"\"",
            "", 'del "%~f0"',
        ]
        bat.write_text("\r\n".join(bat_lines), encoding="mbcs")
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat)],
            creationflags=subprocess.DETACHED_PROCESS,
            close_fds=True, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        os._exit(0)
    except Exception:
        for f in (new_exe, bat):
            try: f.unlink(missing_ok=True)
            except Exception: pass

# ── Paleta ─────────────────────────────────────────────────────
BG      = "#0d0d16"
SURFACE = "#12121e"
CARD    = "#181826"
BORDER  = "#222236"
BLUE    = "#4f8ef7"
BLUE_H  = "#3a73e0"
TEXT    = "#e2e2f0"
MUTED   = "#4a4a6a"
GREEN   = "#22c55e"
RED     = "#ef4444"
YELLOW  = "#f59e0b"
ORANGE  = "#fb923c"
PURPLE  = "#a78bfa"

STRIP_ANSI = re.compile(r'\x1b\[[0-9;]*[mGKH]')
def clean(s): return STRIP_ANSI.sub("", s or "").strip()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

HIST = Path.home() / ".offtube_kauefss.json"
def load_hist():
    try: return json.loads(HIST.read_text("utf-8")) if HIST.exists() else []
    except Exception: return []
def save_hist(h):
    try: HIST.write_text(json.dumps(h[-50:], ensure_ascii=False, indent=2), "utf-8")
    except Exception: pass


# ══════════════════════════════════════════════════════════════ #
# ── Janela de seleção de playlist ────────────────────────────
# ══════════════════════════════════════════════════════════════ #
class PlaylistSelectorWindow(ctk.CTkToplevel):
    """
    Exibe os vídeos de uma playlist para o usuário selecionar quais baixar.
    Retorna via callback: callback(selected_entries) onde selected_entries é lista de dicts.
    """

    def __init__(self, parent, entries, pl_title, callback):
        super().__init__(parent)
        self.entries  = entries
        self.callback = callback
        self._checks  = []   # list of BooleanVar

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ww = min(720, int(sw * 0.55))
        wh = min(620, int(sh * 0.80))
        self.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.title("Selecionar vídeos da playlist")
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self.grab_set()

        self._build(pl_title, ww)

    def _build(self, pl_title, ww):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr,
            text="📋  Selecionar vídeos",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT,
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkLabel(hdr,
            text=pl_title[:55] + ("…" if len(pl_title) > 55 else ""),
            font=ctk.CTkFont(size=11), text_color=MUTED,
        ).pack(side="left", padx=(0, 16), pady=14)

        # ── Toolbar (sel all / desel all / contador) ──
        toolbar = ctk.CTkFrame(self, fg_color=CARD,
                               corner_radius=0, height=42)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkButton(toolbar, text="✔  Selecionar tudo",
            width=145, height=28,
            fg_color=BLUE, hover_color=BLUE_H,
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._select_all,
        ).pack(side="left", padx=(12, 6), pady=7)

        ctk.CTkButton(toolbar, text="✕  Desmarcar tudo",
            width=145, height=28,
            fg_color=BORDER, hover_color="#3d1515",
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._deselect_all,
        ).pack(side="left", padx=(0, 12), pady=7)

        self._count_lbl = ctk.CTkLabel(toolbar,
            text=f"{len(self.entries)} de {len(self.entries)} selecionados",
            font=ctk.CTkFont(size=11), text_color=MUTED)
        self._count_lbl.pack(side="left", padx=4)

        # ── Lista rolável ──
        sf = ctk.CTkScrollableFrame(self, fg_color=BG,
                                     scrollbar_button_color=BORDER)
        sf.pack(fill="both", expand=True, padx=0, pady=0)
        sf.grid_columnconfigure(0, weight=1)

        for idx, entry in enumerate(self.entries):
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_, v=var: self._update_count())
            self._checks.append(var)

            row = ctk.CTkFrame(sf, fg_color=CARD if idx % 2 == 0 else SURFACE,
                               corner_radius=6)
            row.grid(row=idx, column=0, sticky="ew", padx=8, pady=2)
            row.grid_columnconfigure(1, weight=1)

            # Número
            ctk.CTkLabel(row,
                text=f"{idx+1:02d}",
                font=ctk.CTkFont(family="Courier New", size=11),
                text_color=MUTED, width=28, anchor="e",
            ).grid(row=0, column=0, padx=(10, 6), pady=8, sticky="e")

            # Título
            title = (entry.get("title") or entry.get("url") or f"Vídeo {idx+1}")[:70]
            ctk.CTkLabel(row,
                text=title,
                font=ctk.CTkFont(size=12), text_color=TEXT,
                anchor="w", wraplength=max(ww - 200, 300),
            ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)

            # Duração
            dur = int(entry.get("duration", 0) or 0)
            dur_str = f"{dur//60}:{dur%60:02d}" if dur else "—"
            ctk.CTkLabel(row,
                text=dur_str,
                font=ctk.CTkFont(family="Courier New", size=10),
                text_color=MUTED, width=42, anchor="e",
            ).grid(row=0, column=2, padx=(0, 8), pady=8, sticky="e")

            # Checkbox
            ctk.CTkCheckBox(row, text="", variable=var,
                width=24, height=24,
                checkmark_color=BG, hover_color=BLUE,
                fg_color=BLUE, border_color=MUTED,
            ).grid(row=0, column=3, padx=(0, 10), pady=8)

        # ── Footer ──
        footer = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=58)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(footer, text="⬇  Baixar selecionados",
            height=38, fg_color=BLUE, hover_color=BLUE_H,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            command=self._confirm,
        ).pack(side="right", padx=14, pady=10)

        ctk.CTkButton(footer, text="Cancelar",
            height=38, width=90, fg_color=BORDER, hover_color="#3d1515",
            font=ctk.CTkFont(size=12), corner_radius=8,
            command=self.destroy,
        ).pack(side="right", padx=(0, 6), pady=10)

    def _select_all(self):
        for v in self._checks: v.set(True)

    def _deselect_all(self):
        for v in self._checks: v.set(False)

    def _update_count(self):
        n = sum(1 for v in self._checks if v.get())
        total = len(self._checks)
        color = GREEN if n == total else (ORANGE if n > 0 else RED)
        self._count_lbl.configure(
            text=f"{n} de {total} selecionados", text_color=color)

    def _confirm(self):
        selected = [e for e, v in zip(self.entries, self._checks) if v.get()]
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um vídeo.", parent=self)
            return
        self.destroy()
        self.callback(selected)


# ══════════════════════════════════════════════════════════════ #
class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.title("OffTube")
        self.resizable(True, True)

        self.url_v    = ctk.StringVar()
        self.fmt_v    = ctk.StringVar(value="mp4")
        self.qual_v   = ctk.StringVar(value="Melhor")
        self.folder_v = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.pl_v     = ctk.BooleanVar(value=False)
        self.sub_v    = ctk.BooleanVar(value=False)
        self.thumb_v      = ctk.BooleanVar(value=False)
        self.thumb_fmt_v  = ctk.StringVar(value="jpg")
        self.mp3_qual_v   = ctk.StringVar(value="192k")

        self._dl_t           = None
        self._th_t           = None
        self._stop           = False
        self._last_url       = ""
        self._img_ref        = None
        self._pl_total       = 0
        self._pl_done        = 0
        self._last_finished  = None   # evita dupla contagem no hook "finished"
        self._pl_entries = []    # entries carregadas no preview (playlist)
        self._is_playlist = False
        self.history     = load_hist()

        self._build()
        self.update_idletasks()
        self._fit_screen()
        self.url_v.trace_add("write", self._url_changed)
        self.after(500, self._start_update_check)
        # Notifica abertura no Discord
        threading.Thread(target=_send_discord_open, daemon=True).start()

    def _fit_screen(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(min(1100, int(sw * 0.75)), 1000)
        h = max(min(700,  int(sh * 0.80)), 600)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(1000, 600)

    def _start_update_check(self):
        threading.Thread(target=self._check_update, daemon=True).start()
        threading.Thread(target=self._update_loop,  daemon=True).start()

    def _check_update(self):
        if not IS_FROZEN:
            self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION} (Dev)", MUTED))
            return
        self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION}  verificando...", MUTED))
        dl_url, tag, body = _fetch_release()
        if not tag or not dl_url:
            self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION}", MUTED))
            return
        if _version_tuple(tag) > _version_tuple(APP_VERSION):
            self.after(0, lambda: self._set_update_lbl(f"⟳ Atualizando para {tag}...", ORANGE))
            exe_bytes = _download_exe(dl_url, progress_cb=lambda r: self.after(
                0, lambda p=int(r*100): self._set_update_lbl(f"⬇ Baixando {p}%...", YELLOW)))
            if exe_bytes:
                self.after(0, lambda: self._set_update_lbl("🔄 Aplicando... reiniciando!", YELLOW))
                # Notifica atualização no Discord
                threading.Thread(target=_send_discord_updated, daemon=True).start()
                time.sleep(0.8)
                _apply_update(exe_bytes)
            else:
                self.after(0, lambda: self._set_update_lbl("✗ Falha no download", RED))
        else:
            self.after(0, lambda: self._set_update_lbl(f"✓ {tag} (atual)", GREEN))

    def _update_loop(self):
        while True:
            time.sleep(UPDATE_CHECK_INTERVAL)
            try: self._check_update()
            except Exception: pass

    def _set_update_lbl(self, text, color):
        try: self.update_lbl.configure(text=text, text_color=color)
        except Exception: pass

    # ── UI ─────────────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=50)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Off",
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
            text_color=TEXT).grid(row=0, column=0, padx=(18, 0), pady=14, sticky="w")
        ctk.CTkLabel(top, text="Tube",
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
            text_color=BLUE).grid(row=0, column=1, pady=14, sticky="w")

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, padx=14, sticky="e")

        ctk.CTkLabel(right, text="by KaueFSS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT).pack(side="left", padx=(0, 12))

        self.update_lbl = ctk.CTkLabel(right, text=f"● {APP_VERSION}",
            font=ctk.CTkFont(size=11), text_color=MUTED)
        self.update_lbl.pack(side="left", padx=(0, 12))

        ctk.CTkButton(right, text="GitHub ↗", width=80, height=28,
            font=ctk.CTkFont(size=11), fg_color=BORDER, hover_color="#2a2a42",
            corner_radius=5,
            command=lambda: webbrowser.open("https://github.com/KaueFSS"),
        ).pack(side="left")

        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BORDER)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        P = {"padx": 18, "sticky": "ew"}

        row0 = ctk.CTkFrame(body, fg_color="transparent")
        row0.grid(row=0, column=0, pady=(14, 0), padx=18, sticky="ew")
        row0.grid_columnconfigure(1, weight=1)

        thumb_card = ctk.CTkFrame(row0, fg_color=CARD, corner_radius=10,
                                   border_width=1, border_color=BORDER, width=200, height=118)
        thumb_card.grid(row=0, column=0, sticky="w")
        thumb_card.grid_propagate(False)

        self.thumb_lbl = ctk.CTkLabel(thumb_card, text="🎬",
            font=ctk.CTkFont(size=22), text_color=MUTED,
            width=200, height=118, fg_color="transparent")
        self.thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")

        info_col = ctk.CTkFrame(row0, fg_color="transparent")
        info_col.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        info_col.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(info_col, text="Cole um link para começar",
            font=ctk.CTkFont(size=13), text_color=MUTED,
            anchor="nw", wraplength=560, justify="left")
        self.title_lbl.grid(row=0, column=0, sticky="nw", pady=(4, 0))

        self.meta_lbl = ctk.CTkLabel(info_col, text="",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=MUTED, anchor="w")
        self.meta_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # ── Banner de playlist detectada ──────────────────────
        self._pl_banner = ctk.CTkFrame(info_col,
            fg_color="#1a1a2e", corner_radius=8,
            border_width=1, border_color=PURPLE)
        self._pl_banner.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._pl_banner.grid_columnconfigure(0, weight=1)
        self._pl_banner.grid_remove()

        pl_inner = ctk.CTkFrame(self._pl_banner, fg_color="transparent")
        pl_inner.grid(row=0, column=0, padx=10, pady=6, sticky="ew")
        pl_inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(pl_inner,
            text="📋  Playlist detectada!  Clique em Baixar para selecionar os vídeos.",
            font=ctk.CTkFont(size=11), text_color=PURPLE, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        url_row = ctk.CTkFrame(body, fg_color="transparent")
        url_row.grid(row=1, column=0, pady=(12, 0), **P)
        url_row.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(url_row, placeholder_text="URL do YouTube...",
            textvariable=self.url_v, height=40, font=ctk.CTkFont(size=13),
            fg_color=CARD, border_color=BORDER, border_width=1)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(url_row, text="Colar", width=70, height=40,
            fg_color=BORDER, hover_color="#2a2a42", corner_radius=6,
            command=self._paste).grid(row=0, column=1)

        line2 = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                              border_width=1, border_color=BORDER)
        line2.grid(row=2, column=0, pady=(10, 0), **P)
        line2.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._sl(line2, "Formato", 0, 0)
        ctk.CTkOptionMenu(line2, values=["mp4", "mp3", "mkv", "webm"],
            variable=self.fmt_v, command=self._fmt_changed,
            height=32, fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H,
        ).grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        self._sl(line2, "Qualidade vídeo", 0, 1)
        self.qual_om = ctk.CTkOptionMenu(line2,
            values=["360p", "480p", "720p", "1080p", "4K", "Melhor"],
            variable=self.qual_v,
            height=32, fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H)
        self.qual_om.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="ew")

        self.mp3_qual_lbl = ctk.CTkLabel(line2, text="Qualidade MP3",
            font=ctk.CTkFont(size=10), text_color=MUTED)
        self.mp3_qual_lbl.grid(row=0, column=2, padx=10, pady=(8, 2), sticky="w")
        self.mp3_qual_lbl.grid_remove()

        self.mp3_qual_om = ctk.CTkOptionMenu(line2,
            values=["320k", "256k", "192k", "128k", "96k"],
            variable=self.mp3_qual_v,
            height=32, fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H)
        self.mp3_qual_om.grid(row=1, column=2, padx=10, pady=(2, 10), sticky="ew")
        self.mp3_qual_om.grid_remove()

        self._sl(line2, "Pasta de destino", 0, 3)
        folder_inner = ctk.CTkFrame(line2, fg_color="transparent")
        folder_inner.grid(row=1, column=3, padx=10, pady=(2, 10), sticky="ew")
        folder_inner.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(folder_inner, textvariable=self.folder_v, state="readonly",
            height=32, fg_color=BORDER, border_color=BORDER, border_width=0,
            font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(folder_inner, text="📁", width=32, height=32,
            fg_color=SURFACE, hover_color="#2a2a42", corner_radius=5,
            command=self._pick_folder).grid(row=0, column=1)

        chk = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)
        chk.grid(row=3, column=0, pady=(8, 0), **P)
        chk.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (lbl, var) in enumerate([
            ("Legendas (pt/en)", self.sub_v),
        ]):
            ctk.CTkCheckBox(chk, text=lbl, variable=var,
                font=ctk.CTkFont(size=12), checkmark_color=BLUE,
                hover_color=BLUE, fg_color=BLUE, border_color=MUTED,
            ).grid(row=0, column=i, padx=14, pady=8)

        # Thumbnail
        thumb_cell = ctk.CTkFrame(chk, fg_color="transparent")
        thumb_cell.grid(row=0, column=1, padx=14, pady=8, sticky="ew")

        self.thumb_cb = ctk.CTkCheckBox(thumb_cell, text="Salvar thumbnail",
            variable=self.thumb_v,
            font=ctk.CTkFont(size=12), checkmark_color=BLUE,
            hover_color=BLUE, fg_color=BLUE, border_color=MUTED,
            command=self._thumb_toggle,
        )
        self.thumb_cb.pack(side="left")

        self.thumb_fmt_om = ctk.CTkOptionMenu(
            thumb_cell,
            values=["jpg", "png", "webp"],
            variable=self.thumb_fmt_v,
            width=72, height=26,
            fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H,
            font=ctk.CTkFont(size=11),
            state="disabled",
        )
        self.thumb_fmt_om.pack(side="left", padx=(8, 0))

        pgcard = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                               border_width=1, border_color=BORDER)
        pgcard.grid(row=4, column=0, pady=(8, 0), **P)
        pgcard.grid_columnconfigure(0, weight=1)

        ri = ctk.CTkFrame(pgcard, fg_color="transparent")
        ri.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 3))
        ri.grid_columnconfigure(0, weight=1)

        self.prog_lbl = ctk.CTkLabel(ri, text="Aguardando",
            font=ctk.CTkFont(size=12), text_color=MUTED, anchor="w")
        self.prog_lbl.grid(row=0, column=0, sticky="w")

        self.speed_lbl = ctk.CTkLabel(ri, text="",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=BLUE, anchor="e")
        self.speed_lbl.grid(row=0, column=1, sticky="e")

        self.pl_count_lbl = ctk.CTkLabel(pgcard, text="",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ORANGE, anchor="w")
        self.pl_count_lbl.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.pbar = ctk.CTkProgressBar(pgcard, height=5, corner_radius=3,
            progress_color=BLUE, fg_color=BORDER)
        self.pbar.set(0)
        self.pbar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(pgcard, text="",
            font=ctk.CTkFont(size=10), text_color=MUTED,
            wraplength=700, anchor="w")
        self.status_lbl.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 4))

        self.vid_prog_lbl = ctk.CTkLabel(pgcard, text="",
            font=ctk.CTkFont(family="Courier New", size=10), text_color=BLUE, anchor="w")
        self.vid_prog_lbl.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.vid_pbar = ctk.CTkProgressBar(pgcard, height=3, corner_radius=2,
            progress_color=GREEN, fg_color=BORDER)
        self.vid_pbar.set(0)
        self.vid_pbar.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 2))

        # Barra de processamento (ffmpeg merge) — laranja, logo abaixo da verde
        self.proc_lbl = ctk.CTkLabel(pgcard, text="",
            font=ctk.CTkFont(family="Courier New", size=10), text_color=ORANGE, anchor="w")
        self.proc_lbl.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.proc_pbar = ctk.CTkProgressBar(pgcard, height=3, corner_radius=2,
            progress_color=ORANGE, fg_color=BORDER, mode="indeterminate",
            indeterminate_speed=0.8)
        self.proc_pbar.set(0)
        self.proc_pbar.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.proc_pbar.grid_remove()
        self.proc_lbl.grid_remove()

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.grid(row=5, column=0, pady=(10, 4), **P)
        btn_row.grid_columnconfigure(0, weight=1)

        self.dl_btn = ctk.CTkButton(btn_row, text="⬇  Baixar", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=BLUE, hover_color=BLUE_H, corner_radius=8,
            command=self._start)
        self.dl_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.cancel_btn = ctk.CTkButton(btn_row, text="✕", width=40, height=40,
            fg_color=BORDER, hover_color="#3d1515",
            corner_radius=8, state="disabled", command=self._cancel)
        self.cancel_btn.grid(row=0, column=1, padx=(0, 6))

        ctk.CTkButton(btn_row, text="📋", width=40, height=40,
            fg_color=BORDER, hover_color="#2a2a42", corner_radius=8,
            command=self._history_window).grid(row=0, column=2)

        ctk.CTkLabel(body,
            text="OffTube  ·  yt-dlp  ·  FFmpeg embutido  ·  KaueFSS",
            font=ctk.CTkFont(size=10), text_color=BORDER,
        ).grid(row=6, column=0, pady=(4, 10))

    # ── Helpers ────────────────────────────────────────────────
    def _sl(self, p, t, r, c):
        ctk.CTkLabel(p, text=t, font=ctk.CTkFont(size=10), text_color=MUTED
        ).grid(row=r, column=c, padx=10, pady=(8, 2), sticky="w")

    def _paste(self):
        try: self.url_v.set(self.clipboard_get().strip())
        except Exception: pass

    def _pick_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_v.get())
        if d: self.folder_v.set(d)

    def _fmt_changed(self, v):
        if v == "mp3":
            self.qual_om.grid_remove()
            for w in self.qual_om.master.grid_slaves(row=0, column=1):
                w.grid_remove()
            self.mp3_qual_lbl.grid()
            self.mp3_qual_om.grid()
        else:
            self.mp3_qual_lbl.grid_remove()
            self.mp3_qual_om.grid_remove()
            for w in self.qual_om.master.grid_slaves(row=0, column=1):
                w.grid()
            self.qual_om.grid()

    def _thumb_toggle(self):
        state = "normal" if self.thumb_v.get() else "disabled"
        self.thumb_fmt_om.configure(state=state)

    def _set_busy(self, on):
        self.dl_btn.configure(state="disabled" if on else "normal")
        self.cancel_btn.configure(state="normal" if on else "disabled")

    def _reset_prog(self):
        self.pbar.set(0)
        self.vid_pbar.set(0)
        self._pl_total       = 0
        self._pl_done        = 0
        self._last_finished  = None
        self.prog_lbl.configure(text="Iniciando...", text_color=TEXT)
        self.speed_lbl.configure(text="")
        self.status_lbl.configure(text="", text_color=MUTED)
        self.pl_count_lbl.configure(text="")
        self.vid_prog_lbl.configure(text="")
        try:
            self.proc_pbar.stop()
            self.proc_pbar.grid_remove()
            self.proc_lbl.grid_remove()
        except Exception:
            pass

    # ── Preview ────────────────────────────────────────────────
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
        if len(url) < 16: return
        if hasattr(self, "_preview_after"):
            self.after_cancel(self._preview_after)
        self._preview_after = self.after(700, lambda: self._trigger_preview(url))

    def _trigger_preview(self, url):
        if url != self.url_v.get().strip(): return
        if self._th_t and self._th_t.is_alive():
            self.after(800, lambda: self._trigger_preview(url))
            return
        self._last_url = url
        self._th_t = threading.Thread(target=self._load_preview, args=(url,), daemon=True)
        self._th_t.start()

    def _load_preview(self, url):
        if url != self.url_v.get().strip(): return
        self.after(0, lambda: (
            self.title_lbl.configure(text="Carregando...", text_color=MUTED),
            self.meta_lbl.configure(text=""),
        ))
        try:
            ydl_opts = {
                "quiet"          : True,
                "no_warnings"    : True,
                "skip_download"  : True,
                "extract_flat"   : "in_playlist",
                "ffmpeg_location": FFMPEG,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if url != self.url_v.get().strip(): return
            if not info: raise Exception("sem info")

            is_playlist = info.get("_type") == "playlist" or "entries" in info

            if is_playlist:
                entries  = list(info.get("entries") or [])
                count    = len(entries)
                pl_title = info.get("title", "Playlist")
                ch       = info.get("uploader") or info.get("channel", "")
                short    = pl_title[:70] + ("…" if len(pl_title) > 70 else "")
                meta     = f"📋 Playlist  ·  {count} vídeo{'s' if count != 1 else ''}   📺 {ch[:30]}"
                thumb = info.get("thumbnail", "")
                if not thumb and entries:
                    thumb = entries[0].get("thumbnail", "") if entries[0] else ""

                # Guarda entries para o seletor
                self._pl_entries  = entries
                self._is_playlist = True
                self._pl_title    = pl_title

                self.after(0, lambda: self._pl_banner.grid())
            else:
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
                self.after(0, lambda: self._pl_banner.grid_remove())

            self.after(0, lambda s=short, m=meta: (
                self.title_lbl.configure(text=s, text_color=TEXT),
                self.meta_lbl.configure(text=m, text_color=MUTED),
            ))

            if thumb:
                try:
                    req  = urllib.request.Request(thumb, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        data = r.read()
                    img  = Image.open(io.BytesIO(data)).convert("RGB").resize((200, 113), Image.LANCZOS)
                    cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 113))
                    self._img_ref = cimg
                    self.after(0, lambda i=cimg: self.thumb_lbl.configure(image=i, text=""))
                except Exception:
                    pass
        except Exception as e:
            self.after(0, lambda: self.title_lbl.configure(
                text="Não foi possível carregar o preview.", text_color=MUTED))

    # ── Progress hook ──────────────────────────────────────────
    def _hook(self, d):
        if self._stop:
            raise yt_dlp.utils.DownloadCancelled()

        st = d.get("status")

        info = d.get("info_dict", {})
        n_entries = info.get("n_entries") or d.get("n_entries")
        if n_entries and n_entries != self._pl_total:
            self._pl_total = n_entries

        if st == "downloading":
            raw = clean(d.get("_percent_str", "0%")).replace("%", "")
            try:
                pct = float(raw)
                self.after(0, lambda p=pct: (
                    self.vid_pbar.set(p / 100),
                    self.vid_prog_lbl.configure(
                        text=f"Vídeo atual: {p:.1f}%", text_color=BLUE),
                ))
            except Exception: pass

            sp  = clean(d.get("_speed_str", ""))
            eta = clean(d.get("_eta_str", ""))
            if sp and sp != "N/A":
                self.after(0, lambda s=sp, e=eta:
                    self.speed_lbl.configure(text=f"{s}  ETA {e}"))

            fn = d.get("filename", "")
            if fn:
                self.after(0, lambda b=os.path.basename(fn):
                    self.status_lbl.configure(text=b, text_color=MUTED))

            if self._pl_total > 1:
                try:
                    vid_frac = pct / 100
                except Exception:
                    vid_frac = 0
                overall = (self._pl_done + vid_frac) / self._pl_total
                faltam  = self._pl_total - self._pl_done - 1
                self.after(0, lambda o=overall, d=self._pl_done+1, t=self._pl_total, f=max(faltam,0): (
                    self.pbar.set(o),
                    self.prog_lbl.configure(
                        text=f"Vídeo {d} de {t}", text_color=TEXT),
                    self.pl_count_lbl.configure(
                        text=f"⏳ Faltam {f} vídeo{'s' if f!=1 else ''}", text_color=ORANGE),
                ))
            else:
                try:
                    self.after(0, lambda p=pct: (
                        self.pbar.set(p / 100),
                        self.prog_lbl.configure(text=f"{p:.1f}%", text_color=TEXT),
                    ))
                except Exception: pass

        elif st == "finished":
            # yt-dlp dispara "finished" para cada stream baixado (ex: vídeo .f137 e áudio .f251).
            # Usa o ID do vídeo para contar cada vídeo apenas 1x.
            vid_id = d.get("info_dict", {}).get("id") or d.get("filename", "")
            if vid_id and vid_id == self._last_finished:
                # segundo stream do mesmo vídeo → mostra barra de processamento (merge ffmpeg)
                self.after(0, lambda: (
                    self.proc_lbl.configure(text="Processando (merge)...", text_color=ORANGE),
                    self.proc_lbl.grid(),
                    self.proc_pbar.grid(),
                    self.proc_pbar.start(),
                    self.vid_prog_lbl.configure(text=""),
                    self.speed_lbl.configure(text=""),
                ))
                return
            self._last_finished = vid_id or None
            self._pl_done += 1
            done = self._pl_done
            total = self._pl_total
            overall = done / total if total > 0 else 1.0
            faltam  = max(total - done, 0)

            self.after(0, lambda o=overall, dn=done, t=total, f=faltam: (
                self.pbar.set(o),
                self.vid_pbar.set(1),
                # esconde proc bar quando começa próximo vídeo
                self.proc_pbar.stop(),
                self.proc_pbar.grid_remove(),
                self.proc_lbl.grid_remove(),
                self.prog_lbl.configure(
                    text=f"Vídeo {dn} de {t}" if t > 1 else "Baixando...",
                    text_color=TEXT),
                self.pl_count_lbl.configure(
                    text=f"⏳ Faltam {f} vídeo{'s' if f!=1 else ''}" if t > 1 and f > 0 else (
                         "✓ Todos baixados!" if t > 1 else ""),
                    text_color=GREEN if f == 0 else ORANGE),
                self.speed_lbl.configure(text=""),
                self.vid_prog_lbl.configure(text=""),
            ))

    # ── ydl opts ───────────────────────────────────────────────
    def _opts(self, folder, urls=None):
        fmt  = self.fmt_v.get()
        qual = self.qual_v.get()

        o = {
            "progress_hooks"  : [self._hook],
            "outtmpl"         : os.path.join(folder, "%(title)s.%(ext)s"),
            "noplaylist"      : True,   # sempre True — gerenciamos a lista manualmente
            "writethumbnail"  : self.thumb_v.get(),
            "ignoreerrors"    : True,
            "retries"         : 5,
            "fragment_retries": 10,
            "socket_timeout"  : 30,
            "ffmpeg_location" : FFMPEG,
            "keepvideo"       : False,
        }

        if self.thumb_v.get():
            thumb_fmt = self.thumb_fmt_v.get()
            o["postprocessors"] = o.get("postprocessors", []) + [{
                "key"            : "FFmpegThumbnailsConvertor",
                "format"         : thumb_fmt,
                "when"           : "before_dl",
            }]

        if self.sub_v.get():
            o.update({"writesubtitles": True, "subtitleslangs": ["pt", "en"],
                      "writeautomaticsub": True})

        if fmt == "mp3":
            quality = self.mp3_qual_v.get().replace("k", "")
            mp3_pp = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality}]
            o["format"] = "bestaudio/best"
            o["postprocessors"] = o.get("postprocessors", []) + mp3_pp
            return o

        h = {"360p":"360","480p":"480","720p":"720","1080p":"1080","4K":"2160","Melhor":None}.get(qual)

        if fmt == "mp4":
            f = (f"bestvideo[height<={h}][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]"
                 f"/bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                 f"/bestvideo[height<={h}]+bestaudio/best") if h else (
                "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]"
                "/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best")
        else:
            f = (f"bestvideo[height<={h}][ext={fmt}]+bestaudio/bestvideo[height<={h}]+bestaudio/best"
                 if h else f"bestvideo[ext={fmt}]+bestaudio/bestvideo+bestaudio/best")

        o["format"]              = f
        o["merge_output_format"] = fmt
        return o

    # ── Download ───────────────────────────────────────────────
    def _run(self, selected_entries=None):
        """
        selected_entries: lista de dicts com 'url' e 'title', ou None para vídeo único.
        """
        url    = self.url_v.get().strip()
        folder = self.folder_v.get().strip()

        if not url:
            messagebox.showwarning("Aviso", "Insira um link.")
            self.after(0, lambda: self._set_busy(False))
            return
        if not os.path.isdir(folder):
            messagebox.showwarning("Aviso", "Pasta inválida.")
            self.after(0, lambda: self._set_busy(False))
            return

        self._stop = False
        start_time = time.time()
        downloaded_titles = []

        try:
            opts = self._opts(folder)

            if selected_entries:
                # ── Playlist: baixa um a um conforme seleção ──
                self._pl_total = len(selected_entries)
                self._pl_done  = 0

                for entry in selected_entries:
                    if self._stop:
                        break
                    vid_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
                    if not vid_url:
                        continue
                    # Monta URL absoluta se vier só o ID
                    if not vid_url.startswith("http"):
                        vid_url = f"https://www.youtube.com/watch?v={vid_url}"

                    try:
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            info = ydl.extract_info(vid_url, download=not self._stop)
                        title = (info.get("title", "") if info else "") or vid_url
                        downloaded_titles.append(title)
                    except yt_dlp.utils.DownloadCancelled:
                        break
                    except Exception:
                        pass  # ignora erros individuais e continua

            else:
                # ── Vídeo único ──
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=not self._stop)
                title = (info.get("title", "") if info else "") or url
                downloaded_titles.append(title)

            elapsed = time.time() - start_time

            if self._stop:
                self.after(0, lambda: (
                    self.prog_lbl.configure(text="Cancelado", text_color=MUTED),
                    self.status_lbl.configure(text=""),
                ))
            else:
                # Salva histórico
                for t in downloaded_titles:
                    self.history.append({
                        "url": url, "title": t, "folder": folder,
                        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    })
                save_hist(self.history)

                n = len(downloaded_titles)
                self.after(0, lambda: (
                    self.prog_lbl.configure(text=f"Concluído ✓  ({n} vídeo{'s' if n!=1 else ''})", text_color=GREEN),
                    self.status_lbl.configure(text="", text_color=MUTED),
                    self.proc_pbar.stop(),
                    self.proc_pbar.grid_remove(),
                    self.proc_lbl.grid_remove(),
                ))

                # Envia notificação no Discord em background
                threading.Thread(
                    target=_send_discord,
                    args=(n, elapsed, downloaded_titles, folder,
                          self.fmt_v.get(), self.qual_v.get(), self.mp3_qual_v.get(),
                          self.thumb_v.get(), self.thumb_fmt_v.get()),
                    daemon=True,
                ).start()

                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                tempo_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
                messagebox.showinfo(
                    "Pronto",
                    f"{'Download' if n == 1 else f'{n} downloads'} concluído{'s' if n!=1 else ''} em {tempo_str}!\n"
                    + (downloaded_titles[0][:70] if n == 1 else f"{n} vídeos baixados")
                )

        except yt_dlp.utils.DownloadCancelled:
            self.after(0, lambda: (
                self.prog_lbl.configure(text="Cancelado", text_color=MUTED),
                self.status_lbl.configure(text=""),
            ))
        except yt_dlp.utils.DownloadError as e:
            if not self._stop:
                messagebox.showerror("Erro", str(e)[:200])
                self.after(0, lambda: self.prog_lbl.configure(text="Erro no download", text_color=RED))
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e)[:200])
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _start(self):
        url = self.url_v.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Insira um link.")
            return

        if self._is_playlist and self._pl_entries:
            # Abre o seletor de vídeos da playlist
            pl_title = getattr(self, "_pl_title", "Playlist")
            PlaylistSelectorWindow(
                self, self._pl_entries, pl_title,
                callback=self._start_with_selection,
            )
        else:
            self._reset_prog()
            self._set_busy(True)
            threading.Thread(target=self._run, args=(None,), daemon=True).start()

    def _start_with_selection(self, selected_entries):
        self._reset_prog()
        self._set_busy(True)
        threading.Thread(target=self._run, args=(selected_entries,), daemon=True).start()

    def _cancel(self):
        self._stop = True
        self.after(0, lambda: self.prog_lbl.configure(text="Cancelando...", text_color=YELLOW))

    # ── Histórico ──────────────────────────────────────────────
    def _history_window(self):
        if hasattr(self, "_hist_win") and self._hist_win.winfo_exists():
            self._hist_win.focus()
            return

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ww = min(600, int(sw * 0.45))
        wh = min(460, int(sh * 0.65))

        self._hist_win = ctk.CTkToplevel(self)
        w = self._hist_win
        w.title("Histórico — OffTube")
        w.configure(fg_color=BG)
        w.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        w.grab_set()

        ctk.CTkLabel(w, text="Histórico",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT).pack(padx=16, pady=(14, 8), anchor="w")

        sf = ctk.CTkScrollableFrame(w, fg_color=BG, scrollbar_button_color=BORDER)
        sf.pack(fill="both", expand=True, padx=16)

        if not self.history:
            ctk.CTkLabel(sf, text="Nenhum download ainda.", text_color=MUTED).pack(pady=20)
        else:
            for item in reversed(self.history):
                card = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=8,
                                     border_width=1, border_color=BORDER)
                card.pack(fill="x", pady=3)
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(card, text=item.get("title", item["url"])[:65],
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=TEXT, anchor="w",
                ).grid(row=0, column=0, padx=10, pady=(7, 1), sticky="ew")

                ctk.CTkLabel(card,
                    text=f"{item['date']}  ·  {Path(item.get('folder','')).name}",
                    font=ctk.CTkFont(size=10), text_color=MUTED, anchor="w",
                ).grid(row=1, column=0, padx=10, pady=(0, 7), sticky="ew")

                ctk.CTkButton(card, text="↗", width=36, height=36,
                    fg_color=BORDER, hover_color=BLUE_H, corner_radius=6,
                    command=lambda u=item["url"]: (self.url_v.set(u), w.destroy()),
                ).grid(row=0, column=1, rowspan=2, padx=8)

        btn_row = ctk.CTkFrame(w, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 14))
        btn_row.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(btn_row, text="Limpar histórico",
            height=34, fg_color=BORDER, hover_color=RED, corner_radius=6,
            font=ctk.CTkFont(size=12),
            command=lambda: (self.history.clear(), save_hist([]), w.destroy()),
        ).grid(row=0, column=0, sticky="ew")


# ══════════════════════════════════════════════════════════════ #
if __name__ == "__main__":
    app = App()
    app.mainloop()