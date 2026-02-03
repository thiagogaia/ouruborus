Criar componente Engram on-the-fly durante o trabalho.

Diferente do `/create` (que é interativo e detalhado), o `/spawn` é rápido e orientado
para uso no meio de uma tarefa, quando o Claude detecta que precisa de expertise
que nenhum componente existente cobre.

Uso:
- `/spawn agent [nome] [propósito]`
- `/spawn skill [nome] [propósito]`

## Workflow Rápido

1. Interpretar $ARGUMENTS: tipo + nome + propósito (uma frase)

2. Verificar se já existe:
```bash
ls .claude/agents/ 2>/dev/null | grep -i [nome]
ls .claude/skills/ 2>/dev/null | grep -i [nome]
```
   - Se existir similar: usar o existente em vez de duplicar

3. Anunciar ao dev:
   "⚡ Criando [tipo] `[nome]` — [propósito]"

4. Gerar scaffold:
```bash
python3 .claude/skills/engram-genesis/scripts/generate_component.py \
  --type [tipo] --name [nome] --project-dir .
```

5. Customizar o scaffold com:
   - Contexto real da tarefa atual
   - Conhecimento concreto (não genérico)
   - Regras e guardrails específicos
   - Se agent: persona + responsabilidades + checklist
   - Se skill: workflow + padrões + exemplos de código

6. Validar:
```bash
python3 .claude/skills/engram-genesis/scripts/validate.py \
  --type [tipo] --path [caminho]
```

7. Registrar com source=runtime:
```bash
python3 .claude/skills/engram-genesis/scripts/register.py \
  --type [tipo] --name [nome] --source runtime --project-dir .
```

8. Reportar:
   "✅ [tipo] `[nome]` criado e registrado (source: runtime).
    O `/learn` vai avaliar se vale manter."

9. Delegar a tarefa atual ao componente recém-criado.

## Auto-Spawn (sem comando explícito)

O Claude também pode invocar este workflow SOZINHO, sem o dev digitar `/spawn`.
Isso acontece quando o protocolo de orquestração detecta a necessidade:

```
Claude avalia tarefa
  → precisa de expertise especializada
  → nenhum agent/skill existente cobre
  → é reutilizável
  → executa /spawn internamente
```

Ver `.claude/skills/engram-factory/references/orchestration-protocol.md` para a
decision tree completa.

## Guardrails
- Máximo 2 spawns por sessão
- SEMPRE anunciar antes de criar
- NUNCA duplicar componente existente
- Se $ARGUMENTS vazio ou insuficiente: perguntar tipo, nome e propósito
- Se validação falhar: corrigir e re-validar (não registrar inválido)
