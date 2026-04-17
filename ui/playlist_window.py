# ═══════════════════════════════════════════════════════════════
#  ui/playlist_window.py — Janela de seleção de vídeos da playlist
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk
from tkinter import messagebox

from ui.theme import (BG, SURFACE, CARD, BORDER, BLUE, BLUE_H,
                      TEXT, MUTED, GREEN, RED, ORANGE)


class PlaylistSelectorWindow(ctk.CTkToplevel):
    """
    Exibe os vídeos de uma playlist para o usuário selecionar quais baixar.
    Retorna via callback: callback(selected_entries).
    """

    def __init__(self, parent, entries, pl_title, callback):
        super().__init__(parent)
        self.entries  = entries
        self.callback = callback
        self._checks  = []

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
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="📋  Selecionar vídeos",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT,
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkLabel(hdr,
            text=pl_title[:55] + ("…" if len(pl_title) > 55 else ""),
            font=ctk.CTkFont(size=11), text_color=MUTED,
        ).pack(side="left", padx=(0, 16), pady=14)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=42)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkButton(toolbar, text="✔  Selecionar tudo",
            width=145, height=28, fg_color=BLUE, hover_color=BLUE_H,
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._select_all,
        ).pack(side="left", padx=(12, 6), pady=7)

        ctk.CTkButton(toolbar, text="✕  Desmarcar tudo",
            width=145, height=28, fg_color=BORDER, hover_color="#3d1515",
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._deselect_all,
        ).pack(side="left", padx=(0, 12), pady=7)

        self._count_lbl = ctk.CTkLabel(toolbar,
            text=f"{len(self.entries)} de {len(self.entries)} selecionados",
            font=ctk.CTkFont(size=11), text_color=MUTED)
        self._count_lbl.pack(side="left", padx=4)

        # Lista rolável
        sf = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BORDER)
        sf.pack(fill="both", expand=True)
        sf.grid_columnconfigure(0, weight=1)

        for idx, entry in enumerate(self.entries):
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_, v=var: self._update_count())
            self._checks.append(var)

            row = ctk.CTkFrame(sf, fg_color=CARD if idx % 2 == 0 else SURFACE, corner_radius=6)
            row.grid(row=idx, column=0, sticky="ew", padx=8, pady=2)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=f"{idx+1:02d}",
                font=ctk.CTkFont(family="Courier New", size=11),
                text_color=MUTED, width=28, anchor="e",
            ).grid(row=0, column=0, padx=(10, 6), pady=8, sticky="e")

            title = (entry.get("title") or entry.get("url") or f"Vídeo {idx+1}")[:70]
            ctk.CTkLabel(row, text=title,
                font=ctk.CTkFont(size=12), text_color=TEXT,
                anchor="w", wraplength=max(ww - 200, 300),
            ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)

            dur     = int(entry.get("duration", 0) or 0)
            dur_str = f"{dur//60}:{dur%60:02d}" if dur else "—"
            ctk.CTkLabel(row, text=dur_str,
                font=ctk.CTkFont(family="Courier New", size=10),
                text_color=MUTED, width=42, anchor="e",
            ).grid(row=0, column=2, padx=(0, 8), pady=8, sticky="e")

            ctk.CTkCheckBox(row, text="", variable=var,
                width=24, height=24, checkmark_color=BG,
                hover_color=BLUE, fg_color=BLUE, border_color=MUTED,
            ).grid(row=0, column=3, padx=(0, 10), pady=8)

        # Footer
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
