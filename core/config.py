# ═══════════════════════════════════════════════════════════════
#  core/config.py — Configurações centrais do Kyra Tube
#  ► Para lançar uma versão nova use `python scripts/release.py`
#    (ele muda APP_VERSION, cria a tag e o GitHub publica o instalador)
# ═══════════════════════════════════════════════════════════════

APP_NAME    = "Kyra Tube"
APP_VERSION = "3.0.0"

# ── Atualizações (GitHub Releases) ──────────────────────────────
GITHUB_USER     = "KaueFSS"
GITHUB_REPO     = "Kyra-Tube"
INSTALLER_ASSET = "Kyra-Tube-Setup.exe"
UPDATE_CHECK_INTERVAL = 6 * 60 * 60   # segundos entre checagens (6 horas)
