# EXP-001: Validar Componente Antes de Registrar

**ID**: 801b61db
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

Componente criado manualmente tinha erros no frontmatter
- **Stack**: Python scripts, manifest.json
- **Padrão**: PAT-007
- **Abordagem**: SEMPRE rodar validate.py antes de register.py. Corrigir todos os erros reportados. Só então registrar.
- **Resultado**: Sucesso — evita componentes inválidos no sistema
- **Data**: 2026-02-03
