"""
Descoberta de endpoints de dados num portal de transparência.

Varre o HTML procurando pistas de onde há dado estruturado: links para
arquivos (CSV/JSON/XML/planilhas/ZIP), rotas de exportação/download, e
pistas de API (CKAN, wp-json, /api). Classifica cada achado por tipo e
registra *por que* foi considerado candidato — a transparência do próprio
coletor importa tanto quanto a do portal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# extensões que denotam dado estruturado (peso maior) ou documento (menor)
DATA_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".xml": "xml",
    ".xlsx": "planilha",
    ".xls": "planilha",
    ".ods": "planilha",
    ".zip": "arquivo-compactado",
}
DOC_EXTENSIONS = {".pdf": "pdf"}

# palavras em href/texto que sugerem rota de dados mesmo sem extensão
KEYWORD_HINTS = (
    "dados-abertos", "dadosabertos", "opendata", "open-data",
    "exporta", "export", "download", "baixar", "arquivo",
    "/api", "consulta", "relatorio", "planilha",
)

# pistas fortes de API programática
API_HINTS = (
    ("/api/3/action/", "ckan"),      # CKAN
    ("wp-json", "wordpress-rest"),   # WordPress REST
    ("/odata", "odata"),
    ("/rest/", "rest"),
    ("/api/", "api-generica"),
)


@dataclass
class Endpoint:
    url: str
    kind: str          # csv | json | api-ckan | download | pdf | ...
    reason: str
    source_text: str = ""

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "kind": self.kind,
            "reason": self.reason,
            "source_text": self.source_text[:120],
        }


@dataclass
class DiscoveryResult:
    endpoints: list[Endpoint] = field(default_factory=list)
    api_hits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "count": len(self.endpoints),
            "api_hits": self.api_hits,
            "endpoints": [e.to_dict() for e in self.endpoints],
        }


def _ext_of(path: str) -> str:
    m = re.search(r"(\.[a-z0-9]{2,5})(?:$|\?)", path.lower())
    return m.group(1) if m else ""


def discover(base_url: str, html: str) -> DiscoveryResult:
    soup = BeautifulSoup(html or "", "html.parser")
    result = DiscoveryResult()
    seen: set[str] = set()

    def add(raw_href: str, text: str) -> None:
        if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return
        url = urljoin(base_url, raw_href.strip())
        if url in seen:
            return
        path = urlparse(url).path
        ext = _ext_of(url)
        text = (text or "").strip()

        if ext in DATA_EXTENSIONS:
            kind = DATA_EXTENSIONS[ext]
            result.endpoints.append(Endpoint(url, kind, f"extensão {ext}", text))
            seen.add(url)
            return
        if ext in DOC_EXTENSIONS:
            result.endpoints.append(Endpoint(url, "pdf", "documento pdf", text))
            seen.add(url)
            return
        low = (url + " " + text).lower()
        for hint in KEYWORD_HINTS:
            if hint in low:
                result.endpoints.append(
                    Endpoint(url, "rota-dados", f"pista '{hint}'", text))
                seen.add(url)
                return

    # <a href>, <link href>, <form action>, <iframe src>
    for a in soup.find_all("a", href=True):
        add(a["href"], a.get_text())
    for link in soup.find_all("link", href=True):
        add(link["href"], link.get("rel", [""])[0] if link.get("rel") else "")
    for form in soup.find_all("form", action=True):
        add(form["action"], "form")
    for frame in soup.find_all(["iframe", "frame"], src=True):
        add(frame["src"], "iframe")

    # pistas de API no HTML bruto (podem estar em scripts, não em <a>)
    blob = (html or "").lower()
    for needle, tag in API_HINTS:
        if needle in blob and tag not in result.api_hits:
            result.api_hits.append(tag)

    # ordena: dados estruturados primeiro, pdf por último
    priority = {"csv": 0, "json": 0, "xml": 1, "planilha": 1,
                "arquivo-compactado": 2, "rota-dados": 3, "pdf": 9}
    result.endpoints.sort(key=lambda e: priority.get(e.kind, 5))
    return result
