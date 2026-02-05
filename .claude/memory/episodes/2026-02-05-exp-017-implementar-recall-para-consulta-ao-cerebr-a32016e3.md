# EXP-017: Implementar /recall para Consulta ao Cerebro (5db29c67)

**ID**: a32016e3
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

Criar interface human-friendly para consultar cerebro organizacional
- **Stack**: Python, argparse, brain.py, embeddings.py, commands
- **Abordagem**:
  1. Criar recall.py com busca semantica + spreading activation
  2. Implementar fallback gracioso quando deps nao estao disponiveis
  3. Dual output: JSON para scripts, human-readable para devs
  4. Criar command em .claude/commands/ E core/commands/
  5. Atualizar CLAUDE.md com instrucoes de quando usar /recall
- **Padroes Aplicados**: PAT-023 (Fallback), PAT-024 (Hibrido), PAT-025 (Dual Output), PAT-026 (Dois Locais), PAT-027 (Spreading)
- **Descoberta**: recall.py usa type_map para traduzir tipos amigaveis ("adr") para labels do grafo (["ADR", "Decision"])
- **Resultado**: 4 arquivos, 575 linhas. Interface: `/recall "query" --type ADR --depth 3`
- **Data**: 2026-02-03 (commit 5db29c67)
1. Criar recall.py com busca semantica + spreading activation
  2. Implementar fallback gracioso quando deps nao estao disponiveis
  3. Dual output: JSON para scripts, human-readable para devs
  4. Criar command em .claude/commands/ E core/commands/
  5. Atualizar CLAUDE.md com instrucoes de quando usar /recall
- **Padroes Aplicados**: PAT-023 (Fallback), PAT-024 (Hibrido), PAT-025 (Dual Output), PAT-026 (Dois Locais), PAT-027 (Spreading)
- **Descoberta**: recall.py usa type_map para traduzir tipos amigaveis ("adr") para labels do grafo (["ADR", "Decision"])
- **Resultado**: 4 arquivos, 575 linhas. Interface: `/recall "query" --type ADR --depth 3`
- **Data**: 2026-02-03 (commit 5db29c67)
