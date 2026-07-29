# Coletor Fiscalizaí

Prova de conceito do **coletor autônomo** de dados públicos de portais de
transparência municipais (LAI). Este módulo é o primeiro tijolo: dado o portal
de um município, ele **reconhece a plataforma** por trás do portal e **descobre
endpoints candidatos** de dados, gerando um relatório auditável.

## Por que não é um app de celular

A coleta é um serviço de **backend**, não um APK/WebView:

- Celular suspende trabalho em segundo plano; um coletor precisa rodar sozinho,
  no horário, sem tela aberta.
- WebView é sandbox de navegador — bate em CORS em portais de terceiros e não
  tem acesso confiável a disco/cron.
- O agente precisa de compute, chaves e orquestração — isso mora num worker.

O celular, no máximo, é um **painel** (o PWA na raiz deste repositório serve pra
isso). Este módulo roda na sua infra.

## A alavanca: plataforma, não cidade

Milhares de prefeituras rodam o **mesmo punhado de plataformas** (Betha, IPM
Atende.net, Instar, e-Cidade, Fiorilli, Equiplano/GOVBR, Publicasoft, CKAN…).
Em vez de raspar cada cidade do zero, o coletor:

1. **Fingerprint** — reconhece a plataforma (`fingerprint.py`).
2. **Adapter** — aplica a rota de coleta conhecida daquela plataforma.
3. **Modo descoberta** — só cai na exploração assistida por agente quando a
   plataforma é nova/incerta.

Cada plataforma nova no catálogo cobre, de uma vez, centenas de municípios.

## Componentes

| arquivo | papel |
| --- | --- |
| `fingerprint.py` | catálogo de assinaturas + `detect()` com confiança [0,1] |
| `discovery.py`   | varre o HTML e classifica endpoints candidatos |
| `report.py`      | monta o relatório (JSON + Markdown) com proveniência |
| `fetch.py`       | busca HTML de URL **ou** arquivo local (modo offline/CI) |
| `cli.py`         | `python -m coletor <alvo>` |

## Uso

```bash
pip install -r coletor/requirements.txt

# a partir de um HTML local (não precisa de rede)
python -m coletor coletor/tests/fixtures/betha.html --municipio "Exemplo/CE"

# ao vivo (exige egress liberado para o portal)
python -m coletor https://transparencia.cidade.uf.gov.br \
    --municipio "Cidade/UF" --json rel.json --md rel.md
```

## Saída

O relatório traz: plataforma reconhecida + confiança, **modo sugerido**
(`adapter-conhecido` / `adapter-provavel` / `descoberta`), lista de endpoints
candidatos (com o *porquê* de cada um), pistas de API e **proveniência**
(URL, timestamp, `sha256` do HTML) — sem proveniência, dado público não é
auditável.

## Testes

```bash
python -m pytest coletor/tests/ -q
```

Rodam offline, a partir das fixtures em `coletor/tests/fixtures/`.

## Limitação conhecida deste ambiente

O ambiente de desenvolvimento remoto tem **saída de rede bloqueada** para
portais gov.br (política de egress). Por isso toda a lógica é desenvolvida e
testada com fixtures locais. A coleta ao vivo (`--url`) roda na sua
infraestrutura ou em um ambiente com egress liberado.

## Próximos passos

1. Primeiro **adapter completo** de uma plataforma (descobrir → coletar →
   normalizar).
2. **Schema normalizado** comum (o alvo LAI) e o contrato da API pública.
3. **Registry** persistente de endpoints válidos + agendamento (cron/fila).
4. Respeito a `robots.txt` e limites de taxa na coleta ao vivo.
