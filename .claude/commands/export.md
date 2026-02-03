Exportar conhecimento deste projeto para a memória global (~/.engram/).

Uso:
- `/export skill [nome]` — exporta um skill para uso em outros projetos
- `/export pattern [PAT-NNN]` — exporta um padrão para memória global
- `/export experience [EXP-NNN]` — exporta uma experiência

## Workflow

1. Interpretar $ARGUMENTS: primeiro argumento é tipo, segundo é nome

2. Inicializar memória global se necessário:
```bash
python3 .claude/skills/engram-evolution/scripts/global_memory.py init
```

3. Executar o export:
```bash
# Para skills
python3 .claude/skills/engram-evolution/scripts/global_memory.py export-skill --name [nome] --project-dir .

# Para patterns
python3 .claude/skills/engram-evolution/scripts/global_memory.py export-pattern --name [nome] --project-dir .

# Para experiences
python3 .claude/skills/engram-evolution/scripts/global_memory.py export-experience --name [nome] --project-dir .
```

4. Confirmar ao dev o que foi exportado e como importar em outro projeto.

Se $ARGUMENTS vazio, listar o conteúdo da memória global:
```bash
python3 .claude/skills/engram-evolution/scripts/global_memory.py list
```
