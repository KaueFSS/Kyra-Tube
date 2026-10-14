# ═══════════════════════════════════════════════════════════════
#  ui/update_banner.py — Aviso de atualização (faixa na parte de baixo)
#
#  Estados: aviso → baixando (barra de progresso) → instalando.
#  A lógica de rede fica em core/updater.py; aqui é só a aparência.
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk

from core.config import APP_NAME
from ui.theme import CARD, BORDER, BLUE, BLUE_H, TEXT, MUTED, RED


class UpdateBanner(ctk.CTkFrame):
    def __init__(self, master, on_update, on_later):
        super().__init__(master, fg_color=CARD, corner_radius=0, border_width=1, border_color=BLUE)
        self._on_update = on_update
        self._on_later = on_later
        self.grid_columnconfigure(0, weight=1)

        text = ctk.CTkFrame(self, fg_color="transparent")
        text.grid(row=0, column=0, sticky="w", padx=(18, 8), pady=10)
        self.title = ctk.CTkLabel(text, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT, anchor="w")
        self.title.pack(anchor="w")
        self.detail = ctk.CTkLabel(text, text="", font=ctk.CTkFont(size=11), text_color=MUTED, anchor="w", justify="left")
        self.detail.pack(anchor="w")

        self.bar = ctk.CTkProgressBar(self, width=200, height=6, corner_radius=3, progress_color=BLUE, fg_color=BORDER)
        self.bar.set(0)

        self.buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.later_btn = ctk.CTkButton(
            self.buttons, text="Depois", width=80, height=32, fg_color=BORDER, hover_color="#2a2a42",
            corner_radius=6, command=self._on_later,
        )
        self.update_btn = ctk.CTkButton(
            self.buttons, text="Atualizar agora", width=130, height=32, fg_color=BLUE, hover_color=BLUE_H,
            corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"), command=self._on_update,
        )
        self.later_btn.pack(side="left", padx=(0, 8))
        self.update_btn.pack(side="left")

    # ── Estados ─────────────────────────────────────────────────
    def _place(self, widgets):
        for w in (self.bar, self.buttons):
            w.grid_remove()
        if "bar" in widgets:
            self.bar.grid(row=0, column=1, padx=(0, 18))
        if "buttons" in widgets:
            self.buttons.grid(row=0, column=1, padx=(0, 18))

    def show_available(self, version, notes):
        self.title.configure(text=f"{APP_NAME} {version} está disponível", text_color=TEXT)
        self.detail.configure(text="  ·  ".join(notes) if notes else "Uma versão nova, pronta para instalar.")
        self.update_btn.configure(state="normal")
        self._place(["buttons"])
        self.grid()

    def show_downloading(self, fraction=0.0):
        self.title.configure(text="Baixando a atualização…", text_color=TEXT)
        self.detail.configure(text=f"{int(fraction * 100)}%")
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
