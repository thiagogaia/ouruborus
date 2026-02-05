# EXP-012: Limpar __pycache__ do Histórico Git

**ID**: 111d92de
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

Arquivos __pycache__ foram commitados acidentalmente antes do .gitignore
- **Stack**: Git, .gitignore
- **Abordagem**: 1) Criar .gitignore robusto 2) `git rm -r --cached **/__pycache__/` 3) Commit de cleanup
- **Descoberta**: Remover do cache (--cached) preserva arquivos locais mas remove do tracking
- **Resultado**: Sucesso — 22 binários removidos do histórico, repositório mais limpo
- **Data**: 2026-02-03
