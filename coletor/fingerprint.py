"""
Fingerprint de plataformas de portais de transparência municipais.

A maioria das prefeituras brasileiras não desenvolve o próprio portal: contrata
uma de poucas empresas de software. Reconhecer qual plataforma está por trás de
um portal permite reaproveitar um *adapter* já conhecido em vez de raspar cada
cidade do zero — é o que torna a coleta em escala viável.

Cada assinatura pontua sinais independentes (host, marcadores no HTML, meta
generator, cabeçalhos). A soma vira uma confiança normalizada em [0, 1].
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Signature:
    """Regras de reconhecimento de uma plataforma."""

    name: str
    vendor: str
    # regex aplicadas ao host (sem esquema). Peso alto: host é forte indício.
    host_patterns: tuple[str, ...] = ()
    # substrings (minúsculas) procuradas no corpo do HTML.
    body_markers: tuple[str, ...] = ()
    # substrings procuradas no <meta name="generator">.
    generator_markers: tuple[str, ...] = ()
    # substrings procuradas nos cabeçalhos HTTP (ex.: Server, X-Powered-By).
    header_markers: tuple[str, ...] = ()
    # caminhos relativos conhecidos que costumam expor dados nessa plataforma.
    # Servem como candidatos a *probe* quando a coleta rodar com rede.
    known_data_paths: tuple[str, ...] = ()

    # pesos por tipo de sinal
    W_HOST = 3.0
    W_GENERATOR = 3.0
    W_BODY = 1.0
    W_HEADER = 2.0

    def score(self, host: str, body_lower: str, generator: str,
              headers_blob: str) -> tuple[float, list[str]]:
        """
        Retorna (pontuação bruta, motivos que casaram).

        A pontuação é por *categoria*, não por marcador: dentro de host e
        generator, os padrões são grafias alternativas do mesmo sinal, então
        casar qualquer um já vale a categoria inteira. Corpo é a fração de
        marcadores encontrados (evidência acumula, mas satura no peso da
        categoria).
        """
        pts = 0.0
        reasons: list[str] = []

        for pat in self.host_patterns:
            if re.search(pat, host, re.I):
                pts += self.W_HOST
                reasons.append(f"host casa /{pat}/")
                break  # categoria já pontuada
        for m in self.generator_markers:
            if m in generator:
                pts += self.W_GENERATOR
                reasons.append(f"meta generator contém '{m}'")
                break
        if self.body_markers:
            hits = [m for m in self.body_markers if m in body_lower]
            if hits:
                pts += self.W_BODY * (len(hits) / len(self.body_markers))
                for m in hits:
                    reasons.append(f"corpo contém '{m}'")
        for m in self.header_markers:
            if m in headers_blob:
                pts += self.W_HEADER
                reasons.append(f"cabeçalho contém '{m}'")
                break
        return pts, reasons

    # teto usado para normalizar a confiança em [0, 1]: uma unidade por
    # categoria presente na assinatura (não por número de alternativas).
    def max_points(self) -> float:
        return (
            (self.W_HOST if self.host_patterns else 0.0)
            + (self.W_GENERATOR if self.generator_markers else 0.0)
            + (self.W_BODY if self.body_markers else 0.0)
            + (self.W_HEADER if self.header_markers else 0.0)
        ) or 1.0


# ── Catálogo de plataformas ─────────────────────────────────────────────
# Cobertura inicial das plataformas mais recorrentes em municípios brasileiros.
# Ampliar este catálogo é o principal vetor de escala do coletor.
SIGNATURES: tuple[Signature, ...] = (
    Signature(
        name="Betha Cloud / Governo Transparente",
        vendor="Betha Sistemas",
        host_patterns=(r"betha\.cloud", r"betha\.com\.br", r"e-gov\.betha"),
        body_markers=("betha sistemas", "governo transparente", "betha cloud"),
        generator_markers=("betha",),
        known_data_paths=(
            "/api/transparencia",
            "/transparencia/api",
        ),
    ),
    Signature(
        name="Atende.Net (IPM)",
        vendor="IPM Sistemas",
        host_patterns=(r"atende\.net",),
        body_markers=("ipm sistemas", "atende.net", "!portaltransparencia"),
        generator_markers=("ipm", "atende"),
        known_data_paths=(
            "/?pg=transparencia",
        ),
    ),
    Signature(
        name="Portal Instar",
        vendor="Instar Sistemas",
        host_patterns=(r"instar\.com\.br",),
        body_markers=("instar", "instar sistemas"),
        generator_markers=("instar",),
        known_data_paths=(
            "/portaltransparencia",
        ),
    ),
    Signature(
        name="e-Cidade",
        vendor="e-Cidade (software livre) / DBSeller",
        host_patterns=(r"e-?cidade",),
        body_markers=("e-cidade", "dbseller"),
        generator_markers=("e-cidade",),
        known_data_paths=(
            "/transparencia/",
        ),
    ),
    Signature(
        name="Fiorilli (Cidade Transparente)",
        vendor="Fiorilli Software",
        host_patterns=(r"fiorilli",),
        body_markers=("fiorilli", "cidade transparente"),
        generator_markers=("fiorilli",),
    ),
    Signature(
        name="Equiplano / GOVBR",
        vendor="Governança Brasil / Equiplano",
        host_patterns=(r"equiplano", r"govbr\b", r"e-govbr"),
        body_markers=("equiplano", "governança brasil", "govbr"),
        generator_markers=("equiplano", "govbr"),
    ),
    Signature(
        name="Publicasoft / Grupo Publica",
        vendor="Grupo Publica",
        host_patterns=(r"publicasoft", r"grupopublica"),
        body_markers=("publicasoft", "grupo publica"),
        generator_markers=("publicasoft",),
    ),
    Signature(
        name="Portal CKAN (dados abertos)",
        vendor="CKAN (software livre)",
        host_patterns=(r"dados\.", r"ckan"),
        body_markers=("ckan", "data catalog", "/dataset/"),
        generator_markers=("ckan",),
        header_markers=("ckan",),
        known_data_paths=(
            "/api/3/action/package_list",
            "/api/3/action/package_search",
        ),
    ),
)


@dataclass
class Match:
    platform: str
    vendor: str
    confidence: float          # [0, 1]
    reasons: list[str] = field(default_factory=list)
    known_data_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "vendor": self.vendor,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "known_data_paths": self.known_data_paths,
        }


def _extract_generator(body_lower: str) -> str:
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)',
                  body_lower)
    return m.group(1) if m else ""


def detect(url: str, html: str, headers: dict | None = None) -> list[Match]:
    """
    Classifica o portal. Retorna todas as plataformas com confiança > 0,
    ordenadas da mais provável para a menos provável.
    """
    host = re.sub(r"^\w+://", "", url or "").split("/", 1)[0].lower()
    body_lower = (html or "").lower()
    generator = _extract_generator(body_lower)
    headers_blob = " ".join(
        f"{k}:{v}" for k, v in (headers or {}).items()
    ).lower()

    matches: list[Match] = []
    for sig in SIGNATURES:
        pts, reasons = sig.score(host, body_lower, generator, headers_blob)
        if pts <= 0:
            continue
        confidence = min(1.0, pts / sig.max_points())
        matches.append(Match(
            platform=sig.name,
            vendor=sig.vendor,
            confidence=confidence,
            reasons=reasons,
            known_data_paths=list(sig.known_data_paths),
        ))

    matches.sort(key=lambda m: m.confidence, reverse=True)
    return matches
