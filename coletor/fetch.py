"""
Aquisição do HTML de um portal.

Aceita tanto uma URL (coleta ao vivo) quanto um arquivo local (`file://` ou
caminho) — este último é o modo usado em ambientes sem saída de rede, como
CI ou desenvolvimento com fixtures.

Boas práticas de coleta cívica embutidas: identifica o agente, respeita um
timeout curto e devolve os cabeçalhos para o fingerprint. Checagem de
robots.txt fica como próximo passo do adapter de coleta real.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

USER_AGENT = (
    "FiscalizaiColetor/0.1 (+transparência LAI; coleta de dados públicos)"
)


@dataclass
class Fetched:
    url: str
    html: str
    headers: dict
    from_cache: bool = False


def fetch(target: str, *, timeout: float = 15.0) -> Fetched:
    """
    Busca o HTML de `target`. Se for caminho de arquivo existente (ou file://),
    lê do disco; caso contrário faz GET HTTP.
    """
    path = target[len("file://"):] if target.startswith("file://") else target
    if not target.lower().startswith(("http://", "https://")) and os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return Fetched(url=target, html=fh.read(), headers={}, from_cache=True)

    import httpx  # import tardio: só necessário na coleta ao vivo

    with httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        resp = client.get(target)
        return Fetched(
            url=str(resp.url),
            html=resp.text,
            headers={k: v for k, v in resp.headers.items()},
        )
