# EXP-022: Redesign de Grafo — Diagnóstico Antes de Código

**ID**: f2aad3c1
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

cérebro com 151 nós, 234 arestas, mas 0 semânticas — espelho burro dos .md
- **Stack**: Python, NetworkX, brain.py, sleep.py
- **Abordagem**:
  1. Diagnóstico quantitativo primeiro: contar tipos de aresta, medir topologia
  2. Identificar causas raiz (5): uuid4, resolve quebrado, populate sem refs, venv não ativado, consolidação no-op
  3. Corrigir fundação antes de adicionar features (IDs determinísticos, upsert, resolve por prop)
  4. Depois sim: criar sleep.py com 5 fases incrementais (cada uma autônoma)
  5. Auto-ativação de venv — o problema mais simples com maior impacto
- **Descoberta**: "existe" != "funciona" — venv criado pelo setup.sh nunca era ativado pelos scripts
- **Resultado**: de 0 para 68 arestas semânticas, 134 duplicatas removidas, health 0.47→0.75
- **Data**: 2026-02-05
1. Diagnóstico quantitativo primeiro: contar tipos de aresta, medir topologia
  2. Identificar causas raiz (5): uuid4, resolve quebrado, populate sem refs, venv não ativado, consolidação no-op
  3. Corrigir fundação antes de adicionar features (IDs determinísticos, upsert, resolve por prop)
  4. Depois sim: criar sleep.py com 5 fases incrementais (cada uma autônoma)
  5. Auto-ativação de venv — o problema mais simples com maior impacto
- **Descoberta**: "existe" != "funciona" — venv criado pelo setup.sh nunca era ativado pelos scripts
- **Resultado**: de 0 para 68 arestas semânticas, 134 duplicatas removidas, health 0.47→0.75
- **Data**: 2026-02-05
