# Estado Atual do Projeto
> Ultima atualizacao: 2026-02-06 (/learn sessao 8 - do_update rewrite)

## Status Geral
- **Fase**: v3.0.0 — Engram com Cérebro Organizacional (brain-primary, .md sincronizados)
- **Saúde**: 🟢 Healthy (Health Score 0.95, Doctor 96%)
- **Cérebro**: 214 nós, 506+ arestas, 202 embeddings — **fonte primária**
- **Próximo Marco**: Testes unitários + observar loop de auto-alimentação em ação

## Identidade
**Engram v3** — Sistema metacircular de memória persistente para Claude Code.
O sistema que gera a si mesmo (ouroboros), agora com cérebro organizacional.

## Arquitetura Core

### Diretórios Principais
```
engram/
├── core/                          # DNA do sistema (copiado para projetos)
│   ├── schemas/                   # Definições formais de componentes
│   ├── genesis/                   # Motor de auto-geração (SKILL.md + scripts/)
│   ├── evolution/                 # Motor de evolução (SKILL.md + scripts/)
│   ├── seeds/                     # Skills universais
│   ├── agents/                    # Templates de agents
│   └── commands/                  # Slash commands
├── templates/                     # Templates de stacks (nextjs, django, etc)
│   ├── knowledge/                 # Templates de knowledge files
│   └── stacks/                    # Templates por framework
├── extras/                        # Skills/agents opcionais
├── setup.sh                       # Instalador principal
└── docs/                          # Documentação
```

### Fluxo de Dados (Brain-Only)
```
setup.sh → instala DNA (schemas) + genesis + evolution + seeds + brain
              ↓
/init-engram → genesis analisa projeto → popula cérebro → gera skills
              ↓
/recall → busca semântica → reforça memórias → PERSISTE (brain.save())
              ↓
/learn → brain.add_memory() direto → sleep in-memory → embeddings ricos
              ↓
genesis → evolui componentes → ciclo recomeça
```

### Ciclo Metacircular Completo
```
                    ┌─────────────────────────────┐
                    │       ENGRAM-GENESIS        │
                    │   (Motor de Auto-Geração)   │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
   ┌─────────┐              ┌─────────────┐            ┌──────────┐
   │ /create │              │ /init-engram │            │ Gera a   │
   │         │              │              │            │ si mesmo │
   └────┬────┘              └──────┬──────┘            └────┬─────┘
        │                          │                        │
        ▼                          ▼                        ▼
   Gera skill,              Popular brain,          Capacidade
   agent ou                 gerar skills,           metacircular
   command                  knowledge
        │                          │                        │
        └──────────────────────────┼────────────────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │      ENGRAM-EVOLUTION       │
                    │    (Motor de Evolução)      │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
   ┌─────────┐              ┌──────────┐              ┌──────────┐
   │ /learn  │              │ /doctor  │              │ Propõe   │
   │         │              │          │              │ melhorias│
   └────┬────┘              └────┬─────┘              └────┬─────┘
        │                        │                         │
        ▼                        ▼                         ▼
   Rastreia uso,          Verifica saúde,          Merge, split,
   co-ativações,          inconsistências          archive
   cria memórias
        │                        │                         │
        └────────────────────────┴─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │         RETROALIMENTA       │
                    │         ENGRAM-GENESIS      │
                    └─────────────────────────────┘
```

## Componentes Instalados

### Skills Core (2)
| Nome | Função | Scripts |
|------|--------|---------|
| engram-genesis | Motor de auto-geração | analyze_project.py, generate_component.py, validate.py, register.py, compose.py, migrate_backup.py |
| engram-evolution | Motor de evolução | track_usage.py, doctor.py, archive.py, curriculum.py, co_activation.py, global_memory.py |

### Seeds (6 skills universais)
| Nome | Função |
|------|--------|
| project-analyzer | Análise profunda de codebase |
| knowledge-manager | Gerencia feedback loop |
| domain-expert | Descoberta de regras de negócio |
| priority-engine | Priorização com ICE Score |
| code-reviewer | Code review em 4 camadas |
| engram-factory | Orquestração runtime |

### Agents (3)
| Nome | Especialidade |
|------|---------------|
| architect | Decisões arquiteturais, ADRs |
| db-expert | Schema, queries, migrations |
| domain-analyst | Regras de negócio, glossário |

### Commands (15)
/init-engram, /status, /plan, /commit, /review, /priorities, /learn, /create, /spawn, /doctor, /curriculum, /export, /import, /recall, **/domain**

## O Que Mudou Recentemente
- [2026-02-06] **do_update() reescrito (commit 313c4dd)**: 8 gaps corrigidos — brain scripts, backup timestampado, comparação de versão (VERSION source vs local), manifest update, seed warnings, --force, --regenerate. batch-setup.sh usa --force em vez de pipe hack. [[ADR-016]], [[PAT-039]], [[PAT-040]], [[EXP-025]] | Impacto: ALTO
- [2026-02-06] **CHANGELOG.md + /commit auto-update (commit 9d7b5e3)**: Changelog gerado e atualizado automaticamente em cada /commit | Impacto: MÉDIO
- [2026-02-06] **VERSION como fonte da verdade (commit 3d7905a)**: .engram-version lê de VERSION, não hardcoded | Impacto: MÉDIO
- [2026-02-05] **Brain-Primary com .md Sincronizados (commits 2500005, 05ac19c)**: Filosofia mudou de brain-only para brain-primary. Cérebro é fonte primária, .md mantidos em sincronia como espelho legível. LIFECYCLE_GUIDE, CLAUDE.md, learn.md alinhados. [[ADR-015]], [[PAT-038]], [[EXP-024]] | Impacto: CRÍTICO
- [2026-02-05] **Brain-Only Self-Feeding Architecture (commit b33fd9c)**: Conteúdo in-graph (props.content), recall persiste reforço, sleep zero disk I/O, embeddings com content[:1000]. 184 nós migrados. | Impacto: CRÍTICO
- [2026-02-05] **REFERENCES fix + CO_ACCESSED + EXP nodes (commit e39c7f5)**: sleep.py lê .md canônicos para cross-refs (REFERENCES: 3→30). consolidate() cria CO_ACCESSED edges. populate_experiences() cria nós EXP. pat_id nos patterns. Health: 0.79→0.89. | Impacto: CRÍTICO
- [2026-02-05] **LIFECYCLE_GUIDE.md criado**: Guia completo do ciclo de vida (instalar → trabalhar → aprender → evoluir → dormir). Documenta relação .md ↔ cérebro. | Impacto: ALTO
- [2026-02-05] **CLAUDE.md como fonte primária (commit d5d40ce)**: Cérebro promovido a consulta primária, .md como fallback. Push de 4 commits ao origin. | Impacto: ALTO
- [2026-02-05] **Ciclo de Sono do Cérebro (commit 4ea39bc)**: sleep.py com 5 fases (dedup/connect/relate/themes/calibrate). IDs determinísticos, upsert, _resolve_link corrigido, auto-ativação de venv. De 0 para 68 arestas semânticas, 134 duplicatas removidas. [[ADR-014]], [[PAT-036]], [[EXP-022]] | Impacto: CRÍTICO
- [2026-02-05] **Detecção de infra (commit c5b8efa)**: analyze_project.py detecta CI/CD, K8s, ArgoCD, Terraform + sugere devops-patterns | Impacto: ALTO
- [2026-02-05] **Remoção de 3 órfãos**: execution-pipeline, microservices-navigator, SERVICE_MAP.md.tmpl — não participavam do ciclo ouroboros | Impacto: MÉDIO
- [2026-02-05] **ANALISE_IMPLEMENTA.md encerrada**: 9/9 itens implementados, análise revelou 4 gaps, 3 componentes removidos por falta de integração | Impacto: ALTO
- [2026-02-04] **ADR-012 + PAT-033 + EXP-020**: Separação setup.sh / batch-setup.sh (SRP) | Impacto: ALTO
- [2026-02-04] **README corrigido (commit c7a67be)**: Seeds 8→6, batch docs, /domain, CLI split | Impacto: MÉDIO
- [2026-02-04] **setup.sh revertido (commit bbcf725)**: 958→783 linhas, batch extraído | Impacto: ALTO
- [2026-02-04] **batch-setup.sh criado**: 177 linhas, wrapper para múltiplos projetos | Impacto: MÉDIO
- [2026-02-04] **Embeddings regenerados**: 134/134 nós com vetores (busca semântica OK) | Impacto: MÉDIO
- [2026-02-04] **cognitive.py verificado**: health, consolidate, decay — todos funcionais | Impacto: BAIXO
- [2026-02-04] **/domain command criado (commit bfc9ef1)**: Command para análise de domínio + instrução proativa no CLAUDE.md | Impacto: ALTO
- [2026-02-04] **CLAUDE.md expandido**: Seção "Quando Usar Domain-Expert Automaticamente" com 6 triggers | Impacto: ALTO
- [2026-02-04] **domain-expert ativado**: Primeira ativação do skill (sessão de análise) | Impacto: MÉDIO
- [2026-02-04] **/learn manutenção (commit 53c9fab)**: Cérebro expandido para 127 nós, 204 arestas | Impacto: BAIXO
- [2026-02-04] **README atualizado para v3**: Documentação do cérebro organizacional + badges | Impacto: MÉDIO
- [2026-02-04] **Logo adicionado**: logo.svg com design ouroboros | Impacto: BAIXO
- [2026-02-04] **commit bbcc8777 analisado (fundacional)**: Commit inicial do repositório com DNA conceitual completo | Impacto: CRÍTICO
- [2026-02-04] **ADR-000 criado**: Decisão de inspiração arquitetural (Voyager + DGM + BOSS) | Impacto: ALTO
- [2026-02-04] **PAT-028/029/030/031**: Padrões fundacionais extraídos (análise de mercado, templates, documentação, extras vs core) | Impacto: ALTO
- [2026-02-04] **Glossário expandido**: 8 novos termos (Voyager, DGM, BOSS, Skill Library, Curriculum, etc) | Impacto: MÉDIO
- [2026-02-04] **EXP-019**: Experiência de análise de commit fundacional documentada | Impacto: MÉDIO
- [2026-02-04] **commit 5db29c67 analisado (/recall)**: Interface de consulta ao cerebro organizacional | Impacto: ALTO
- [2026-02-04] **recall.py**: Busca semantica + spreading activation + fallback gracioso (228 linhas) | Impacto: ALTO
- [2026-02-04] **/recall command**: .claude/commands/recall.md + core/commands/recall.md (156 linhas cada) | Impacto: MEDIO
- [2026-02-04] **PAT-023/024/025/026/027**: Padroes de interface de busca extraidos | Impacto: MEDIO
- [2026-02-04] **CLAUDE.md atualizado**: Instrucoes de quando usar /recall automaticamente | Impacto: ALTO
- [2026-02-04] **commit cb64fd73 analisado (v3.0.0)**: Major upgrade com cerebro organizacional completo | Impacto: CRITICO
- [2026-02-04] **Seeds completos**: 5 seeds adicionados (knowledge-manager, domain-expert, priority-engine, code-reviewer, engram-factory) | Impacto: ALTO
- [2026-02-04] **PAT-020/021/022**: Padroes de major upgrade, seeds universais, cognitive log extraidos | Impacto: MEDIO
- [2026-02-04] **Cerebro v3**: 68 nos, 106 arestas, 61 embeddings, health 100%, hubs: person-engram (49), domain-frontend (29) | Impacto: CRITICO
- [2026-02-04] **commit 6d7c3077**: Conceito "Modelo de Orquestração Sequencial" documentado | Impacto: ALTO
- [2026-02-04] **Co-ativação detectada**: engram-evolution + project-analyzer (3 sessões, 50%) | Impacto: MÉDIO
- [2026-02-04] **commit 5da6535c analisado**: ADR-008/009/010/011 extraídos - Arquitetura v3.0 Git-Native | Impacto: CRÍTICO
- [2026-02-04] **Cérebro atualizado**: 93 nós, 145 arestas (conceitos: Git-Native Architecture, Wikilinks Pattern) | Impacto: ALTO
- [2026-02-04] **setup.sh**: Auto-instalação de python3-venv em Debian/Ubuntu (commit 367a4c1) | Impacto: MÉDIO
- [2026-02-04] **[[PAT-015]]**: Padrão de auto-instalação de dependências do sistema | Impacto: MÉDIO
- [2026-02-04] **Cérebro expandido**: 77 nós, 119 arestas (+5 commits processados) | Impacto: MÉDIO
- [2026-02-04] **PAT-016**: Padrão de Commit de Documentação Arquitetural extraído do commit 7f7f221 | Impacto: MÉDIO
- [2026-02-03] **populate.py**: Script para popular cérebro com ADRs, domain, patterns, commits | Impacto: ALTO
- [2026-02-03] **Cérebro populado**: 61 nós, 97 arestas (11 ADRs, 27 conceitos, 11 patterns, 5 commits) | Impacto: CRÍTICO

## Sugestões Evolutivas Pendentes
| Tipo | Descrição | Prioridade |
|------|-----------|------------|
| Composição | engram-evolution + project-analyzer (37% co-ativação) | 🟡 Média |
| Stale | 8 componentes nunca usados - avaliar necessidade | 🟢 Baixa |
| Observar | CO_ACCESSED edges — serão criadas conforme /recall for usado | 🟢 Info |
- [2026-02-03] **/learn integrado**: Fase 4 adicionada para criar memórias automaticamente | Impacto: ALTO
- [2026-02-03] **maintain.sh**: Script de manutenção para cron/manual | Impacto: MÉDIO
- [2026-02-03] **[[ADR-011]]**: Arquitetura de Cérebro Organizacional implementada | Impacto: CRÍTICO
- [2026-02-03] **brain.py**: Grafo NetworkX com spreading activation, decay, consolidation | Impacto: CRÍTICO
- [2026-02-03] **embeddings.py**: Busca semântica com sentence-transformers/OpenAI | Impacto: ALTO
- [2026-02-03] **cognitive.py**: Processos cognitivos (consolidate, decay, archive) | Impacto: ALTO

## Dívidas Técnicas
| Item | Severidade | Descrição |
|------|------------|-----------|
| DT-001 | 🟡 Baixa | Falta coverage de testes nos scripts Python |
| DT-002 | 🟡 Baixa | Templates de stack incompletos (só 7 frameworks) |
| DT-003 | 🟢 Info | Documentação poderia ter mais exemplos |

## Bloqueios Conhecidos
Nenhum bloqueio ativo.

## Métricas de Uso (acumulado)
| Componente | Ativações | Status |
|------------|-----------|--------|
| engram-genesis | 5 | 🟢 Ativo |
| engram-evolution | 4 | 🟢 Ativo |
| python-scripts | 1 | 🟢 Novo |
| project-analyzer | 3 | 🟢 Ativo |
| knowledge-manager | 0 | 🟡 Stale (seed) |
| domain-expert | 1 | 🟢 Ativo |
| priority-engine | 0 | 🟡 Stale (seed) |
| code-reviewer | 0 | 🟡 Stale (seed) |
| engram-factory | 0 | 🟡 Stale (seed) |
| architect | 0 | 🟡 Stale (core) |
| db-expert | 0 | 🟡 Stale (core) |
| domain-analyst | 0 | 🟡 Stale (core) |

### Co-ativações Detectadas
- **engram-evolution + project-analyzer**: 3 sessões (37%) → Candidato a composição

## Contexto Para Próxima Sessão

### Cérebro Organizacional (Brain-Only)

Arquitetura: [[ADR-011]] (original) + [[ADR-015]] (brain-only). Fonte única de verdade auto-alimentada.

**Estrutura:**
```
.claude/
├── brain/                    ← FONTE ÚNICA DE VERDADE
│   ├── brain.py             ← Núcleo (NetworkX + content in-graph)
│   ├── recall.py            ← Busca + persistência de reforço
│   ├── sleep.py             ← Consolidação semântica (in-memory)
│   ├── embeddings.py        ← Vetores com content[:1000]
│   ├── populate.py          ← Commits (refresh) + migrate (one-time)
│   ├── cognitive.py         ← Health, consolidate, decay
│   └── graph.json           ← Grafo com conteúdo completo
│
├── knowledge/context/        ← BOOT FILES (apenas 2)
│   └── CURRENT_STATE.md     ← Contexto rápido para iniciar sessão
├── knowledge/priorities/
│   └── PRIORITY_MATRIX.md   ← Prioridades
│
├── memory/                   ← LEGADO (conteúdo migrado para graph.json)
└── archive/                  ← Memórias arquivadas
```

**Funcionalidades Implementadas:**
- ✅ Grafo com nós tipados (labels) e arestas tipadas (REFERENCES, AUTHORED_BY, etc)
- ✅ Estado de memória (strength, decay_rate, access_count)
- ✅ Spreading activation para busca
- ✅ Curva de esquecimento (Ebbinghaus)
- ✅ Consolidação de conexões
- ✅ Embeddings para busca semântica
- ✅ **Ciclo de Sono** (sleep.py): 5 fases de consolidação semântica
- ✅ **IDs determinísticos**: md5(title|labels) — repopular é idempotente
- ✅ **Auto-ativação de venv**: numpy/networkx sempre disponíveis
- ✅ **8 tipos de aresta semântica**: REFERENCES, INFORMED_BY, APPLIES, RELATED_TO, SAME_SCOPE, MODIFIES_SAME, BELONGS_TO_THEME, CLUSTERED_IN
- ✅ **Brain-Only Architecture**: Conteúdo in-graph, recall persiste reforço, sleep zero disk I/O
- ✅ **Self-Feeding Loop**: recall→reinforce→save | add_memory→sleep→embeddings

**Uso:**
```bash
# Instalar dependências
pip install networkx numpy sentence-transformers

# Estatísticas
python .claude/brain/brain.py stats

# Busca
python .claude/brain/brain.py search "autenticação"

# Processos cognitivos
python .claude/brain/cognitive.py health
python .claude/brain/cognitive.py decay
python .claude/brain/cognitive.py consolidate

# Embeddings
python .claude/brain/embeddings.py build
python .claude/brain/embeddings.py search "como resolver bugs"
```

### Próximos Passos
1. [x] Popular o cérebro com conhecimento existente (ADRs, patterns) ✅
2. [x] Integrar brain.py no /learn para criar memórias automaticamente ✅
3. [ ] Integrar no /status para mostrar estado do cérebro
4. [x] Configurar manutenção (maintain.sh + documentação cron/CI) ✅
5. [x] Instalar dependências no venv: `.claude/brain/.venv` ✅
6. [x] Gerar embeddings (61 vetores) e testar busca semântica ✅
7. [x] Integrar no setup.sh e /init-engram ✅
8. [x] Documentar fluxo de uso para equipe ✅ (LIFECYCLE_GUIDE.md)
9. [x] Ciclo de Sono — consolidação semântica com 5 fases ✅
10. [x] Gerar embeddings para todos os nós ✅ (167/167)
11. [x] Integrar sleep no workflow do Claude — cérebro como fonte primária ✅ (CLAUDE.md atualizado)
12. [x] Brain-Only Self-Feeding Architecture ✅ (ADR-015, 184 nós migrados)
