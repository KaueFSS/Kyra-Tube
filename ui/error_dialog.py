# ═══════════════════════════════════════════════════════════════
#  ui/error_dialog.py — Janela "o que aconteceu e o que fazer"
#
#  Mostra o problema em português, por que costuma acontecer e as
#  soluções em ordem. "Copiar detalhes" leva o texto técnico para a
#  área de transferência (para colar num aviso no GitHub, por exemplo).
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk

from ui.theme import (BG, SURFACE, CARD, CARD_HI, BORDER, ACCENT, ACCENT_H, TEAL, TEXT, MUTED, DIM, RED, font, mono)


class ProblemDialog(ctk.CTkToplevel):
    def __init__(self, parent, problem, details="", extra=None, on_retry=None):
        """problem: core.errors.Problem · details: texto técnico · extra: linhas a mais (ex.: lista de vídeos)."""
        super().__init__(parent)
        self.attributes("-alpha", 0.0)          # monta invisível, aparece pronta
        self._parent = parent
        self._details = details
        self.title("O que aconteceu")
        self.configure(fg_color=BG)
        self.resizable(False, False)

        scale = self._get_window_scaling()
        sw, sh = self.winfo_screenwidth() / scale, self.winfo_screenheight() / scale
        w = min(560, int(sw * 0.9))
        self.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        head.grid(row=0, column=0, sticky="ew")
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(head, fg_color=RED, width=10, height=10, corner_radius=5).grid(row=0, column=0, padx=(22, 12), pady=(20, 0), sticky="n")
        ctk.CTkLabel(head, text=problem.title, font=font(16, "bold"), text_color=TEXT, anchor="w",
                     justify="left", wraplength=w - 90).grid(row=0, column=1, sticky="w", pady=(16, 4), padx=(0, 22))
        ctk.CTkLabel(head, text=problem.message, font=font(12), text_color=MUTED, anchor="w",
                     justify="left", wraplength=w - 90).grid(row=1, column=1, sticky="w", pady=(0, 16), padx=(0, 22))

        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="ew", padx=22, pady=(16, 4))
        body.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(body, text="O que você pode fazer", font=font(12, "bold"), text_color=TEAL, anchor="w",
                     ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        for i, tip in enumerate(problem.tips, start=1):
            ctk.CTkLabel(body, text=str(i), font=font(11, "bold"), text_color=TEXT, fg_color=CARD_HI,
                         width=22, height=22, corner_radius=11).grid(row=i, column=0, sticky="n", pady=3, padx=(0, 10))
            ctk.CTkLabel(body, text=tip, font=font(13), text_color=TEXT, anchor="w", justify="left",
                         wraplength=w - 100).grid(row=i, column=1, sticky="w", pady=3)

        if extra:
            box = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
            box.grid(row=2, column=0, sticky="ew", padx=22, pady=(10, 0))
            ctk.CTkLabel(box, text="\n".join(extra[:6]) + (f"\n… e mais {len(extra) - 6}" if len(extra) > 6 else ""),
                         font=font(11), text_color=MUTED, anchor="w", justify="left", wraplength=w - 80,
                         ).pack(anchor="w", padx=14, pady=10)

        if details:
            ctk.CTkLabel(self, text="Detalhe técnico: " + details[:220], font=mono(10), text_color=DIM, anchor="w",
                         justify="left", wraplength=w - 44).grid(row=3, column=0, sticky="w", padx=22, pady=(12, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=4, column=0, sticky="ew", padx=22, pady=(16, 20))
        buttons.grid_columnconfigure(0, weight=1)
        self._copy_btn = ctk.CTkButton(buttons, text="Copiar detalhes", width=130, height=36, font=font(12),
                                       fg_color="transparent", hover_color=CARD_HI, border_width=1,
                                       border_color=BORDER, text_color=TEXT, corner_radius=8, command=self._copy)
        self._copy_btn.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(buttons, text="Fechar", width=90, height=36, font=font(12), fg_color=CARD_HI,
                      hover_color=BORDER, text_color=TEXT, corner_radius=8, command=self.destroy,
                      ).grid(row=0, column=1, padx=(8, 0))
        if on_retry:
            ctk.CTkButton(buttons, text="Tentar de novo", width=130, height=36, font=font(12, "bold"),
                          fg_color=ACCENT, hover_color=ACCENT_H, text_color="#ffffff", corner_radius=8,
                          command=lambda: (self.destroy(), on_retry())).grid(row=0, column=2, padx=(8, 0))

        self.update_idletasks()
        h = self.winfo_reqheight() / scale
        x = parent.winfo_rootx() / scale + (parent.winfo_width() / scale - w) / 2
        y = parent.winfo_rooty() / scale + max((parent.winfo_height() / scale - h) / 3, 20)
        self.geometry(f"{w}x{int(h)}+{int(max(x, 0))}+{int(max(y, 0))}")
        self.attributes("-alpha", 1.0)
        self.after(60, self._take_focus)

    def _take_focus(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _copy(self):
        self._parent.clipboard_clear()
        self._parent.clipboard_append(self._details or "")
        self._copy_btn.configure(text="Copiado ✓")
        self.after(1800, lambda: self._copy_btn.winfo_exists() and self._copy_btn.configure(text="Copiar detalhes"))
