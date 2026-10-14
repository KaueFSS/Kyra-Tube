"""Teste de ponta a ponta da interface, com internet (a janela abre e é fechada sozinha).

    python scripts/smoke_ui.py

Baixa um vídeo curto, tenta de novo (deve avisar que já estava baixado) e tenta
um vídeo que não existe (deve abrir a janela com o que fazer).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.theme import apply_theme  # noqa: E402

apply_theme()
import customtkinter as ctk  # noqa: E402

from ui.app import App  # noqa: E402

SHORT = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
MISSING = "https://www.youtube.com/watch?v=zzzzzzzzzzz"

tmp = tempfile.TemporaryDirectory()
app = App()
app.folder_v.set(tmp.name)
app.qual_v.set("360p")
log, checks = [], []


def labels(widget):
    out = []
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkLabel):
            out.append(child.cget("text"))
        out += labels(child)
    return out


def note(name, ok, detail=""):
    checks.append(ok)
    print(("  OK   " if ok else "  FALHOU ") + name + (f"  → {detail}" if detail else ""))


def wait_idle(then, waited=0):
    if str(app.dl_btn.cget("state")) == "disabled" and waited < 120_000:
        app.after(500, lambda: wait_idle(then, waited + 500))
    else:
        app.after(300, then)


def step1():
    app.url_v.set(SHORT)
    app.after(1500, lambda: (app._start(), app.after(1500, check_busy)))


def check_busy():
    note("durante o download, o card de progresso ocupa o lugar das opções",
         app.progress_card.winfo_ismapped() and not app.options_card.winfo_ismapped())
    wait_idle(check_first)


def check_first():
    text = app.prog_lbl.cget("text")
    note("primeiro download termina com 'Concluído'", text.startswith("Concluído"), text)
    note("botões de resultado aparecem", app.result_row.winfo_ismapped())
    note("o arquivo foi salvo", any(Path(tmp.name).glob("*.mp4")))
    app._new_download()
    app.after(300, step2)


def step2():
    app.url_v.set(SHORT)
    app.after(1500, lambda: (app._start(), wait_idle(check_second)))


def check_second():
    text = app.prog_lbl.cget("text")
    note("baixar de novo avisa que já estava baixado", "já estava baixado" in text, text)
    note("e não diz 'Concluído em 0s'", "Concluído" not in text)
    app._new_download()
    app.after(300, step3)


def step3():
    app.url_v.set(MISSING)
    app.after(1500, lambda: (app._start(), wait_idle(check_missing)))


def check_missing():
    dialogs = [w for w in app.winfo_children() if w.winfo_class() == "Toplevel"]
    note("vídeo inexistente abre a janela do problema", bool(dialogs))
    if dialogs:
        texts = labels(dialogs[0])
        note("com o título em português", any("não está disponível" in t for t in texts), next((t for t in texts if "disponível" in t), ""))
        note("e com soluções", any(t.startswith("O que você pode fazer") for t in texts))
        dialogs[0].destroy()
    note("o card mostra 'Não foi possível baixar'", app.prog_lbl.cget("text") == "Não foi possível baixar", app.prog_lbl.cget("text"))
    finish()


def finish():
    print("\nRESULTADO:", "tudo certo" if all(checks) else "ALGO FALHOU")
    app.destroy()
    tmp.cleanup()
    sys.exit(0 if all(checks) else 1)


app.after(1500, step1)
app.mainloop()
