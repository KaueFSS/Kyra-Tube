# ══════════════════════════════════════════════════════════════
#  main.py — Ponto de entrada do Kyra Tube
#
#  Rodar pelo código:   python main.py
#  Gerar o instalador:  scripts/build.ps1
#  Versão do app:       core/config.py  →  APP_VERSION
# ══════════════════════════════════════════════════════════════

import ctypes

# Identidade própria no Windows: sem isso, rodando pelo código, a barra de tarefas
# mostra o ícone do Python; com isso, mostra o do Kyra Tube (e agrupa e fixa certo).
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KaueFSS.KyraTube")
except Exception:
    pass

from core.setup import ensure_dependencies, resource_path
ensure_dependencies()

# A tela de abertura aparece antes de qualquer coisa pesada ser carregada.
from ui.splash import Splash
splash = Splash(resource_path("assets/kyra-tube.png"))

from ui.theme import apply_theme
apply_theme()

from ui.app import App

if __name__ == "__main__":
    splash.close()
    app = App()
    app.mainloop()
