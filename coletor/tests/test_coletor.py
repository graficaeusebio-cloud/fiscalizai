"""Testes do coletor. Rodam offline, a partir das fixtures."""

import os

from coletor import build_report, detect, discover, to_markdown
from coletor.fetch import fetch

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


# ── fingerprint ─────────────────────────────────────────────────────────

def test_detecta_betha_com_alta_confianca():
    html = _load("betha.html")
    matches = detect("https://transparencia.exemplo.betha.cloud/", html)
    assert matches, "deveria reconhecer ao menos uma plataforma"
    best = matches[0]
    assert "Betha" in best.platform
    assert best.confidence >= 0.7  # host + generator + corpo


def test_detecta_ckan_pelo_generator_e_host():
    html = _load("ckan.html")
    matches = detect("https://dados.exemplo.gov.br/", html)
    assert matches and "CKAN" in matches[0].platform


def test_portal_generico_nao_casa_plataforma():
    html = _load("generico.html")
    matches = detect("https://transparencia.exemplo.gov.br/", html)
    assert matches == []  # nenhuma assinatura conhecida


# ── discovery ───────────────────────────────────────────────────────────

def test_descobre_csv_e_api_no_betha():
    html = _load("betha.html")
    r = discover("https://exemplo.betha.cloud/", html)
    kinds = {e.kind for e in r.endpoints}
    assert "csv" in kinds
    assert "pdf" in kinds
    urls = " ".join(e.url for e in r.endpoints)
    assert "despesas-2025.csv" in urls
    # csv deve vir antes de pdf pela priorização
    assert r.endpoints[0].kind != "pdf"


def test_descobre_pista_ckan_em_script():
    html = _load("ckan.html")
    r = discover("https://dados.exemplo.gov.br/", html)
    assert "ckan" in r.api_hits


def test_ignora_links_nao_dados():
    html = _load("generico.html")
    r = discover("https://exemplo.gov.br/", html)
    urls = " ".join(e.url for e in r.endpoints)
    assert "javascript" not in urls
    assert "/contato" not in urls          # link comum é ignorado
    assert "folha-pagamento.xlsx" in urls  # planilha é capturada
    assert "/dados-abertos" in urls        # pista por palavra-chave


# ── report + fetch ──────────────────────────────────────────────────────

def test_fetch_local_e_report_completo():
    caminho = os.path.join(FIX, "betha.html")
    f = fetch(caminho)
    assert f.from_cache and f.html
    report = build_report(
        municipality="Exemplo/CE",
        url=f.url, html=f.html,
        matches=detect(f.url, f.html, f.headers),
        discovery=discover(f.url, f.html),
    )
    assert report["municipality"] == "Exemplo/CE"
    assert report["provenance"]["html_sha256"]
    assert report["platform"]["mode"] in {
        "descoberta", "adapter-provavel", "adapter-conhecido"}
    md = to_markdown(report)
    assert "Relatório de descoberta" in md
    assert "Endpoints candidatos" in md


def test_modo_descoberta_para_portal_desconhecido():
    html = _load("generico.html")
    report = build_report(
        municipality=None, url="https://x.gov.br/", html=html,
        matches=detect("https://x.gov.br/", html),
        discovery=discover("https://x.gov.br/", html),
    )
    assert report["platform"]["mode"] == "descoberta"
