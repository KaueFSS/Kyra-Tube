#!/usr/bin/env python
"""Lança uma versão nova do Kyra Tube em um comando:

    python scripts/release.py 3.1.0          # entrega a todos
    python scripts/release.py 3.1.0 --pre    # pré-lançamento: dá para baixar e testar, o app não oferece

As notas vêm do CHANGELOG.md (a seção "## 3.1.0"). O script muda APP_VERSION em
core/config.py, faz o commit, cria a tag com as notas e envia. O GitHub Actions
gera o executável e o instalador e publica a release; quem já tem o app recebe
o aviso de atualização.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "core" / "config.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def fail(message):
    sys.exit(f"\n✖ {message}\n")


def run(*cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, check=True, text=True, capture_output=kw.pop("capture", False), **kw)


def parse_version(value):
    return tuple(int(x) for x in value.split("."))


def main():
    args = [a for a in sys.argv[1:] if a != "--pre"]
    pre = "--pre" in sys.argv[1:]
    if len(args) != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", args[0]):
        fail("Use: python scripts/release.py <versão> [--pre]   (ex.: python scripts/release.py 3.1.0)")
    version = args[0]

    config = CONFIG.read_text("utf-8")
    current = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', config).group(1)
    if parse_version(version) <= parse_version(current):
        fail(f"A nova versão ({version}) precisa ser maior que a atual ({current}).")
    if run("git", "status", "--porcelain", capture=True).stdout.strip():
        fail("Há alterações não salvas no git. Faça commit (ou descarte) antes de lançar.")
    if run("git", "rev-parse", "--abbrev-ref", "HEAD", capture=True).stdout.strip() != "main":
        fail("Lance a partir da branch main.")
    if run("git", "tag", "-l", f"v{version}", capture=True).stdout.strip():
        fail(f"A tag v{version} já existe.")

    # Notas: a seção "## <versão>" do CHANGELOG.md. Conferido antes de mexer em qualquer arquivo.
    section = re.search(rf"^## {re.escape(version)}\b.*?\n(.*?)(?=^## |\Z)", CHANGELOG.read_text("utf-8"), re.S | re.M)
    bullets = [l.strip() for l in (section.group(1) if section else "").splitlines() if l.strip().startswith("- ")]
    if not bullets:
        fail(f"Adicione a seção '## {version}' ao CHANGELOG.md (o que foi adicionado) antes de lançar.")
    notes = "\n".join(["Novidades:", *bullets])
    message = f"[pre-release]\n{notes}" if pre else notes

    CONFIG.write_text(re.sub(r'(APP_VERSION\s*=\s*)"[^"]+"', rf'\1"{version}"', config, count=1), "utf-8")
    run("git", "add", "core/config.py")
    run("git", "commit", "-m", f"Versão {version}")
    run("git", "tag", "-a", f"v{version}", "-m", message)
    run("git", "push", "origin", "main", "--follow-tags")

    print(f"\n✔ v{version} enviada. Acompanhe em: https://github.com/KaueFSS/Kyra-Tube/actions")
    print(
        f"  Pré-lançamento: para entregar a todos use: gh release edit v{version} --prerelease=false --latest\n"
        if pre
        else "  Quando terminar, quem já tem o Kyra Tube recebe o aviso de atualização.\n"
    )


if __name__ == "__main__":
    main()
