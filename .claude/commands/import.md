Importar um skill da memória global (~/.engram/) para este projeto.

Uso: `/import [nome-do-skill]`

## Workflow

1. Se $ARGUMENTS vazio, listar skills disponíveis:
```bash
python3 .claude/skills/engram-evolution/scripts/global_memory.py list
```

2. Se nome fornecido, importar:
```bash
python3 .claude/skills/engram-evolution/scripts/global_memory.py import-skill --name [nome] --project-dir .
```

3. Registrar o skill importado no manifest:
```bash
python3 .claude/skills/engram-genesis/scripts/register.py --type skill --name [nome] --source global --project-dir .
```

4. Validar o skill importado:
```bash
python3 .claude/skills/engram-genesis/scripts/validate.py --type skill --path .claude/skills/[nome]/
```

5. Informar ao dev se precisa customizar o skill para este projeto.

Buscar na memória global:
```bash
python3 .claude/skills/engram-evolution/scripts/global_memory.py search --query "[termo]"
```
