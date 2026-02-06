---
name: project-analyzer
description: Análise profunda do codebase para atualizar estado do projeto.
  Use no início de sessão, quando executar /status, ou quando o contexto
  do projeto parecer desatualizado. Analisa código, dependências e estrutura.
---

# Project Analyzer

Analisa o codebase e reporta o estado do projeto.

## Workflow

1. **Consultar cérebro**: `python3 .claude/brain/recall.py --recent 7d --top 10 --format json`
2. **Verificar saúde**: `python3 .claude/brain/cognitive.py health`
3. **Analisar codebase**:
   - Estrutura de diretórios (mudou desde última análise?)
   - Dependências (novas, removidas, atualizadas?)
   - Código recente: `git log --oneline -20` + `git diff --stat HEAD~5`
   - TODOs e FIXMEs: `grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.js"`
4. **Detectar mudanças significativas**:
   - Novos módulos ou features
   - Mudanças de dependência
   - Migrações de banco
   - Mudanças de configuração
5. **Reportar** descobertas ao dev

## Regras
- NUNCA invente informação — só reporte o que encontrar no código
- Se encontrar dívidas técnicas, registre no cérebro via `brain.add_memory()`
- Priorize brevidade — seções com mais de 10 linhas devem ser resumidas
- Marque data de cada atualização

## Output Esperado

```
📊 Análise do Projeto
═════════════════════
Status: 🟢/🟡/🔴
Desde última análise:
  + [mudanças positivas]
  - [problemas detectados]
  △ [coisas que mudaram]

Próxima ação sugerida: [...]
```
