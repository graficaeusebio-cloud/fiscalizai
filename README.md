# 🔍 Fiscalizaí — Emendas Parlamentares

PWA para acompanhamento transparente de emendas parlamentares do orçamento federal brasileiro.

## Funcionalidades

- **Busca por parlamentar** — informe o código do autor (ex: `4028` para Junior Mano)
- **Filtro por período e função orçamentária**
- **Filtros rápidos locais**: emendas com valor empenhado, pago, sem pagamento, do Ceará
- **Armazenamento IndexedDB** — salve emendas de interesse para consulta offline
- **Exportação CSV** — exporte os resultados filtrados
- **Modo offline** — dados salvos ficam disponíveis sem conexão
- **Indicadores visuais de execução** — barras empenhado → liquidado → pago

## Fonte dos Dados

API pública do Portal da Transparência do Governo Federal:
```
https://portaldatransparencia.gov.br/emendas/consulta/resultado
```

## Deploy

### Opção 1: Qualquer hospedagem estática (recomendado)

Faça upload dos 3 arquivos para uma pasta pública no servidor:
- `index.html`
- `manifest.json`
- `sw.js`

**Requisito:** O servidor deve servir os arquivos via **HTTPS** para que o Service Worker funcione.

### Opção 2: GitHub Pages

```bash
git init
git add .
git commit -m "Fiscalizaí v1.0"
git remote add origin https://github.com/SEU_USER/fiscalizai.git
git push -u origin main
# Ative GitHub Pages nas configurações do repositório
```

### Opção 3: Netlify / Vercel (arraste a pasta)

Arraste a pasta `fiscalizai/` para o painel do Netlify ou Vercel.

## Ícones (opcional)

Gere ícones em `icon-192.png` e `icon-512.png` com a logo do app.
Você pode usar: https://realfavicongenerator.net/

## CORS

A API do Portal da Transparência pode retornar erro de CORS dependendo do ambiente.
O app tenta automaticamente um proxy CORS como fallback (`corsproxy.io`).
Para uso em produção, considere configurar um proxy próprio em PHP/Node no mesmo domínio.

## Tecnologias

- HTML5 / CSS3 / Vanilla JS (zero dependências)
- IndexedDB para persistência local
- Service Worker para cache e offline
- Web App Manifest para instalação como PWA

---
Dados públicos — Fonte: portaldatransparencia.gov.br
