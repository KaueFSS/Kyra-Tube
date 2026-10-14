# ═══════════════════════════════════════════════════════════════
#  ui/history_window.py — Janela de histórico de downloads
# ═══════════════════════════════════════════════════════════════
from pathlib import Path

import customtkinter as ctk

from ui.theme  import BG, CARD, BORDER, BLUE_H, TEXT, MUTED, RED
from core.history import save_hist


def open_history_window(parent, history):
    """Abre (ou foca) a janela de histórico. Retorna a janela criada."""
    if hasattr(parent, "_hist_win") and parent._hist_win.winfo_exists():
        parent._hist_win.focus()
        return parent._hist_win

    sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
    ww = min(600, int(sw * 0.45))
    wh = min(460, int(sh * 0.65))

    w = ctk.CTkToplevel(parent)
    parent._hist_win = w
    w.title("Histórico — Kyra Tube")
    w.configure(fg_color=BG)
    w.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
    w.grab_set()

    ctk.CTkLabel(w, text="Histórico",
        font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT,
    ).pack(padx=16, pady=(14, 8), anchor="w")

    sf = ctk.CTkScrollableFrame(w, fg_color=BG, scrollbar_button_color=BORDER)
    sf.pack(fill="both", expand=True, padx=16)

    if not history:
        ctk.CTkLabel(sf, text="Nenhum download ainda.", text_color=MUTED).pack(pady=20)
    else:
        for item in reversed(history):
            card = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=8,
                                border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=3)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card,
                text=item.get("title", item["url"])[:65],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT, anchor="w",
            ).grid(row=0, column=0, padx=10, pady=(7, 1), sticky="ew")

            ctk.CTkLabel(card,
                text=f"{item['date']}  ·  {Path(item.get('folder', '')).name}",
                font=ctk.CTkFont(size=10), text_color=MUTED, anchor="w",
            ).grid(row=1, column=0, padx=10, pady=(0, 7), sticky="ew")

            ctk.CTkButton(card, text="↗", width=36, height=36,
                fg_color=BORDER, hover_color=BLUE_H, corner_radius=6,
                command=lambda u=item["url"]: (parent.url_v.set(u), w.destroy()),
            ).grid(row=0, column=1, rowspan=2, padx=8)

    btn_row = ctk.CTkFrame(w, fg_color="transparent")
    btn_row.pack(fill="x", padx=16, pady=(8, 14))
    btn_row.grid_columnconfigure(0, weight=1)

    ctk.CTkButton(btn_row, text="Limpar histórico",
        height=34, fg_color=BORDER, hover_color=RED, corner_radius=6,
        font=ctk.CTkFont(size=12),
        command=lambda: (history.clear(), save_hist([]), w.destroy()),
    ).grid(row=0, column=0, sticky="ew")

    return w
