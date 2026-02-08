Diagnosticar a saúde do Engram neste projeto.

## Execução Rápida

Rodar o health check automatizado:
```bash
python3 .claude/skills/engram-evolution/scripts/doctor.py --project-dir .
```

Isso valida: estrutura, knowledge freshness, componentes, consistência.

## Saúde do Cérebro

Verificar estado do cérebro organizacional (grafo + vector store):
```bash
.claude/brain/.venv/bin/python3 .claude/brain/cognitive.py health
```

Verificar que:
- `health_score >= 0.8`
- `vector_backend: chromadb` (se npz, alertar sobre performance)
- `embeddings >= nodes * 0.5` (cobertura mínima)

## Aprofundamento (se necessário)

### 1. Validar Componentes Individuais

Para cada skill em `.claude/skills/`:
```bash
python3 .claude/skills/engram-genesis/scripts/validate.py --type skill --path .claude/skills/[nome]/
```

Para cada agent em `.claude/agents/`:
```bash
python3 .claude/skills/engram-genesis/scripts/validate.py --type agent --path .claude/agents/[nome].md
```

### 2. Composition Graph
```bash
python3 .claude/skills/engram-genesis/scripts/compose.py --graph --project-dir .
```

### 3. Usage Health
```bash
python3 .claude/skills/engram-evolution/scripts/track_usage.py --project-dir . --report health
```

### 4. Co-Activation Patterns
```bash
python3 .claude/skills/engram-evolution/scripts/co_activation.py --project-dir .
```

### 5. Stale Components
```bash
python3 .claude/skills/engram-evolution/scripts/track_usage.py --project-dir . --report stale
```

## Ao Final

Apresentar relatório consolidado com:
- Score de saúde (🟢🟡🔴 + percentual)
- Issues encontrados com sugestões de fix
- Sugestões evolutivas
