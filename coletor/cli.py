"""
CLI do coletor: fingerprint + descoberta → relatório.

Uso:
    python -m coletor <url-ou-arquivo> [--municipio NOME] [--json saida.json]
                                       [--md saida.md] [--quiet]

Exemplos:
    python -m coletor https://transparencia.exemplo.gov.br --municipio "Exemplo/CE"
    python -m coletor coletor/tests/fixtures/betha.html --md /tmp/rel.md
"""

from __future__ import annotations

import argparse
import json
import sys

from .discovery import discover
from .fetch import fetch
from .fingerprint import detect
from .report import build_report, to_markdown


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="coletor", description=__doc__)
    ap.add_argument("target", help="URL do portal ou caminho de HTML local")
    ap.add_argument("--municipio", default=None, help="rótulo do município")
    ap.add_argument("--json", dest="json_out", default=None, help="grava relatório JSON")
    ap.add_argument("--md", dest="md_out", default=None, help="grava relatório Markdown")
    ap.add_argument("--quiet", action="store_true", help="não imprime o Markdown")
    args = ap.parse_args(argv)

    try:
        f = fetch(args.target)
    except Exception as exc:  # rede bloqueada, host inválido, etc.
        print(f"erro ao buscar {args.target}: {exc}", file=sys.stderr)
        return 2

    matches = detect(f.url, f.html, f.headers)
    disc = discover(f.url, f.html)
    report = build_report(
        municipality=args.municipio,
        url=f.url,
        html=f.html,
        matches=matches,
        discovery=disc,
    )

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    md = to_markdown(report)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as fh:
            fh.write(md)
    if not args.quiet:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
