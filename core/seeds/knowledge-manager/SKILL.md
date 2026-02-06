---
name: knowledge-manager
description: Motor de retroalimentação do Engram. Gerencia o ciclo de registro
  de conhecimento nos arquivos persistentes. Use ao final de tarefas, durante
  /learn, ou quando precisar registrar padrões, decisões, estado ou domínio.
  Coração do sistema — sem ele o ciclo não fecha.
---

# Knowledge Manager

Gerencia o ciclo de retroalimentação — o coração do Engram.

## Knowledge Files

| Arquivo | Propósito | Quando Atualizar |
|---------|-----------|------------------|
| `PRIORITY_MATRIX.md` | Tarefas com ICE Score | Ao completar/criar tarefas |
| `PATTERNS.md` | Padrões e anti-padrões | Ao descobrir padrões |
| `ADR_LOG.md` | Decisões arquiteturais | Ao tomar decisões |
| `DOMAIN.md` | Glossário + regras de negócio | Ao aprender sobre domínio |
| `EXPERIENCE_LIBRARY.md` | Soluções reutilizáveis | Ao resolver problemas bem |

## Workflow de Registro

### 1. Identificar Tipo de Conhecimento
Classifique o que foi aprendido/decidido/feito:
- **Estado** → cérebro via `brain.add_memory()` (labels: ["State"])
- **Padrão** → PATTERNS.md (incluir: contexto, solução, exemplo)
- **Decisão** → ADR_LOG.md (incluir: contexto, alternativas, trade-offs)
- **Prioridade** → PRIORITY_MATRIX.md (incluir: ICE Score)
- **Domínio** → DOMAIN.md (incluir: termo + definição ou regra)
- **Experiência** → EXPERIENCE_LIBRARY.md (incluir: abordagem + resultado)

### 2. Registrar no Arquivo Correto
- Ler o arquivo atual para evitar duplicação
- Adicionar entrada com data
- Manter formato consistente (ver schema em `.claude/schemas/knowledge.schema.md`)

### 3. Cross-Reference
Se o registro impacta outros files, atualize-os também:
- ADR que cria padrão → atualizar PATTERNS.md
- Padrão que resolve prioridade → atualizar PRIORITY_MATRIX.md
- Estado que revela bloqueio → atualizar PRIORITY_MATRIX.md

### 4. Limpar Obsoletos
- Mover tarefas completas para "Cemitério" no PRIORITY_MATRIX.md
- Marcar padrões depreciados (nunca deletar — marcar com ~~strikethrough~~)
- Atualizar status de ADRs (aceita → depreciada quando substituída)

## ICE Score (para PRIORITY_MATRIX)

```
ICE = (Impacto × Confiança) / Esforço
```

- **Impacto** (1-10): quanto valor entrega se concluído
- **Confiança** (1-10): quão certo estamos de que funciona
- **Esforço** (1-10): quanto trabalho exige (1=pouco, 10=muito)

Exemplo: Feature com alto impacto (8), boa confiança (7), esforço médio (5) = (8×7)/5 = 11.2

## Regras
- NUNCA delete conhecimento — marque como obsoleto
- SEMPRE inclua data em cada entrada
- SEMPRE mantenha o formato do schema
- Se em dúvida sobre onde registrar: registre no cérebro via `brain.add_memory()`
- Desprioritização é tão importante quanto priorização
- Máximo 50 entradas em EXPERIENCE_LIBRARY.md (manter as mais úteis)
