---
name: engram-evolution
description: Motor de evolução do Engram. Rastreia uso de componentes, mede
  impacto, propõe melhorias, composições e aposentadorias. Use no /learn
  para análise evolutiva, quando detectar skill ineficiente, ou via /doctor
  para health check. Mantém manifest.json e evolution-log.md atualizados.
---

# Engram Evolution

Evolui o ecossistema de componentes baseado em dados de uso real.

## Dados Rastreados (manifest.json)

Para cada componente, o manifest armazena:
- `activations`: quantas vezes foi usado
- `last_used`: data do último uso
- `health`: active | stale | archived
- `version`: versão atual
- `source`: genesis | seed | manual | evolution

## Ações Evolutivas

### Detectar Padrão → Propor Novo Skill
**Trigger:** Claude nota que executa a mesma sequência 3+ vezes sem skill.

Workflow:
1. Registrar o padrão em `references/evolution-log.md`
2. Perguntar ao dev: "Notei padrão recorrente [X]. Criar skill?"
3. Se aprovado → invocar `engram-genesis` para gerar
4. Registrar no manifest com source: "evolution"

### Skill Subutilizado → Propor Merge ou Archive
**Trigger:** Componente com 0 activations em 10+ sessões.

```bash
python3 .claude/skills/engram-evolution/scripts/track_usage.py \
  --project-dir . --report stale
```

Workflow:
1. Listar componentes stale
2. Para cada um: é redundante com outro? → propor merge
3. Se não é redundante, é simplesmente inútil? → propor archive
4. Sempre perguntar ao dev antes de agir

### Skill Muito Grande → Propor Split
**Trigger:** SKILL.md com mais de 400 linhas.

Workflow:
1. Identificar responsabilidades distintas no skill
2. Propor divisão em N skills menores
3. Se aprovado → genesis gera os novos + archive o original

### Skills Sempre Juntos → Propor Composição
**Trigger:** Dois+ skills ativados em sequência em 3+ sessões.

Workflow:
1. Consultar manifest para padrões de co-ativação
2. Propor skill composto com `composes:` no frontmatter
3. Se aprovado → genesis gera o skill composto

### Evoluir Skill Existente
**Trigger:** Dev frequentemente adiciona instruções extras após ativar um skill.

Workflow:
1. Identificar as instruções extras recorrentes
2. Incorporar no SKILL.md do skill
3. Versionar: backup em `.claude/versions/`
4. Atualizar manifest (version bump)

## Versionamento

Ao modificar qualquer componente:
```bash
python3 .claude/skills/engram-evolution/scripts/archive.py \
  --type skill --name my-skill --project-dir .
```

Cria backup em `.claude/versions/my-skill/v1.0.0.md` antes de modificar.

## Integração com /learn

No `/learn`, após registro de conhecimento:
1. Consultar manifest para componentes stale
2. Verificar se houve padrões de co-ativação
3. Reportar sugestões evolutivas ao dev
4. Registrar observações em evolution-log.md

## Regras
- NUNCA arquivar componente sem confirmação do dev
- NUNCA modificar skill sem criar backup versionado
- SEMPRE registrar decisões evolutivas em evolution-log.md
- Propor ações, não executar autonomamente (exceto tracking)
