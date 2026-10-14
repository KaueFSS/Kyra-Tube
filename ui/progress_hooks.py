# ═══════════════════════════════════════════════════════════════
#  ui/progress_hooks.py — Hook de progresso do yt-dlp
#  ► Para mudar como o progresso é exibido, edite apenas este arquivo
# ═══════════════════════════════════════════════════════════════
import os
import yt_dlp

from core.setup import clean
from ui.theme   import TEXT, MUTED, TEAL, GREEN, ORANGE


class ProgressMixin:
    """
    Mixin que adiciona o hook de progresso do yt-dlp à App.
    Depende dos widgets e atributos definidos em app.py.
    """

    def _reset_prog(self):
        self.pbar.set(0)
        self.vid_pbar.set(0)
        self._pl_total      = 0
        self._pl_done       = 0
        self._last_finished = None
        self.prog_lbl.configure(text="Iniciando…", text_color=TEXT)
        self.pbar.configure(progress_color=TEAL)
        self.result_row.grid_remove()
        self.vid_prog_lbl.grid_remove()
        self.vid_pbar.grid_remove()
        self.speed_lbl.configure(text="")
        self.status_lbl.configure(text="", text_color=MUTED)
        self.pl_count_lbl.configure(text="")
        self.vid_prog_lbl.configure(text="")
        try:
            self.proc_pbar.stop()
            self.proc_pbar.grid_remove()
            self.proc_lbl.grid_remove()
        except Exception:
            pass

    def _hook(self, d):
        if self._stop:
            raise yt_dlp.utils.DownloadCancelled()

        st        = d.get("status")
        info      = d.get("info_dict", {})
        n_entries = info.get("n_entries") or d.get("n_entries")
        if n_entries and n_entries != self._pl_total:
            self._pl_total = n_entries

        if st == "downloading":
            self._hook_downloading(d)
        elif st == "finished":
            self._hook_finished(d)

    def _hook_downloading(self, d):
        if self._pl_total > 1:            # em playlist, mostra também o progresso do vídeo atual
            self.after(0, lambda: (self.vid_prog_lbl.grid(), self.vid_pbar.grid()))
        raw = clean(d.get("_percent_str", "0%")).replace("%", "")
        try:
            pct = float(raw)
            self.after(0, lambda p=pct: (
                self.vid_pbar.set(p / 100),
                self.vid_prog_lbl.configure(text=f"Vídeo atual: {p:.1f}%", text_color=TEAL),
            ))
        except Exception:
            pct = 0

        sp  = clean(d.get("_speed_str", ""))
        eta = clean(d.get("_eta_str", ""))
        if sp and sp != "N/A":
            self.after(0, lambda s=sp, e=eta:
                self.speed_lbl.configure(text=f"{s}  ETA {e}"))

        fn = d.get("filename", "")
        if fn:
            self.after(0, lambda b=os.path.basename(fn):
                self.status_lbl.configure(text=b, text_color=MUTED))

        if self._pl_total > 1:
            try:
                vid_frac = pct / 100
            except Exception:
                vid_frac = 0
            overall = (self._pl_done + vid_frac) / self._pl_total
            faltam  = self._pl_total - self._pl_done - 1
            self.after(0, lambda o=overall, d=self._pl_done+1, t=self._pl_total, f=max(faltam, 0): (
                self.pbar.set(o),
                self.prog_lbl.configure(text=f"Vídeo {d} de {t}", text_color=TEXT),
                self.pl_count_lbl.configure(
                    text=f"Faltam {f} vídeo{'s' if f!=1 else ''}", text_color=ORANGE),
            ))
        else:
            try:
                self.after(0, lambda p=pct: (
                    self.pbar.set(p / 100),
                    self.prog_lbl.configure(text=f"{p:.1f}%", text_color=TEXT),
                ))
            except Exception:
                pass

    def _hook_finished(self, d):
        vid_id = d.get("info_dict", {}).get("id") or d.get("filename", "")
        if vid_id and vid_id == self._last_finished:
            # Segundo stream do mesmo vídeo → merge ffmpeg
            self.after(0, lambda: (
                self.proc_lbl.configure(text="Processando (merge)...", text_color=ORANGE),
                self.proc_lbl.grid(),
                self.proc_pbar.grid(),
                self.proc_pbar.start(),
                self.vid_prog_lbl.configure(text=""),
                self.speed_lbl.configure(text=""),
            ))
            return

        self._last_finished = vid_id or None
        self._pl_done += 1
        done    = self._pl_done
        total   = self._pl_total
        overall = done / total if total > 0 else 1.0
        faltam  = max(total - done, 0)

        self.after(0, lambda o=overall, dn=done, t=total, f=faltam: (
            self.pbar.set(o),
            self.vid_pbar.set(1),
            self.proc_pbar.stop(),
            self.proc_pbar.grid_remove(),
            self.proc_lbl.grid_remove(),
            self.prog_lbl.configure(
                text=f"Vídeo {dn} de {t}" if t > 1 else "Baixando...",
                text_color=TEXT),
            self.pl_count_lbl.configure(
                text=f"Faltam {f} vídeo{'s' if f!=1 else ''}" if t > 1 and f > 0
                     else ("Todos baixados" if t > 1 else ""),
                text_color=GREEN if f == 0 else ORANGE),
            self.speed_lbl.configure(text=""),
            self.vid_prog_lbl.configure(text=""),
        ))
