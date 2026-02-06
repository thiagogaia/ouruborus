---
name: engram-genesis
description: Motor de auto-geração do Engram. Gera skills, agents, commands
  e knowledge files customizados para o projeto. Use quando precisar criar
  qualquer componente Engram novo, no /init-engram para instalação completa,
  ou via /create para geração sob demanda. Capacidade metacircular — pode
  gerar versões atualizadas de si mesmo.
---

# Engram Genesis

Motor de auto-geração. Gera componentes Engram estruturalmente corretos
e adaptados ao projeto atual.

## Workflow de Geração

### 1. Entender a Necessidade
- Qual componente? (skill / agent / command / knowledge)
- Qual problema resolve?
- Já existe componente similar? (verificar `.claude/skills/`, `agents/`, `commands/`)
- Se existe similar: evoluir em vez de duplicar

### 2. Consultar Schema
Ler o schema correspondente em `.claude/schemas/`:
- `skill.schema.md` para skills
- `agent.schema.md` para agents
- `command.schema.md` para commands
- `knowledge.schema.md` para knowledge files

O schema define estrutura obrigatória e regras de validação.

### 3. Consultar Padrões
Ler `references/skill-patterns.md` para boas práticas comprovadas.
Ler `references/anti-patterns.md` para erros comuns a evitar.
Analisar componentes existentes em `.claude/` como exemplos reais.

### 4. Gerar o Componente
Usar o script apropriado:
```bash
# Gerar skill
python3 .claude/skills/engram-genesis/scripts/generate_component.py \
  --type skill --name "nome-do-skill" --project-dir .

# Gerar agent
python3 .claude/skills/engram-genesis/scripts/generate_component.py \
  --type agent --name "nome-do-agent" --project-dir .

# Gerar command
python3 .claude/skills/engram-genesis/scripts/generate_component.py \
  --type command --name "nome-do-command" --project-dir .
```

O script gera a estrutura inicial a partir dos templates.
Claude DEVE customizar o conteúdo gerado para o projeto específico.

### 5. Validar
```bash
python3 .claude/skills/engram-genesis/scripts/validate.py \
  --type skill --path .claude/skills/nome-do-skill/
```

Se falhar: corrigir e re-validar. NÃO registrar componente inválido.

### 6. Registrar no Manifest
```bash
python3 .claude/skills/engram-genesis/scripts/register.py \
  --type skill --name "nome-do-skill" --source "genesis" --project-dir .
```

Atualiza `.claude/manifest.json` com metadados do componente.

## Modo /init-engram (Instalação Completa)

Quando invocado via `/init-engram`, executar análise completa:

### Fase A: Análise do Projeto
```bash
python3 .claude/skills/engram-genesis/scripts/analyze_project.py --project-dir .
```

O script analisa codebase e sugere componentes necessários.
Claude valida as sugestões e decide quais gerar.

### Fase B: Geração em Lote
Para cada componente aprovado:
1. Gerar via generate_component.py (estrutura inicial)
2. Customizar o conteúdo para o projeto (Claude edita o gerado)
3. Validar via validate.py
4. Registrar via register.py

### Fase C: Popular Knowledge
Preencher knowledge files com dados reais do projeto:
- PATTERNS.md → padrões detectados no código
- DOMAIN.md → glossário extraído do código/docs
- PRIORITY_MATRIX.md → TODOs e issues detectados
- Cérebro → estado inicial via `brain.add_memory()`

### Fase D: Health Check
Executar `/doctor` para validação final.

## Modo /create (Geração Sob Demanda)

Quando invocado via `/create [tipo] [nome]`:
1. Validar que o tipo é válido (skill/agent/command)
2. Verificar se nome já existe
3. Executar workflow de geração (steps 1-6)

## Capacidade Metacircular

Este skill pode gerar versões atualizadas de si mesmo:
1. Analisar a versão atual de engram-genesis
2. Identificar melhorias baseado em feedback/uso
3. Gerar nova versão seguindo skill.schema.md
4. Validar a nova versão
5. Fazer backup da versão anterior em `.claude/versions/`
6. Substituir

## Regras
- NUNCA gerar componente sem validar contra schema
- NUNCA registrar componente que falhou validação
- SEMPRE customizar template para o projeto (nunca usar template cru)
- SEMPRE perguntar ao dev antes de gerar em modo interativo
- Em /init-engram, apresentar plano de geração ANTES de executar
