# ═══════════════════════════════════════════════════════════════
#  ui/playlist_window.py — Janela de seleção de vídeos da playlist
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk
from tkinter import messagebox

from ui.theme import (BG, SURFACE, CARD, CARD_HI, BORDER, ACCENT, ACCENT_H, ACCENT_SOFT,
                      TEXT, MUTED, DIM, GREEN, RED, ORANGE, font, mono)


class PlaylistSelectorWindow(ctk.CTkToplevel):
    """
    Exibe os vídeos de uma playlist para o usuário selecionar quais baixar.
    Retorna via callback: callback(selected_entries).
    """

    def __init__(self, parent, entries, pl_title, callback):
        super().__init__(parent)
        self.attributes("-alpha", 0.0)
        self.entries  = entries
        self.callback = callback
        self._checks  = []

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ww = min(760, int(sw * 0.6))
        wh = min(660, int(sh * 0.82))
        self.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//3}")
        self.title("Escolher vídeos da playlist")
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self._build(pl_title, ww)
        self.update_idletasks()
        self.attributes("-alpha", 1.0)
        self.after(50, self.grab_set)

    def _build(self, pl_title, ww):
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Escolher vídeos", font=font(16, "bold"), text_color=TEXT,
        ).pack(side="left", padx=(22, 12))
        ctk.CTkLabel(hdr, text=pl_title[:60] + ("…" if len(pl_title) > 60 else ""),
            font=font(12), text_color=MUTED,
        ).pack(side="left")

        toolbar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0, height=52)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        ctk.CTkButton(toolbar, text="Selecionar tudo", width=130, height=32, font=font(12),
            fg_color=CARD_HI, hover_color=BORDER, text_color=TEXT, corner_radius=8,
            command=self._select_all).pack(side="left", padx=(18, 8), pady=10)
        ctk.CTkButton(toolbar, text="Desmarcar tudo", width=130, height=32, font=font(12),
            fg_color="transparent", hover_color=CARD_HI, border_width=1, border_color=BORDER,
            text_color=TEXT, corner_radius=8, command=self._deselect_all).pack(side="left", pady=10)
        self._count_lbl = ctk.CTkLabel(toolbar,
            text=f"{len(self.entries)} de {len(self.entries)} selecionados",
            font=font(12, "bold"), text_color=GREEN)
        self._count_lbl.pack(side="right", padx=22)

        sf = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BORDER)
        sf.pack(fill="both", expand=True, padx=10)
        sf.grid_columnconfigure(0, weight=1)

        for idx, entry in enumerate(self.entries):
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_, v=var: self._update_count())
            self._checks.append(var)

            row = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORDER)
            row.grid(row=idx, column=0, sticky="ew", padx=6, pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=f"{idx+1:02d}", font=mono(12), text_color=DIM, width=30, anchor="e",
            ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="e")

            title = (entry.get("title") or entry.get("url") or f"Vídeo {idx+1}")[:72]
            ctk.CTkLabel(row, text=title, font=font(13), text_color=TEXT, anchor="w",
                wraplength=max(ww - 220, 300),
            ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)

            dur     = int(entry.get("duration", 0) or 0)
            dur_str = f"{dur//60}:{dur%60:02d}" if dur else "—"
            ctk.CTkLabel(row, text=dur_str, font=mono(12), text_color=MUTED, width=46, anchor="e",
            ).grid(row=0, column=2, padx=(0, 8), pady=10, sticky="e")

            ctk.CTkCheckBox(row, text="", variable=var, width=24, height=24, checkbox_width=22,
                checkbox_height=22, corner_radius=6, checkmark_color="#ffffff",
                hover_color=ACCENT_H, fg_color=ACCENT, border_color=DIM,
            ).grid(row=0, column=3, padx=(0, 12), pady=10)

        footer = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=68)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Baixar selecionados", height=42, width=190, font=font(14, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_H, text_color="#ffffff", corner_radius=10,
            command=self._confirm).pack(side="right", padx=(8, 20), pady=13)
        ctk.CTkButton(footer, text="Cancelar", height=42, width=100, font=font(13),
            fg_color="transparent", hover_color=CARD_HI, border_width=1, border_color=BORDER,
            text_color=TEXT, corner_radius=10, command=self.destroy).pack(side="right", pady=13)

    def _select_all(self):
        for v in self._checks:
            v.set(True)

    def _deselect_all(self):
        for v in self._checks:
            v.set(False)

    def _update_count(self):
        n     = sum(1 for v in self._checks if v.get())
        total = len(self._checks)
        color = GREEN if n == total else (ORANGE if n > 0 else RED)
        self._count_lbl.configure(text=f"{n} de {total} selecionados", text_color=color)

    def _confirm(self):
        selected = [e for e, v in zip(self.entries, self._checks) if v.get()]
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um vídeo.", parent=self)
            return
        self.destroy()
        self.callback(selected)
