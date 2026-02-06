# Agent Schema v1.0

Define a estrutura obrigatória e regras de validação para subagentes Engram.
Subagentes são especialistas invocados para tarefas que exigem foco profundo.

## Estrutura

```
agents/
└── agent-name.md           # Arquivo único, kebab-case
```

Agents são arquivos Markdown únicos (não diretórios como skills).

## Frontmatter YAML

Campos obrigatórios:
- `name`: string — identificador único, kebab-case
- `description`: string — especialidade + quando invocar (50-500 chars)
- `tools`: list — permissões do agent (subset de settings.json)

Campos opcionais:
- `skills`: list — skills que o agent consulta durante execução

## Body Markdown

Seções obrigatórias:
1. **Identidade** — Quem é o agent (1 parágrafo)
2. **Responsabilidades** — O que faz (lista ou parágrafos)
3. **Regras** — Limites e guardrails

Seções opcionais:
4. **Princípios** — Como decide entre alternativas
5. **Output Esperado** — Formato de resposta
6. **Workflow** — Steps quando aplicável

## Regras de Validação

1. Arquivo DEVE ser `.md` dentro de `.claude/agents/`
2. Frontmatter DEVE conter `name`, `description`, `tools`
3. `name` DEVE ser kebab-case e corresponder ao nome do arquivo (sem .md)
4. `tools` DEVE ser subset das permissões em `settings.json`
5. Skills referenciados em `skills:` DEVEM existir em `.claude/skills/`
6. Body DEVE conter seção de "Regras" (guardrails são obrigatórios)
7. Agent NÃO PODE invocar outros agents (regra de design do Engram)
8. Body DEVE ter menos de 300 linhas

## Regra de Não-Encadeamento

Subagentes executam em contexto isolado (fork). Um agent NÃO pode
invocar outro agent. Se uma tarefa exige múltiplos especialistas,
a orquestração acontece na conversa principal:

```
Conversa Principal → Agent A (retorna resultado)
                   → Agent B (recebe resultado de A como contexto)
```

## Exemplo Mínimo Válido

```yaml
---
name: architect
description: Especialista em decisões arquiteturais. Invoque para avaliar
  trade-offs, escolher padrões, definir estrutura de módulos, ou registrar
  ADRs. Consulta ADR_LOG.md e PATTERNS.md antes de decidir.
tools:
  - Read
  - Grep
  - Glob
skills:
  - project-analyzer
---
```

```markdown
Você é um Arquiteto de Software sênior.

## Responsabilidades
- Avaliar trade-offs entre abordagens técnicas
- Propor estrutura de módulos e componentes
- Registrar decisões no cérebro via `brain.add_memory(labels=["Decision", "ADR"])`

## Regras
- SEMPRE consulte o cérebro (`recall.py --type ADR`) antes de propor algo novo
- SEMPRE apresente pelo menos 2 alternativas com trade-offs
- NUNCA mude arquitetura sem registrar ADR
- Priorize simplicidade sobre elegância
```
