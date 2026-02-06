# Brain - Cerebro Organizacional

Sistema de memoria com grafo de conhecimento, busca semantica via ChromaDB (HNSW) e processos cognitivos.

## Estrutura

```
brain/
├── brain_sqlite.py   # Nucleo do cerebro (SQLite v2 + ChromaDB)
├── brain.py          # Backend legado (JSON, deprecated)
├── embeddings.py     # Geracao/busca de embeddings
├── recall.py         # Interface de busca (CLI + lib)
├── sleep.py          # Consolidacao semantica (5 fases)
├── cognitive.py      # Processos: consolidate, decay, archive, health
├── populate.py       # Popular grafo de commits/knowledge files
├── patch_chromadb.py # Patch Python 3.14 para ChromaDB
├── brain.db          # SQLite database (grafo + FTS5)
├── chroma/           # ChromaDB persistent storage (HNSW index)
├── embeddings.npz    # Fallback numpy (se ChromaDB indisponivel)
└── state/            # Estado por desenvolvedor
    └── @username.json
```

## Dependencias

```bash
# Instalacao completa (recomendado — setup.sh faz isso automaticamente)
pip install networkx numpy sentence-transformers chromadb pydantic-settings

# Python 3.14+: rodar patch apos instalar chromadb
python3 .claude/brain/patch_chromadb.py

# OU para OpenAI embeddings (pago, maior qualidade)
pip install openai numpy chromadb pydantic-settings
export OPENAI_API_KEY=sk-...
```

### Vector Store

| Backend | Busca | Performance | Quando |
|---------|-------|-------------|--------|
| ChromaDB (primario) | HNSW ANN | O(log n) | Quando `chromadb` esta instalado |
| NumPy/npz (fallback) | Brute-force cosine | O(n) | Quando ChromaDB falha ou nao esta instalado |

ChromaDB usa `PersistentClient` com auto-persistencia em `chroma/`. Nao precisa de `save()` explicito.

## Uso Basico

### Python

```python
from brain_sqlite import BrainSQLite

# Carrega cerebro
brain = BrainSQLite()
brain.load()

# Adiciona memoria
node_id = brain.add_memory(
    title="Bug de autenticacao",
    content="Refresh token nao invalidava apos logout...",
    labels=["Episode", "BugFix"],
    author="@joao"
)

# Busca semantica
results = brain.retrieve(query="problemas de autenticacao")
for r in results:
    print(f"{r['score']:.2f} - {r['props']['title']}")

# Salva (no-op se ChromaDB ativo)
brain.save()
```

### CLI

```bash
# Estatisticas (mostra vector_backend: chromadb/npz)
python brain_sqlite.py stats

# Busca semantica via recall
python recall.py "autenticacao" --top 10 --format json

# Busca temporal
python recall.py --recent 7d --type Commit --top 10

# Gerar embeddings
python embeddings.py build

# Migrar npz -> ChromaDB (auto-executado pelo build se necessario)
python embeddings.py migrate

# Busca semantica direta
python embeddings.py search "como resolver bugs de auth"

# Saude do cerebro (inclui vector_backend)
python cognitive.py health

# Consolidacao semantica (5 fases)
python sleep.py
```

## Conceitos

### Labels (Tipos de Memoria)

| Label | Tipo | Decay Rate |
|-------|------|------------|
| Episode | Memoria episodica | 0.01 (medio) |
| Concept | Memoria semantica | 0.003 (lento) |
| Pattern | Memoria procedural | 0.005 (lento) |
| Decision | ADR | 0.001 (muito lento) |
| Person | Membro da equipe | 0.0001 (quase nao decai) |
| Domain | Area de conhecimento | 0.0001 |

### Tipos de Arestas

| Tipo | Significado |
|------|-------------|
| AUTHORED_BY | Pessoa criou a memoria |
| REFERENCES | Mencao explicita ([[link]]) |
| BELONGS_TO | Pertence a dominio |
| SOLVED_BY | Problema resolvido por pattern/decisao |
| SUPERSEDES | Nova versao substitui antiga |
| RELATED_TO | Similaridade semantica (auto-detectado pelo sleep) |
| SAME_SCOPE | Commits no mesmo scope |
| MODIFIES_SAME | Commits que mexeram nos mesmos arquivos |
| CO_ACCESSED | Nos acessados juntos em sessoes |

### Processos Cognitivos

1. **Encode**: Criar memoria com arestas automaticas
2. **Retrieve**: Busca com spreading activation + HNSW
3. **Sleep**: Consolidacao semantica (5 fases in-memory)
4. **Consolidate**: Fortalecer conexoes (semanal)
5. **Decay**: Esquecimento por Ebbinghaus (diario)
6. **Archive**: Mover memorias fracas (quando necessario)

## Integracao com Git

```bash
# O cerebro usa SQLite + ChromaDB, nao precisa de git add manual
# brain.db e chroma/ sao gitignored (reconstruiveis via populate + build)

# Apenas scripts e knowledge files vao pro git
git add .claude/brain/*.py .claude/brain/*.md
```

## Processos Cognitivos Periodicos

Para manter o cerebro saudavel, configure jobs periodicos:

### Opcao 1: Git Hooks (Recomendado)

Adicione ao `.git/hooks/post-commit`:

```bash
#!/bin/bash
# Roda decay a cada commit (leve, ~100ms)
cd "$(git rev-parse --show-toplevel)"
python3 .claude/brain/cognitive.py decay 2>/dev/null || true
```

### Opcao 2: Cron (Para times maiores)

```bash
# Editar crontab
crontab -e

# Adicionar:
# Decay diario (2am)
0 2 * * * cd /path/to/projeto && python3 .claude/brain/cognitive.py decay 2>/dev/null || true

# Consolidacao semanal (domingo 3am)
0 3 * * 0 cd /path/to/projeto && python3 .claude/brain/cognitive.py consolidate 2>/dev/null || true

# Archive mensal (dia 1, 4am)
0 4 1 * * cd /path/to/projeto && python3 .claude/brain/cognitive.py archive 2>/dev/null || true
```

### Verificacao Manual

```bash
# Ver saude do cerebro (inclui vector_backend e recomendacoes)
python3 .claude/brain/cognitive.py health

# Ver log de processos
cat .claude/brain/cognitive-log.jsonl | tail -5

# Forcar consolidacao
python3 .claude/brain/cognitive.py consolidate
```

## Escala

| Metrica | Limite Confortavel |
|---------|-------------------|
| Nos | ~1M |
| Arestas | ~5M |
| Embeddings (ChromaDB) | ~1M (HNSW) |
| Embeddings (npz) | ~100k (brute-force) |
| RAM | ~500MB |
| Tempo de carga | <2s |
