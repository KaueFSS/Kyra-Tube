"""Teste de verdade, com internet: baixa, baixa de novo, e tenta um vídeo que não existe.

    python scripts/smoke_download.py

Usa "Me at the zoo" (19 s, o primeiro vídeo do YouTube) e salva numa pasta temporária.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yt_dlp  # noqa: E402

from core.downloader import build_opts, run_download  # noqa: E402
from core.errors import explain, short_reason  # noqa: E402

SHORT = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
MISSING = "https://www.youtube.com/watch?v=zzzzzzzzzzz"
NOT_A_VIDEO = "https://exemplo-que-nao-existe.invalid/video"


def opts_for(folder, fmt, qual="360p", mp3="128k"):
    return build_opts(folder, fmt, qual, mp3, False, False, "jpg", lambda d: None)


def attempt(label, folder, fmt, url):
    try:
        result = run_download(opts_for(folder, fmt), url, fmt)
        state = "já estava baixado" if result.already else "baixado agora"
        print(f"  {label}: {state}  ({Path(result.path).name})")
        return result
    except Exception as exc:  # noqa: BLE001
        problem = explain(str(exc))
        print(f"  {label}: ERRO [{problem.key}] {problem.title}")
        print(f"      técnico: {short_reason(str(exc), 140)}")
        return problem


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        print("MP4 360p")
        first = attempt("1ª vez ", tmp, "mp4", SHORT)
        second = attempt("2ª vez ", tmp, "mp4", SHORT)
        ok &= hasattr(first, "already") and not first.already
        ok &= hasattr(second, "already") and second.already

        print("MP3 128k")
        mp3_first = attempt("1ª vez ", tmp, "mp3", SHORT)
        mp3_second = attempt("2ª vez ", tmp, "mp3", SHORT)
        ok &= hasattr(mp3_first, "already") and not mp3_first.already
        ok &= hasattr(mp3_second, "already") and mp3_second.already

        print("Vídeo que não existe")
        missing = attempt("link   ", tmp, "mp4", MISSING)
        ok &= getattr(missing, "key", "") in ("unavailable", "private", "unknown")

        print("Link que não é de vídeo")
        bad = attempt("link   ", tmp, "mp4", NOT_A_VIDEO)
        ok &= getattr(bad, "key", "") in ("bad_url", "network", "unknown")

    print("\nRESULTADO:", "tudo certo" if ok else "ALGO FALHOU")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
