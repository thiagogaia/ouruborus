# Estado Atual do Projeto
> Última atualização: 2026-02-03 (/init-engram)

## Status Geral
- **Fase**: Produção v2.0.0 — pronto para uso
- **Saúde**: 🟢 Saudável
- **Próximo Marco**: Testar em projetos reais + evoluir com feedback

## Identidade
**Engram v2** — Sistema metacircular de memória persistente para Claude Code.
O sistema que gera a si mesmo (ouroboros).

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
setup.sh → instala DNA (schemas) + genesis + evolution + seeds
              ↓
/init-engram → genesis analisa projeto → gera skills customizados
              ↓
/learn → evolution rastreia uso → propõe melhorias
              ↓
genesis → evolui componentes → ciclo recomeça
```

## Componentes Instalados

### Skills Core (2)
| Nome | Função | Scripts |
|------|--------|---------|
| engram-genesis | Motor de auto-geração | analyze_project.py, generate_component.py, validate.py, register.py, compose.py |
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
- [2026-02-03] Engram v2.0.0 — primeira versão pública | Impacto: ALTO
- [2026-02-03] Sistema metacircular funcionando | Impacto: ALTO
- [2026-02-03] /init-engram completado | Impacto: ALTO

## Dívidas Técnicas
| Item | Severidade | Descrição |
|------|------------|-----------|
| DT-001 | 🟡 Baixa | Falta coverage de testes nos scripts Python |
| DT-002 | 🟡 Baixa | Templates de stack incompletos (só 7 frameworks) |
| DT-003 | 🟢 Info | Documentação poderia ter mais exemplos |

## Bloqueios Conhecidos
Nenhum bloqueio ativo.

## Contexto Para Próxima Sessão
- O projeto está funcional e pronto para uso
- Testar em projetos reais de diferentes stacks
- Coletar feedback via /learn para evoluir o sistema
- Considerar adicionar mais templates em templates/stacks/
