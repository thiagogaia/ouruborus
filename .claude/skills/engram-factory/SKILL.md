---
name: engram-factory
description: Interface de alto nível para gerenciar o ecossistema Engram.
  Cria, evolui, compõe e aposenta componentes. Use via /create, quando
  precisar gerar novos skills/agents/commands, compor skills existentes,
  ou gerenciar o ciclo de vida de componentes. Também ativa automaticamente
  durante orquestração runtime para criar subagents sob demanda.
composes:
  - engram-genesis
  - engram-evolution
---

# Engram Factory

Interface unificada para criação e gestão de componentes.
Orquestra genesis (geração) + evolution (evolução) numa experiência simplificada.

## Orquestração Runtime (Auto-criação sob demanda)

O Claude NÃO precisa esperar o dev pedir `/create`.
Quando detecta que uma tarefa precisa de expertise que nenhum agent ou skill existente cobre,
o Claude cria o componente na hora, usa, e reporta.

### Protocolo de Detecção

Antes de iniciar qualquer tarefa, o orquestrador avalia:

```
1. A tarefa requer conhecimento especializado?
   NÃO → prosseguir normalmente
   SIM ↓

2. Existe agent/skill que cobre?
   → Listar agents em .claude/agents/
   → Listar skills em .claude/skills/
   SIM → ativar o componente existente
   NÃO ↓

3. É reutilizável (vai precisar de novo)?
   SIM → criar componente permanente (agent ou skill)
   NÃO → resolver inline, registrar no /learn para avaliação futura
```

### Quando Criar Agent vs Skill

| Criar Agent | Criar Skill |
|-------------|-------------|
| Precisa de persona/especialização profunda | Precisa de workflow/processo repetitivo |
| Exige julgamento e trade-offs | Exige steps e regras fixas |
| Ex: "oracle-migration-expert" | Ex: "csv-import-workflow" |
| Ex: "security-auditor" | Ex: "api-versioning-patterns" |

### Workflow de Criação Runtime

```
Detecção → Anúncio → Geração → Validação → Uso → Report

1. ANUNCIAR ao dev (não criar silenciosamente):
   "⚡ Nenhum agent cobre [expertise]. Vou criar [nome] para esta tarefa."

2. GERAR via genesis:
   python3 .claude/skills/engram-genesis/scripts/generate_component.py \
     --type [agent|skill] --name [nome] --project-dir .

3. CUSTOMIZAR o scaffold com contexto real da tarefa
   (não usar template genérico — preencher com conhecimento concreto)

4. VALIDAR:
   python3 .claude/skills/engram-genesis/scripts/validate.py \
     --type [agent|skill] --path [caminho]

5. REGISTRAR:
   python3 .claude/skills/engram-genesis/scripts/register.py \
     --type [agent|skill] --name [nome] --source runtime --project-dir .

6. USAR: delegar a tarefa ao componente recém-criado

7. REPORTAR ao final:
   "🐍 Criei [tipo] '[nome]' durante esta sessão porque [razão].
    Ele está em .claude/[tipo]/[nome]. O /learn vai registrar o uso."
```

### Guardrails de Criação Runtime

- SEMPRE anunciar ao dev ANTES de criar (não criar silenciosamente)
- NUNCA criar duplicata — verificar se já existe componente similar
- NUNCA criar se a tarefa é trivial (não precisa de especialista para somar 2+2)
- Máximo 2 componentes criados por sessão (evitar inflação)
- Se criar 2+ na mesma sessão, avaliar se não é melhor 1 composto
- Componentes runtime nascem com `source: runtime` no manifest para rastreamento
- O `/learn` avalia se o componente runtime vale manter ou aposentar

### Exemplos de Trigger

| Situação | Ação |
|----------|------|
| "Migrar banco para Oracle" e db-expert é genérico | → criar agent `oracle-migration-expert` |
| "Implementar sistema de notificações por email" sem skill de email | → criar skill `email-notification-patterns` |
| "Garantir LGPD compliance nos dados de pacientes" sem expertise legal | → criar agent `compliance-checker` |
| "Otimizar SEO das páginas" sem skill de SEO | → criar skill `seo-patterns` |
| "Corrigir bug no CSS" com expertise geral suficiente | → NÃO criar (trivial) |
| "Adicionar campo no form" com patterns existentes | → NÃO criar (já coberto) |

## Operações

### Criar Componente
1. Validar nome e tipo
2. Consultar curriculum: já existe? é recomendado?
3. Consultar templates de stack: existe template pronto?
4. Invocar genesis: gerar scaffold → customizar → validar → registrar
5. Reportar ao dev: o que foi criado, como customizar

### Compor Skills
1. Identificar skills candidatos (co-activation ou request do dev)
2. Resolver cadeia de composição: `compose.py --skill [nome]`
3. Gerar skill composto com `composes:` no frontmatter
4. Validar + registrar

### Evoluir Componente
1. Criar backup: `archive.py --type [tipo] --name [nome]`
2. Aplicar mudanças ao componente
3. Revalidar: `validate.py --type [tipo] --path [caminho]`
4. Atualizar manifest: version bump
5. Registrar em evolution-log.md

### Aposentar Componente
1. Verificar se é usado (manifest activations)
2. Confirmar com dev
3. Arquivar: `archive.py --type [tipo] --name [nome]`
4. Atualizar manifest: health = archived
5. Registrar em evolution-log.md

### Importar/Exportar
- Import de global: `global_memory.py import-skill --name [nome]`
- Export para global: `global_memory.py export-skill --name [nome]`
- Import de template: copiar de `templates/stacks/[stack]/`

## Workflow de Criação (detalhado)

```
Dev: /create skill api-validator
  │
  ├─ Factory consulta curriculum
  │   → "api-validator não existe, recomendado para projetos com APIs"
  │
  ├─ Factory consulta templates
  │   → nenhum template específico
  │
  ├─ Factory invoca genesis
  │   ├─ generate_component.py --type skill --name api-validator
  │   ├─ (Claude customiza o scaffold para o projeto)
  │   ├─ validate.py --type skill --path .claude/skills/api-validator/
  │   └─ register.py --type skill --name api-validator --source genesis
  │
  └─ Factory reporta
      → "Skill api-validator criado em .claude/skills/api-validator/"
      → "Customize o SKILL.md com regras específicas do seu projeto"
```

## Regras
- SEMPRE validar antes de registrar
- SEMPRE criar backup antes de evoluir
- SEMPRE confirmar com dev antes de aposentar
- SEMPRE anunciar antes de criar em runtime
- Usar templates de stack quando disponíveis
- Registrar todas as operações em evolution-log.md
- Componentes runtime: source=runtime no manifest
