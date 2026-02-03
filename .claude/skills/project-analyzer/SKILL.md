---
name: project-analyzer
description: Análise profunda do codebase para atualizar estado do projeto.
  Use no início de sessão, quando executar /status, ou quando o contexto
  do projeto parecer desatualizado. Analisa código, dependências, estrutura
  e atualiza CURRENT_STATE.md automaticamente.
---

# Project Analyzer

Analisa o codebase e atualiza o conhecimento do projeto.

## Workflow

1. **Ler estado anterior**: Consultar `.claude/knowledge/context/CURRENT_STATE.md`
2. **Analisar codebase**:
   - Estrutura de diretórios (mudou desde última análise?)
   - Dependências (novas, removidas, atualizadas?)
   - Código recente: `git log --oneline -20` + `git diff --stat HEAD~5`
   - TODOs e FIXMEs: `grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.js"`
3. **Detectar mudanças significativas**:
   - Novos módulos ou features
   - Mudanças de dependência
   - Migrações de banco
   - Mudanças de configuração
4. **Atualizar CURRENT_STATE.md** com descobertas
5. **Reportar** diferenças entre estado anterior e atual

## Regras
- NUNCA invente informação — só reporte o que encontrar no código
- SEMPRE compare com CURRENT_STATE.md anterior para detectar delta
- Se encontrar dívidas técnicas, registre na seção correta
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
