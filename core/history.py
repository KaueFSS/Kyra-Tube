# ═══════════════════════════════════════════════════════════════
#  core/history.py — Persistência do histórico de downloads
# ═══════════════════════════════════════════════════════════════
import json
from pathlib import Path

HIST = Path.home() / ".offtube_kauefss.json"


def load_hist():
    """Carrega o histórico de downloads do disco."""
    try:
        return json.loads(HIST.read_text("utf-8")) if HIST.exists() else []
    except Exception:
        return []


def save_hist(h):
    """Salva os últimos 50 downloads no disco."""
    try:
        HIST.write_text(json.dumps(h[-50:], ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
