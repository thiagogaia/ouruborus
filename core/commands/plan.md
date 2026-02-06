Criar plano de implementação para uma feature ou tarefa.

O tópico a planejar é: $ARGUMENTS

## Workflow

1. Consulte o cérebro para contexto:
   ```bash
   python3 .claude/brain/recall.py "$ARGUMENTS" --top 10 --format json
   ```
   O recall retorna ADRs, patterns, experiências e conexões relevantes.
   Só leia os `.md` se o recall não cobrir.

2. Analise o codebase para entender o que já existe:
   - Modules/components relevantes
   - APIs ou serviços que serão impactados
   - Testes existentes na área

3. Crie o plano em formato de steps executáveis:

```
📋 Plano: [feature/tarefa]
═══════════════════════════════
Complexidade: [baixa|média|alta]
Estimativa: [N steps, ~tempo]
Impacta: [listar módulos/arquivos]

Steps:
  1. [ação concreta com arquivo/componente]
  2. [ação concreta]
  ...
  N. [testes + validação]

Riscos:
  - [risco identificado + mitigação]

Decisões necessárias:
  - [decisão que o dev precisa tomar antes de implementar]
```

4. Se o plano envolver decisão arquitetural, sugerir registro em ADR_LOG.md
5. Adicionar a tarefa em PRIORITY_MATRIX.md com ICE Score
