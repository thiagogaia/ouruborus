# Gaps: Ideia do Projeto vs Implementação Atual

> Análise comparando a visão declarada com o estado atual do Engram v4.

---

## Visão Declarada

1. **Gerar agentes iniciais de acordo com cada projeto**
2. **Cérebro para diminuir uso de tokens** — guardar código, documentações, etc.
3. **Carga inicial no cérebro** — commits, códigos, padrões criados pelo Engram (arquivos .md criados inicialmente, editados por IA para a realidade do projeto, adicionados ao cérebro)
4. **Sistema evolui e aprende** — pode criar agentes que ainda não existem

---

## GAP 1: Agentes por Projeto

### Estado Atual

| Aspecto | Hoje | Onde |
|---------|------|------|
| **Instalação** | 3 agents universais copiados do `core/` (architect, db-expert, domain-analyst) | `setup.sh` |
| **Sugestão** | `analyze_project.py` sugere os mesmos 3 (db-expert só se ORM/DB) | `core/genesis/scripts/analyze_project.py` |
| **Geração** | Genesis gera scaffold genérico com TODO; Claude deve customizar | `generate_component.py` |
| **Extras** | infra-expert, prompt-engineer em `extras/` — instalação manual | `install_extras.sh` |

### Gaps Identificados

| # | Gap | Impacto | Sugestão |
|---|-----|---------|----------|
| G1.1 | **Catálogo fixo** — Não há agents específicos por stack (auth-expert para NextAuth, k8s-expert para infra, redis-expert, etc.) | Projeto NextAuth não recebe agent de auth; projeto K8s não recebe agent de infra | Expandir `suggest_components()` com mapeamento stack→agents (auth, infra, cache, etc.) |
| G1.2 | **Agents não são gerados automaticamente** — init-engram apresenta plano; Claude gera sob aprovação. Não há "geração automática" de N agents por stack | Fluxo depende de intervenção manual | Opção de init-engram: `--auto-generate` que gera todos sugeridos sem prompts |
| G1.3 | **Scaffold genérico** — `generate_agent` produz conteúdo placeholder ("Você é um especialista em X"). Não usa contexto do projeto (ex: "NextAuth", "Prisma") | Claude precisa reescrever do zero | Templates de agent por tipo (db-expert-prisma.md.tmpl, auth-expert-nextauth.md.tmpl) |

---

## GAP 2: Cérebro para Tokens — Código e Documentação

### Estado Atual

| Conteúdo | O que o cérebro armazena | Fonte |
|----------|--------------------------|-------|
| **ADRs, Patterns, Domain, Experiences** | Conteúdo completo (extraído de .md) | `populate.py` |
| **Commits** | Subject + body + diff summary (símbolos add/mod/del, shape) | `populate.py` |
| **Estrutura de código** | Module, Class, Function — metadata (path, name, signature, docstring, linhas) | `populate.py` + `ast_parser.py` |
| **Código fonte** | ❌ Não armazenado | — |
| **Documentação raw** | `/ingest` via base-ingester ingere .md de pasta externa | Manual |

### Gaps Identificados

| # | Gap | Impacto | Sugestão |
|---|-----|---------|----------|
| G2.1 | **Código não é armazenado** — Brain guarda estrutura (assinaturas, docstrings), não trechos ou arquivos completos | Recall não retorna "como X está implementado"; economia de tokens limitada para código | Opção: `populate ast --include-body` para trechos relevantes (ex: primeiras N linhas) ou chunks por função |
| G2.2 | **Docs do projeto fora do fluxo inicial** — README, CONTRIBUTING, docs/ não são ingeridos no /init-engram | Dev precisa rodar `/ingest docs/` manualmente | Incluir `docs/` e `README.md` no populate inicial ou fase opcional do init-engram |
| G2.3 | **/ingest é manual** — base-ingester existe mas não faz parte do fluxo padrão | Documentação externa (API, runbooks) fica de fora | Documentar /ingest no workflow de onboarding; ou auto-sugerir no /init-engram |
| G2.4 | **Token economy não mensurada para código** — ENGRAM_TOKEN_ECONOMY.md mede knowledge .md vs recall; não mede "ler arquivo X vs recall de código" | Dificulta justificar investimento em armazenar código | Benchmark: recall "implementação de auth" vs ler auth.ts |

---

## GAP 3: Carga Inicial

### Estado Atual

Fluxo do `/init-engram`:
1. **Fase 4** — AI popula knowledge (.md) com análise do codebase
2. **Fase 5** — `populate.py all` lê ADR_LOG, DOMAIN, PATTERNS, EXPERIENCE e commits; AST para estrutura de código

### Gaps Identificados

| # | Gap | Impacto | Sugestão |
|---|-----|---------|----------|
| G3.1 | **Ordem OK** — Fluxo está correto: .md preenchidos → populate lê | — | Nenhum |
| G3.2 | **Padrões do template vs realidade** — Templates (nextjs-patterns.skill.tmpl) são instanciados; conteúdo é genérico até AI customizar | Inconsistência se AI não preencher bem | Validar que init-engram Phase 3 produziu conteúdo não-TODO antes de populate |
| G3.3 | **CURRENT_STATE.md genesis-only** — Após init, cérebro é fonte; mas populate não lê CURRENT_STATE | Estado inicial pode ir para brain em Phase 4 via add_memory; populate não precisa | Já coberto por init-engram Phase 4 (brain.add_memory para Estado Inicial) |

---

## GAP 4: Evolução e Criação de Agentes

### Estado Atual

| Mecanismo | Como funciona | Onde |
|-----------|---------------|------|
| **/create agent X** | Comando explícito; Genesis gera scaffold | `core/commands/create.md` |
| **Orquestração runtime** | Claude cria agent quando tarefa exige expertise não coberta | `orchestration-protocol.md` |
| **Evolution** | track_usage, co_activation, stale check | `engram-evolution` |
| **Sugestão de novo componente** | "Padrão recorrente sem skill" → propor skill | `engram-evolution/SKILL.md` |

### Gaps Identificados

| # | Gap | Impacto | Sugestão |
|---|-----|---------|----------|
| G4.1 | **Evolution foca em skills** — Sugestões de "criar skill" quando padrão repetido; não há "criar agent X porque precisamos de expertise Y com frequência" | Agentes evoluem só por orquestração reativa (tarefa pede) | Adicionar ao Evolution: "Agent usage pattern" — se db-expert é muito usado e auth não existe, sugerir agent auth |
| G4.2 | **Não há detector de "precisamos de agent X"** — Co-ativação detecta skills usados juntos; não detecta "tarefas que falharam por falta de expertise" | Sistema não aprende proativamente quais agentes faltam | Inferir de recall: "quantas vezes buscamos temas de auth e não temos agent auth?" |
| G4.3 | **Agents criados em runtime não entram no catálogo** | Agent `auth-migration-expert` criado em sessão fica em .claude/agents/ mas não é sugerido para projetos similares | Global memory (~/.engram/) permite import; mas não há "library de agents por stack" |

---

## Resumo Executivo

| Ideia | Status | Gap Principal |
|-------|--------|---------------|
| **Agentes por projeto** | Parcial | Catálogo fixo (3); não gera agents específicos de stack |
| **Cérebro para tokens** | Parcial | Código real não armazenado; docs só via /ingest manual |
| **Carga inicial** | OK | Fluxo .md → populate correto |
| **Evolução e novos agentes** | Parcial | Criação runtime existe; Evolution não propõe agents |

### Priorização Sugerida

1. **Alto** — G1.1 (expandir sugestão de agents por stack)
2. **Alto** — G2.2 (incluir docs/ no init ou sugerir)
3. **Médio** — G4.1 (Evolution sugerir agents)
4. **Médio** — G1.3 (templates de agent por stack)
5. **Baixo** — G2.1 (armazenar código) — complexo, impacto a validar
