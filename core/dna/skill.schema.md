# Skill Schema v1.0

Define a estrutura obrigatória e regras de validação para skills Engram.
Usado pelo `engram-genesis` para gerar skills corretos por construção
e pelo `validate.py` para verificar skills existentes.

## Estrutura de Diretório

```
skill-name/                 # kebab-case, único no projeto
├── SKILL.md                # (obrigatório) Instruções para o Claude
├── scripts/                # (opcional) Código executável
│   └── *.py | *.sh
├── references/             # (opcional) Docs carregados sob demanda
│   └── *.md
└── assets/                 # (opcional) Arquivos usados no output
    └── *
```

## SKILL.md — Frontmatter YAML

Campos obrigatórios:
- `name`: string — identificador único, kebab-case, sem espaços
- `description`: string — O QUE faz + QUANDO ativar (triggers explícitos)

Campos opcionais:
- `composes`: list — skills que este skill orquestra (composição)
- `version`: string — semver (default: "1.0.0")

### Regras do description
- Mínimo 50 caracteres, máximo 500
- Deve conter pelo menos 1 trigger explícito ("Use quando...")
- Deve descrever o que o skill FAZ, não o que ele É

## SKILL.md — Body Markdown

Seções recomendadas (ordem livre):
1. **Propósito** — 1-2 parágrafos do que resolve
2. **Workflow** — Steps numerados do processo
3. **Regras/Guardrails** — O que PODE e NÃO PODE fazer
4. **Output Esperado** — Formato de resposta esperado

### Regras do Body
- Máximo 500 linhas (progressive disclosure — mover detalhes para references/)
- Use linguagem imperativa ("Analise", "Gere", não "Você deve analisar")
- Referencie scripts/ e references/ explicitamente quando existirem
- Não inclua informação que o Claude já sabe (ele é inteligente)

## Regras de Validação

1. `SKILL.md` DEVE existir na raiz do diretório do skill
2. Frontmatter YAML DEVE ser válido e conter `name` + `description`
3. `name` DEVE ser kebab-case e corresponder ao nome do diretório
4. `description` DEVE ter entre 50-500 caracteres
5. Body DEVE ter menos de 500 linhas
6. Referências a `scripts/` DEVEM apontar para arquivos existentes
7. Scripts DEVEM ter permissão de execução e shebang line
8. Se `composes` existe, todos os skills listados DEVEM existir no projeto
9. Diretório NÃO DEVE conter: README.md, CHANGELOG.md, INSTALLATION.md

## Exemplo Mínimo Válido

```yaml
---
name: api-validator
description: Validação automática de APIs REST. Use quando criar ou modificar
  endpoints de API para garantir que seguem padrões do projeto, incluem
  validação de input, error handling e documentação.
---
```

```markdown
# API Validator

Validar endpoints de API contra os padrões do projeto.

## Workflow
1. Identificar o endpoint sendo criado/modificado
2. Verificar: validação de input (Zod/Yup/etc)
3. Verificar: error handling (try/catch, status codes)
4. Verificar: tipagem de request/response
5. Verificar: documentação (JSDoc ou OpenAPI)

## Regras
- NUNCA aprovar endpoint sem validação de input
- SEMPRE sugerir testes para novos endpoints
- Reportar como lista: ✅ passou | ❌ falhou | ⚠️ sugestão
```
