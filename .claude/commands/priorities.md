Reavaliar prioridades do projeto usando ICE Score.

1. Ativar skill `priority-engine`

2. Leia `.claude/knowledge/priorities/PRIORITY_MATRIX.md`

3. Consulte o cérebro para contexto: `python3 .claude/brain/recall.py --recent 7d --top 5`

4. Se $ARGUMENTS contiver uma tarefa nova:
   - Avaliar com ICE Score
   - Inserir na posição correta
   - Apresentar comparação com as demais

5. Se $ARGUMENTS estiver vazio:
   - Reavaliar ICE de todas as tarefas ativas
   - Mover tarefas completadas para Cemitério
   - Identificar bloqueios
   - Reordenar por ICE atualizado

6. Apresentar a matrix atualizada e salvar em PRIORITY_MATRIX.md

7. Destacar a próxima ação recomendada.
