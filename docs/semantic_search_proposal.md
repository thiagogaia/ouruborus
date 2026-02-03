# Proposta: Busca Semântica para Skills do Engram

**Data:** 2026-02-03
**Status:** Proposta (não implementado)
**Prioridade:** Média

---

## 1. Problema Atual

Os skills são ativados por **trigger words** — palavras-chave explícitas na description:

```yaml
---
name: prisma-workflow
description: Padrões de Prisma ORM. Use quando trabalhar com migrations,
  queries, schema design, ou relacionamentos no banco de dados.
---
```

### Limitações

| Query do Dev | Trigger Words | Resultado |
|--------------|---------------|-----------|
| "criar migration para users" | ✅ "migration" | Ativa corretamente |
| "otimizar busca de usuários" | ❌ sem match | Pode não ativar |
| "melhorar performance do banco" | ❌ sem "banco" literal | Pode não ativar |
| "como fazer join entre tabelas" | ❌ sem match | Não ativa |

O sistema não entende **sinônimos** nem **contexto semântico**.

---

## 2. Solução Proposta: Embeddings Vetoriais

### O que são Embeddings?

Embeddings são representações numéricas (vetores) de texto que capturam o **significado semântico**. Textos com significados similares ficam próximos no espaço vetorial.

```
"otimizar queries de banco"     → [0.23, -0.41, 0.89, ...]
"melhorar performance do DB"    → [0.21, -0.39, 0.91, ...]  ← similar!
"fazer deploy na AWS"           → [-0.15, 0.67, -0.22, ...] ← diferente
```

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUSCA SEMÂNTICA DE SKILLS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INDEXAÇÃO (uma vez, no /init-engram ou quando skill muda)     │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ Para cada skill em .claude/skills/:                    │     │
│  │   1. Lê SKILL.md (description + body)                 │     │
│  │   2. Gera embedding (vetor de 384-1536 dimensões)     │     │
│  │   3. Salva em .claude/semantic-index.json             │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
│  BUSCA (a cada tarefa do dev)                                  │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ Dev: "otimizar a busca de usuários por email"         │     │
│  │   1. Gera embedding da query                          │     │
│  │   2. Calcula similaridade coseno com cada skill       │     │
│  │   3. Retorna top-3 skills mais similares              │     │
│  │   → prisma-workflow (0.87), db-expert (0.82)          │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Opções de Implementação

### Opção A: API de Embeddings (Cloud)

Usar APIs como OpenAI, Cohere, Voyage AI, Google.

| Provider | Modelo | Dimensões | Custo |
|----------|--------|-----------|-------|
| OpenAI | text-embedding-3-small | 1536 | $0.02/1M tokens |
| OpenAI | text-embedding-3-large | 3072 | $0.13/1M tokens |
| Cohere | embed-english-v3.0 | 1024 | $0.10/1M tokens |
| Voyage AI | voyage-2 | 1024 | $0.10/1M tokens |
| Google | text-embedding-004 | 768 | $0.025/1M tokens |

**Prós:**
- Alta qualidade de embeddings
- Sem necessidade de hardware
- Sempre atualizado

**Contras:**
- Custo recorrente (mesmo que baixo)
- Requer internet
- Latência de rede (+100-300ms)
- Dependência de terceiros

---

### Opção B: Modelo Local (Recomendada)

Usar modelos de embedding que rodam **localmente**, sem API externa.

#### Modelos Locais Recomendados

| Modelo | Tamanho | Dimensões | Qualidade | Velocidade |
|--------|---------|-----------|-----------|------------|
| **all-MiniLM-L6-v2** | 80MB | 384 | Boa | Muito rápida |
| all-mpnet-base-v2 | 420MB | 768 | Muito boa | Rápida |
| bge-small-en-v1.5 | 130MB | 384 | Muito boa | Muito rápida |
| **nomic-embed-text-v1** | 274MB | 768 | Excelente | Rápida |
| e5-small-v2 | 130MB | 384 | Boa | Muito rápida |

**Recomendação:** `all-MiniLM-L6-v2` ou `bge-small-en-v1.5`
- Apenas 80-130MB
- Roda em CPU (não precisa GPU)
- Qualidade suficiente para ~50 skills
- Latência <50ms por query

**Prós:**
- Custo ZERO após download
- Funciona offline
- Sem dependência externa
- Privacidade total
- Latência baixa

**Contras:**
- Download inicial do modelo
- Usa ~100-500MB de RAM
- Qualidade ligeiramente inferior a APIs

---

### Opção C: TF-IDF Local (Mais Simples)

Usar algoritmo clássico de Information Retrieval, sem redes neurais.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Cria índice
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
tfidf_matrix = vectorizer.fit_transform(skill_texts)

# Busca
query_vec = vectorizer.transform([query])
similarities = cosine_similarity(query_vec, tfidf_matrix)
```

**Prós:**
- Extremamente simples
- Zero dependências além de sklearn
- Muito rápido
- Funciona offline

**Contras:**
- Não entende sinônimos ("DB" ≠ "banco de dados")
- Não entende contexto
- Qualidade inferior a embeddings

---

## 4. Recomendação: Modelo Local com Sentence-Transformers

### Por quê?

1. **Custo zero** — Nenhuma API, roda local
2. **Offline** — Funciona sem internet
3. **Qualidade** — Modelos pequenos já são muito bons para ~50 skills
4. **Velocidade** — <50ms por busca em CPU
5. **Privacidade** — Código nunca sai da máquina

### Dependências

```bash
pip install sentence-transformers numpy
# Download automático do modelo na primeira execução (~80MB)
```

### Estrutura de Arquivos

```
.claude/
├── skills/
│   ├── prisma-workflow/
│   ├── nextjs-patterns/
│   └── ...
├── semantic-index.json      # Índice de embeddings
└── ...

core/genesis/scripts/
├── semantic_index.py        # Gera índice
└── semantic_search.py       # Busca por similaridade
```

---

## 5. Implementação Proposta

### 5.1 Script: `semantic_index.py`

```python
#!/usr/bin/env python3
"""
Engram — Semantic Index Builder
Gera embeddings locais para todos os skills usando sentence-transformers.

Usage:
    python3 semantic_index.py --project-dir .
    python3 semantic_index.py --project-dir . --model all-MiniLM-L6-v2
"""

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

# Lazy import para não falhar se não instalado
def get_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except ImportError:
        print("❌ sentence-transformers não instalado.")
        print("   Instale com: pip install sentence-transformers")
        raise SystemExit(1)


def extract_skill_text(skill_path: Path) -> str:
    """Extrai texto relevante do SKILL.md para embedding."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ""

    content = skill_md.read_text()

    # Extrai description do frontmatter
    description = ""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].split("\n"):
                if line.strip().startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                    break
            body = parts[2].strip()
        else:
            body = content
    else:
        body = content

    # Combina description + primeiras 500 palavras do body
    body_words = " ".join(body.split()[:500])
    return f"{description}\n\n{body_words}"


def compute_hash(text: str) -> str:
    """Hash para detectar mudanças no skill."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def build_index(project_dir: str, model_name: str = "all-MiniLM-L6-v2") -> dict:
    """Constrói índice semântico de todos os skills."""
    skills_dir = Path(project_dir) / ".claude" / "skills"

    if not skills_dir.exists():
        print(f"❌ Diretório de skills não encontrado: {skills_dir}")
        raise SystemExit(1)

    print(f"🔍 Carregando modelo: {model_name}")
    model = get_model(model_name)

    index = {
        "model": model_name,
        "dimensions": model.get_sentence_embedding_dimension(),
        "indexed_at": datetime.now().isoformat(),
        "skills": {}
    }

    # Coleta textos de todos os skills
    skill_data = []
    for skill_path in sorted(skills_dir.iterdir()):
        if not skill_path.is_dir():
            continue
        text = extract_skill_text(skill_path)
        if text:
            skill_data.append({
                "name": skill_path.name,
                "text": text,
                "hash": compute_hash(text)
            })

    if not skill_data:
        print("⚠️  Nenhum skill encontrado para indexar.")
        return index

    print(f"📊 Indexando {len(skill_data)} skills...")

    # Gera embeddings em batch (mais eficiente)
    texts = [s["text"] for s in skill_data]
    embeddings = model.encode(texts, show_progress_bar=True)

    for i, skill in enumerate(skill_data):
        index["skills"][skill["name"]] = {
            "embedding": embeddings[i].tolist(),
            "hash": skill["hash"]
        }

    return index


def save_index(project_dir: str, index: dict):
    """Salva índice em arquivo JSON."""
    index_path = Path(project_dir) / ".claude" / "semantic-index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"✅ Índice salvo: {index_path}")
    print(f"   • {len(index['skills'])} skills indexados")
    print(f"   • {index['dimensions']} dimensões")
    print(f"   • Modelo: {index['model']}")


def main():
    parser = argparse.ArgumentParser(description="Engram Semantic Index Builder")
    parser.add_argument("--project-dir", default=".", help="Diretório do projeto")
    parser.add_argument("--model", default="all-MiniLM-L6-v2",
                        help="Modelo de embedding (default: all-MiniLM-L6-v2)")
    args = parser.parse_args()

    index = build_index(args.project_dir, args.model)
    save_index(args.project_dir, index)


if __name__ == "__main__":
    main()
```

### 5.2 Script: `semantic_search.py`

```python
#!/usr/bin/env python3
"""
Engram — Semantic Skill Search
Busca skills por similaridade semântica.

Usage:
    python3 semantic_search.py --query "otimizar queries de banco" --project-dir .
    python3 semantic_search.py --query "como fazer deploy" --top-k 5 --project-dir .
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np


def load_index(project_dir: str) -> dict:
    """Carrega índice semântico."""
    index_path = Path(project_dir) / ".claude" / "semantic-index.json"
    if not index_path.exists():
        print(f"❌ Índice não encontrado: {index_path}")
        print("   Execute primeiro: python3 semantic_index.py --project-dir .")
        sys.exit(1)

    with open(index_path) as f:
        return json.load(f)


def get_query_embedding(query: str, model_name: str) -> np.ndarray:
    """Gera embedding para a query."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        return model.encode(query)
    except ImportError:
        print("❌ sentence-transformers não instalado.")
        sys.exit(1)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade coseno entre dois vetores."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search(query: str, index: dict, top_k: int = 3) -> list[dict]:
    """Busca skills mais similares à query."""
    query_emb = get_query_embedding(query, index["model"])

    results = []
    for skill_name, data in index["skills"].items():
        skill_emb = np.array(data["embedding"])
        similarity = cosine_similarity(query_emb, skill_emb)
        results.append({
            "skill": skill_name,
            "similarity": round(similarity, 3)
        })

    # Ordena por similaridade decrescente
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Engram Semantic Skill Search")
    parser.add_argument("--query", required=True, help="Texto para buscar")
    parser.add_argument("--project-dir", default=".", help="Diretório do projeto")
    parser.add_argument("--top-k", type=int, default=3, help="Número de resultados")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Similaridade mínima (0-1)")
    args = parser.parse_args()

    index = load_index(args.project_dir)
    results = search(args.query, index, args.top_k)

    # Filtra por threshold
    results = [r for r in results if r["similarity"] >= args.threshold]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n🔍 Query: \"{args.query}\"")
        print(f"{'─' * 50}")
        if results:
            for i, r in enumerate(results, 1):
                bar = "█" * int(r["similarity"] * 20)
                print(f"  {i}. {r['skill']:<25} {r['similarity']:.3f} {bar}")
        else:
            print("  Nenhum skill encontrado acima do threshold.")
        print()


if __name__ == "__main__":
    main()
```

---

## 6. Integração com Engram

### 6.1 Quando Indexar

1. **No `/init-engram`** — Indexa todos os skills gerados
2. **No `/create` ou `/spawn`** — Re-indexa após criar novo skill
3. **No `/learn`** — Re-indexa se detectar skills modificados

### 6.2 Quando Buscar

No início de cada tarefa, o Claude pode:

```python
# Pseudocódigo no fluxo do Claude
def handle_task(user_query):
    # 1. Busca semântica
    relevant_skills = semantic_search(user_query, top_k=3, threshold=0.5)

    # 2. Carrega skills relevantes
    for skill in relevant_skills:
        load_skill(skill["name"])

    # 3. Executa tarefa com contexto dos skills
    execute_task(user_query)
```

### 6.3 Command: `/semantic`

Novo command opcional para busca explícita:

```markdown
# /semantic

Buscar skills por similaridade semântica.

## Uso
/semantic [query]

## Exemplo
/semantic como otimizar queries do banco de dados

## Output
🔍 Query: "como otimizar queries do banco de dados"
──────────────────────────────────────────────────
  1. prisma-workflow           0.847 ████████████████
  2. db-expert                 0.812 ████████████████
  3. code-reviewer             0.523 ██████████
```

---

## 7. Comparação de Custos

| Abordagem | Custo Inicial | Custo por Query | Custo Mensal (1000 queries) |
|-----------|---------------|-----------------|----------------------------|
| **API OpenAI** | $0 | ~$0.0001 | ~$0.10 |
| **Modelo Local** | $0 (download 80MB) | $0 | **$0** |
| **TF-IDF** | $0 | $0 | $0 |

### Recursos de Hardware (Modelo Local)

| Recurso | Requisito |
|---------|-----------|
| RAM | +100-200MB durante indexação |
| Disco | 80-130MB para o modelo |
| CPU | Qualquer (não precisa GPU) |
| Tempo indexação | ~1-2s para 50 skills |
| Tempo busca | ~30-50ms por query |

---

## 8. Roadmap de Implementação

### Fase 1: Fundação
1. Criar `semantic_index.py`
2. Criar `semantic_search.py`
3. Adicionar ao `requirements.txt`: `sentence-transformers>=2.2.0`
4. Testar com skills existentes

### Fase 2: Integração
5. Integrar no `/init-engram` (indexação automática)
6. Integrar no `/create` e `/spawn` (re-indexação)
7. Criar command `/semantic` (busca explícita)

### Fase 3: Automação
8. Claude usa busca semântica automaticamente
9. Fallback para trigger words se índice não existir
10. Métricas de qualidade das buscas

---

## 9. Conclusão

A **Opção B (Modelo Local)** é a recomendada porque:

- **Zero custo** após instalação
- **Funciona offline**
- **Qualidade suficiente** para o caso de uso
- **Simples** de implementar e manter
- **Privado** — código nunca sai da máquina

O modelo `all-MiniLM-L6-v2` com apenas 80MB oferece qualidade excelente para buscar entre ~50-100 skills, com latência <50ms.

Não é uma "rede neural treinada do zero" — é um modelo **pré-treinado** que apenas usamos para gerar vetores. O "aprendizado" já foi feito pelos criadores do modelo em datasets massivos de texto. Nós apenas aplicamos.
