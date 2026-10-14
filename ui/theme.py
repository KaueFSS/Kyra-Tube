# ═══════════════════════════════════════════════════════════════
#  ui/theme.py — Identidade visual do Kyra Tube
#  ► As cores vêm do ícone: o coral do "K" e o turquesa do ponto.
#  ► Altere aqui para mudar o visual de todo o app.
# ═══════════════════════════════════════════════════════════════
import customtkinter as ctk

# ── Superfícies (do mais fundo ao mais alto) ────────────────────
BG        = "#0d0f13"
SURFACE   = "#11141a"
CARD      = "#161a21"
CARD_HI   = "#1c212a"
BORDER    = "#262c36"

# ── Texto ───────────────────────────────────────────────────────
TEXT      = "#eceff4"
MUTED     = "#8b94a4"
DIM       = "#566071"

# ── Marca ───────────────────────────────────────────────────────
ACCENT      = "#ff5a4f"     # coral do ícone: ações principais
ACCENT_H    = "#ee4439"
ACCENT_SOFT = "#2a1a1c"     # fundo suave do coral
TEAL        = "#2dd4bf"     # turquesa do ponto do ícone: progresso e sucesso

# ── Estados ─────────────────────────────────────────────────────
GREEN     = "#34d399"
YELLOW    = "#fbbf24"
ORANGE    = "#fb923c"
RED       = "#f87171"

# ── Tipografia ──────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"      # já vem no Windows: abre na hora, sem carregar fonte
MONO_FAMILY = "Consolas"

RADIUS = 12


def font(size=13, weight="normal"):
    """Fonte do app (use depois que a janela existir)."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono(size=11, weight="normal"):
    return ctk.CTkFont(family=MONO_FAMILY, size=size, weight=weight)


def apply_theme():
    """Aplica o tema global do customtkinter (modo escuro e fonte padrão)."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    # Todo widget sem fonte explícita também usa a fonte do app.
    ctk.ThemeManager.theme["CTkFont"]["family"] = FONT_FAMILY
