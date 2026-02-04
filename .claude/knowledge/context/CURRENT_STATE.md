# Estado Atual do Projeto
> Última atualização: 2026-02-03 (/learn após implementação do cérebro)

## Status Geral
- **Fase**: v3.0.0 — Engram com Cérebro Organizacional
- **Saúde**: 🟢 Saudável (Health Score 100%)
- **Próximo Marco**: Testar reinstalação em projeto existente

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

### Fluxo de Dados
```
setup.sh → instala DNA (schemas) + genesis + evolution + seeds + brain
              ↓
/init-engram → genesis analisa projeto → popula cérebro → gera skills
              ↓
/learn → evolution rastreia uso → cria memórias → propõe melhorias
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

### Commands (13)
/init-engram, /status, /plan, /commit, /review, /priorities, /learn, /create, /spawn, /doctor, /curriculum, /export, /import

## O Que Mudou Recentemente
- [2026-02-03] **populate.py**: Script para popular cérebro com ADRs, domain, patterns, commits | Impacto: ALTO
- [2026-02-03] **Cérebro populado**: 61 nós, 97 arestas (11 ADRs, 27 conceitos, 11 patterns, 5 commits) | Impacto: CRÍTICO
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
| engram-genesis | 2 | 🟢 Ativo |
| engram-evolution | 3 | 🟢 Ativo |
| python-scripts | 1 | 🟢 Novo |
| project-analyzer | 2 | 🟢 Ativo |
| architect | 0 | ⚪ Não usado |
| db-expert | 0 | ⚪ Não usado |
| domain-analyst | 0 | ⚪ Não usado |

## Contexto Para Próxima Sessão

### Cérebro Organizacional Implementado

Arquitetura definida em [[ADR-011]]. Sistema de memória com grafo de conhecimento real.

**Estrutura Implementada:**
```
.claude/
├── brain/                    ← GRAFO E PROCESSOS
│   ├── brain.py             ← Núcleo (NetworkX + operações)
│   ├── embeddings.py        ← Busca semântica
│   ├── cognitive.py         ← Consolidate, decay, archive
│   ├── graph.json           ← Grafo serializado
│   └── state/               ← Estado por dev
│
├── memory/                   ← CONTEÚDO LEGÍVEL
│   ├── episodes/            ← Memória episódica
│   ├── concepts/            ← Memória semântica
│   ├── patterns/            ← Memória procedural
│   ├── decisions/           ← ADRs
│   ├── people/              ← Expertise
│   └── domains/             ← Áreas
│
├── consolidated/             ← Summaries
└── archive/                  ← Memórias arquivadas
```

**Funcionalidades Implementadas:**
- ✅ Grafo com nós tipados (labels) e arestas tipadas (REFERENCES, AUTHORED_BY, etc)
- ✅ Estado de memória (strength, decay_rate, access_count)
- ✅ Spreading activation para busca
- ✅ Curva de esquecimento (Ebbinghaus)
- ✅ Consolidação de conexões
- ✅ Embeddings para busca semântica

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
8. [ ] Documentar fluxo de uso para equipe
