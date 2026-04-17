# ═══════════════════════════════════════════════════════════════
#  ui/app.py — Janela principal do OffTube
#  ► Layout / widgets: edite os métodos _build_*()
#  ► Progresso: ui/progress_hooks.py
#  ► Preview:   ui/preview.py
#  ► Download:  core/downloader.py
# ═══════════════════════════════════════════════════════════════
import os, threading, time, webbrowser
from datetime import datetime
from pathlib  import Path
from tkinter  import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

from core.config     import APP_VERSION, UPDATE_CHECK_INTERVAL
from core.history    import load_hist, save_hist
from core.downloader import build_opts, run_download, FFMPEG
from core.setup      import IS_FROZEN
from core.updater    import fetch_release, download_exe, apply_update, is_newer
from core            import discord as dc
from ui.theme        import (BG, SURFACE, CARD, BORDER,
                              BLUE, BLUE_H, TEXT, MUTED,
                              GREEN, RED, YELLOW, ORANGE, PURPLE)
from ui.progress_hooks  import ProgressMixin
from ui.preview         import PreviewMixin
from ui.playlist_window import PlaylistSelectorWindow
from ui.history_window  import open_history_window


class App(ProgressMixin, PreviewMixin, ctk.CTk):

    def __init__(self):
        ctk.CTk.__init__(self)
        self.configure(fg_color=BG)
        self.title("OffTube")
        self.resizable(True, True)

        # Variáveis de controle
        self.url_v       = ctk.StringVar()
        self.fmt_v       = ctk.StringVar(value="mp4")
        self.qual_v      = ctk.StringVar(value="Melhor")
        self.folder_v    = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.sub_v       = ctk.BooleanVar(value=False)
        self.thumb_v     = ctk.BooleanVar(value=False)
        self.thumb_fmt_v = ctk.StringVar(value="jpg")
        self.mp3_qual_v  = ctk.StringVar(value="192k")

        # Estado interno
        self._dl_t          = None
        self._th_t          = None
        self._stop          = False
        self._last_url      = ""
        self._img_ref       = None
        self._pl_total      = 0
        self._pl_done       = 0
        self._last_finished = None
        self._pl_entries    = []
        self._is_playlist   = False
        self.history        = load_hist()

        self._build()
        self.update_idletasks()
        self._fit_screen()
        self.url_v.trace_add("write", self._url_changed)
        self.after(500, self._start_update_check)
        threading.Thread(target=dc.send_open, daemon=True).start()

    # ── Tamanho ─────────────────────────────────────────────────
    def _fit_screen(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(min(1100, int(sw * 0.75)), 1000)
        h = max(min(700,  int(sh * 0.80)), 600)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(1000, 600)

    # ── Auto-atualização ────────────────────────────────────────
    def _start_update_check(self):
        threading.Thread(target=self._check_update, daemon=True).start()
        threading.Thread(target=self._update_loop,  daemon=True).start()

    def _check_update(self):
        if not IS_FROZEN:
            self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION} (Dev)", MUTED))
            return
        self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION}  verificando...", MUTED))
        dl_url, tag, _ = fetch_release()
        if not tag or not dl_url:
            self.after(0, lambda: self._set_update_lbl(f"● {APP_VERSION}", MUTED))
            return
        if is_newer(tag):
            self.after(0, lambda: self._set_update_lbl(f"⟳ Atualizando para {tag}...", ORANGE))
            exe_bytes = download_exe(dl_url, progress_cb=lambda r: self.after(
                0, lambda p=int(r*100): self._set_update_lbl(f"⬇ Baixando {p}%...", YELLOW)))
            if exe_bytes:
                self.after(0, lambda: self._set_update_lbl("🔄 Aplicando... reiniciando!", YELLOW))
                threading.Thread(target=dc.send_updated, daemon=True).start()
                time.sleep(0.8)
                apply_update(exe_bytes)
            else:
                self.after(0, lambda: self._set_update_lbl("✗ Falha no download", RED))
        else:
            self.after(0, lambda: self._set_update_lbl(f"✓ {tag} (atual)", GREEN))

    def _update_loop(self):
        while True:
            time.sleep(UPDATE_CHECK_INTERVAL)
            try:
                self._check_update()
            except Exception:
                pass

    def _set_update_lbl(self, text, color):
        try:
            self.update_lbl.configure(text=text, text_color=color)
        except Exception:
            pass

    # ── Build ───────────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_topbar()
        body = self._build_body()
        self._build_preview_area(body)
        self._build_url_row(body)
        self._build_options(body)
        self._build_checkboxes(body)
        self._build_progress(body)
        self._build_buttons(body)
        ctk.CTkLabel(body,
            text="OffTube  ·  yt-dlp  ·  FFmpeg embutido  ·  KaueFSS",
            font=ctk.CTkFont(size=10), text_color=BORDER,
        ).grid(row=6, column=0, pady=(4, 10))

    def _build_topbar(self):
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

    def _build_body(self):
        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BORDER)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        return body

    def _build_preview_area(self, body):
        """Widgets do preview; a lógica vive em ui/preview.py (PreviewMixin)."""
        row0 = ctk.CTkFrame(body, fg_color="transparent")
        row0.grid(row=0, column=0, pady=(14, 0), padx=18, sticky="ew")
        row0.grid_columnconfigure(1, weight=1)

        tc = ctk.CTkFrame(row0, fg_color=CARD, corner_radius=10,
                           border_width=1, border_color=BORDER, width=200, height=118)
        tc.grid(row=0, column=0, sticky="w")
        tc.grid_propagate(False)
        self.thumb_lbl = ctk.CTkLabel(tc, text="🎬",
            font=ctk.CTkFont(size=22), text_color=MUTED,
            width=200, height=118, fg_color="transparent")
        self.thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")

        ic = ctk.CTkFrame(row0, fg_color="transparent")
        ic.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        ic.grid_columnconfigure(0, weight=1)
        self.title_lbl = ctk.CTkLabel(ic, text="Cole um link para começar",
            font=ctk.CTkFont(size=13), text_color=MUTED,
            anchor="nw", wraplength=560, justify="left")
        self.title_lbl.grid(row=0, column=0, sticky="nw", pady=(4, 0))
        self.meta_lbl = ctk.CTkLabel(ic, text="",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=MUTED, anchor="w")
        self.meta_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._pl_banner = ctk.CTkFrame(ic, fg_color="#1a1a2e", corner_radius=8,
                                        border_width=1, border_color=PURPLE)
        self._pl_banner.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._pl_banner.grid_columnconfigure(0, weight=1)
        self._pl_banner.grid_remove()
        pi = ctk.CTkFrame(self._pl_banner, fg_color="transparent")
        pi.grid(row=0, column=0, padx=10, pady=6, sticky="ew")
        pi.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pi,
            text="📋  Playlist detectada!  Clique em Baixar para selecionar os vídeos.",
            font=ctk.CTkFont(size=11), text_color=PURPLE, anchor="w",
        ).grid(row=0, column=0, sticky="w")

    def _build_url_row(self, body):
        r = ctk.CTkFrame(body, fg_color="transparent")
        r.grid(row=1, column=0, pady=(12, 0), padx=18, sticky="ew")
        r.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(r, placeholder_text="URL do YouTube...",
            textvariable=self.url_v, height=40, font=ctk.CTkFont(size=13),
            fg_color=CARD, border_color=BORDER, border_width=1)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(r, text="Colar", width=70, height=40,
            fg_color=BORDER, hover_color="#2a2a42", corner_radius=6,
            command=self._paste).grid(row=0, column=1)

    def _build_options(self, body):
        f = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                          border_width=1, border_color=BORDER)
        f.grid(row=2, column=0, pady=(10, 0), padx=18, sticky="ew")
        f.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._sl(f, "Formato", 0, 0)
        ctk.CTkOptionMenu(f, values=["mp4", "mp3", "mkv", "webm"],
            variable=self.fmt_v, command=self._fmt_changed,
            height=32, fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H,
        ).grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        self._sl(f, "Qualidade vídeo", 0, 1)
        self.qual_om = ctk.CTkOptionMenu(f,
            values=["360p", "480p", "720p", "1080p", "4K", "Melhor"],
            variable=self.qual_v, height=32,
            fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H)
        self.qual_om.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="ew")

        self.mp3_qual_lbl = ctk.CTkLabel(f, text="Qualidade MP3",
            font=ctk.CTkFont(size=10), text_color=MUTED)
        self.mp3_qual_lbl.grid(row=0, column=2, padx=10, pady=(8, 2), sticky="w")
        self.mp3_qual_lbl.grid_remove()
        self.mp3_qual_om = ctk.CTkOptionMenu(f,
            values=["320k", "256k", "192k", "128k", "96k"],
            variable=self.mp3_qual_v, height=32,
            fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H)
        self.mp3_qual_om.grid(row=1, column=2, padx=10, pady=(2, 10), sticky="ew")
        self.mp3_qual_om.grid_remove()

        self._sl(f, "Pasta de destino", 0, 3)
        fi = ctk.CTkFrame(f, fg_color="transparent")
        fi.grid(row=1, column=3, padx=10, pady=(2, 10), sticky="ew")
        fi.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(fi, textvariable=self.folder_v, state="readonly",
            height=32, fg_color=BORDER, border_color=BORDER, border_width=0,
            font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(fi, text="📁", width=32, height=32,
            fg_color=SURFACE, hover_color="#2a2a42", corner_radius=5,
            command=self._pick_folder).grid(row=0, column=1)

    def _build_checkboxes(self, body):
        chk = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)
        chk.grid(row=3, column=0, pady=(8, 0), padx=18, sticky="ew")
        chk.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkCheckBox(chk, text="Legendas (pt/en)", variable=self.sub_v,
            font=ctk.CTkFont(size=12), checkmark_color=BLUE,
            hover_color=BLUE, fg_color=BLUE, border_color=MUTED,
        ).grid(row=0, column=0, padx=14, pady=8)

        tc = ctk.CTkFrame(chk, fg_color="transparent")
        tc.grid(row=0, column=1, padx=14, pady=8, sticky="ew")
        self.thumb_cb = ctk.CTkCheckBox(tc, text="Salvar thumbnail",
            variable=self.thumb_v, font=ctk.CTkFont(size=12),
            checkmark_color=BLUE, hover_color=BLUE, fg_color=BLUE, border_color=MUTED,
            command=self._thumb_toggle)
        self.thumb_cb.pack(side="left")
        self.thumb_fmt_om = ctk.CTkOptionMenu(tc, values=["jpg", "png", "webp"],
            variable=self.thumb_fmt_v, width=72, height=26,
            fg_color=BORDER, button_color=BLUE, button_hover_color=BLUE_H,
            font=ctk.CTkFont(size=11), state="disabled")
        self.thumb_fmt_om.pack(side="left", padx=(8, 0))

    def _build_progress(self, body):
        pg = ctk.CTkFrame(body, fg_color=CARD, corner_radius=10,
                           border_width=1, border_color=BORDER)
        pg.grid(row=4, column=0, pady=(8, 0), padx=18, sticky="ew")
        pg.grid_columnconfigure(0, weight=1)

        ri = ctk.CTkFrame(pg, fg_color="transparent")
        ri.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 3))
        ri.grid_columnconfigure(0, weight=1)
        self.prog_lbl = ctk.CTkLabel(ri, text="Aguardando",
            font=ctk.CTkFont(size=12), text_color=MUTED, anchor="w")
        self.prog_lbl.grid(row=0, column=0, sticky="w")
        self.speed_lbl = ctk.CTkLabel(ri, text="",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=BLUE, anchor="e")
        self.speed_lbl.grid(row=0, column=1, sticky="e")

        self.pl_count_lbl = ctk.CTkLabel(pg, text="",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ORANGE, anchor="w")
        self.pl_count_lbl.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.pbar = ctk.CTkProgressBar(pg, height=5, corner_radius=3,
            progress_color=BLUE, fg_color=BORDER)
        self.pbar.set(0)
        self.pbar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(pg, text="",
            font=ctk.CTkFont(size=10), text_color=MUTED, wraplength=700, anchor="w")
        self.status_lbl.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 4))

        self.vid_prog_lbl = ctk.CTkLabel(pg, text="",
            font=ctk.CTkFont(family="Courier New", size=10), text_color=BLUE, anchor="w")
        self.vid_prog_lbl.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.vid_pbar = ctk.CTkProgressBar(pg, height=3, corner_radius=2,
            progress_color=GREEN, fg_color=BORDER)
        self.vid_pbar.set(0)
        self.vid_pbar.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.proc_lbl = ctk.CTkLabel(pg, text="",
            font=ctk.CTkFont(family="Courier New", size=10), text_color=ORANGE, anchor="w")
        self.proc_lbl.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 2))

        self.proc_pbar = ctk.CTkProgressBar(pg, height=3, corner_radius=2,
            progress_color=ORANGE, fg_color=BORDER, mode="indeterminate",
            indeterminate_speed=0.8)
        self.proc_pbar.set(0)
        self.proc_pbar.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.proc_pbar.grid_remove()
        self.proc_lbl.grid_remove()

    def _build_buttons(self, body):
        br = ctk.CTkFrame(body, fg_color="transparent")
        br.grid(row=5, column=0, pady=(10, 4), padx=18, sticky="ew")
        br.grid_columnconfigure(0, weight=1)
        self.dl_btn = ctk.CTkButton(br, text="⬇  Baixar", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=BLUE, hover_color=BLUE_H, corner_radius=8, command=self._start)
        self.dl_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.cancel_btn = ctk.CTkButton(br, text="✕", width=40, height=40,
            fg_color=BORDER, hover_color="#3d1515",
            corner_radius=8, state="disabled", command=self._cancel)
        self.cancel_btn.grid(row=0, column=1, padx=(0, 6))
        ctk.CTkButton(br, text="📋", width=40, height=40,
            fg_color=BORDER, hover_color="#2a2a42", corner_radius=8,
            command=self._history_window).grid(row=0, column=2)

    # ── Helpers ─────────────────────────────────────────────────
    def _sl(self, p, t, r, c):
        ctk.CTkLabel(p, text=t, font=ctk.CTkFont(size=10), text_color=MUTED
        ).grid(row=r, column=c, padx=10, pady=(8, 2), sticky="w")

    def _paste(self):
        try:
            self.url_v.set(self.clipboard_get().strip())
        except Exception:
            pass

    def _pick_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_v.get())
        if d:
            self.folder_v.set(d)

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
        self.thumb_fmt_om.configure(state="normal" if self.thumb_v.get() else "disabled")

    def _set_busy(self, on):
        self.dl_btn.configure(state="disabled" if on else "normal")
        self.cancel_btn.configure(state="normal" if on else "disabled")

    # ── Download ───────────────────────────────────────────────
    def _run(self, selected_entries=None):
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

        self._stop        = False
        start_time        = time.time()
        downloaded_titles = []
        opts = build_opts(
            folder, self.fmt_v.get(), self.qual_v.get(),
            self.mp3_qual_v.get(), self.sub_v.get(),
            self.thumb_v.get(), self.thumb_fmt_v.get(), self._hook,
        )

        try:
            if selected_entries:
                self._pl_total = len(selected_entries)
                self._pl_done  = 0
                for entry in selected_entries:
                    if self._stop:
                        break
                    vid_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
                    if not vid_url:
                        continue
                    if not vid_url.startswith("http"):
                        vid_url = f"https://www.youtube.com/watch?v={vid_url}"
                    try:
                        downloaded_titles.append(run_download(opts, vid_url))
                    except yt_dlp.utils.DownloadCancelled:
                        break
                    except Exception:
                        pass
            else:
                downloaded_titles.append(run_download(opts, url))

            elapsed = time.time() - start_time
            if self._stop:
                self.after(0, lambda: (
                    self.prog_lbl.configure(text="Cancelado", text_color=MUTED),
                    self.status_lbl.configure(text=""),
                ))
            else:
                for t in downloaded_titles:
                    self.history.append({
                        "url": url, "title": t, "folder": folder,
                        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    })
                save_hist(self.history)
                n = len(downloaded_titles)
                self.after(0, lambda: (
                    self.prog_lbl.configure(
                        text=f"Concluído ✓  ({n} vídeo{'s' if n!=1 else ''})", text_color=GREEN),
                    self.status_lbl.configure(text="", text_color=MUTED),
                    self.proc_pbar.stop(),
                    self.proc_pbar.grid_remove(),
                    self.proc_lbl.grid_remove(),
                ))
                threading.Thread(target=dc.send_download,
                    args=(n, elapsed, downloaded_titles, folder,
                          self.fmt_v.get(), self.qual_v.get(), self.mp3_qual_v.get(),
                          self.thumb_v.get(), self.thumb_fmt_v.get()),
                    daemon=True).start()
                mins, secs = int(elapsed // 60), int(elapsed % 60)
                messagebox.showinfo("Pronto",
                    f"{'Download' if n == 1 else f'{n} downloads'} concluído{'s' if n!=1 else ''} "
                    f"em {f'{mins}m {secs:02d}s' if mins else f'{secs}s'}!\n"
                    + (downloaded_titles[0][:70] if n == 1 else f"{n} vídeos baixados"))

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
            PlaylistSelectorWindow(self, self._pl_entries,
                                   getattr(self, "_pl_title", "Playlist"),
                                   callback=self._start_with_selection)
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

    def _history_window(self):
        open_history_window(self, self.history)
