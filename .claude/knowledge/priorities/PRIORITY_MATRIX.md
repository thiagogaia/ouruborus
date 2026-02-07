# Priority Matrix
> Ultima atualizacao: 2026-02-07 (bump v3→v4)
> ICE = (Impacto x Confianca) / Esforco - todos 1-10

## Ativas

| # | Tarefa | I | C | E | ICE | Status |
|---|--------|---|---|---|-----|--------|
| — | Nenhuma tarefa ativa | — | — | — | — | — |

## Backlog

| # | Tarefa | I | C | E | ICE | Notas |
|---|--------|---|---|---|-----|-------|
| 10 | Métricas de uso agregadas | 4 | 5 | 7 | 2.9 | Futuro |

## Cemitério

| Tarefa | Motivo | Data |
|--------|--------|------|
| Instalar Engram | ✅ Concluído | 2026-02-03 |
| Completar /init-engram | ✅ Concluído | 2026-02-03 |
| Popular knowledge files | ✅ Concluído | 2026-02-03 |
| Gerar skill python-scripts | ✅ Concluído | 2026-02-03 |
| Rodar /learn inicial | ✅ Concluído | 2026-02-03 |
| Commit inicial com 61 arquivos | ✅ Concluído | 2026-02-03 |
| Implementar cérebro organizacional | ✅ Concluído | 2026-02-03 |
| Popular cérebro com ADRs/patterns/commits | ✅ Concluído | 2026-02-03 |
| Integrar brain no /learn e /init-engram | ✅ Concluído | 2026-02-03 |
| Gerar embeddings para busca semântica | ✅ Concluído | 2026-02-03 |
| Adicionar .gitignore para __pycache__ | ✅ Concluído | 2026-02-03 |
| Instalar seeds faltantes (5 de 6) | ✅ Concluído | 2026-02-03 |
| Adicionar diagrama metacircular à doc | ✅ Concluído | 2026-02-03 |
| Upgrade para v3.0.0 | ✅ Concluido | 2026-02-03 |
| Analisar commit cb64fd73 via /learn | ✅ Concluido | 2026-02-04 |
| Extrair padroes PAT-020/021/022 | ✅ Concluido | 2026-02-04 |
| Documentar EXP-016 (major upgrade) | ✅ Concluido | 2026-02-04 |
| ANALISE_IMPLEMENTA.md — 9/9 itens | ✅ Concluído | 2026-02-05 |
| Fix detecção infra analyze_project.py | ✅ Concluído | 2026-02-05 |
| Remover execution-pipeline (órfão) | ✅ Concluído | 2026-02-05 |
| Remover microservices-navigator (fora escopo) | ✅ Concluído | 2026-02-05 |
| Remover SERVICE_MAP.md.tmpl (órfão) | ✅ Concluído | 2026-02-05 |
| Testar em projeto real Next.js | ✅ Já em uso | 2026-02-05 |
| Testar em projeto real Python | ✅ Já em uso | 2026-02-05 |
| Integrar /status com cérebro | ❌ Desnecessário — CURRENT_STATE.md já cobre, /doctor faz diagnóstico | 2026-02-05 |
| Documentar exemplos de uso | ✅ Concluído — LIFECYCLE_GUIDE.md | 2026-02-05 |
| Integrar sleep no workflow Claude | ✅ Concluído — CLAUDE.md atualizado | 2026-02-05 |
| Gerar embeddings completos | ✅ Concluído — 167/167 nós | 2026-02-05 |
| Melhorar REFERENCES no sleep | ✅ Concluído — 3→30 refs via canonical .md parsing | 2026-02-05 |
| CO_ACCESSED no consolidate() | ✅ Concluído — cria edges entre nós co-acessados | 2026-02-05 |
| populate_experiences() | ✅ Concluído — EXP nodes no grafo | 2026-02-05 |
| Rewrite do_update() setup.sh | ✅ Concluído — 8 gaps corrigidos | 2026-02-06 |
| Redesign SQLite schema v2 | ✅ Concluído — hybrid property graph, 212 nós migrados | 2026-02-06 |
| Remover JSON fallback, SQLite v2 único backend | ✅ Concluído — brain_sqlite.py sole backend | 2026-02-06 |
| 195 unit tests para brain scripts | ✅ Concluído — 206/206 passando | 2026-02-06 |
| CURRENT_STATE genesis-only + temporal recall | ✅ Concluído — 30+ arquivos, 0 tokens/sessão | 2026-02-06 |
| Knowledge files genesis-only (ADR, PAT, DOMAIN, EXP) | ✅ Concluído — 30+ arquivos, brain é fonte primária | 2026-02-06 |
| Fix ghost brain.db path bug | ✅ Concluído — Path(__file__).parent em 4 scripts | 2026-02-06 |
| Fix 5+1 parser bugs populate.py | ✅ Concluído — 227→331 nós, 0 dados perdidos | 2026-02-06 |
| Migrar vector store para ChromaDB | ✅ Concluído — HNSW O(log n), fallback npz, 227 tests | 2026-02-06 |
| Bump Engram v3→v4 | ✅ Concluído — 11 arquivos, ADR-023, Milestone v4.0.0 | 2026-02-07 |
| Adicionar template Laravel | ✅ Já existia — laravel-patterns.skill.tmpl criado em 2026-02-04 | 2026-02-07 |
| Template Angular | ✅ Concluído — angular-patterns.skill.tmpl | 2026-02-07 |
| Template Ruby on Rails | ✅ Concluído — rails-patterns.skill.tmpl + detecção | 2026-02-07 |
| CI/CD para validar schemas | ✅ Concluído — .github/workflows/validate.yml | 2026-02-07 |

## Como Priorizar

### ICE Score
- **Impacto (I)**: Quanto valor entrega se completado? (1-10)
- **Confiança (C)**: Quão certo estou que funciona? (1-10)
- **Esforço (E)**: Quanto trabalho requer? (1-10, onde 10 = muito esforço)
- **ICE** = (I × C) / E — maior = mais prioritário

### Status
- 🔵 pendente — não iniciado
- 🟡 em progresso — trabalho ativo
- 🟢 concluído — feito
- ⚫ bloqueado — impedido por dependência externa
