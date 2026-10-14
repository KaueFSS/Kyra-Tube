# ═══════════════════════════════════════════════════════════════
#  ui/history_window.py — Janela de histórico de downloads
# ═══════════════════════════════════════════════════════════════
from pathlib import Path

import customtkinter as ctk

from ui.theme  import BG, SURFACE, CARD, CARD_HI, BORDER, ACCENT, ACCENT_SOFT, TEXT, MUTED, DIM, font
from core.history import save_hist


def open_history_window(parent, history):
    """Abre (ou foca) a janela de histórico. Retorna a janela criada."""
    if hasattr(parent, "_hist_win") and parent._hist_win.winfo_exists():
        parent._hist_win.focus()
        return parent._hist_win

    sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
    ww = min(640, int(sw * 0.5))
    wh = min(520, int(sh * 0.7))

    w = ctk.CTkToplevel(parent)
    w.attributes("-alpha", 0.0)
    parent._hist_win = w
    w.title("Histórico — Kyra Tube")
    w.configure(fg_color=BG)
    w.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//3}")

    head = ctk.CTkFrame(w, fg_color=SURFACE, corner_radius=0, height=58)
    head.pack(fill="x")
    head.pack_propagate(False)
    ctk.CTkLabel(head, text="Histórico", font=font(16, "bold"), text_color=TEXT).pack(side="left", padx=22)
    ctk.CTkLabel(head, text=f"{len(history)} download{'s' if len(history) != 1 else ''}",
        font=font(12), text_color=MUTED).pack(side="left")
    ctk.CTkButton(head, text="Limpar", width=84, height=32, font=font(12), fg_color="transparent",
        hover_color=ACCENT_SOFT, border_width=1, border_color=BORDER, text_color=TEXT, corner_radius=8,
        command=lambda: (history.clear(), save_hist([]), w.destroy()),
    ).pack(side="right", padx=22)

    sf = ctk.CTkScrollableFrame(w, fg_color=BG, scrollbar_button_color=BORDER)
    sf.pack(fill="both", expand=True, padx=14, pady=(10, 14))

    if not history:
        ctk.CTkLabel(sf, text="Nenhum download ainda.", font=font(13), text_color=DIM).pack(pady=40)
    else:
        for item in reversed(history):
            card = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=4, padx=4)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=item.get("title", item["url"])[:70], font=font(13, "bold"),
                text_color=TEXT, anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(10, 1), sticky="ew")
            ctk.CTkLabel(card, text=f"{item['date']}  ·  {Path(item.get('folder', '')).name}",
                font=font(11), text_color=MUTED, anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
            ctk.CTkButton(card, text="Baixar de novo", width=118, height=32, font=font(12),
                fg_color=CARD_HI, hover_color=BORDER, text_color=TEXT, corner_radius=8,
                command=lambda u=item["url"]: (parent.url_v.set(u), w.destroy()),
            ).grid(row=0, column=1, rowspan=2, padx=12)

    w.update_idletasks()
    w.attributes("-alpha", 1.0)
    w.after(50, w.grab_set)
    return w
