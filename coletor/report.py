"""
Geração do relatório de descoberta por município.

Dois formatos a partir da mesma estrutura:
- JSON: consumível pelo restante do pipeline (registry, API).
- Markdown: legível por humano, para auditoria e curadoria.

Todo relatório carrega proveniência (fonte, timestamp, hash do HTML) — sem
proveniência, dado público não é auditável.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .discovery import DiscoveryResult
from .fingerprint import Match


def build_report(
    *,
    municipality: str | None,
    url: str,
    html: str,
    matches: list[Match],
    discovery: DiscoveryResult,
    fetched_at: str | None = None,
) -> dict:
    best = matches[0] if matches else None
    return {
        "municipality": municipality,
        "source_url": url,
        "provenance": {
            "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(),
            "html_sha256": hashlib.sha256((html or "").encode("utf-8")).hexdigest(),
            "html_bytes": len((html or "").encode("utf-8")),
        },
        "platform": {
            "best_guess": best.platform if best else None,
            "vendor": best.vendor if best else None,
            "confidence": best.confidence if best else 0.0,
            "mode": _mode(best),
            "candidates": [m.to_dict() for m in matches],
        },
        "discovery": discovery.to_dict(),
        "recommended_probes": best.known_data_paths if best else [],
    }


def _mode(best: Match | None) -> str:
    """Como o coletor deve prosseguir a partir daqui."""
    if best is None or best.confidence < 0.3:
        return "descoberta"   # plataforma nova/incerta: agente explora
    if best.confidence < 0.7:
        return "adapter-provavel"
    return "adapter-conhecido"  # aplica adapter direto


def to_markdown(report: dict) -> str:
    p = report["platform"]
    d = report["discovery"]
    prov = report["provenance"]
    lines = [
        f"# Relatório de descoberta — {report.get('municipality') or 'município'}",
        "",
        f"- **Fonte:** {report['source_url']}",
        f"- **Coletado em:** {prov['fetched_at']}",
        f"- **Hash HTML (sha256):** `{prov['html_sha256'][:16]}…`",
        "",
        "## Plataforma",
        f"- **Palpite:** {p['best_guess'] or '— (não reconhecida)'}"
        + (f" ({p['vendor']})" if p['vendor'] else ""),
        f"- **Confiança:** {p['confidence']:.0%}",
        f"- **Modo sugerido:** `{p['mode']}`",
    ]
    if p["candidates"]:
        lines.append("")
        lines.append("### Sinais reconhecidos")
        for c in p["candidates"]:
            lines.append(f"- **{c['platform']}** — {c['confidence']:.0%}")
            for r in c["reasons"]:
                lines.append(f"  - {r}")
    lines += ["", "## Endpoints candidatos", f"Total: **{d['count']}**"]
    if d["api_hits"]:
        lines.append(f"Pistas de API: {', '.join('`'+h+'`' for h in d['api_hits'])}")
    lines.append("")
    if d["endpoints"]:
        lines.append("| tipo | url | por quê |")
        lines.append("| --- | --- | --- |")
        for e in d["endpoints"]:
            url = e["url"] if len(e["url"]) <= 80 else e["url"][:77] + "…"
            lines.append(f"| `{e['kind']}` | {url} | {e['reason']} |")
    else:
        lines.append("_Nenhum endpoint candidato encontrado no HTML._")
    if report["recommended_probes"]:
        lines += ["", "## Caminhos recomendados para probe (rodar com rede)"]
        for path in report["recommended_probes"]:
            lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)
