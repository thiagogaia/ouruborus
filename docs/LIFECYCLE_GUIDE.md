# Engram/Ouroboros — Guia do Ciclo de Vida Completo

> Documento gerado em 2026-02-05. Descreve o fluxo real de uso do sistema.

---

## Visao Geral

```
Instalar → Trabalhar → Aprender → Evoluir → Dormir → Repetir
   ↑                                                    |
   └────────────── cada sessao mais inteligente ←───────┘
```

---

## ATO 1: Instalacao (uma unica vez)

```bash
$ git clone git@github.com:meu-org/meu-projeto.git
$ cd meu-projeto
$ /init-engram
```

O `/init-engram` roda 8 fases automaticas:

0. **Migracao de backup** — detecta instalacao anterior, faz backup antes de sobrescrever
1. **Analisa o projeto** — detecta stack (Next.js, Flask, NestJS, etc.)
2. **Apresenta plano** — mostra o que sera gerado para aprovacao do dev
3. **Auto-geracao via Genesis** — gera skills, agents, commands baseados na stack
4. **Popula knowledge** — CURRENT_STATE.md, PRIORITY_MATRIX.md (boot files)
5. **Popula o cerebro** — le commits, ADRs, patterns, regras de negocio → grafo via `brain.add_memory()`
6. **Health check** — verifica saude do cerebro recem-populado
7. **Cleanup e relatorio** — remove scaffolds ja usados, apresenta resumo

**Resultado:** `.claude/` populado, cerebro com ~100-200 nos, CLAUDE.md com instrucoes.

---

## ATO 2: Inicio de Sessao

O dev abre o Claude Code e pede uma feature. O Claude automaticamente:

### Passo 1: Le os Boot Files
```
CURRENT_STATE.md   → onde o projeto esta agora
PRIORITY_MATRIX.md → prioridades atuais
```
Esses dois .md vem de `templates/knowledge/` (instalados pelo setup.sh). Sao pequenos por design — reescritos a cada /learn.

### Passo 2: Consulta o Cerebro (fonte unica)
```
/recall "tema da tarefa"
```
Retorna nos relevantes COM conexoes semanticas e conteudo completo:
- ADRs relacionados
- Bugs anteriores no mesmo escopo
- Regras de negocio aplicaveis
- Patterns aprovados

### Passo 3: Entende o contexto completo antes de codificar

---

## ATO 3: Trabalho na Feature

### Decisao Arquitetural
Se ha decisao a tomar:
- Consulta ADRs existentes via /recall
- Registra nova ADR antes de implementar

### Orquestracao Runtime
Se precisa de expertise nao coberta:
- Claude cria skill/agent sob demanda via engram-genesis
- Registra no manifest com `source=runtime`
- Maximo 2 componentes por sessao

### Implementacao
- Usa skills existentes
- Delega a agents especializados
- Segue patterns do PATTERNS.md

### Review
```
/review
```
Pipeline: correcao → padroes → seguranca → performance

---

## ATO 4: Commit

```
/commit
```
Gera mensagem semantica automatica baseada no diff.

---

## ATO 5: Aprendizado (/learn) — Final da Sessao

### Fase 1: Coleta
```bash
git diff --stat HEAD~5
git log --oneline -10
```

### Fase 2: Introspeccao
Claude reflete: patterns, decisoes, problemas, conhecimento de dominio.

### Fase 3: Encode no Cerebro
Todo conhecimento vai direto para o grafo via `brain.add_memory()`:
```python
brain.add_memory(title="ADR-015: ...", labels=["ADR", "Decision"], content="...")
brain.add_memory(title="PAT-037: ...", labels=["Pattern", "ApprovedPattern"], content="...")
brain.add_memory(title="Bug: ...", labels=["Episode", "BugFix"], content="...")
```
Os boot files (CURRENT_STATE.md, PRIORITY_MATRIX.md) sao atualizados separadamente — sao os unicos .md mantidos pequenos para leitura rapida.

### Fase 4: Alimentar o Cerebro

#### 4.1 Processar commits + cross-refs
```bash
python3 .claude/brain/populate.py refresh
```

#### 4.2 Memorias episodicas (bugs, solucoes)
```python
brain.add_memory(title="Bug: ...", labels=["Episode", "BugFix"])
```

#### 4.3 Memorias conceituais (glossario)
```python
brain.add_memory(title="Conceito X", labels=["Concept", "Glossary"])
```

#### 4.4 Consolidacao leve
```bash
python3 .claude/brain/cognitive.py consolidate
```

#### 4.4b SONO — Consolidacao Semantica
```bash
python3 .claude/brain/sleep.py
```

5 fases do sono:

| Fase | Funcao |
|------|--------|
| **dedup** | Encontra e merge nos duplicados |
| **connect** | Descobre refs cruzadas (ADR-xxx, PAT-xxx, [[wikilinks]]), SAME_SCOPE, MODIFIES_SAME |
| **relate** | Cosine similarity entre embeddings → RELATED_TO |
| **themes** | Agrupa commits por scope → Theme nodes |
| **calibrate** | Ajusta pesos por frequencia de acesso |

**Resultado:** conexoes que nenhum humano escreveu. O sistema descobre sozinho que Bug X esta ligado ao ADR Y.

#### 4.5 Health Check
```bash
python3 .claude/brain/cognitive.py health
```

#### 4.6 Embeddings
```bash
python3 .claude/brain/embeddings.py build
```

### Fase 5: Evolucao
```bash
# Rastreia uso de skills
python3 .claude/skills/engram-genesis/scripts/register.py --activate --type skill --name [nome]

# Detecta co-ativacoes
python3 co_activation.py --log-session --skills [skill1],[skill2]

# Verifica componentes subutilizados
python3 track_usage.py --report stale
```

### Fase 6: Resumo ao Dev
Apresenta tudo que foi registrado + sugestoes evolutivas.

---

## ATO 6: Proxima Sessao

O Claude consulta o cerebro e **sabe tudo** da sessao anterior:
- Decisoes tomadas e seus trade-offs
- Bugs resolvidos e como foram resolvidos
- Regras de negocio descobertas
- Connections semanticas entre tudo isso

**Cada sessao comeca onde a anterior parou.**

---

## Arquitetura Brain-Only

```
cerebro (graph.json)  = FONTE UNICA DE VERDADE (conteudo em props.content)
boot files (.md)      = CURRENT_STATE.md + PRIORITY_MATRIX.md (leitura rapida)
knowledge files (.md) = legado — conteudo ja migrado para o grafo
```

### Fluxo de Dados

```
brain.add_memory() ──────────────────→ Conteudo direto no grafo (props.content)
                                              ↓
populate.py refresh ─── git log ────→ Commit nodes + cross-refs
                                              ↓
                                         sleep.py
                                     (le .md canonicos para
                                      descobrir REFERENCES)
                                              ↓
                                    Conexoes Semanticas
                                    (RELATED_TO, SAME_SCOPE,
                                     MODIFIES_SAME, REFERENCES,
                                     BELONGS_TO_THEME, CLUSTERED_IN)
                                              ↓
                                      embeddings.py build
                                              ↓
                                    Vetores para busca semantica
```

O loop auto-alimentado:
1. `/recall` busca → reforca memorias acessadas → **persiste** (brain.save())
2. Trabalho acontece → novas memorias via `brain.add_memory()` (zero disk I/O)
3. `/learn` consolida → sleep in-memory → embeddings mais ricos
4. Proximo recall acha resultados melhores (memorias reforcadas + novas conexoes)

### Capacidades do Cerebro

| Capacidade | Descricao |
|---|---|
| Armazenamento de conteudo | Texto completo em `props.content` — recall retorna campo `content` |
| Busca por similaridade | Embeddings (sentence-transformers) — cosine similarity |
| Conexoes semanticas | Criadas pelo sleep.py — 8 tipos de aresta |
| Travessia de grafo | Spreading activation — encontra conhecimento indireto |
| Pesos de relevancia | Calibrate ajusta por frequencia de acesso |
| Performance | Constante (~200ms) independente do tamanho do grafo |

### Boot Files (.md)

Apenas dois .md sao mantidos ativamente:
- **CURRENT_STATE.md** — snapshot do estado do projeto (leitura no inicio de sessao)
- **PRIORITY_MATRIX.md** — tarefas priorizadas com ICE Score

Sao pequenos por design. Todo o resto (ADRs, patterns, experiencias, dominio) vive no cerebro.

### Escalabilidade

O cerebro escala sem degradacao:
- **~100 nos:** busca instantanea, conexoes visiveis
- **~500 nos:** spreading activation revela padroes nao-obvios
- **~1000+ nos:** embeddings sao essenciais para filtrar ruido
- **Sem limite pratico:** grafo em memoria, busca O(n) com vetores

Os boot files (.md) nunca crescem — sao reescritos a cada /learn.

### Regra de Ouro

> O cerebro e a fonte unica de verdade. Conteudo vive em `props.content`.
> Se apagar o cerebro: `populate.py migrate` recria a partir dos .md legados.
> Se apagar os .md legados: o cerebro continua funcionando normalmente.

---

## Tipos de Aresta Semantica (criadas pelo Sono)

| Tipo | Significado | Exemplo |
|------|-------------|---------|
| REFERENCES | Ref cruzada explicita | ADR-015 cita [[RN-035]] |
| INFORMED_BY | Pattern informado por ADR | PAT-014 ← ADR-015 |
| APPLIES | Commit aplica Pattern | commit abc ← PAT-014 |
| RELATED_TO | Similaridade semantica | "JWT auth" ~ "2FA TOTP" |
| SAME_SCOPE | Mesmo scope de commit | feat(auth): X ~ feat(auth): Y |
| MODIFIES_SAME | Tocam mesmos arquivos | commit A e B ambos tocam auth.ts |
| BELONGS_TO_THEME | Commit pertence a Theme | commit → Theme:auth |
| CLUSTERED_IN | Pattern em cluster | PAT-014 → Cluster:security |

---

## Metricas de Saude

```bash
python3 .claude/brain/cognitive.py health
```

| Metrica | Peso | O que mede |
|---|---|---|
| Weak memory ratio | 30% | % de memorias fracas (peso < 0.3) |
| Semantic connectivity | 40% | % de nos com arestas semanticas |
| Embedding coverage | 30% | % de nos com embeddings |

| Score | Status | Acao |
|---|---|---|
| > 0.9 | healthy | Nenhuma |
| 0.7-0.9 | needs_attention | Rodar sleep.py |
| < 0.7 | critical | Rodar populate + sleep + embeddings build |

---

## Referencia de CLI Completa

### brain.py
```bash
python3 .claude/brain/brain.py stats          # Estatisticas do grafo
python3 .claude/brain/brain.py search "termo" # Busca por titulo
python3 .claude/brain/brain.py add "titulo"   # Adiciona no via CLI
python3 .claude/brain/brain.py load           # Carrega grafo do disco
python3 .claude/brain/brain.py save           # Persiste grafo no disco
python3 .claude/brain/brain.py consolidate    # Consolida conexoes
python3 .claude/brain/brain.py decay          # Aplica curva de esquecimento
```

### cognitive.py
```bash
python3 .claude/brain/cognitive.py health      # Health check completo
python3 .claude/brain/cognitive.py consolidate  # Consolidacao leve
python3 .claude/brain/cognitive.py decay        # Curva de Ebbinghaus
python3 .claude/brain/cognitive.py archive      # Arquiva memorias fracas
python3 .claude/brain/cognitive.py sleep        # Roda ciclo de sono completo
python3 .claude/brain/cognitive.py daily        # Manutencao diaria (decay + consolidate)
python3 .claude/brain/cognitive.py weekly       # Manutencao semanal (daily + archive)
```

### embeddings.py
```bash
python3 .claude/brain/embeddings.py build              # Gera vetores para todos os nos
python3 .claude/brain/embeddings.py search "consulta"  # Busca semantica direta
```

### recall.py
```bash
python3 .claude/brain/recall.py "pergunta"                      # Busca legivel
python3 .claude/brain/recall.py "pergunta" --top 10 --format json  # JSON parseavel
python3 .claude/brain/recall.py "pergunta" --type ADR --top 5   # Filtro por tipo
```

### sleep.py
```bash
python3 .claude/brain/sleep.py           # Roda todas as 5 fases
python3 .claude/brain/sleep.py --phase dedup     # Roda fase especifica
python3 .claude/brain/sleep.py --phase connect
python3 .claude/brain/sleep.py --phase relate
python3 .claude/brain/sleep.py --phase themes
python3 .claude/brain/sleep.py --phase calibrate
```

### populate.py
```bash
python3 .claude/brain/populate.py refresh       # Modo recorrente (commits + cross-refs)
python3 .claude/brain/populate.py migrate       # Migracao unica (.md → grafo)
python3 .claude/brain/populate.py commits 20    # Processar N commits recentes
python3 .claude/brain/populate.py stats         # Estatisticas de populacao
python3 .claude/brain/populate.py all           # Rodar todas as funcoes de populacao
```
