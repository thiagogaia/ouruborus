# Boot
> Atualizado: 2026-02-06 (sessao 10 - temporal recall)

## Status
- **Fase**: v3.0.0 — Engram com Cerebro Organizacional
- **Saude**: 🟢 Healthy (Score 0.97, Doctor 96%)
- **Cerebro**: 222 nos, 567 arestas, 222 embeddings — SQLite schema v2
- **Testes**: 195/195 passando (0.14s)
- **Proximo marco**: Validar recall temporal em sessoes reais

## Bloqueios
Nenhum.

## Dividas Tecnicas
| Item | Severidade | Descricao |
|------|------------|-----------|
| DT-002 | 🟡 Baixa | Templates de stack incompletos (so 7 frameworks) |
| DT-003 | 🟢 Info | Documentacao poderia ter mais exemplos |

## Sugestoes Evolutivas
| Tipo | Descricao | Prioridade |
|------|-----------|------------|
| Composicao | engram-evolution + project-analyzer (37% co-ativacao) | 🟡 Media |
| Stale | 8 componentes nunca usados — avaliar necessidade | 🟢 Baixa |

## Como Consultar o Historico

O historico de mudancas agora vive no cerebro. Use recall temporal:

```bash
# O que mudou nos ultimos 7 dias (substitui "O Que Mudou Recentemente")
python3 .claude/brain/recall.py --recent 7d --type Commit --top 10

# Busca semantica + temporal
python3 .claude/brain/recall.py "tema" --since 2026-02-01 --sort date

# Busca semantica pura (conhecimento relevante)
python3 .claude/brain/recall.py "tema da tarefa" --top 10 --format json
```
