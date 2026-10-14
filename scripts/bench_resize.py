"""Mede quanto custa redimensionar a janela (ms por quadro). Quanto menor, mais liso.

    python scripts/bench_resize.py
"""
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.theme import apply_theme  # noqa: E402

apply_theme()
from ui.app import App  # noqa: E402

app = App()
app.geometry("1000x640+40+20")


def run():
    app.update()
    times = []
    for _ in range(3):
        for w in list(range(900, 1300, 8)) + list(range(1300, 900, -8)):
            t = time.perf_counter()
            app.geometry(f"{w}x640")
            app.update()
            times.append((time.perf_counter() - t) * 1000)
    print(f"quadros: {len(times)}  mediana: {statistics.median(times):.1f} ms  "
          f"p90: {sorted(times)[int(len(times) * .9)]:.1f} ms  máx: {max(times):.0f} ms")
    app.destroy()


app.after(1500, run)
app.mainloop()
