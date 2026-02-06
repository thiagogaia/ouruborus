Mostrar o estado atual do projeto de forma concisa.

1. Consulte o cérebro: `python3 .claude/brain/recall.py --recent 7d --top 10`
2. Verifique saúde: `python3 .claude/brain/cognitive.py health`
3. Leia `.claude/knowledge/priorities/PRIORITY_MATRIX.md`
4. Verifique `git status` e `git log --oneline -5`

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
