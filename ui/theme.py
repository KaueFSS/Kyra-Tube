# ═══════════════════════════════════════════════════════════════
#  ui/theme.py — Paleta de cores e configuração visual do OffTube
#  ► Altere as cores aqui para mudar todo o visual do app
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk

# ── Paleta principal ─────────────────────────────────────────────
BG      = "#0d0d16"
SURFACE = "#12121e"
CARD    = "#181826"
BORDER  = "#222236"
BLUE    = "#4f8ef7"
BLUE_H  = "#3a73e0"
TEXT    = "#e2e2f0"
MUTED   = "#4a4a6a"
GREEN   = "#22c55e"
RED     = "#ef4444"
YELLOW  = "#f59e0b"
ORANGE  = "#fb923c"
PURPLE  = "#a78bfa"

def apply_theme():
    """Aplica o tema global do customtkinter."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
