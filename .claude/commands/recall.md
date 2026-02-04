Consultar o Cérebro Organizacional para recuperar conhecimento relevante.

## Como Funciona

```
┌─────────────────────────────────────────────────────────┐
│  Dev pergunta: "como funciona a autenticação?"          │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Claude executa: /recall "autenticação"                 │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  recall.py:                                             │
│  1. Carrega grafo (nós + arestas)                       │
│  2. Gera embedding da query (sentence-transformers)     │
│  3. Busca por similaridade semântica                    │
│  4. Spreading activation (expande para nós conectados)  │
│  5. Rankeia por score combinado                         │
│  6. Retorna top-K resultados                            │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Claude usa as memórias como contexto para responder    │
└─────────────────────────────────────────────────────────┘
```

## Uso

```
/recall <pergunta ou tema>
```

Exemplos:
- `/recall como funciona a autenticação`
- `/recall decisões sobre arquitetura de banco`
- `/recall padrões de error handling`

## Como Funciona

O `/recall` ativa o cérebro organizacional em `.claude/brain/` para buscar memórias relevantes usando:

1. **Busca Semântica** — Usa embeddings para encontrar conteúdo semanticamente similar
2. **Spreading Activation** — Expande a busca para nós conectados no grafo
3. **Ranking por Relevância** — Ordena por score combinado (similaridade + conexões)

## Execução

### Passo 1: Busca no Cérebro

```bash
source .claude/brain/.venv/bin/activate 2>/dev/null || true
python3 .claude/brain/recall.py "<QUERY_DO_USUARIO>"
```

O script retorna JSON com:
```json
{
  "query": "pergunta original",
  "results": [
    {
      "id": "node-id",
      "title": "Título da memória",
      "type": "ADR|Concept|Pattern|Episode|...",
      "summary": "Resumo do conteúdo",
      "score": 0.95,
      "file": "caminho/para/arquivo.md (se existir)"
    }
  ],
  "total": 5
}
```

### Passo 2: Ler Conteúdo Relevante

Para cada resultado com `file`, leia o arquivo se precisar de mais contexto.

### Passo 3: Apresentar ao Dev

```
🧠 Recall: "[query]"
═══════════════════════════════════════

Encontrei [N] memórias relevantes:

📋 [score] [Tipo] [Título]
   [Resumo...]
   📄 [arquivo se houver]

📋 [score] [Tipo] [Título]
   [Resumo...]

💡 Baseado nessas memórias: [insight ou resposta à pergunta]
```

## Quando Usar Automaticamente

O Claude deve executar `/recall` automaticamente quando:

1. **Pergunta sobre arquitetura** — "como funciona X?", "por que Y foi feito assim?"
2. **Pergunta sobre domínio** — "o que é X?", "qual a regra de Y?"
3. **Antes de decisões** — para verificar se já existe ADR relacionado
4. **Debug de problemas** — para encontrar soluções anteriores similares
5. **Contexto histórico** — "quando foi implementado X?", "quem fez Y?"

## Tipos de Memória

| Tipo | Label | Descrição |
|------|-------|-----------|
| Decisão | ADR, Decision | Decisões arquiteturais documentadas |
| Conceito | Concept, Glossary | Termos e definições do domínio |
| Padrão | Pattern, ApprovedPattern | Padrões aprovados de código |
| Episódio | Episode, Commit, BugFix | Eventos e mudanças históricas |
| Regra | Rule, BusinessRule | Regras de negócio |
| Pessoa | Person | Expertise e autoria |

## Modos de Busca

O recall.py suporta diferentes modos:

```bash
# Busca semântica (padrão) — melhor para perguntas naturais
python3 .claude/brain/recall.py "como funciona X"

# Busca por tipo — filtrar por categoria
python3 .claude/brain/recall.py "autenticação" --type ADR

# Busca por autor — quem escreveu sobre isso
python3 .claude/brain/recall.py "autenticação" --author @thiago

# Busca expandida — mais profundidade no grafo
python3 .claude/brain/recall.py "autenticação" --depth 3
```

## Integração com Workflow

```
Pergunta do dev
      ↓
  /recall (busca memórias)
      ↓
  Memórias encontradas?
      ├─ SIM → Usar como contexto para resposta
      └─ NÃO → Responder normalmente + sugerir /learn para registrar
```

## Fallback

Se o cérebro não estiver disponível (venv não existe, dependências faltando):

```
⚠️ Cérebro não disponível. Consultando knowledge files diretamente...
```

Então consultar os arquivos em `.claude/knowledge/` manualmente.
