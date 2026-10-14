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
app.geometry("1000x690+60+30")


def grab(name):
    """Foto só da região da janela do app, com checagem de que é ela mesma (e não outra coisa na tela)."""
    app.lift()
    app.attributes("-topmost", True)
    app.update()
    x, y, w, h = app.winfo_rootx(), app.winfo_rooty(), app.winfo_width(), app.winfo_height()
    shot = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")
    bar = shot.getpixel((w // 2, 12))                 # a barra de cima tem a cor SURFACE
    if max(abs(bar[0] - 17), abs(bar[1] - 20), abs(bar[2] - 26)) > 6:
        raise SystemExit(f"A captura não parece ser a janela do app (cor {bar}). Tente de novo.")
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
    # Estado "baixando" simulado só para o print (nada é baixado de verdade).
    app.progress_card.grid()
    app.prog_lbl.configure(text="Baixando…  42,3%")
    app.speed_lbl.configure(text="4,8 MiB/s  ·  ETA 00:21")
    app.pbar.set(0.423)
    app.status_lbl.configure(text="Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film.mp4")
    app.vid_prog_lbl.configure(text="")
    app.vid_pbar.set(0)
    app.dl_btn.configure(state="disabled", text="Baixando…")
    app.cancel_btn.configure(state="normal")
    app.after(800, step_shot_progress)


def step_shot_progress():
    grab("baixando.png")
    app.destroy()


app.after(1500, step_banner)
app.mainloop()
