Registrar conhecimento adquirido nesta sessão e evoluir o sistema.

## Fase 1: Coleta de Mudanças

1. Execute `git diff --stat HEAD~5` (ou desde o último /learn) para ver o que mudou
2. Execute `git log --oneline -10` para ver commits recentes
3. Consulte o cérebro: `python3 .claude/brain/recall.py --recent 3d --type Commit --top 10 --format json`

## Fase 2: Introspecção

Reflita sobre a sessão:
- Que padrões foram usados ou descobertos?
- Que decisões arquiteturais foram tomadas?
- Que problemas foram resolvidos?
- Que conhecimento de domínio foi adquirido?
- Alguma experiência vale preservar para reutilização?

## Fase 3: Encode no Cérebro (fonte primária)

O cérebro em `.claude/brain/` é a **fonte primária de conhecimento**. Todo aprendizado vai direto para o grafo.

### 3.1 Processar Novos Commits

```bash
python3 .claude/brain/populate.py refresh 20
```

### 3.2 Registrar Conhecimento Direto no Grafo

Para cada tipo de conhecimento descoberto, use `brain.add_memory()` diretamente:

```python
import sys
sys.path.insert(0, '.claude/brain')
from brain import Brain, get_current_developer

brain = Brain()
brain.load()
dev = get_current_developer()

# ADR (decisão arquitetural)
brain.add_memory(
    title="ADR-NNN: [Título da Decisão]",
    content="## Contexto\n[...]\n\n## Decisão\n[...]\n\n## Consequências\n[...]",
    labels=["Decision", "ADR"],
    author=dev["author"],
    props={"adr_id": "ADR-NNN", "status": "Aceito", "date": "YYYY-MM-DD"}
)

# Pattern (padrão aprovado)
brain.add_memory(
    title="PAT-NNN: [Nome do Padrão]",
    content="[Descrição, quando usar, exemplo]",
    labels=["Pattern", "ApprovedPattern"],
    author=dev["author"],
    props={"pat_id": "PAT-NNN"}
)

# Experience (experiência reutilizável)
brain.add_memory(
    title="EXP-NNN: [Título]",
    content="[Contexto, abordagem, resultado, aprendizado]",
    labels=["Episode", "Experience"],
    author=dev["author"],
    props={"exp_id": "EXP-NNN"}
)

# Concept (termo de domínio)
brain.add_memory(
    title="[Nome do Conceito]",
    content="[Definição e contexto]",
    labels=["Concept", "Glossary"],
    author="@engram"
)

# Bug fix episódico
brain.add_memory(
    title="Bug: [descrição curta]",
    content="[O que aconteceu, como foi resolvido, arquivos afetados]",
    labels=["Episode", "BugFix"],
    author=dev["author"],
    references=["[[ADR-001]]", "[[PAT-005]]"]  # opcional
)

brain.save()
```

### 3.3 Atualizar Knowledge Files

Os .md são o espelho legível do cérebro — mantidos em sincronia para fallback, git diffs e leitura humana.

**PRIORITY_MATRIX.md** — desprioritizar tarefas completadas, adicionar novas

**Knowledge files (atualizados quando houver conteúdo novo):**
- **PATTERNS.md** — patterns novos ou refinados
- **ADR_LOG.md** — decisões arquiteturais registradas
- **DOMAIN.md** — regras de negócio e glossário
- **EXPERIENCE_LIBRARY.md** — experiências reutilizáveis

O cérebro já contém tudo via `add_memory()` (passo 3.2). O sono enriquece com conexões semânticas. Os .md garantem que o conhecimento permanece acessível sem rodar Python.

## Fase 4: Consolidar

### 4.1 Ciclo de Sono (Consolidação Semântica)

```bash
python3 .claude/brain/sleep.py
```

Roda 5 fases in-memory (zero disk I/O): dedup, connect, relate, themes, calibrate.

### 4.2 Verificar Saúde do Cérebro

```bash
python3 .claude/brain/cognitive.py health
```

Se `health_score < 0.8`, seguir recomendações exibidas.

### 4.3 Atualizar Embeddings

```bash
python3 .claude/brain/embeddings.py build 2>/dev/null || echo "⚠️ Embeddings: instale sentence-transformers para busca semântica"
```

Embeddings agora usam conteúdo completo (até 1000 chars) para vetores mais ricos.

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
- O que foi registrado no cérebro (quantos nós criados, tipos)
- Sugestões evolutivas (novos skills, archives, composições)
- Próxima ação recomendada

Lembrete: o cérebro é a fonte primária. O recall temporal (`--recent 7d`) dá
ao Claude da próxima sessão o contexto de onde retomar.
