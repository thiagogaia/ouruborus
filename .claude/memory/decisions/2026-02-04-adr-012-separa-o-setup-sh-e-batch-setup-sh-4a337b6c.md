# ADR-012: Separação setup.sh e batch-setup.sh

**ID**: 4a337b6c
**Autor**: [[@engram]]
**Data**: 2026-02-04
**Labels**: Decision, ADR, Refactor

---

Decisão de reverter feature creep no setup.sh, separando lógica de batch em arquivo dedicado. Unix philosophy: do one thing well. setup.sh 783 linhas (single project), batch-setup.sh 177 linhas (wrapper multi-project).
