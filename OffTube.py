# python -m PyInstaller --onefile --windowed --name OffTube OffTube.py
# py -m PyInstaller --clean OffTube.spec

# ══════════════════════════════════════════════════════════════
#  OffTube.py — Ponto de entrada
#  ► Para mudar a versão edite: core/config.py  →  APP_VERSION
# ══════════════════════════════════════════════════════════════

from core.setup import ensure_dependencies
ensure_dependencies()

from ui.theme import apply_theme
apply_theme()

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
