# EXP-011: Implementar Sistema de Migração de Backups

**ID**: f729cc3c
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

/init-engram não tinha lógica para migrar backups criados pelo setup.sh
- **Stack**: Python, engram-genesis scripts
- **Padrão**: PAT-011
- **Abordagem**: 1) Analisar como setup.sh cria backups 2) Criar migrate_backup.py com --detect, --analyze, --migrate, --cleanup 3) Atualizar init-engram.md com Fase 0 e Fase 6
- **Descoberta**: Merge semântico é melhor que sobrescrita — preserva EXP entries, PAT entries, ADRs únicos
- **Resultado**: Sucesso — testado com backups simulados, todas as fases funcionam
- **Data**: 2026-02-03
