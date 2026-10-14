# ═══════════════════════════════════════════════════════════════
#  ui/update_banner.py — Aviso de atualização (faixa na parte de baixo)
#
#  Estados: aviso → baixando (barra de progresso) → instalando.
#  A lógica de rede fica em core/updater.py; aqui é só a aparência.
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk

from core.config import APP_NAME
from ui.theme import SURFACE, CARD_HI, BORDER, ACCENT, ACCENT_H, TEAL, TEXT, MUTED, RED, font


class UpdateBanner(ctk.CTkFrame):
    def __init__(self, master, on_update, on_later):
        super().__init__(master, fg_color=SURFACE, corner_radius=0)
        self._on_update = on_update
        self._on_later = on_later
        self.grid_columnconfigure(1, weight=1)

        # Linha fina na cor da marca, no topo da faixa.
        ctk.CTkFrame(self, fg_color=ACCENT, height=2, corner_radius=0).grid(row=0, column=0, columnspan=3, sticky="ew")

        dot = ctk.CTkFrame(self, fg_color=TEAL, width=10, height=10, corner_radius=5)
        dot.grid(row=1, column=0, padx=(24, 12), pady=16)

        text = ctk.CTkFrame(self, fg_color="transparent")
        text.grid(row=1, column=1, sticky="w", pady=12)
        self.title = ctk.CTkLabel(text, text="", font=font(13, "bold"), text_color=TEXT, anchor="w")
        self.title.pack(anchor="w")
        self.detail = ctk.CTkLabel(text, text="", font=font(11), text_color=MUTED, anchor="w", justify="left")
        self.detail.pack(anchor="w")

        self.bar = ctk.CTkProgressBar(self, width=220, height=8, corner_radius=4, progress_color=TEAL, fg_color=BORDER)
        self.bar.set(0)

        self.buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.later_btn = ctk.CTkButton(
            self.buttons, text="Depois", width=84, height=34, font=font(12), fg_color="transparent",
            hover_color=CARD_HI, border_width=1, border_color=BORDER, text_color=TEXT,
            corner_radius=8, command=self._on_later,
        )
        self.update_btn = ctk.CTkButton(
            self.buttons, text="Atualizar agora", width=140, height=34, fg_color=ACCENT, hover_color=ACCENT_H,
            text_color="#ffffff", corner_radius=8, font=font(12, "bold"), command=self._on_update,
        )
        self.later_btn.pack(side="left", padx=(0, 8))
        self.update_btn.pack(side="left")

    # ── Estados ─────────────────────────────────────────────────
    def _place(self, widgets):
        for w in (self.bar, self.buttons):
            w.grid_remove()
        if "bar" in widgets:
            self.bar.grid(row=1, column=2, padx=(0, 24))
        if "buttons" in widgets:
            self.buttons.grid(row=1, column=2, padx=(0, 24))

    def show_available(self, version, notes):
        self.title.configure(text=f"{APP_NAME} {version} está disponível", text_color=TEXT)
        self.detail.configure(text="  ·  ".join(notes) if notes else "Uma versão nova, pronta para instalar.")
        self.update_btn.configure(text="Atualizar agora", state="normal")
        self._place(["buttons"])
        self.grid()

    def show_downloading(self, fraction=0.0):
        self.title.configure(text="Baixando a atualização…", text_color=TEXT)
        self.detail.configure(text=f"{int(fraction * 100)}%")
        self.bar.configure(mode="determinate")
        self.bar.set(fraction)
        self._place(["bar"])

    def show_installing(self):
        self.title.configure(text="Instalando…", text_color=TEXT)
        self.detail.configure(text=f"O {APP_NAME} vai fechar e abrir de novo sozinho em instantes.")
        self.bar.configure(mode="indeterminate")
        self.bar.start()
        self._place(["bar"])

    def show_error(self, message):
        self.bar.stop()
        self.bar.configure(mode="determinate")
        self.title.configure(text="Não deu para atualizar agora", text_color=RED)
        self.detail.configure(text=message)
        self.update_btn.configure(text="Tentar de novo", state="normal")
        self._place(["buttons"])
