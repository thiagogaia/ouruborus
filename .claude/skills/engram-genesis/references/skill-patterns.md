# Skill Patterns — Boas Práticas Comprovadas

Referência para o engram-genesis ao gerar novos skills.

## Pattern 1: Workflow Linear

Para skills que seguem uma sequência fixa de passos.

```markdown
## Workflow
1. Analisar [input]
2. Verificar [condição]
3. Executar [ação]
4. Validar [resultado]
5. Registrar em [knowledge file]
```

**Quando usar:** Code review, migrations, deploy.

## Pattern 2: Decisão + Ação

Para skills que precisam decidir entre abordagens.

```markdown
## Análise
Avaliar o contexto e decidir entre:
- **Abordagem A**: quando [condição A]
- **Abordagem B**: quando [condição B]

## Execução
Aplicar a abordagem escolhida seguindo [referência].
```

**Quando usar:** Refactoring, escolha de padrão, troubleshooting.

## Pattern 3: Template + Customização

Para skills que geram artefatos a partir de templates.

```markdown
## Geração
1. Escolher template base em assets/
2. Substituir placeholders com dados do projeto
3. Customizar para o caso específico
4. Validar output
```

**Quando usar:** Scaffolding, geração de código, documentação.

## Pattern 4: Análise + Report

Para skills que inspecionam e reportam.

```markdown
## Coleta
Analisar [escopo] usando [ferramenta/abordagem].

## Avaliação
Para cada item encontrado, classificar:
- ✅ Conforme
- ⚠️ Atenção (sugestão de melhoria)
- ❌ Problema (ação necessária)

## Report
Apresentar resultado em formato tabular com ação sugerida.
```

**Quando usar:** Code review, audit, health check.

## Pattern 5: Composição (v2)

Para skills que orquestram outros skills.

```yaml
composes:
  - skill-a
  - skill-b
  - skill-c
```

```markdown
## Orquestração
1. Ativar skill-a com contexto [X]
2. Usar output de skill-a como input de skill-b
3. Finalizar com skill-c para validação
```

**Quando usar:** Pipelines complexos (feature completa, release).

## Princípios Universais

1. **Um skill, uma responsabilidade** — se faz duas coisas, divida
2. **Imperativo, não descritivo** — "Analise X" não "Este skill analisa X"
3. **Guardrails explícitos** — seção "Regras" é obrigatória
4. **Progressive disclosure** — SKILL.md enxuto, detalhes em references/
5. **Output previsível** — sempre especifique o formato de resposta
6. **Knowledge-aware** — referencie knowledge files quando relevante
