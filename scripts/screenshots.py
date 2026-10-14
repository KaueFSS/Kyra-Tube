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

from core.downloader import Result  # noqa: E402
from core.errors import explain  # noqa: E402
from ui.theme import apply_theme  # noqa: E402

apply_theme()
from ui.app import App  # noqa: E402
from ui.error_dialog import ProblemDialog  # noqa: E402

OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

app = App()
app.geometry("1000x690+60+30")


def grab(name, widget=None):
    """Foto só da região da janela (ou de um widget), com checagem de que são pixels do app."""
    target = widget or app
    app.lift()
    app.attributes("-topmost", True)
    if widget is not None:                     # janela de diálogo: precisa ficar na frente do app
        widget.attributes("-topmost", True)
        widget.lift()
    app.update()
    x, y, w, h = target.winfo_rootx(), target.winfo_rooty(), target.winfo_width(), target.winfo_height()
    shot = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")
    probe = shot.getpixel((w // 2, 12))
    known = [(13, 15, 19), (17, 20, 26), (22, 26, 33)]            # BG, SURFACE, CARD: as cores do app
    if not any(max(abs(probe[i] - c[i]) for i in range(3)) <= 6 for c in known):
        raise SystemExit(f"A captura não parece ser do app (cor {probe}). Tente de novo.")
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
    app._reset_prog()
    app._set_busy(True)
    app.prog_lbl.configure(text="Baixando…  42,3%")
    app.speed_lbl.configure(text="4,8 MiB/s  ·  ETA 00:21")
    app.pbar.set(0.423)
    app.status_lbl.configure(text="Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film.mp4")
    app.after(900, step_shot_progress)


def step_shot_progress():
    grab("baixando.png")
    # Já estava baixado.
    app._finish([Result("Big Buck Bunny", already=True, path="C:/Users/voce/Downloads/Big Buck Bunny.mp4")], [], 0.4, False)
    app.after(900, step_shot_already)


def step_shot_already():
    grab("ja-baixado.png")
    # Erro explicado, aberto sobre a janela.
    raw = "ERROR: [youtube] abc123: Sign in to confirm you're not a bot"
    app._dialog = ProblemDialog(app, explain(raw), details="[youtube] abc123: Sign in to confirm you're not a bot",
                                on_retry=lambda: None)
    app.after(1300, step_shot_error)


def step_shot_error():
    grab("erro.png", widget=app._dialog)
    app._dialog.destroy()
    app.destroy()


app.after(1500, step_banner)
app.mainloop()
