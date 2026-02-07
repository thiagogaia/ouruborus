# Análise Profunda do Engram v3.0.0

## 1. Filosofia Ouroboros — A Serpente que Come a Própria Cauda

O Engram é um sistema de **memória organizacional auto-alimentada**. A metáfora do Ouroboros não é decorativa — ela é a arquitetura:

```
Trabalho gera Conhecimento
    ↓
Conhecimento alimenta o Cérebro
    ↓
Cérebro informa o próximo Trabalho
    ↓
Trabalho gera Conhecimento melhor
    ↓
(loop infinito, cada ciclo mais inteligente)
```

O ciclo fecha porque **nenhuma etapa é opcional**. O CLAUDE.md impõe um workflow mandatório: antes de codificar consulte o cérebro, depois de codificar alimente-o. Sem disciplina, o Ouroboros morre.

---

## 2. Metacircularidade — O Sistema Gera a Si Mesmo

Três camadas de metacircularidade:

| Camada | Como funciona |
|--------|---------------|
| **Componentes** | `engram-genesis` gera skills/agents/commands seguindo schemas em `.claude/schemas/`. Pode gerar versões atualizadas de **si mesmo**. |
| **Runtime** | Se Claude detecta que nenhum componente existente cobre uma tarefa, ele **cria um novo** em tempo real (max 2/sessão, sempre anuncia antes). |
| **Evolução** | `engram-evolution` monitora uso, propõe composições, aposenta inúteis. O sistema se **poda** sozinho. |

O fluxo é: **schema define → genesis gera → evolution avalia → genesis regera**. O Engram é um compilador de si mesmo.

---

## 3. A Arquitetura do Cérebro

O cérebro é um **grafo de propriedades híbrido** em SQLite v2:

```
NODOS (283+)
├── Decision/ADR (24 ADRs, decay 0.001 — quase permanentes)
├── Pattern (53 padrões, decay 0.005)
├── Concept/Glossary (107 termos de domínio, decay 0.003)
├── Episode/Commit (82 episódios, 53 commits, decay 0.01 — memória curta)
├── Experience (24 experiências, decay 0.01)
├── Theme (4 sintéticos, agrupam commits por escopo)
├── PatternCluster (5, agrupam patterns por domínio)
└── Person (3 desenvolvedores, decay 0.0001 — nunca esquecem)
```

### Arestas (776 total)

```
ARESTAS ESTRUTURAIS (468)
├── AUTHORED_BY (270) — Nó → Pessoa
└── BELONGS_TO (198) — Nó → Domínio

ARESTAS SEMÂNTICAS (308)
├── REFERENCES (88) — referência cruzada (ADR cita Pattern)
├── RELATED_TO (59) — Similaridade semântica (embeddings ≥ 0.75)
├── MODIFIES_SAME (47) — Commits que tocam mesmos arquivos
├── CLUSTERED_IN (47) — Pattern → PatternCluster
├── SAME_SCOPE (40) — Commits no mesmo escopo
└── BELONGS_TO_THEME (27) — Commit → Theme
```

### Mecanismo de Busca (3 estratégias combinadas)

1. **Embedding search**: vetores de 384 dimensões (sentence-transformers local), similaridade por cosseno
2. **Spreading activation**: a partir dos seeds, propaga sinal pelo grafo com decay de 50% por nível. Arestas com peso alto conduzem mais sinal. Nós fracos conduzem menos.
3. **Fallback textual**: FTS5 (BM25) ou LIKE se embeddings não disponíveis

**Score final** = `(similaridade_embedding × 2) + soma(ativação_espalhada)`

### Curva de Esquecimento (Ebbinghaus)

```
strength_novo = strength_antigo × e^(-taxa_decay × dias_sem_acesso)
```

- Cada `/recall` **reforça** os top 10 resultados (+5% strength)
- Sem acesso, memórias decaem naturalmente
- `strength < 0.3` → marca como WeakMemory
- `strength < 0.1` → candidata a arquivo

Isso significa: **o que você consulta se fortalece, o que ignora enfraquece**. O cérebro auto-curada sua relevância.

---

## 4. O Pipeline de Inicialização

### Fase 1: `setup.sh` — Infraestrutura (1019 linhas)

```
setup.sh [diretório]
    │
    ├── Detecção de stack (linguagem, framework, ORM, auth, CI/CD, infra)
    ├── Instala DNA (4 schemas: skill, agent, command, knowledge)
    ├── Instala core (genesis + evolution)
    ├── Instala 7 seeds universais (project-analyzer, knowledge-manager, etc.)
    ├── Instala 3 agents (architect, db-expert, domain-analyst)
    ├── Instala 15 commands (/learn, /recall, /create, etc.)
    ├── Cria templates de conhecimento (6 .md vazios)
    ├── Copia brain scripts (7 Python modules)
    ├── Cria .venv isolado + instala numpy, networkx, sentence-transformers
    ├── Gera CLAUDE.md (stack-aware, com workflow obrigatório)
    ├── Gera settings.json (permissões de segurança)
    └── Inicializa manifest.json (registro de componentes)
```

**O que setup.sh NÃO faz**: não analisa o código, não gera skills customizados, não popula o cérebro. Ele apenas instala a infraestrutura.

### Fase 2: `/init-engram` — Análise + Geração + População (7 fases)

```
/init-engram
    │
    ├── Fase 0: Migração de backup (se .claude.bak/ existe → SMART merge)
    ├── Fase 1: Análise profunda do projeto (analyze_project.py)
    ├── Fase 2: Apresenta plano de geração → pede aprovação
    ├── Fase 3: Auto-gera skills/agents/commands customizados
    │           (template → customize → validate → register)
    ├── Fase 4: Popula knowledge files
    │           ├── CURRENT_STATE.md (snapshot do codebase)
    │           ├── PATTERNS.md (padrões detectados no código)
    │           ├── DOMAIN.md (glossário + regras de negócio)
    │           ├── ADR_LOG.md (decisões arquiteturais)
    │           ├── EXPERIENCE_LIBRARY.md (experiências)
    │           └── PRIORITY_MATRIX.md (TODOs + ICE score)
    ├── Fase 5: Popula o cérebro
    │           ├── populate.py all → parseia .md → cria nós no grafo
    │           ├── git log → parseia commits → cria nós Episode/Commit
    │           ├── embeddings.py build → gera vetores semânticos
    │           └── cognitive.py health → valida saúde
    ├── Fase 6: /doctor → health check
    └── Fase 7: Cleanup + relatório + próximos passos
```

**Este é o momento chave**: os .md files alimentam o cérebro pela primeira e **única** vez. A partir daqui, o cérebro é a fonte primária.

---

## 5. O Ciclo de Retroalimentação (Loop Contínuo)

### Antes de Codificar (consumo)
```bash
python3 .claude/brain/recall.py --recent 7d --type Commit --top 10 --format json
python3 .claude/brain/recall.py "<tema>" --top 10 --format json
```

### Depois de Codificar (alimentação)
```bash
# Registra direto no cérebro (zero I/O em disco)
brain.add_memory(title="...", content="...", labels=["Pattern", "ApprovedPattern"])
```

### `/learn` (consolidação — 6 fases)
```
1. Coleta: git diff + git log + recall recent
2. Introspecção: que padrões, decisões, experiências surgiram?
3. Encode: brain.add_memory() para cada tipo
4. Sleep: 5 fases de consolidação semântica
   ├── DEDUP — remove duplicatas (merge nós com mesmo título)
   ├── CONNECT — descobre referências cruzadas (ADR→Pattern→Commit)
   ├── RELATE — cria RELATED_TO via similaridade de embeddings (≥0.75)
   ├── THEMES — agrupa commits em temas sintéticos
   └── CALIBRATE — ajusta pesos das arestas por padrão de acesso
5. Rebuild: embeddings.py build + cognitive.py health
6. Evolution: analisa componentes, propõe melhorias/aposentadorias
```

### O Loop Fecha Assim:

```
/recall busca → reforça memórias acessadas (strength × 1.05)
    ↓
Trabalho acontece → novas memórias via brain.add_memory()
    ↓
/learn consolida → sleep 5 fases → embeddings mais ricos
    ↓
Próximo /recall acha resultados melhores
    ↓
(volta ao início, cada ciclo mais preciso)
```

---

## 6. Consumo de Conhecimento Externo

O sistema **pode consumir** conhecimento externo de duas formas:

### Via populate.py (bootstrap)
Parseia arquivos .md com formatos específicos:
- `## ADR-NNN: Título` → nó Decision/ADR
- Seções de glossário → nós Concept/Glossary
- Regras de negócio → nós Concept/Rule
- Padrões aprovados → nós Pattern/ApprovedPattern

### Via brain.add_memory() (runtime)
Qualquer conteúdo pode ser ingerido diretamente:
```python
brain.add_memory(
    title="Padrão externo: Circuit Breaker",
    content="Conteúdo completo do padrão...",
    labels=["Pattern", "ApprovedPattern"],
    props={"source": "external", "pat_id": "PAT-EXT-001"}
)
```

### Via /ingest (command)
Existe o comando `/ingest` e o skill `base-ingester` para processar dados externos de forma estruturada.

---

## 7. Arquitetura de Dados — Três Camadas de Persistência

| Camada | O que armazena | Quando atualiza | Para que serve |
|--------|---------------|-----------------|----------------|
| **Brain** (SQLite + embeddings) | Grafo completo com conteúdo | Cada /learn | Fonte primária — todas as queries |
| **Knowledge files** (.md) | Espelho legível do brain | Genesis-only (5 de 6) | Fallback, git diffs, leitura humana |
| **Memory files** (.md) | Nós individuais como arquivos | Cada brain.add_memory() | Rebuild do brain, traceabilidade git |

**PRIORITY_MATRIX.md** é a exceção: único .md ativamente atualizado, pois prioridades são voláteis e precisam de visibilidade humana constante.

---

## 8. Visão Sistêmica Completa

```
                    ┌──────────────────────────────────┐
                    │           OUROBOROS               │
                    │     (Auto-Alimentação Perpétua)   │
                    └──────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ↓                           ↓                           ↓
   ┌─────────┐              ┌──────────────┐            ┌───────────┐
   │ GENESIS │              │    BRAIN     │            │ EVOLUTION │
   │ (criar) │              │  (memória)   │            │ (adaptar) │
   └────┬────┘              └──────┬───────┘            └─────┬─────┘
        │                          │                          │
   setup.sh                   recall.py                 track_usage.py
   /init-engram               sleep.py                  co_activation.py
   /create                    cognitive.py              doctor.py
   generate_component.py      embeddings.py             curriculum.py
   validate.py                populate.py               archive.py
   register.py                brain_sqlite.py           global_memory.py
        │                          │                          │
        └──────────────┬───────────┘                          │
                       │                                      │
              ┌────────┴─────────┐                           │
              │ KNOWLEDGE CYCLE  │ ←─────────────────────────┘
              │                  │
              │  /recall → work  │
              │  → add_memory   │
              │  → /learn       │
              │  → sleep        │
              │  → better recall│
              └──────────────────┘
```

---

## 9. Pontos Fortes e Fragilidades

### Pontos Fortes

1. **Self-healing memory**: o que é acessado se fortalece, o que ignora enfraquece
2. **Zero infraestrutura externa**: tudo roda local (SQLite + sentence-transformers)
3. **195 testes passando**: brain system é robusto e testado
4. **Deterministic IDs**: `md5(title|labels)` garante idempotência — re-rodar populate não duplica
5. **Graceful fallbacks**: sem numpy → TF-IDF; sem FTS5 → LIKE; sem brain.db → auto-cria

### Fragilidades (operacionais, não arquiteturais)

1. **3 skills com 0 ativações** (priority-engine, code-reviewer, engram-factory): subutilizados, se provam ou são aposentados com o uso
2. **Sem edges CO_ACCESSED**: surgem naturalmente com mais ciclos de uso
3. **Sem edges INFORMED_BY / APPLIES**: dependem de referências explícitas no conteúdo, melhoram com `/learn`
4. **manifest.json sem backup**: baixo risco, melhoria futura

---

## 10. Estado Atual do Cérebro (2026-02-06)

| Métrica | Valor | Status |
|---------|-------|--------|
| Nós | 283 | OK |
| Arestas | 776 (308 semânticas) | OK |
| Embeddings | 283/283 (100%) | OK |
| Memórias fracas | 0 | OK |
| Grau médio | 5.48 | OK |
| Health score | **1.0** | Perfeito |
| Recall temporal | Funcionando | OK |
| Recall semântico | Funcionando | OK |

---

## 11. Resumo Conceitual

O Engram é, na essência, um **sistema nervoso artificial para projetos de software**:

- **setup.sh** = nascimento (instala órgãos)
- **/init-engram** = primeiro sopro de vida (popula memória com o que já existe)
- **brain** = cérebro (armazena, conecta, esquece, consolida)
- **recall** = percepção (consulta antes de agir)
- **add_memory** = aprendizado (registra experiências)
- **/learn** = sono REM (consolida, conecta, fortalece, poda)
- **evolution** = adaptação (o sistema evolui seus próprios componentes)
- **genesis** = reprodução (gera novos componentes quando precisa)

A filosofia Ouroboros garante que **cada sessão de trabalho deixa o sistema mais inteligente para a próxima**. O conhecimento não se perde — ele se acumula, se conecta, e se auto-organiza.

---

## 12. Conclusão

**O sistema está funcionalmente completo.** O ciclo Ouroboros fecha. O cérebro está saudável (score 1.0). A arquitetura entrega o que promete.

O que falta **não é construção, é uso**. O sistema está projetado para melhorar com o tempo — e precisa de tempo para isso. A cada `/learn`, mais edges semânticas. A cada `/recall`, memórias reforçadas. A cada sessão, o grafo fica mais denso e preciso.

O Ouroboros **já está girando**. Só precisa de mais voltas.
