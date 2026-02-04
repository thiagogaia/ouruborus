---
name: priority-engine
description: Framework de priorização com ICE Score. Use quando precisar
  decidir o que fazer a seguir, avaliar prioridades, adicionar ou
  desprioritizar tarefas, ou quando executar /priorities. Mantém
  PRIORITY_MATRIX.md organizado e atualizado.
---

# Priority Engine

Decide o que importa agora usando ICE Score.

## ICE Score

```
ICE = (Impacto × Confiança) / Esforço
```

| Dimensão | 1-3 | 4-6 | 7-10 |
|----------|-----|-----|------|
| **Impacto** | Nice-to-have | Importante | Crítico/Bloqueador |
| **Confiança** | Hipótese | Provável | Certeza |
| **Esforço** | Semanas | Dias | Horas |

> Esforço é INVERSO: 1 = muito trabalho, 10 = trivial.

## Workflow

### Avaliar Novas Tarefas
1. Para cada tarefa, perguntar:
   - **Impacto**: "Se isso estivesse pronto agora, quanto melhoraria o projeto?"
   - **Confiança**: "Quão certo estamos de que a solução funciona?"
   - **Esforço**: "Quanto tempo/trabalho exige?" (inverter: pouco esforço = score alto)
2. Calcular ICE
3. Inserir na posição correta em PRIORITY_MATRIX.md

### Desprioritizar
Tão importante quanto priorizar:
- Tarefa completada → mover para Cemitério com data e resultado
- Tarefa irrelevante → mover para Cemitério com justificativa
- Tarefa bloqueada → marcar status e registrar bloqueio em CURRENT_STATE.md

### Reavaliação
Ao final de cada sessão (via /learn):
- ICE Scores ainda fazem sentido? Contexto mudou?
- Alguma tarefa nova deveria ser HIGH priority?
- Alguma tarefa no topo está bloqueada? (se sim, próxima da fila sobe)

## Formato do PRIORITY_MATRIX.md

```markdown
## Ativas
| # | Tarefa | I | C | E | ICE | Status |
|---|--------|---|---|---|-----|--------|
| 1 | Implementar auth | 9 | 8 | 4 | 18.0 | 🔵 em progresso |

## Backlog
(ordenado por ICE desc)

## Cemitério
| Tarefa | Motivo | Data |
|--------|--------|------|
| Setup inicial | ✅ Concluído | 2026-01-15 |
```

## Regras
- NUNCA tenha mais de 3 tarefas "em progresso" simultaneamente
- SEMPRE desprioritize o que foi resolvido (mover para Cemitério)
- Se ICE > 15: urgente. Se ICE < 3: questione se vale fazer.
- Bloqueios são prioridade máxima (desbloqueiam outras tarefas)
- Reavalie ICE quando o contexto mudar significativamente
