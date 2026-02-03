Mostrar o estado atual do projeto de forma concisa.

1. Leia `.claude/knowledge/context/CURRENT_STATE.md`
2. Leia `.claude/knowledge/priorities/PRIORITY_MATRIX.md`
3. Verifique `git status` e `git log --oneline -5`

Apresente em formato compacto:

```
🐍 Status: [nome do projeto]
═══════════════════════════════
Fase: [fase atual]  |  Saúde: [emoji]
Último commit: [hash] [mensagem] ([quando])

📋 Top 3 Prioridades:
  1. [ICE: X] [tarefa] — [status]
  2. [ICE: X] [tarefa] — [status]
  3. [ICE: X] [tarefa] — [status]

⚠️ Bloqueios: [listar ou "nenhum"]

💡 Próxima ação: [sugestão concreta baseada nas prioridades]
```

Se $ARGUMENTS contiver um tópico, foque nele em vez de dar overview geral.
