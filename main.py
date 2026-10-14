# ══════════════════════════════════════════════════════════════
#  main.py — Ponto de entrada do Kyra Tube
#
#  Rodar pelo código:   python main.py
#  Gerar o instalador:  veja docs/DESENVOLVIMENTO.md
#  Versão do app:       core/config.py  →  APP_VERSION
# ══════════════════════════════════════════════════════════════

from core.setup import ensure_dependencies
ensure_dependencies()

from ui.theme import apply_theme
apply_theme()

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
