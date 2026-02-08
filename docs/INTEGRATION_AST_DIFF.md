# Integracao AST + Diff Summary no Workflow Engram

> Como a ingestao de estrutura de codigo (AST) e o enriquecimento de commits (Diff Summary) se integram ao ciclo de vida do Engram.

---

## 1. Visao Geral do Fluxo

Existem tres pontos de entrada para a ingestao de AST e enriquecimento de diffs no cerebro:

### /init-engram (populacao completa)

O comando `/init-engram` executa `populate.py all`, que inclui AST (codebase completo) e diffs (ate 200 commits) como etapas obrigatorias. Essa e a forma recomendada para o setup inicial do cerebro, pois garante que toda a estrutura de codigo e o historico de mudancas estejam disponiveis desde o primeiro momento.

### /learn (refresh automatico)

O comando `/learn` executa `populate.py refresh`, que inclui AST incremental (apenas arquivos cujo `body_hash` mudou) e diffs (apenas commits nao enriquecidos) automaticamente. Nenhuma intervencao manual e necessaria: a cada sessao de aprendizado, o cerebro atualiza tanto o conhecimento de codigo quanto o entendimento das mudancas recentes.

### Manual (sob demanda)

Os comandos `populate.py ast` e `populate.py diffs` podem ser executados individualmente para operacoes pontuais:

- `populate.py ast` para ingerir estrutura de codigo pela primeira vez (sem ter rodado `/init-engram`)
- `populate.py ast ./src` para ingestao parcial de um diretorio especifico
- `populate.py diffs --unenriched` para completar o enriquecimento de commits pendentes
- `populate.py diffs --since 2025-01-01 --max 500` para backfill de historico

---

## 2. Fluxo Automatico (/learn)

Ao executar `/learn`, o sistema roda `populate.py refresh N` (onde N e o numero de commits recentes a processar, padrao 20). O refresh executa as seguintes etapas em sequencia:

### Etapa 1: populate_commits(brain, N)

Adiciona novos Commit nodes ao cerebro. Busca os ultimos N commits via `git log` e cria nodes do tipo Episode/Commit para cada commit nao existente.

### Etapa 2: populate_diffs(brain, N, unenriched_only=True)

Enriquece os commits recem-adicionados com analise de diff. O parametro `unenriched_only=True` garante que apenas commits sem a propriedade `diff_enriched_at` sejam processados, evitando retrabalho.

### Etapa 3: AST incremental

O sistema verifica se ja existem Code nodes no cerebro:

```sql
SELECT COUNT(*) FROM node_labels WHERE label = 'Module'
```

- Se o resultado for maior que 0: executa `populate_ast(brain, root_dir=".")`. O AST incremental so processa arquivos cujo `body_hash` (md5 do conteudo) difere do registrado no cerebro, tornando a operacao proporcional ao volume de mudancas.
- Se o resultado for 0: imprime mensagem indicando que o AST foi pulado e sugere executar `populate.py ast` primeiro para a ingestao inicial.

### Etapa 4: cross_reference_pass(brain)

Resolve referencias cruzadas no formato `[[ADR-001]]`, `[[PAT-005]]`, etc., criando edges entre os nodes referenciados.

### Conexoes via sleep.py

Apos o refresh, o `sleep.py` executa suas 8 fases de consolidacao. A fase `phase_connect` inclui dois passes dedicados a conectar commits ao codigo:

- **Pass 4 (Commit -> Module via file paths):** Para cada Commit que possui uma lista de arquivos tocados, busca Module nodes com `file_path` correspondente e cria edges `MODIFIES_SAME` com peso 0.5.
- **Pass 5 (Commit -> Function/Class via diff symbols):** Para cada Commit com propriedades `symbols_added`, `symbols_modified` ou `symbols_deleted`, busca Code nodes (Function, Class) pelo nome do simbolo e cria edges `MODIFIES` com peso 0.7.

---

## 3. Fluxo Inicial (/init-engram)

O comando `populate.py all` executa a populacao completa do cerebro na seguinte ordem:

1. **ADRs** do ADR_LOG.md — decisoes arquiteturais como nodes Concept/ADR
2. **Domain concepts** do DOMAIN.md — glossario e regras de negocio como nodes Concept/Domain
3. **Patterns** do PATTERNS.md — padroes de codigo como nodes Concept/Pattern
4. **Experiences** do EXPERIENCE_LIBRARY.md — experiencias passadas como nodes Episode/Experience
5. **Commits** (ate 7000) — historico de commits como nodes Episode/Commit
6. **AST full codebase** (obrigatorio) — escaneia todos os arquivos suportados, criando nodes Module, Class, Function e Interface com seus edges estruturais (DEFINES, IMPORTS, INHERITS, MEMBER_OF)
7. **Diff enrichment** (ate 200 commits, apenas nao enriquecidos) — analisa diffs dos commits mais recentes, adicionando `diff_summary`, `symbols_added`, `symbols_modified`, `symbols_deleted` e `change_shape` aos Commit nodes existentes
8. **Cross-reference pass** — resolve todas as referencias cruzadas `[[ADR-001]]`, `[[PAT-005]]`, etc.

A etapa 6 (AST) e executada com `populate_ast(brain, root_dir=".")`, processando o codebase inteiro. A etapa 7 (Diffs) e executada com `populate_diffs(brain, max_commits=200, unenriched_only=True)`.

---

## 4. Completar Diff Enrichment

Apos o `/init-engram` ou `/learn`, o enriquecimento de diffs pode estar parcial. O `/init-engram` processa ate 200 commits e o `/learn` processa apenas os mais recentes. Para completar a cobertura:

```bash
# Enriquecer todos os commits pendentes
python3 .claude/brain/populate.py diffs --unenriched

# Backfill a partir de uma data especifica
python3 .claude/brain/populate.py diffs --since 2025-01-01 --max 500

# Verificar cobertura atual
python3 .claude/brain/cognitive.py health
```

O health check retorna a metrica `diff_enrichment.enrichment_pct` no JSON de saida. Se o valor estiver abaixo de 50%, o sistema gera automaticamente uma recomendacao sugerindo a execucao de `populate.py diffs --unenriched` para melhorar a cobertura.

Exemplo de saida do health check com recomendacao:

```json
{
  "diff_enrichment": {
    "total_commits": 69,
    "enriched_commits": 10,
    "enrichment_pct": 14.5
  },
  "recommendations": [
    {
      "type": "diffs",
      "message": "Apenas 14.5% dos commits tem diff analysis. Rode 'populate.py diffs --unenriched' para enriquecer."
    }
  ]
}
```

---

## 5. Comparacao: Antes vs Depois

Metricas reais deste projeto, mostrando o impacto da ingestao AST.

### Antes do AST (apenas brain/)

- 485 nodes, 1526 edges
- 118 Code nodes (13 modules, 2 classes, 103 functions)
- Recall "sleep" retornava apenas Commits + Concepts

### Depois do AST (codebase completo)

- 820 nodes (+69%), 2517 edges (+65%)
- 451 Code nodes (27 modules, 59 classes, 365 functions)
- Recall "sleep" retorna Commits + Concepts + Functions + Modules misturados
- Health score: 0.99

O salto de 118 para 451 Code nodes reflete a diferenca entre indexar apenas os scripts do brain e indexar todo o codebase (incluindo testes, scripts de genesis, templates e modulos auxiliares).

---

## 6. Como o Recall Muda

A ingestao de AST transforma fundamentalmente os resultados do recall. O cerebro deixa de entender apenas decisoes e commits e passa a entender tambem a estrutura do codigo.

### Busca por funcoes

Antes:

```text
recall "populate" --type function → apenas funcoes de brain/ (103)
```

Depois:

```text
recall "populate" --type function → todas as funcoes do codebase (365),
incluindo testes, scripts core, scripts de genesis
```

### Busca semantica geral

Antes:

```text
recall "sleep consolidation" → 3 resultados (Commit, Concept, Concept)
```

Depois:

```text
recall "sleep consolidation" → 5 resultados misturando Episode, Concept,
Function, Module
```

O cerebro agora entende a estrutura do codigo, nao apenas decisoes e commits. Uma busca por "sleep" retorna nao so os commits que mencionam sleep, mas tambem as funcoes `phase_connect`, `phase_relate`, `phase_decay` e o modulo `sleep.py`, todos com suas conexoes semanticas.

---

## 7. AST Incremental (body_hash)

O mecanismo de skip por `body_hash` torna re-execucoes do AST eficientes:

- Cada Module node armazena `body_hash`, que e o md5 do conteudo do arquivo no momento da ingestao.
- Ao re-executar `populate_ast`, o sistema carrega todos os hashes existentes dos Module nodes.
- Para cada arquivo no codebase, calcula o md5 do conteudo atual e compara com o hash registrado.
- Se igual: o arquivo nao mudou e e ignorado (skip).
- Se diferente ou inexistente: o arquivo e reprocessado, com upsert do Module e seus simbolos.
- O resultado e que re-execucoes custam O(mudancas) em vez de O(total).

Isso e particularmente relevante no contexto do `/learn`, onde o AST incremental roda a cada sessao. Se apenas 3 arquivos foram editados desde a ultima sessao, apenas esses 3 serao reprocessados, mesmo que o codebase tenha milhares de arquivos.

A query usada para carregar os hashes existentes:

```sql
SELECT n.id,
       json_extract(n.properties, '$.file_path') AS fp,
       json_extract(n.properties, '$.body_hash') AS bh
FROM nodes n
JOIN node_labels nl ON n.id = nl.node_id
WHERE nl.label = 'Module'
```

---

## 8. Referencia Rapida

| Acao | Comando | Quando |
| --- | --- | --- |
| Setup inicial | `populate.py all` | /init-engram (automatico) |
| Refresh sessao | `populate.py refresh 20` | /learn (automatico) |
| AST manual | `populate.py ast` | Primeira vez sem /init-engram |
| AST dir especifico | `populate.py ast ./src` | Ingestao parcial |
| Completar diffs | `populate.py diffs --unenriched` | Apos setup |
| Backfill diffs | `populate.py diffs --since 2025-01-01` | Historico |
| Verificar cobertura | `cognitive.py health` | Qualquer momento |
