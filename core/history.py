# ═══════════════════════════════════════════════════════════════
#  core/history.py — Persistência do histórico de downloads
# ═══════════════════════════════════════════════════════════════
import json
from pathlib import Path

HIST = Path.home() / ".kyra_tube.json"
# Nome do arquivo na época em que o app se chamava OffTube: quem já usava
# continua vendo o próprio histórico depois da troca de nome.
LEGACY_HIST = Path.home() / ".offtube_kauefss.json"


def load_hist(path=HIST, legacy=LEGACY_HIST):
    """Carrega o histórico de downloads do disco (migrando o arquivo antigo, se houver)."""
    try:
        source = path if path.exists() else legacy
        return json.loads(source.read_text("utf-8")) if source.exists() else []
    except Exception:
        return []


def save_hist(h, path=HIST):
    """Salva os últimos 50 downloads no disco."""
    try:
        path.write_text(json.dumps(h[-50:], ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
