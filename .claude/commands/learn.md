Registrar conhecimento adquirido nesta sessão e evoluir o sistema.

## Fase 1: Coleta de Mudanças

1. Execute `git diff --stat HEAD~5` (ou desde o último /learn) para ver o que mudou
2. Execute `git log --oneline -10` para ver commits recentes
3. Leia `.claude/knowledge/context/CURRENT_STATE.md` para comparar com estado anterior

## Fase 2: Introspecção

Reflita sobre a sessão:
- Que padrões foram usados ou descobertos?
- Que decisões arquiteturais foram tomadas?
- Que problemas foram resolvidos?
- Que conhecimento de domínio foi adquirido?
- Alguma experiência vale preservar para reutilização?

## Fase 3: Atualizar Knowledge

Para cada tipo de conhecimento descoberto:

### CURRENT_STATE.md
- Atualizar status geral, fase, saúde
- Registrar mudanças recentes com data e impacto
- Atualizar bloqueios e contexto para próxima sessão

### PATTERNS.md
- Registrar padrões novos descobertos
- Marcar anti-padrões encontrados e corrigidos

### ADR_LOG.md
- Registrar decisões arquiteturais tomadas (se houver)

### PRIORITY_MATRIX.md
- Desprioritizar tarefas completadas (mover para cemitério)
- Adicionar tarefas novas identificadas
- Recalcular ICE Scores se contexto mudou

### DOMAIN.md
- Adicionar termos novos ao glossário
- Registrar regras de negócio descobertas

### EXPERIENCE_LIBRARY.md
- Se alguma interação desta sessão foi particularmente bem-sucedida,
  registrar como experiência reutilizável (max 10 linhas por entry)

## Fase 4: Evolução do Sistema ← NOVO

Ativar skill `engram-evolution` para análise evolutiva:

1. **Tracking**: Registrar quais skills/agents foram usados nesta sessão
```bash
python3 .claude/skills/engram-genesis/scripts/register.py --activate --type skill --name [nome] --project-dir .
```
(Repetir para cada componente usado)

Registrar co-ativações para o detector de composição:
```bash
python3 .claude/skills/engram-evolution/scripts/co_activation.py --log-session --skills [skill1],[skill2],[...] --project-dir .
```

2. **Stale Check**: Verificar componentes subutilizados
```bash
python3 .claude/skills/engram-evolution/scripts/track_usage.py --project-dir . --report stale
```

3. **Pattern Detection**: Houve alguma sequência repetitiva que não é coberta por um skill?
   - Se sim: propor criação via genesis
   - Registrar em evolution-log.md

4. **Co-activation**: Os mesmos skills foram ativados juntos (como em sessões anteriores)?
```bash
python3 .claude/skills/engram-evolution/scripts/co_activation.py --project-dir .
```
   - Se pairs com 3+ sessões: propor composição
   - Registrar em evolution-log.md

5. **Reportar** sugestões evolutivas ao dev

6. **Runtime Components**: Se componentes foram criados durante esta sessão (source=runtime):
   - O componente foi realmente útil para a tarefa?
   - É reutilizável em futuras sessões?
     - SIM → manter, recomendar refinamento se necessário
     - NÃO → propor archive
   - Pode ser mergeado com componente existente?
     - SIM → propor evolução do existente + archive do runtime
   - Reportar ao dev: "Criei [nome] nesta sessão. Manter ou aposentar?"

## Fase 5: Resumo

Apresentar:
- O que foi registrado em cada knowledge file
- Sugestões evolutivas (novos skills, archives, composições)
- Próxima ação recomendada

Lembrete: se o `.claude/knowledge/context/CURRENT_STATE.md` foi modificado,
o Claude da próxima sessão saberá exatamente onde retomar.
