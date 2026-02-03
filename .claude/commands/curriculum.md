Analisar a cobertura de skills do projeto e sugerir o que criar/melhorar.

## Execução

```bash
python3 .claude/skills/engram-evolution/scripts/curriculum.py --project-dir .
```

Isso compara:
- Skills instalados vs skills ideais para a stack detectada
- Agents instalados vs agents recomendados
- Skills instalados mas nunca usados (usage gaps)

## Ações Sugeridas

Se faltar skill de framework (e.g. `nextjs-patterns`):
- Verificar se existe template em `templates/stacks/`
- Se existe: copiar e customizar
- Se não: `/create skill [nome]` via genesis

Se skill instalado mas nunca usado:
- Avaliar se é necessário para o projeto
- Se não: `/learn` + propor archive

Se cobertura > 90%:
- Foco em evolução dos skills existentes
- Procurar oportunidades de composição
