# ═══════════════════════════════════════════════════════════════
#  ui/app.py — Janela principal do Kyra Tube
#  ► Layout / widgets: edite os métodos _build_*()
#  ► Cores e fontes: ui/theme.py
#  ► Progresso: ui/progress_hooks.py   ► Preview: ui/preview.py
#  ► Download:  core/downloader.py     ► Atualização: core/updater.py
#
#  A janela é montada INVISÍVEL (alpha 0) e só aparece quando está pronta, para
#  nada "montar aos poucos" na frente de quem usa.
# ═══════════════════════════════════════════════════════════════
import os, threading, time, webbrowser
from datetime import datetime
from pathlib  import Path
from tkinter  import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

from core.config     import APP_NAME, APP_VERSION, GITHUB_USER, GITHUB_REPO, UPDATE_CHECK_INTERVAL
from core.history    import load_hist, save_hist
from core.downloader import build_opts, run_download, FFMPEG
from core.errors     import explain, short_reason
from core.setup      import IS_FROZEN, resource_path
from core            import updater
from ui.theme        import (BG, SURFACE, CARD, CARD_HI, BORDER, ACCENT, ACCENT_H, ACCENT_SOFT, TEAL,
                              TEXT, MUTED, DIM, GREEN, RED, YELLOW, ORANGE, RADIUS, font, mono)
from ui.progress_hooks  import ProgressMixin
from ui.preview         import PreviewMixin
from ui.playlist_window import PlaylistSelectorWindow
from ui.history_window  import open_history_window
from ui.update_banner   import UpdateBanner
from ui.error_dialog    import ProblemDialog

VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "4K", "Melhor"]
MP3_QUALITIES   = ["320k", "256k", "192k", "128k", "96k"]
PAD = 24   # margem lateral do conteúdo


class App(ProgressMixin, PreviewMixin, ctk.CTk):

    def __init__(self):
        ctk.CTk.__init__(self)
        self.attributes("-alpha", 0.0)        # monta invisível; aparece pronta em _reveal()
        self.configure(fg_color=BG)
        self.title(APP_NAME)
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
        self._pending_release = None
        self._dismissed     = None
        self._resize_job    = None
        self._problem       = None      # (Problem, texto técnico) do último erro de preview
        self.history        = load_hist()

        self._build()
        self.url_v.trace_add("write", self._url_changed)
        self.bind("<Configure>", self._on_configure, add="+")
        self._reveal()

    # ── Abrir pronta ────────────────────────────────────────────
    def _reveal(self):
        """Calcula tudo escondida e só então mostra a janela, já completa."""
        self.update_idletasks()
        self._fit_screen()
        self.update_idletasks()
        self._apply_size()
        self.update_idletasks()
        self.attributes("-alpha", 1.0)
        self._set_window_icon()
        self.after(600, self._start_update_check)

    # ── Redimensionar sem travar ─────────────────────────────────
    # O customtkinter redesenha dezenas de widgets arredondados a cada pixel
    # arrastado (≈250 ms por quadro). Por isso o conteúdo fica num quadro de
    # tamanho fixo que só é ajustado quando a pessoa para de arrastar: a borda
    # da janela acompanha o mouse na hora, e o conteúdo se acomoda em seguida.
    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(90, self._apply_size)

    def _apply_size(self):
        self._resize_job = None
        scale = self._get_window_scaling()
        w, h = max(int(self.winfo_width() / scale), 1), max(int(self.winfo_height() / scale), 1)
        self.shell.configure(width=w, height=h)

    def _fit_screen(self):
        scale = self._get_window_scaling()           # telas com zoom (125%, 150%...)
        sw, sh = self.winfo_screenwidth() / scale, self.winfo_screenheight() / scale
        w = min(1000, int(sw * 0.82))
        h = min(640, int(sh * 0.90))
        self.minsize(min(860, w), min(540, h))
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max((sh - h) // 3, 0)}")

    def _set_window_icon(self):
        ico = resource_path("assets/kyra-tube.ico")
        # O customtkinter troca o ícone logo ao abrir; por isso o atraso.
        self.after(250, lambda: self._safe(lambda: self.iconbitmap(default=str(ico))))
        self.after(260, lambda: self._safe(lambda: self.iconbitmap(str(ico))))

    @staticmethod
    def _safe(fn):
        try:
            fn()
        except Exception:
            pass

    # ── Atualizações ────────────────────────────────────────────
    # Só no app instalado. O aviso aparece embaixo e a pessoa decide;
    # nada é baixado ou instalado sem o clique em "Atualizar agora".
    def _start_update_check(self):
        if not IS_FROZEN:
            self._set_update_lbl("modo desenvolvimento", MUTED)
            return
        threading.Thread(target=self._check_update, kwargs={"silent": True}, daemon=True).start()
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _manual_update_check(self):
        if not IS_FROZEN:
            self._set_update_lbl("modo desenvolvimento", MUTED)
            return
        self._set_update_lbl("Verificando…", MUTED)
        self._dismissed = None
        threading.Thread(target=self._check_update, kwargs={"silent": False}, daemon=True).start()

    def _check_update(self, silent=True):
        release = updater.fetch_latest()
        if release and updater.is_newer(release.version):
            if release.version == self._dismissed:
                return
            self._pending_release = release
            self.after(0, lambda: (
                self._set_update_lbl(f"{release.version} disponível", ACCENT),
                self.update_banner.show_available(release.version, release.notes),
            ))
        elif not silent:
            msg, color = ("Você está na versão mais recente", GREEN) if release else ("Sem conexão com o GitHub", RED)
            self.after(0, lambda: self._set_update_lbl(msg, color))
            self.after(5000, lambda: self._set_update_lbl(f"v{APP_VERSION}", MUTED))

    def _update_loop(self):
        while True:
            time.sleep(UPDATE_CHECK_INTERVAL)
            try:
                self._check_update(silent=True)
            except Exception:
                pass

    def _update_later(self):
        if self._pending_release:
            self._dismissed = self._pending_release.version
        self.update_banner.grid_remove()

    def _update_now(self):
        release = self._pending_release
        if not release:
            return
        self.update_banner.show_downloading(0.0)
        threading.Thread(target=self._download_and_install, args=(release,), daemon=True).start()

    def _download_and_install(self, release):
        try:
            path = updater.download(
                release, progress=lambda f: self.after(0, lambda v=f: self.update_banner.show_downloading(v)))
        except updater.UpdateError as exc:
            self.after(0, lambda: self.update_banner.show_error(str(exc)))
            return
        self.after(0, self.update_banner.show_installing)
        time.sleep(0.8)
        updater.launch_installer(path)
        updater.exit_now()

    def _set_update_lbl(self, text, color):
        self._safe(lambda: self.update_lbl.configure(text=text, text_color=color))

    # ── Construção da interface ─────────────────────────────────
    def _build(self):
        self.shell = ctk.CTkFrame(self, fg_color=BG, corner_radius=0, width=1000, height=640)
        self.shell.grid_propagate(False)                          # o tamanho vem de _apply_size(), não dos filhos
        self.shell.place(x=0, y=0)
        self.shell.grid_columnconfigure(0, weight=1)
        self.shell.grid_rowconfigure(1, weight=1)
        self._build_topbar()
        body = ctk.CTkFrame(self.shell, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(14, 0))
        body.grid_columnconfigure(0, weight=1)
        self._build_url_row(body)            # linha 0
        self._build_preview_area(body)       # linha 1
        self._build_options(body)            # linha 2 (opções OU progresso do download)
        self._build_buttons(body)            # linha 3
        self._build_progress(body)           # linha 2, no lugar das opções enquanto baixa
        ctk.CTkLabel(body, text="Kyra Tube  ·  yt-dlp  ·  FFmpeg embutido  ·  por Kauê (@KaueFSS)",
            font=font(10), text_color=DIM,
        ).grid(row=4, column=0, pady=(8, 10))
        self.update_banner = UpdateBanner(self.shell, on_update=self._update_now, on_later=self._update_later)
        self.update_banner.grid(row=2, column=0, sticky="ew")
        self.update_banner.grid_remove()

    def _card(self, parent, row, pady=(0, 10)):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=RADIUS, border_width=1, border_color=BORDER)
        f.grid(row=row, column=0, sticky="ew", pady=pady)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build_topbar(self):
        top = ctk.CTkFrame(self.shell, fg_color=SURFACE, corner_radius=0, height=52)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)
        self._logo_img = self._load_logo()
        brand = ctk.CTkFrame(top, fg_color="transparent")
        brand.grid(row=0, column=0, padx=(PAD, 0), sticky="w")
        if self._logo_img:
            ctk.CTkLabel(brand, text="", image=self._logo_img).pack(side="left", padx=(0, 10), pady=9)
        ctk.CTkLabel(brand, text="Kyra", font=font(18, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(brand, text=" Tube", font=font(18, "bold"), text_color=ACCENT).pack(side="left")
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, padx=(0, PAD), sticky="e")
        self.update_lbl = ctk.CTkLabel(right, text=f"v{APP_VERSION}", font=font(11), text_color=MUTED)
        self.update_lbl.pack(side="left", padx=(0, 12))
        self._ghost_btn(right, "Atualizações", self._manual_update_check).pack(side="left", padx=(0, 8))
        self._ghost_btn(right, "GitHub ↗", lambda: webbrowser.open(f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}")).pack(side="left")
        ctk.CTkFrame(self.shell, fg_color=BORDER, height=1, corner_radius=0).place(x=0, y=52, relwidth=1)

    def _ghost_btn(self, parent, text, command, width=0, height=32):
        return ctk.CTkButton(parent, text=text, height=height, width=width or 10, font=font(12),
            fg_color="transparent", hover_color=CARD_HI, border_width=1, border_color=BORDER,
            text_color=TEXT, corner_radius=8, command=command)

    def _load_logo(self):
        try:
            from PIL import Image
            img = Image.open(resource_path("assets/kyra-tube.png"))
            return ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
        except Exception:
            return None

    def _build_url_row(self, body):
        card = self._card(body, 0)
        card.grid_columnconfigure(0, weight=1)
        # Sem textvariable de propósito: com ela o customtkinter esconde o texto de ajuda.
        # A ligação com url_v é feita à mão (entry → url_v e url_v → entry).
        self.entry = ctk.CTkEntry(card, placeholder_text="Cole o link de um vídeo ou playlist do YouTube",
            height=42, font=font(14), fg_color=BG, border_color=BORDER, border_width=1,
            corner_radius=10, text_color=TEXT)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=11)
        for event in ("<KeyRelease>", "<<Paste>>", "<<Cut>>", "<<Clear>>"):
            self.entry.bind(event, lambda _e: self.after(1, self._entry_to_var), add="+")
        self.url_v.trace_add("write", lambda *_: self._var_to_entry())
        ctk.CTkButton(card, text="Colar", width=88, height=42, font=font(13, "bold"),
            fg_color=CARD_HI, hover_color=BORDER, text_color=TEXT, corner_radius=10,
            command=self._paste).grid(row=0, column=1, padx=(0, 12), pady=11)

    def _build_preview_area(self, body):
        """Widgets do preview; a lógica vive em ui/preview.py (PreviewMixin)."""
        card = self._card(body, 1)
        card.grid_columnconfigure(0, weight=0)   # a capa não estica; o texto ocupa o resto
        card.grid_columnconfigure(1, weight=1)

        tc = ctk.CTkFrame(card, fg_color=BG, corner_radius=10, width=192, height=108)
        tc.grid(row=0, column=0, padx=12, pady=12, sticky="w")
        tc.grid_propagate(False)
        # Imagem vazia em vez de image=None: o customtkinter guarda uma referência velha e dá TclError ao limpar a capa.
        from PIL import Image
        self._blank_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
        self.thumb_lbl = ctk.CTkLabel(tc, text="▶", image=self._blank_img, font=font(26), text_color=DIM,
            width=192, height=108, fg_color="transparent")
        self.thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")

        ic = ctk.CTkFrame(card, fg_color="transparent")
        ic.grid(row=0, column=1, padx=(2, 16), pady=12, sticky="nsew")
        ic.grid_columnconfigure(0, weight=1)
        self.title_lbl = ctk.CTkLabel(ic, text="Cole um link para começar", font=font(16, "bold"),
            text_color=MUTED, anchor="nw", wraplength=620, justify="left")
        self.title_lbl.grid(row=0, column=0, sticky="nw", pady=(2, 0))
        self.meta_lbl = ctk.CTkLabel(ic, text="O título, a duração e o canal aparecem aqui.", font=font(12),
            text_color=DIM, anchor="w")
        self.meta_lbl.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self._pl_banner = ctk.CTkFrame(ic, fg_color=ACCENT_SOFT, corner_radius=8, border_width=1, border_color=ACCENT)
        self._pl_banner.grid(row=2, column=0, sticky="w", pady=(12, 0))
        ctk.CTkLabel(self._pl_banner, text="Playlist detectada — clique em Baixar para escolher os vídeos",
            font=font(12, "bold"), text_color=ACCENT, anchor="w",
        ).grid(row=0, column=0, padx=12, pady=7)
        self._pl_banner.grid_remove()

        self.problem_btn = ctk.CTkButton(ic, text="Ver o que fazer", height=32, width=130, font=font(12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_H, text_color="#ffffff", corner_radius=8,
            command=self._show_problem)
        self.problem_btn.grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.problem_btn.grid_remove()

    def _build_options(self, body):
        f = self._card(body, 2)
        self.options_card = f
        f.grid_columnconfigure((0, 1), weight=1)
        f.grid_columnconfigure(2, weight=2)

        self._label(f, "Formato", 0, 0)
        self.fmt_seg = ctk.CTkSegmentedButton(f, values=["MP4", "MP3", "MKV", "WEBM"],
            command=self._fmt_changed, height=32, font=font(12, "bold"),
            fg_color=BG, selected_color=ACCENT, selected_hover_color=ACCENT_H,
            unselected_color=BG, unselected_hover_color=CARD_HI, text_color=TEXT, corner_radius=8)
        self.fmt_seg.set("MP4")
        self.fmt_seg.grid(row=1, column=0, padx=(16, 8), pady=(2, 8), sticky="ew")

        self.qual_lbl = self._label(f, "Qualidade do vídeo", 0, 1)
        self.qual_om = ctk.CTkOptionMenu(f, values=VIDEO_QUALITIES, variable=self.qual_v, height=32,
            font=font(12), dropdown_font=font(12), fg_color=BG, button_color=CARD_HI,
            button_hover_color=BORDER, dropdown_fg_color=CARD, dropdown_hover_color=CARD_HI,
            text_color=TEXT, corner_radius=8)
        self.qual_om.grid(row=1, column=1, padx=8, pady=(2, 8), sticky="ew")

        self._label(f, "Salvar em", 0, 2)
        fi = ctk.CTkFrame(f, fg_color="transparent")
        fi.grid(row=1, column=2, padx=(8, 16), pady=(2, 8), sticky="ew")
        fi.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(fi, textvariable=self.folder_v, state="readonly", height=32, font=font(11),
            fg_color=BG, border_color=BORDER, border_width=1, corner_radius=8, text_color=MUTED,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(fi, text="Alterar", width=72, height=32, font=font(12),
            fg_color=CARD_HI, hover_color=BORDER, text_color=TEXT, corner_radius=8,
            command=self._pick_folder).grid(row=0, column=1)

        ctk.CTkFrame(f, fg_color=BORDER, height=1, corner_radius=0).grid(
            row=2, column=0, columnspan=3, sticky="ew", padx=16, pady=(2, 0))
        toggles = ctk.CTkFrame(f, fg_color="transparent")
        toggles.grid(row=3, column=0, columnspan=3, sticky="ew", padx=16, pady=(8, 10))
        switch = dict(font=font(12), text_color=TEXT, progress_color=ACCENT, button_color=TEXT,
                      button_hover_color=TEXT, fg_color=BORDER, switch_width=38, switch_height=20)
        ctk.CTkSwitch(toggles, text="Baixar legendas (pt/en)", variable=self.sub_v, **switch).pack(side="left", padx=(0, 28))
        self.thumb_cb = ctk.CTkSwitch(toggles, text="Salvar a capa", variable=self.thumb_v,
            command=self._thumb_toggle, **switch)
        self.thumb_cb.pack(side="left")
        self.thumb_fmt_om = ctk.CTkOptionMenu(toggles, values=["jpg", "png", "webp"], variable=self.thumb_fmt_v,
            width=76, height=28, font=font(11), dropdown_font=font(11), fg_color=BG, button_color=CARD_HI,
            button_hover_color=BORDER, dropdown_fg_color=CARD, dropdown_hover_color=CARD_HI,
            text_color=TEXT, corner_radius=8, state="disabled")
        self.thumb_fmt_om.pack(side="left", padx=(10, 0))

    def _build_buttons(self, body):
        br = ctk.CTkFrame(body, fg_color="transparent")
        br.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        br.grid_columnconfigure(0, weight=1)
        self.dl_btn = ctk.CTkButton(br, text="Baixar", height=46, font=font(15, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_H, text_color="#ffffff", text_color_disabled="#ffe1de",
            corner_radius=12, command=self._start)
        self.dl_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.cancel_btn = ctk.CTkButton(br, text="Cancelar", width=104, height=46, font=font(13),
            fg_color=CARD, hover_color=ACCENT_SOFT, text_color=TEXT, border_width=1, border_color=BORDER,
            corner_radius=12, state="disabled", command=self._cancel)
        self.cancel_btn.grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(br, text="Histórico", width=104, height=46, font=font(13),
            fg_color=CARD, hover_color=CARD_HI, text_color=TEXT, border_width=1, border_color=BORDER,
            corner_radius=12, command=self._history_window).grid(row=0, column=2)

    def _build_progress(self, body):
        pg = self._card(body, 2)
        pg.grid_columnconfigure(0, weight=1)
        self.progress_card = pg      # ocupa o lugar das opções durante o download e mostra o resultado

        ri = ctk.CTkFrame(pg, fg_color="transparent")
        ri.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 2))
        ri.grid_columnconfigure(0, weight=1)
        self.prog_lbl = ctk.CTkLabel(ri, text="", font=font(14, "bold"), text_color=TEXT, anchor="w")
        self.prog_lbl.grid(row=0, column=0, sticky="w")
        self.speed_lbl = ctk.CTkLabel(ri, text="", font=mono(12), text_color=TEAL, anchor="e")
        self.speed_lbl.grid(row=0, column=1, sticky="e")

        self.pl_count_lbl = ctk.CTkLabel(pg, text="", font=font(11, "bold"), text_color=ORANGE, anchor="w", height=14)
        self.pl_count_lbl.grid(row=1, column=0, sticky="ew", padx=16)

        self.pbar = ctk.CTkProgressBar(pg, height=8, corner_radius=4, progress_color=TEAL, fg_color=BORDER)
        self.pbar.set(0)
        self.pbar.grid(row=2, column=0, sticky="ew", padx=16, pady=(2, 4))

        self.status_lbl = ctk.CTkLabel(pg, text="", font=font(10), text_color=DIM, wraplength=860, anchor="w", height=14)
        self.status_lbl.grid(row=3, column=0, sticky="ew", padx=16)

        self.vid_prog_lbl = ctk.CTkLabel(pg, text="", font=mono(10), text_color=TEAL, anchor="w", height=14)
        self.vid_prog_lbl.grid(row=4, column=0, sticky="ew", padx=16)

        self.vid_pbar = ctk.CTkProgressBar(pg, height=4, corner_radius=2, progress_color=GREEN, fg_color=BORDER)
        self.vid_pbar.set(0)
        self.vid_pbar.grid(row=5, column=0, sticky="ew", padx=16, pady=(2, 2))

        self.proc_lbl = ctk.CTkLabel(pg, text="", font=mono(10), text_color=YELLOW, anchor="w", height=14)
        self.proc_lbl.grid(row=6, column=0, sticky="ew", padx=16)

        self.proc_pbar = ctk.CTkProgressBar(pg, height=4, corner_radius=2, progress_color=YELLOW,
            fg_color=BORDER, mode="indeterminate", indeterminate_speed=0.8)
        self.proc_pbar.set(0)
        self.proc_pbar.grid(row=7, column=0, sticky="ew", padx=16, pady=(2, 6))

        self.result_row = ctk.CTkFrame(pg, fg_color="transparent")
        self.result_row.grid(row=8, column=0, sticky="w", padx=16, pady=(4, 12))
        ctk.CTkButton(self.result_row, text="Abrir pasta", width=110, height=32, font=font(12, "bold"),
            fg_color=CARD_HI, hover_color=BORDER, text_color=TEXT, corner_radius=8,
            command=self._open_folder).pack(side="left", padx=(0, 8))
        ctk.CTkButton(self.result_row, text="Novo download", width=130, height=32, font=font(12),
            fg_color="transparent", hover_color=CARD_HI, border_width=1, border_color=BORDER, text_color=TEXT,
            corner_radius=8, command=self._new_download).pack(side="left")
        self.result_row.grid_remove()
        self.proc_pbar.grid_remove()
        self.proc_lbl.grid_remove()
        self.vid_prog_lbl.grid_remove()   # só aparecem em playlist (veja progress_hooks)
        self.vid_pbar.grid_remove()
        pg.grid_remove()

    # ── Helpers ─────────────────────────────────────────────────
    def _label(self, parent, text, row, col):
        lbl = ctk.CTkLabel(parent, text=text, font=font(11, "bold"), text_color=MUTED)
        lbl.grid(row=row, column=col, padx=(16 if col == 0 else 8, 8), pady=(10, 0), sticky="w")
        return lbl

    def _entry_to_var(self):
        text = self.entry.get()
        if text != self.url_v.get():
            self.url_v.set(text)

    def _var_to_entry(self):
        text = self.url_v.get()
        if text != self.entry.get():
            self.entry.delete(0, "end")
            self.entry.insert(0, text)

    def _paste(self):
        try:
            self.url_v.set(self.clipboard_get().strip())
        except Exception:
            pass

    def _pick_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_v.get())
        if d:
            self.folder_v.set(d)

    def _fmt_changed(self, shown):
        fmt = shown.lower()
        self.fmt_v.set(fmt)
        if fmt == "mp3":
            self.qual_lbl.configure(text="Qualidade do áudio")
            self.qual_om.configure(values=MP3_QUALITIES, variable=self.mp3_qual_v)
        else:
            self.qual_lbl.configure(text="Qualidade do vídeo")
            self.qual_om.configure(values=VIDEO_QUALITIES, variable=self.qual_v)

    def _thumb_toggle(self):
        self.thumb_fmt_om.configure(state="normal" if self.thumb_v.get() else "disabled")

    def _show_options(self):
        self.progress_card.grid_remove()
        self.options_card.grid()

    def _hide_progress_idle(self):
        """Parado e com link novo: volta a mostrar as opções no lugar do resultado anterior."""
        if str(self.dl_btn.cget("state")) != "disabled":
            self._show_options()
        self.problem_btn.grid_remove()
        self._problem = None

    def _new_download(self):
        self._show_options()
        self.url_v.set("")

    def _open_folder(self):
        folder = self.folder_v.get()
        if os.path.isdir(folder):
            os.startfile(folder)

    def _show_problem(self):
        if self._problem:
            problem, raw = self._problem
            ProblemDialog(self, problem, details=short_reason(raw))

    def _set_busy(self, on):
        if on:
            self.options_card.grid_remove()
            self.progress_card.grid()
        self.dl_btn.configure(state="disabled" if on else "normal", text="Baixando…" if on else "Baixar")
        self.cancel_btn.configure(state="normal" if on else "disabled")

    # ── Download ───────────────────────────────────────────────
    def _run(self, selected_entries=None):
        url    = self.url_v.get().strip()
        folder = self.folder_v.get().strip()
        if not url:
            self.after(0, lambda: (messagebox.showwarning("Aviso", "Insira um link."), self._set_busy(False)))
            return
        if not os.path.isdir(folder):
            self.after(0, lambda: (messagebox.showwarning("Aviso", "Essa pasta não existe mais. Escolha outra em \"Salvar em\"."),
                                   self._set_busy(False)))
            return

        self._stop = False
        start_time = time.time()
        fmt        = self.fmt_v.get()
        results, failures = [], []          # Result · (nome do vídeo, texto técnico do erro)
        opts = build_opts(
            folder, fmt, self.qual_v.get(),
            self.mp3_qual_v.get(), self.sub_v.get(),
            self.thumb_v.get(), self.thumb_fmt_v.get(), self._hook,
        )

        entries = selected_entries or [None]
        self._pl_total = len(selected_entries) if selected_entries else 0
        self._pl_done  = 0
        for entry in entries:
            if self._stop:
                break
            if entry is None:
                vid_url, label = url, url
            else:
                vid_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
                if not vid_url:
                    continue
                if not vid_url.startswith("http"):
                    vid_url = f"https://www.youtube.com/watch?v={vid_url}"
                label = entry.get("title") or vid_url
            try:
                result = run_download(opts, vid_url, fmt)
                results.append(result)
                if result.already:                    # nada foi baixado: conta como feito na barra da playlist
                    self._pl_done += 1
            except yt_dlp.utils.DownloadCancelled:
                break
            except Exception as exc:  # noqa: BLE001 — qualquer falha vira uma explicação, não um travamento
                failures.append((label, str(exc)))

        for r in results:
            if not r.already:
                self.history.append({
                    "url": url, "title": r.title, "folder": folder,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
        save_hist(self.history)
        elapsed, cancelled = time.time() - start_time, self._stop
        self.after(0, lambda: self._finish(results, failures, elapsed, cancelled))

    def _finish(self, results, failures, elapsed, cancelled):
        """Mostra o que aconteceu no próprio card (nada de janelinha de 'Pronto')."""
        self._set_busy(False)
        self.proc_pbar.stop()
        for w in (self.proc_pbar, self.proc_lbl, self.vid_prog_lbl, self.vid_pbar):
            w.grid_remove()
        self.speed_lbl.configure(text="")
        self.pl_count_lbl.configure(text="")
        new = [r for r in results if not r.already]
        old = [r for r in results if r.already]
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        took = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        plural = lambda n, one, many: f"{n} {one if n == 1 else many}"  # noqa: E731

        if cancelled:
            self.prog_lbl.configure(text="Cancelado", text_color=MUTED)
            self.status_lbl.configure(text=f"{plural(len(new), 'vídeo baixado', 'vídeos baixados')} antes de cancelar." if new else "")
            self.pbar.configure(progress_color=MUTED)
        elif failures and not results:
            self.prog_lbl.configure(text="Não foi possível baixar", text_color=RED)
            self.pbar.configure(progress_color=RED)
            self.pbar.set(1)
        elif not new and old:
            self.prog_lbl.configure(text="Este vídeo já estava baixado" if len(old) == 1 else f"Esses {len(old)} vídeos já estavam baixados", text_color=YELLOW)
            self.status_lbl.configure(
                text=f"{os.path.basename(old[0].path)} — já está na pasta, então nada foi baixado de novo. "
                     "Para baixar outra vez, apague o arquivo da pasta.", text_color=MUTED)
            self.pbar.configure(progress_color=YELLOW)
            self.pbar.set(1)
        else:
            parts = [plural(len(new), "vídeo baixado", "vídeos baixados")]
            if old:
                parts.append(plural(len(old), "já existia", "já existiam"))
            if failures:
                parts.append(plural(len(failures), "falhou", "falharam"))
            self.prog_lbl.configure(text=f"Concluído em {took}", text_color=GREEN if not failures else YELLOW)
            self.status_lbl.configure(text="  ·  ".join(parts), text_color=MUTED)
            self.pbar.configure(progress_color=GREEN if not failures else YELLOW)
            self.pbar.set(1)
        self.result_row.grid()

        if failures and not cancelled:
            problem = explain(failures[0][1])
            extra = None
            if len(failures) > 1:
                extra = [f"• {name[:60]} — {explain(raw).title}" for name, raw in failures]
            ProblemDialog(self, problem, details=short_reason(failures[0][1]), extra=extra, on_retry=self._start)

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
