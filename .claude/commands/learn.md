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

## Fase 4: Criar Memórias no Cérebro ← NOVO

O cérebro organizacional em `.claude/brain/` deve ser atualizado com o conhecimento desta sessão.

### 4.1 Processar Novos Commits
```bash
# Busca commits desde o último /learn (ou últimos 20 se primeiro run)
python3 .claude/brain/populate.py commits 20
```

### 4.2 Criar Memórias Episódicas

Para cada problema resolvido nesta sessão, criar memória via Python:

```python
import sys
sys.path.insert(0, '.claude/brain')
from brain import Brain, get_current_developer

brain = Brain()
brain.load()

# Exemplo: registrar bug fix
brain.add_memory(
    title="Bug: [descrição curta]",
    content="[O que aconteceu, como foi resolvido, arquivos afetados]",
    labels=["Episode", "BugFix"],
    author=get_current_developer(),
    references=["[[arquivo_relacionado]]"]  # opcional
)

brain.save()
```

### 4.3 Criar Memórias Conceituais

Se novos termos ou conceitos foram aprendidos:

```python
brain.add_memory(
    title="[Nome do Conceito]",
    content="[Definição e contexto]",
    labels=["Concept", "Glossary"],
    author="@engram"
)
```

### 4.4 Rodar Consolidação Leve

Fortalecer conexões acessadas nesta sessão:
```bash
python3 .claude/brain/cognitive.py consolidate
```

### 4.5 Verificar Saúde do Cérebro
```bash
python3 .claude/brain/cognitive.py health
```

Se `health_score < 0.8`, seguir recomendações exibidas.

### 4.6 Atualizar Embeddings

Regenerar embeddings para habilitar busca semântica com novos nós:
```bash
python3 .claude/brain/embeddings.py build 2>/dev/null || echo "⚠️ Embeddings: instale sentence-transformers para busca semântica"
```

Isso garante que novos conceitos, padrões e episódios sejam encontráveis via `/recall`.

---

## Fase 5: Evolução do Sistema

Ativar skill `engram-evolution` para análise evolutiva (se disponível):

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

## Fase 6: Resumo

Apresentar:
- O que foi registrado em cada knowledge file
- Sugestões evolutivas (novos skills, archives, composições)
- Próxima ação recomendada

Lembrete: se o `.claude/knowledge/context/CURRENT_STATE.md` foi modificado,
o Claude da próxima sessão saberá exatamente onde retomar.
