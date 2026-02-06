# Engram (Ouroboros) — Guia do Dia a Dia

> Como usar o Engram no trabalho real, do zero ao ciclo completo.

---

## O Ciclo Ouroboros

```
    ┌──────────────────────────────────────────┐
    │                                          │
    ▼                                          │
 SESSAO                                        │
    │                                          │
    ├─ 1. /status (onde estou?)                │
    ├─ 2. /recall (o que sei sobre isso?)      │
    ├─ 3. Trabalhar (codar, debugar, decidir)  │
    ├─ 4. /commit (salvar trabalho)            │
    ├─ 5. /learn (registrar tudo)              │
    │       │                                  │
    │       ├─ atualiza cerebro                │
    │       ├─ roda sono (conexoes)            │
    │       ├─ atualiza embeddings             │
    │       └─ registra evolucao               │
    │                                          │
    └──────── proxima sessao sabe mais ────────┘
```

Cada volta no ciclo deixa o sistema mais inteligente.
Nao e magica — e o `/learn` que fecha o loop.

---

## Fase 0: Instalacao (uma vez por projeto)

```bash
cd meu-projeto
# O dev roda o init-engram dentro do Claude Code
/init-engram
```

7 fases automaticas:
1. Analisa stack (Next.js, Flask, NestJS, etc.)
2. Gera knowledge files (CURRENT_STATE, PATTERNS, ADR_LOG, DOMAIN, PRIORITY_MATRIX, EXPERIENCE_LIBRARY)
3. Gera skills customizados para a stack
4. Gera agents especializados
5. Gera commands (/learn, /recall, /doctor, etc.)
6. Popula o cerebro com commits, ADRs, patterns
7. Limpa templates usados

**Resultado:** cerebro com ~100-200 nos, 15 commands, skills da stack.

Depois disso, o projeto esta pronto para o ciclo.

---

## Fase 1: Inicio de Sessao

### O que voce faz:
```
/status
```

### O que acontece:
O Claude consulta o cerebro (`recall --recent 7d`) e PRIORITY_MATRIX.md e mostra:
- Fase do projeto e saude do cerebro
- Top prioridades com ICE Score
- Bloqueios
- Sugestao concreta do que fazer

### Quando usar:
- **Sempre** ao abrir sessao nova
- Quando voltar de pausa longa
- Para decidir o que atacar

---

## Fase 2: Consultar o Cerebro

### O que voce faz:
```
/recall como funciona a autenticacao
```

### O que acontece:
1. Gera embedding da sua pergunta
2. Busca por similaridade semantica no grafo (194 nos)
3. Spreading activation — expande para nos conectados
4. Retorna resultados rankeados com conexoes
5. Reforça os nos acessados (auto-alimentacao)

### Resultado tipico:
```
🧠 Recall: "autenticacao"
═══════════════════════════════════════

📋 0.92 [ADR] ADR-008: Arquitetura Git-Native
   Decisao de usar git como backend...
   Conexoes: → PAT-014, → RN-035

📋 0.85 [Pattern] PAT-014: JWT Auth Pattern
   Usar jose library para tokens...
   Conexoes: → ADR-008, → EXP-017

📋 0.71 [Episode] EXP-017: Implementar recall
   Contexto: busca semantica no cerebro...
```

### Variantes:
```
/recall decisoes sobre banco --type ADR          # so ADRs
/recall autenticacao --depth 3                   # mais profundidade
/recall padrao de error handling --type Pattern   # so patterns
```

### Quando usar:
- Antes de implementar algo novo (ver se ja existe solucao)
- Quando encontrar um bug (ver se ja resolveram similar)
- Quando precisa tomar decisao arquitetural (ver ADRs)
- Quando nao lembra de algo (conceito, regra, termo)

### O que voce NAO precisa fazer:
O Claude usa `/recall` automaticamente quando voce faz perguntas como:
- "como funciona X?"
- "por que foi feito assim?"
- "qual a regra de cancelamento?"

---

## Fase 3: Trabalhar

### Fluxo normal de trabalho:

**Codar** — implementar a feature/fix normalmente.

**Decisao arquitetural?** O Claude:
1. Roda `/recall` para ver ADRs existentes
2. Se nao tem ADR: propoe registrar uma nova
3. Implementa seguindo a decisao

**Precisa de expertise que nao existe?** O Claude:
1. Lista agents/skills existentes
2. Se nenhum cobre: anuncia ao dev
3. Cria via `/spawn agent nome proposito`
4. Delega a tarefa ao componente novo
5. Maximo 2 spawns por sessao

**Review antes de commit:**
```
/review
```
Pipeline: correcao → padroes → seguranca → performance.
Veredito: aprovado / sugestoes / requer mudancas.

### Commands disponiveis durante o trabalho:

| Command | Quando usar |
|---------|-------------|
| `/recall [tema]` | Buscar conhecimento no cerebro |
| `/domain [termo]` | Investigar termo de negocio, regra, entidade |
| `/review` | Code review dos arquivos alterados |
| `/plan [feature]` | Planejar implementacao antes de codar |
| `/priorities` | Reavaliar prioridades com ICE Score |
| `/create [tipo] [nome]` | Criar skill/agent/command novo (interativo) |
| `/spawn [tipo] [nome] [motivo]` | Criar componente rapido no meio do trabalho |
| `/doctor` | Diagnosticar saude do Engram |
| `/curriculum` | Ver cobertura de skills e gaps |

---

## Fase 4: Commit

### O que voce faz:
```
/commit
```

### O que acontece:
1. Claude analisa o diff
2. Gera mensagem Conventional Commits (ingles):
   ```
   tipo(escopo): descricao curta

   corpo opcional explicando o "porque"
   ```
3. Mostra a mensagem para voce aprovar/ajustar
4. Faz o commit
5. Sugere: "Quer rodar /learn para registrar?"

### Tipos de commit:
`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`, `ci`, `build`

---

## Fase 5: Aprender (/learn)

**Este e o coracao do Ouroboros.** Sem ele o ciclo nao fecha.

### O que voce faz:
```
/learn
```

### O que acontece (6 fases automaticas):

#### Fase 1 — Coleta
```
git diff, git log → o que mudou nesta sessao?
```

#### Fase 2 — Introspeccao
Claude reflete:
- Que padroes foram usados?
- Que decisoes foram tomadas?
- Que problemas foram resolvidos?
- Que conhecimento de dominio surgiu?

#### Fase 3 — Encode no Cerebro
Para cada tipo de conhecimento:

| Tipo | Label | Exemplo |
|------|-------|---------|
| Decisao arquitetural | ADR, Decision | "ADR-015: Usar Redis para cache" |
| Pattern aprovado | Pattern, ApprovedPattern | "PAT-037: Retry com backoff exponencial" |
| Experiencia | Episode, Experience | "EXP-024: Debug de memory leak no worker" |
| Conceito/Termo | Concept, Glossary | "Idempotencia" |
| Bug fix | Episode, BugFix | "Bug: race condition no checkout" |

Tudo vai para o grafo via `brain.add_memory()`.

Atualiza tambem:
- **PRIORITY_MATRIX.md** — completa tarefas, adiciona novas

#### Fase 4 — Consolidar

**4.1 Processar commits:**
```
populate.py commits 20 → cria nos para commits recentes
```

**4.2 Ciclo de Sono (5 fases):**

| Fase | O que faz | Resultado |
|------|-----------|-----------|
| dedup | Encontra nos duplicados e faz merge | Grafo mais limpo |
| connect | Descobre refs cruzadas (ADR-xxx, PAT-xxx, [[wikilinks]]) | Arestas REFERENCES, SAME_SCOPE, MODIFIES_SAME |
| relate | Cosine similarity entre embeddings | Arestas RELATED_TO |
| themes | Agrupa commits por scope | Nos Theme + arestas BELONGS_TO_THEME |
| calibrate | Ajusta pesos por frequencia de acesso | Nos usados ficam mais fortes |

**4.3 Health check:**
```
cognitive.py health → score de 0 a 1
```

**4.4 Embeddings:**
```
embeddings.py build → vetores para busca semantica
```

#### Fase 5 — Evolucao
- Registra skills usados nesta sessao
- Detecta co-ativacoes (skills usados juntos)
- Verifica componentes subutilizados (stale)
- Propoe composicoes se co-ativacao >= 3 sessoes

#### Fase 6 — Resumo
Apresenta tudo ao dev:
- O que foi registrado (nos, arestas, tipos)
- Metricas (health score, edges semanticas)
- Sugestoes evolutivas
- Proxima acao recomendada

---

## Fase 6: Proxima Sessao

O Claude abre com todo o contexto:

```
recall --recent 7d → onde o projeto esta (cerebro e fonte primaria)
PRIORITY_MATRIX.md → o que fazer a seguir
/recall "tema" → busca qualquer duvida no cerebro
```

**Nada se perde entre sessoes.** Cada /learn e um snapshot completo.

---

## Comandos — Referencia Rapida

### Rotina (usa todo dia)
| Command | Uso | Frequencia |
|---------|-----|------------|
| `/status` | Ver estado do projeto | Inicio de sessao |
| `/recall [tema]` | Consultar cerebro | Quando precisar |
| `/commit` | Salvar trabalho | Apos implementar |
| `/learn` | Fechar o ciclo | **Final de toda sessao** |

### Sob demanda (usa quando precisa)
| Command | Uso | Quando |
|---------|-----|--------|
| `/review` | Code review | Antes de commit importante |
| `/domain [termo]` | Investigar negocio | Termo desconhecido |
| `/plan [feature]` | Planejar implementacao | Feature complexa |
| `/priorities` | Reavaliar ICE Scores | Quando contexto muda |
| `/create [tipo] [nome]` | Criar componente | Necessidade recorrente |
| `/spawn [tipo] [nome]` | Criar rapido | No meio do trabalho |

### Manutencao (usa ocasionalmente)
| Command | Uso | Quando |
|---------|-----|--------|
| `/doctor` | Health check do Engram | Suspeita de problema |
| `/curriculum` | Gaps de skills | Querer expandir |
| `/export` | Exportar para global | Compartilhar entre projetos |
| `/import` | Importar da global | Reaproveitar skill |

---

## O Cerebro por Dentro

### Estrutura
```
.claude/brain/
├── graph.json        ← O grafo (nos + arestas)
├── embeddings.npz    ← Vetores para busca semantica
├── brain.py          ← Nucleo (operacoes de grafo)
├── sleep.py          ← 5 fases de consolidacao
├── recall.py         ← Interface de busca
├── cognitive.py      ← Decay, consolidacao, health
├── populate.py       ← Importa de .md → grafo
├── embeddings.py     ← Gera vetores
└── maintain.sh       ← Manutencao (decay, consolidate)
```

### Tipos de No
| Tipo | O que armazena | Decay |
|------|---------------|-------|
| Person | Desenvolvedores | Quase nunca esquece (0.0001/dia) |
| Decision/ADR | Decisoes arquiteturais | Muito lento (0.001/dia) |
| Concept/Glossary | Termos e definicoes | Lento (0.003/dia) |
| Pattern | Padroes de codigo | Moderado (0.005/dia) |
| Episode/Commit | Eventos e mudancas | Rapido (0.01/dia) |
| Theme | Agrupamento de commits | Moderado (0.005/dia) |

### Tipos de Aresta

**Estruturais** (criadas no populate):
- `AUTHORED_BY` — quem criou o no
- `BELONGS_TO` — a que dominio pertence

**Semanticas** (criadas no sono):
- `REFERENCES` — ref cruzada explicita (ADR cita PAT)
- `INFORMED_BY` — pattern informado por ADR
- `APPLIES` — commit aplica pattern
- `RELATED_TO` — similaridade semantica (embeddings)
- `SAME_SCOPE` — commits no mesmo scope (feat(auth))
- `MODIFIES_SAME` — commits que tocam mesmos arquivos
- `BELONGS_TO_THEME` — commit pertence a tema
- `CLUSTERED_IN` — pattern pertence a cluster

**Operacional** (criada no consolidate):
- `CO_ACCESSED` — nos consultados juntos via /recall

### Spreading Activation
Quando voce faz `/recall "auth"`:
1. Encontra nos seed por embedding (top 5)
2. Propaga ativacao pelos vizinhos (decay 0.5 por hop)
3. Maximo 3 niveis de profundidade
4. Resultado: nos que voce NAO buscou mas sao relevantes

### Esquecimento (Ebbinghaus)
```
forca = e^(-taxa_decay × dias_sem_acesso)
```
- Cada `/recall` reforça o no (+5% forca)
- Nos que caem abaixo de 0.3 viram "WeakMemory"
- Nos abaixo de 0.1 sao candidatos a archive

---

## Exemplo Real: Um Dia Tipico

### 09:00 — Abrir sessao
```
Dev: /status

Claude:
🐍 Status: meu-projeto
Fase: v2.1 — API estavel  |  Saude: 🟢 0.93
Ultimo commit: abc1234 fix(auth): token expiry

📋 Top Prioridades:
  1. [ICE: 14.0] Implementar 2FA — pendente
  2. [ICE: 11.2] Testes de integracao — pendente

💡 Proxima acao: Implementar 2FA (maior ICE)
```

### 09:05 — Entender o contexto
```
Dev: como funciona a autenticacao atual?

Claude automaticamente roda /recall "autenticacao"
→ Encontra ADR-008, PAT-014, EXP-017
→ Responde com contexto completo do cerebro
```

### 09:15 — Planejar
```
Dev: /plan 2FA com TOTP

Claude: [plano de implementacao baseado no /recall]
```

### 09:30–12:00 — Implementar
```
Dev: implementa o plano

Claude: [usa patterns existentes, consulta /recall quando precisa]
       [se precisar de expertise nova, /spawn agent security-expert]
```

### 12:00 — Review + Commit
```
Dev: /review
Claude: ✅ APROVADO — seguranca OK, patterns seguidos

Dev: /commit
Claude: feat(auth): add TOTP-based 2FA with QR code generation
        → Quer rodar /learn?
```

### 12:05 — Fechar o ciclo
```
Dev: /learn

Claude:
[Fase 1] Coleta: 3 commits, 8 arquivos alterados
[Fase 2] Introspeccao: ADR-016 (TOTP), PAT-038 (2FA flow), EXP-025 (QR gen)
[Fase 3] Encode: 5 nos criados no cerebro
[Fase 4] Sono: +12 arestas semanticas, health 0.95
[Fase 5] Evolucao: security-expert (runtime) — manter ou aposentar?

📊 Resumo:
  Cerebro: 199 nos, 468 arestas (164 semanticas)
  Health: 0.95 🟢
  Proxima acao: Testes de integracao (ICE 11.2)
```

### Amanha 09:00
```
Dev: /status
→ Sabe tudo sobre o 2FA implementado ontem
→ Sugere comecar pelos testes de integracao
→ /recall encontra EXP-025 se precisar relembrar detalhes
```

---

## Regras de Ouro

1. **Sempre rode /learn ao final da sessao** — sem ele o ciclo nao fecha
2. **Confie no /recall** — ele sabe mais do que voce lembra
3. **Nao edite graph.json na mao** — use brain.add_memory() ou populate.py
4. **Os .md sao a fonte canonica** — se apagar o cerebro, `populate.py all` recria
5. **Cada sessao alimenta a proxima** — quanto mais /learn, mais inteligente

---

## Recuperacao

| Problema | Solucao |
|----------|---------|
| Cerebro corrompido | `python3 .claude/brain/populate.py all` recria do zero |
| Health baixo (< 0.8) | `python3 .claude/brain/sleep.py` + `embeddings.py build` |
| Muitas WeakMemory | `python3 .claude/brain/cognitive.py consolidate` |
| Embeddings desatualizados | `python3 .claude/brain/embeddings.py build` |
| Componente quebrado | `/doctor` diagnostica e sugere fix |
| Nao sei o que fazer | `/status` + `/priorities` |
