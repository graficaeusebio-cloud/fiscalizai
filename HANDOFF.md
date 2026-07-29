# HANDOFF — Continuar o trabalho no VPS

> **Leia este arquivo primeiro.** Ele existe para que uma nova sessão (sua ou
> de um agente Claude Code rodando no VPS) retome o trabalho sem perder
> contexto. Foi escrito num ambiente sandbox **sem acesso de rede aos portais
> gov.br** — o VPS é justamente o que destrava a coleta ao vivo.

---

## 1. Estado atual em um parágrafo

O repositório `fiscalizai` tem (a) um **PWA** na raiz (`index.html`,
`manifest.json`, `sw.js`, ícones) — pronto para instalar no celular como painel;
e (b) um **coletor Python** em `coletor/` — prova de conceito que reconhece a
plataforma por trás de um portal de transparência municipal e descobre endpoints
candidatos de dados, gerando relatório auditável. 8 testes passando, offline.
Falta: rodar a coleta **ao vivo** (precisa de rede — é aqui que o VPS entra),
construir o primeiro **adapter completo**, definir o **schema LAI normalizado**
e a **API pública**.

Branch de trabalho: `claude/minimal-apk-testing-2klfva`.

---

## 2. Objetivo do projeto

Servir, via **API pública**, dados de transparência de prefeituras (a LAI exige
publicidade). O obstáculo real é a **heterogeneidade** dos portais municipais —
inviável de padronizar à mão, cidade por cidade.

### Decisão de arquitetura (importante)

A coleta é um **serviço de backend**, **não** um APK/WebView no celular:

- Celular suspende trabalho em segundo plano; coletor precisa rodar sozinho, no
  horário, sem tela aberta.
- WebView é sandbox de navegador — bate em CORS e não tem disco/cron confiável.
- O agente precisa de compute, chaves e orquestração → mora num worker/servidor.

O celular é, no máximo, um **painel** (o PWA já serve pra isso).

### A alavanca central: plataforma, não cidade

Milhares de prefeituras rodam o **mesmo punhado de plataformas** (Betha, IPM
Atende.net, Instar, e-Cidade, Fiorilli, Equiplano/GOVBR, Publicasoft, CKAN…).
Estratégia:

1. **Fingerprint** da plataforma;
2. **Adapter** conhecido daquela plataforma (reaproveitável em centenas de
   cidades de uma vez);
3. **Modo descoberta** (agente explora) só quando a plataforma é nova/incerta.

Cada plataforma nova no catálogo cobre muitos municípios de uma vez.

---

## 3. O que já existe no repositório

```
fiscalizai/
├── index.html, manifest.json, sw.js, icon-192.png, icon-512.png   # PWA (painel)
├── coletor/
│   ├── fingerprint.py   # catálogo de assinaturas + detect() → confiança [0,1]
│   ├── discovery.py     # varre HTML e classifica endpoints candidatos
│   ├── report.py        # relatório JSON + Markdown com proveniência
│   ├── fetch.py         # busca HTML de URL OU arquivo local (modo offline/CI)
│   ├── cli.py           # python -m coletor <alvo>
│   ├── requirements.txt
│   ├── README.md        # detalhes do módulo
│   └── tests/           # 8 testes offline + fixtures (betha, ckan, generico)
└── HANDOFF.md           # este arquivo
```

Plataformas já com assinatura em `fingerprint.py`: **Betha, IPM Atende.net,
Instar, e-Cidade, Fiorilli, Equiplano/GOVBR, Publicasoft, CKAN**.

---

## 4. Por que o VPS

Este sandbox de desenvolvimento tem **egress bloqueado** (só HTTPS via proxy com
allowlist; TCP cru e porta 22 bloqueados; `gov.br` responde 403). Consequências:

- Toda a lógica foi feita e testada com **fixtures locais**.
- A **coleta ao vivo não roda aqui** — roda no VPS, que tem rede aberta.
- Uma sessão Claude Code **daqui não consegue SSH** para o VPS (porta 22
  bloqueada). Por isso o caminho certo é **rodar o Claude Code no próprio VPS**,
  onde ele ganha shell + rede — e este arquivo é o ponto de retomada.

---

## 5. Primeiros passos no VPS

```bash
# 1. Clonar e entrar na branch de trabalho
git clone <url-do-repo> fiscalizai
cd fiscalizai
git checkout claude/minimal-apk-testing-2klfva

# 2. Ambiente Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r coletor/requirements.txt

# 3. Sanidade: rodar os testes (offline)
python -m pytest coletor/tests/ -q      # esperado: 8 passed

# 4. Primeira coleta AO VIVO (aqui o VPS faz o que o sandbox não fazia)
python -m coletor https://transparencia.SUACIDADE.uf.gov.br \
    --municipio "Cidade/UF" --json rel.json --md rel.md
cat rel.md
```

Se o relatório trouxer `platform.best_guess` com boa confiança, o município cai
num adapter conhecido. Se vier `mode: descoberta`, é plataforma nova — anotar a
URL e os sinais para virar uma assinatura nova em `fingerprint.py`.

---

## 6. Roadmap (ordem sugerida)

1. **Validar o fingerprint contra portais reais.** Rodar o CLI em 10–20
   municípios variados; ajustar/adicionar assinaturas em `fingerprint.py`
   conforme os relatórios. (Guardar os HTMLs como novas fixtures nos testes.)
2. **Primeiro adapter completo** de UMA plataforma comum (sugestão: Betha ou
   IPM, alto alcance): fluxo `descobrir → coletar → normalizar`.
3. **Schema LAI normalizado** — o formato-alvo único (despesas, receitas,
   licitações, folha, contratos…) para o qual todos os adapters convergem.
4. **Contrato da API pública** que serve esse schema.
5. **Registry** persistente de endpoints válidos + **agendamento** (cron/fila).
6. **Boas práticas de coleta cívica**: respeitar `robots.txt`, limites de taxa,
   e sempre gravar **proveniência** (já embutida no relatório: URL, timestamp,
   sha256 do HTML).

---

## 7. Decisões já tomadas (log)

| decisão | escolha |
| --- | --- |
| Onde roda o coletor | Backend/servidor (VPS), **não** APK/WebView |
| Stack | **Python** |
| Primeiro entregável | **Fingerprinter + relatório de descoberta** ✅ feito |
| Papel do celular | Painel (PWA), opcional |
| Estratégia de escala | Fingerprint de **plataforma**, não raspar por cidade |

## 8. Perguntas em aberto (decidir no VPS, com rede)

- Qual plataforma vira o **primeiro adapter** completo? (depende de qual cobre
  mais os municípios-alvo — validar com o fingerprint rodando ao vivo).
- Runtime de deploy: **Docker** ou **Python + systemd**? (o scaffold de deploy
  ainda não foi gerado — era o próximo passo antes deste handoff).
- Distro/versão do VPS (para o script de deploy).
- Lista inicial de municípios-alvo.

---

## 9. Se você for um agente Claude Code lendo isto no VPS

- Confirme a rede: `curl -sS -o /dev/null -w '%{http_code}\n' https://www.gov.br`
  (deve ser 200/3xx aqui, ao contrário do sandbox onde deu 403).
- Rode os testes antes de mexer (`python -m pytest coletor/tests/ -q`).
- Ao encontrar uma plataforma nova, adicione uma `Signature` em
  `fingerprint.py` **e** uma fixture + teste — o catálogo é o ativo principal.
- Preserve **proveniência** em tudo que coletar. Dado público sem proveniência
  não é auditável.
- Trabalhe na branch `claude/minimal-apk-testing-2klfva`; commit pequeno e
  descritivo; push só quando pedido/combinado.
