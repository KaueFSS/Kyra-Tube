# ═══════════════════════════════════════════════════════════════
#  ui/splash.py — Tela de abertura
#
#  Feita só com o tkinter básico para aparecer na hora, antes de carregar
#  o resto (yt-dlp, customtkinter). A janela principal é montada escondida
#  e só aparece pronta, por isso nada "monta aos poucos" na frente de quem usa.
# ═══════════════════════════════════════════════════════════════
import tkinter as tk

_BG, _TEXT, _MUTED, _ACCENT = "#0d0f13", "#eceff4", "#8b94a4", "#ff5a4f"


class Splash:
    def __init__(self, logo_png, name="Kyra Tube"):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=_BG, highlightthickness=1, highlightbackground="#262c36")
        w, h = 340, 210
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self._img = None
        try:
            self._img = tk.PhotoImage(file=str(logo_png)).subsample(3, 3)
            tk.Label(self.root, image=self._img, bg=_BG).pack(pady=(30, 8))
        except Exception:
            pass
        tk.Label(self.root, text=name, font=("Segoe UI", 17, "bold"), fg=_TEXT, bg=_BG).pack()
        tk.Label(self.root, text="Abrindo…", font=("Segoe UI", 10), fg=_MUTED, bg=_BG).pack(pady=(4, 0))
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass
