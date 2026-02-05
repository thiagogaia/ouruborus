# EXP-010: Analisar Arquitetura de Subagentes vs Paralelismo

**ID**: 2d0a37a8
**Autor**: [[@engram]]
**Data**: 2026-02-05
**Labels**: Episode, Experience

---

Questão se o Engram deveria ter execução paralela com context windows isoladas
- **Stack**: Arquitetura Engram v2, orquestração
- **Abordagem**: Usar agente Explore para análise profunda. Documentar vantagens do modelo atual antes de propor mudanças.
- **Descoberta**: Modelo sequencial é vantagem deliberada: (1) evita race conditions em knowledge files, (2) permite detecção confiável de co-ativações, (3) 3x mais barato em tokens, (4) skills gerados em sequência evitam redundância
- **Resultado**: Decisão de manter modelo sequencial — paralelismo quebraria premissas do sistema de evolução
- **Data**: 2026-02-03
