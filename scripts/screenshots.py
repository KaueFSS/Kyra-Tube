"""Gera os prints do README a partir do próprio app (não mexe em nada na sua tela).

    python scripts/screenshots.py

Abre o Kyra Tube, carrega um vídeo livre de exemplo (o curta "Big Buck Bunny",
da Blender Foundation, licença CC-BY), mostra o aviso de atualização e salva
docs/screenshots/janela.png e docs/screenshots/atualizacao.png.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import ImageGrab  # noqa: E402

from ui.theme import apply_theme  # noqa: E402

apply_theme()
from ui.app import App  # noqa: E402

OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

app = App()
app.geometry("1100x700+60+40")
app.attributes("-topmost", True)


def grab(name):
    app.update_idletasks()
    x, y, w, h = app.winfo_rootx(), app.winfo_rooty(), app.winfo_width(), app.winfo_height()
    shot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    if shot.convert("L").getextrema()[1] < 10:   # tela apagada/bloqueada: não salva imagem preta
        raise SystemExit("A captura saiu preta (tela bloqueada?). Tente de novo com a tela ligada.")
    shot.save(OUT / name)
    print("salvo:", OUT / name)


def step_banner():
    app.update_banner.show_available("3.1.0", ["Fila de downloads", "Tema claro", "Mais formatos de áudio"])
    app.after(1500, step_shot_banner)


def step_shot_banner():
    grab("atualizacao.png")
    app.update_banner.grid_remove()
    app.url_v.set(SAMPLE)
    app.after(11000, step_shot_window)


def step_shot_window():
    grab("janela.png")
    app.destroy()


app.after(1500, step_banner)
app.mainloop()
