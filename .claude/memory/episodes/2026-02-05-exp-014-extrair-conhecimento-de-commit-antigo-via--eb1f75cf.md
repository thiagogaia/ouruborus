# EXP-014: Extrair Conhecimento de Commit Antigo via /learn

**ID**: eb1f75cf
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

Analisar commit específico para documentar padrões retroativamente
- **Stack**: Git, /learn skill
- **Abordagem**: 1) `git show <sha> --stat` para ver scope 2) `git diff <sha>^..<sha>` para diff completo 3) Analisar mudanças e extrair padrões 4) Atualizar knowledge files
- **Descoberta**: Commits fundacionais contêm muitos padrões implícitos que valem documentar
- **Resultado**: 3 novos padrões (PAT-017, PAT-018, PAT-019) extraídos do commit 264072a6
- **Data**: 2026-02-04
