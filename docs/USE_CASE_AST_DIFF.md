# AST Ingestion + Diff Summary — Casos de Uso

> Documento gerado em 2026-02-07. Descreve os casos de uso das features de ingestao de estrutura de codigo (AST) e enriquecimento de commits com analise de diffs.

---

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Modelo de Dados](#modelo-de-dados)
- **Ingestao de Codigo (AST)**
  - [UC-AST-01: Ingerir Estrutura do Codebase](#uc-ast-01-ingerir-estrutura-do-codebase)
  - [UC-AST-02: Re-run Incremental (Skip Inalterados)](#uc-ast-02-re-run-incremental-skip-inalterados)
  - [UC-AST-03: Consultar Funcoes e Classes via Recall](#uc-ast-03-consultar-funcoes-e-classes-via-recall)
- **Enriquecimento de Diffs**
  - [UC-DIFF-01: Enriquecer Commits com Analise de Diff](#uc-diff-01-enriquecer-commits-com-analise-de-diff)
  - [UC-DIFF-02: Backfill de Commits Historicos](#uc-diff-02-backfill-de-commits-historicos)
  - [UC-DIFF-03: Enriquecimento Automatico no Refresh](#uc-diff-03-enriquecimento-automatico-no-refresh)
- **Integracao (Sleep)**
  - [UC-INT-01: Conectar Commits a Codigo via Sleep](#uc-int-01-conectar-commits-a-codigo-via-sleep)
  - [UC-INT-02: Rastrear Impacto de um Commit no Codigo](#uc-int-02-rastrear-impacto-de-um-commit-no-codigo)
- **Diagnostico**
  - [UC-DIAG-01: Verificar Cobertura de Codigo e Diffs](#uc-diag-01-verificar-cobertura-de-codigo-e-diffs)
- [Referencia de CLI](#referencia-de-cli)
- [Arquivos Envolvidos](#arquivos-envolvidos)

---

## Visao Geral

O Engram, ate antes dessas features, capturava apenas **mensagens de commit + nomes de arquivos**. Nao lia codigo. Para funcionar em projetos grandes (10+ anos de historico, 10k+ arquivos), foram adicionadas duas capacidades:

1. **AST Ingestion** — Entende a estrutura do codigo atual (modulos, classes, funcoes, interfaces, dependencias de import, padroes arquiteturais)
2. **Diff Summary** — Entende o que cada commit recente realmente mudou (simbolos adicionados, modificados, removidos; forma da mudanca; resumo estruturado)

Juntas, criam o chain de navegacao:

```text
"como o codigo esta?"  →  Code nodes (Module, Class, Function)
        ↓
"quem mudou isso?"     →  Commit nodes (via edges MODIFIES, MODIFIES_SAME)
        ↓
"o que mais mudou junto?" →  outros Code nodes + Commit nodes relacionados
```

### Principio: Zero LLM, 100% Heuristico

Toda classificacao de diffs e parsing de AST e feita por heuristicas deterministicas. Nao usa LLM para analisar codigo — e rapido, custo zero e reproduzivel.

---

## Arquitetura

```text
                    ┌────────────────────────────────────────┐
                    │             populate.py                 │
                    │                                        │
                    │  populate_ast()    populate_diffs()     │
                    │       │                  │              │
                    │       ▼                  ▼              │
                    │  ast_parser.py      diff_parser.py      │
                    │  (tree-sitter       (state machine      │
                    │   + regex)           + heuristicas)     │
                    │       │                  │              │
                    │       ▼                  ▼              │
                    │  ┌──────────────────────────────┐      │
                    │  │       brain_sqlite.py         │      │
                    │  │  add_memory(node_id=...)      │      │
                    │  │  update_node_content()        │      │
                    │  │  add_edge()                   │      │
                    │  └──────────────────────────────┘      │
                    └────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────┐
                    │              sleep.py                   │
                    │                                        │
                    │  phase_connect():                      │
                    │    Pass 4: Commit → Module (via files)  │
                    │    Pass 5: Commit → Symbol (via diff)   │
                    │                                        │
                    │  phase_relate():                       │
                    │    Stratified sampling (Code + outros)  │
                    └────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────────┐
                    │          recall.py / cognitive.py       │
                    │                                        │
                    │  --type function|class|module|code      │
                    │  health: code_coverage + diff_enrichment│
                    └────────────────────────────────────────┘
```

---

## Modelo de Dados

### Nodes de Codigo (AST)

Todos os nodes de codigo compartilham o label `Code` como parent, alem do label especifico.

| Label | Props Especificos | Decay Rate |
| ------- | ------------------- | ------------ |
| `Module` | `file_path`, `language`, `line_count`, `import_count`, `symbol_count`, `body_hash` | 0.001 |
| `Class` | `file_path`, `language`, `name`, `qualified_name`, `line_start`, `line_end`, `docstring`, `base_classes`, `detected_pattern` | 0.001 |
| `Function` | `file_path`, `language`, `name`, `qualified_name`, `signature`, `line_start`, `line_end`, `docstring`, `is_method`, `param_count`, `complexity_hint` | 0.001 |
| `Interface` | `file_path`, `language`, `name`, `qualified_name`, `method_signatures` | 0.001 |

**IDs**: 16 chars hex (`md5(file_path:qualified_name|label)[:16]`). Compativeis com IDs existentes de 8 chars.

**Content** de cada Code node (compacto, ~200-500 tokens para embedding focado):

```text
def populate_commits(brain: Brain, max_commits: int = 7000) -> int
  File: .claude/brain/populate.py:572-640 (68 lines)
  Docstring: Adiciona commits ao cerebro como memoria episodica
  Complexity: moderate (3 branches, max nesting 2)
```

### Edges de Codigo

| Edge | De → Para | Peso | Significado |
| ------ | ----------- | ------ | ------------- |
| `DEFINES` | Module → Class/Function/Interface | 0.8 | Modulo contem este simbolo |
| `IMPORTS` | Module → Module | 0.5 | Dependencia de import |
| `INHERITS` | Class → Class | 0.7 | Heranca |
| `IMPLEMENTS` | Class → Interface | 0.7 | Implementacao |
| `MEMBER_OF` | Function → Class | 0.8 | Metodo pertence a classe |

### Props de Diff (adicionados a Commit nodes existentes)

| Prop | Tipo | Conteudo |
| ------ | ------ | ---------- |
| `diff_summary` | string | Resumo estruturado, ~500 tokens |
| `diff_stats` | JSON | `{files_changed, insertions, deletions}` |
| `symbols_added` | JSON list | `["function:new_func", "class:NewClass"]` |
| `symbols_modified` | JSON list | `["function:existing_func"]` |
| `symbols_deleted` | JSON list | `["function:old_func"]` |
| `change_shape` | string | Classificacao da mudanca (ver tabela abaixo) |
| `diff_enriched_at` | datetime | Quando o diff foi processado |

### Classificacao de Change Shape

| Shape | Criterio |
| ------- | ---------- |
| `tiny_fix` | <10 linhas, sem simbolos novos |
| `small_fix` | <30 linhas, sem simbolos novos |
| `feature_add` | Novos simbolos adicionados |
| `feature_modify` | Maioria de modificacoes em simbolos existentes |
| `refactor` | Ratio add/delete balanceado (>0.6), >50 linhas |
| `large_refactor` | Ratio balanceado, >200 linhas |
| `config_change` | Apenas arquivos de configuracao |
| `documentation` | Apenas arquivos .md/.rst/.txt |
| `test` | Apenas arquivos de teste |

### Edge de Diff

| Edge | De → Para | Peso | Significado |
| ------ | ----------- | ------ | ------------- |
| `MODIFIES` | Commit → Function/Class | 0.7 | Commit modificou este simbolo especifico |

---

## Ingestao de Codigo (AST)

### UC-AST-01: Ingerir Estrutura do Codebase

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-AST-01 |
| **Nome** | Ingerir Estrutura do Codebase |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA), `ast_parser.py`, `populate.py` |
| **Descricao** | O desenvolvedor ingere a estrutura completa do codebase no cerebro, criando nodes para modulos, classes, funcoes e interfaces com seus relacionamentos. |

**Pre-condicoes:**

1. Engram inicializado com cerebro funcional
2. Codebase com arquivos em linguagens suportadas (Python, JS, TS, Ruby, Go, Java, Rust, PHP)

**Fluxo Principal:**

1. O desenvolvedor executa `python3 .claude/brain/populate.py ast`
2. O sistema detecta linguagens presentes no codebase (por extensao de arquivo)
3. O sistema filtra arquivos ignoraveis: `.gitignore`, `node_modules/`, `vendor/`, `.venv/`, `>500KB`, binarios, lock files
4. Para cada arquivo suportado:
   - Tenta parse via tree-sitter (se `tree-sitter-languages` instalado)
   - Fallback: parse via regex (extrai `def/class/function/interface` top-level)
5. Cria nodes no cerebro:
   - `Module` para cada arquivo (com `body_hash` para skip futuro)
   - `Class` para cada classe/struct/enum
   - `Function` para cada funcao/metodo
   - `Interface` para cada interface/trait/protocol
6. Cria edges:
   - `DEFINES`: Module → Class/Function/Interface
   - `IMPORTS`: Module → Module (por analise de imports)
   - `INHERITS`: Class → Class (por analise de base classes)
   - `MEMBER_OF`: Function → Class (para metodos)
7. Detecta padroes arquiteturais por heuristica de nomes (`*Controller`, `*Service`, `*Repository`, etc.)
8. Gera embeddings para cada Code node (deferido para o modelo de embedding)
9. O sistema exibe estatisticas (total de modulos, classes, funcoes, interfaces criados)

**Fluxos Alternativos:**

- **FA-01: Diretorio especifico**
  - O ator executa `python3 .claude/brain/populate.py ast ./src`
  - Apenas o diretorio `./src` e escaneado
  - Util para projetos monorepo ou ingestao parcial

- **FA-02: Filtro por linguagem**
  - O ator executa `python3 .claude/brain/populate.py ast --lang py,ts`
  - Apenas arquivos Python e TypeScript sao processados
  - Util para focar em um subset do codebase

- **FA-03: Dry run (preview)**
  - O ator executa `python3 .claude/brain/populate.py ast --dry-run`
  - O sistema lista arquivos que seriam processados, sem gravar no cerebro
  - Util para estimar volume antes de ingerir

- **FA-04: tree-sitter nao instalado**
  - O sistema detecta ausencia do pacote `tree-sitter-languages`
  - Usa parser regex como fallback (~80% de cobertura)
  - Exibe aviso: "Using: regex fallback (install tree-sitter-languages for better parsing)"

**Pos-condicoes:**

1. Nodes de codigo criados no cerebro (Module, Class, Function, Interface)
2. Edges estruturais criados (DEFINES, IMPORTS, INHERITS, MEMBER_OF)
3. Padroes arquiteturais detectados e registrados (prop `detected_pattern`)
4. `body_hash` registrado em cada Module para otimizacao de re-runs
5. Recall pode buscar por `--type function`, `--type class`, `--type module`

**Exemplo de saida:**

```text
$ python3 .claude/brain/populate.py ast core --lang py

=== AST Ingestion (core) [languages: {'python'}] ===
Scanning core (languages: {'python'})
Existing modules with hashes: 0
Found 13 files to process
  Created 100 Code nodes...
Created 118 Code nodes
{
  "nodes": 471,
  "edges": 1270,
  "by_label": {
    "Code": 118,
    "Module": 13,
    "Class": 2,
    "Function": 103
  },
  "by_edge_type": {
    "DEFINES": 99,
    "IMPORTS": 11,
    "MEMBER_OF": 6
  }
}
```

---

### UC-AST-02: Re-run Incremental (Skip Inalterados)

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-AST-02 |
| **Nome** | Re-run Incremental |
| **Ator Principal** | Desenvolvedor Solo, CI/CD |
| **Atores Secundarios** | `ast_parser.py`, `populate.py` |
| **Descricao** | Ao executar AST ingestion novamente, o sistema detecta arquivos que nao mudaram (via `body_hash`) e processa apenas os modificados. Custo O(mudancas) em vez de O(total). |

**Pre-condicoes:**

1. AST ingestion ja executada pelo menos uma vez (UC-AST-01)
2. Modules existentes no cerebro com `body_hash` registrado

**Fluxo Principal:**

1. O ator executa `python3 .claude/brain/populate.py ast`
2. O sistema carrega todos os `body_hash` existentes de Module nodes
3. Para cada arquivo no codebase:
   - Calcula `md5` do conteudo atual
   - Compara com `body_hash` registrado
   - Se igual: **skip** (arquivo nao mudou)
   - Se diferente ou inexistente: processa normalmente
4. Apenas arquivos novos ou modificados sao parseados
5. Nodes existentes sao atualizados (upsert), novos sao criados

**Pos-condicoes:**

1. Apenas arquivos modificados foram reprocessados
2. Tempo de execucao proporcional ao volume de mudancas
3. `body_hash` atualizado para os arquivos reprocessados

---

### UC-AST-03: Consultar Funcoes e Classes via Recall

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-AST-03 |
| **Nome** | Consultar Funcoes e Classes via Recall |
| **Ator Principal** | Desenvolvedor Solo, Dev Novo |
| **Atores Secundarios** | `recall.py`, Cerebro Organizacional |
| **Descricao** | O ator consulta o cerebro para encontrar funcoes, classes ou modulos especificos, navegando pelas conexoes semanticas para entender a estrutura do codigo. |

**Pre-condicoes:**

1. AST ingestion executada (UC-AST-01)
2. Cerebro com Code nodes populados

**Fluxo Principal:**

1. O ator executa `python3 .claude/brain/recall.py "populate" --type function`
2. O sistema busca nos Code nodes com label `Function`
3. Retorna funcoes relevantes com:
   - Qualified name (ex: `populate.parse_adr_log`)
   - Arquivo e linhas (ex: `populate.py:34-93`)
   - Docstring e complexidade
   - Conexoes semanticas (DEFINES, MEMBER_OF, MODIFIES)
4. O ator pode navegar pelas conexoes para entender o contexto

**Filtros disponiveis:**

```bash
# Buscar funcoes
python3 .claude/brain/recall.py "autenticacao" --type function

# Buscar classes
python3 .claude/brain/recall.py "brain" --type class

# Buscar modulos
python3 .claude/brain/recall.py "parser" --type module

# Buscar qualquer codigo
python3 .claude/brain/recall.py "serializer" --type code

# Buscar interfaces
python3 .claude/brain/recall.py "handler" --type interface
```

**Pos-condicoes:**

1. Ator encontrou as funcoes/classes relevantes
2. Memorias acessadas foram reforçadas (spreading activation)
3. Ator pode expandir nodes via `--expand` para detalhes completos

---

## Enriquecimento de Diffs

### UC-DIFF-01: Enriquecer Commits com Analise de Diff

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-DIFF-01 |
| **Nome** | Enriquecer Commits com Analise de Diff |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | `diff_parser.py`, `populate.py` |
| **Descricao** | O desenvolvedor enriquece os Commit nodes existentes no cerebro com informacoes estruturadas do diff: quais simbolos foram adicionados/modificados/removidos, forma da mudanca, e um resumo textual. |

**Pre-condicoes:**

1. Commits ja existem no cerebro (via `populate.py commits` ou `refresh`)
2. Repositorio git acessivel

**Fluxo Principal:**

1. O ator executa `python3 .claude/brain/populate.py diffs`
2. O sistema executa `git log -p` (streaming, um processo) para os ultimos 20 commits
3. Para cada commit:
   - Filtra arquivos ignoraveis (binarios, lock files, generated, vendor)
   - Parse do unified diff via state machine → `List[FileDiff]` com hunks
   - Classifica simbolos:
     - Linha adicionada com `def/function/class/struct` sem remocao correspondente = **new symbol**
     - Ambas adicao e remocao no mesmo contexto de funcao = **modified symbol**
     - Linha removida com definicao de simbolo sem adicao correspondente = **deleted symbol**
   - Classifica forma da mudanca (change_shape) por heuristica
   - Gera resumo textual (~500 tokens max)
4. Localiza o Commit node correspondente no cerebro (por `commit_hash`)
5. Atualiza o node existente:
   - Append do resumo ao `content`
   - Merge de props (`diff_summary`, `symbols_added`, `symbols_modified`, `symbols_deleted`, `change_shape`)
   - Regenera embedding (captura contexto do diff na busca semantica)
6. O sistema exibe total de commits enriquecidos

**Fluxos Alternativos:**

- **FA-01: Commit nao encontrado no cerebro**
  - O commit existe no git mas nao tem node correspondente no cerebro
  - O sistema silenciosamente ignora (nao cria node novo)
  - Solucao: rodar `populate.py commits` antes de `diffs`

- **FA-02: Diff muito grande (>5000 linhas)**
  - O parser para de processar apos 5000 linhas
  - O commit recebe analise parcial (primeiros arquivos apenas)

**Pos-condicoes:**

1. Commit nodes atualizados com `diff_summary`, `symbols_*`, `change_shape`
2. Propriedade `diff_enriched_at` registrada (para skip em re-runs)
3. Embeddings regenerados com contexto do diff
4. Busca por "quem adicionou a funcao X?" agora retorna resultados

**Exemplo de content atualizado de um Commit node:**

```text
feat(brain): add fallback graph
Files changed: brain.py, tests/test_brain.py

--- Diff Summary ---
Shape: feature_add (2 files, +120 -5)
Added: class:FallbackGraph, function:add_node, function:add_edge
Modified: function:test_brain_load
```

**Exemplo de saida:**

```text
$ python3 .claude/brain/populate.py diffs --max 10

=== Diff Enrichment (max 10) ===
Getting commits with diffs (max 10)...
Found 10 commits with diffs
Enriched 10 commits
```

---

### UC-DIFF-02: Backfill de Commits Historicos

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-DIFF-02 |
| **Nome** | Backfill de Commits Historicos |
| **Ator Principal** | Tech Lead, CI/CD |
| **Atores Secundarios** | `diff_parser.py`, `populate.py` |
| **Descricao** | O ator enriquece commits historicos (meses ou anos atras) para ter visibilidade completa do que cada commit mudou no codebase ao longo do tempo. |

**Pre-condicoes:**

1. Commits historicos ja existem no cerebro (via `populate.py commits 7000`)
2. A maioria nao tem `diff_enriched_at`

**Fluxo Principal:**

1. O ator executa `python3 .claude/brain/populate.py diffs --since 2025-01-01 --max 500`
2. O sistema busca commits desde a data especificada via `git log -p --since`
3. Para cada commit encontrado, executa o pipeline de enriquecimento (mesmo de UC-DIFF-01)
4. Commits ja enriquecidos sao reprocessados (a menos que `--unenriched` seja usado)

**Fluxos Alternativos:**

- **FA-01: Somente nao processados**
  - O ator executa `python3 .claude/brain/populate.py diffs --unenriched`
  - Apenas commits sem `diff_enriched_at` sao processados
  - Ideal para continuar um backfill interrompido

**Pos-condicoes:**

1. Commits historicos enriquecidos com analise de diff
2. Health check reporta % de enrichment atualizado

**Exemplos de CLI:**

```bash
# Backfill desde janeiro de 2025
python3 .claude/brain/populate.py diffs --since 2025-01-01 --max 500

# Continuar backfill (apenas nao processados)
python3 .claude/brain/populate.py diffs --unenriched

# Limitar quantidade
python3 .claude/brain/populate.py diffs --max 100
```

---

### UC-DIFF-03: Enriquecimento Automatico no Refresh

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-DIFF-03 |
| **Nome** | Enriquecimento Automatico no Refresh |
| **Ator Principal** | Claude Code (IA), `/learn` |
| **Atores Secundarios** | `populate.py`, `diff_parser.py` |
| **Descricao** | Ao executar `refresh` (parte do ciclo `/learn`), o sistema automaticamente enriquece os novos commits com analise de diff, sem intervencao manual. |

**Pre-condicoes:**

1. Novos commits adicionados ao cerebro via refresh

**Fluxo Principal:**

1. O ciclo `/learn` executa `populate.py refresh`
2. O refresh primeiro adiciona novos commits ao cerebro
3. Em seguida, automaticamente executa `populate_diffs(unenriched_only=True)`
4. Apenas os commits recem-adicionados (sem `diff_enriched_at`) sao enriquecidos
5. Cross-references sao criadas normalmente

**Pos-condicoes:**

1. Novos commits automaticamente enriquecidos com diff analysis
2. Nenhuma acao manual necessaria
3. O cerebro ja sabe "o que mudou" em cada commit recente

---

## Integracao (Sleep)

### UC-INT-01: Conectar Commits a Codigo via Sleep

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-INT-01 |
| **Nome** | Conectar Commits a Codigo via Sleep |
| **Ator Principal** | Claude Code (IA), `/learn` |
| **Atores Secundarios** | `sleep.py` (phase_connect) |
| **Descricao** | Durante o ciclo de sleep, o sistema conecta automaticamente Commit nodes a Code nodes atraves de dois passes: por file paths (Commit→Module) e por simbolos de diff (Commit→Function/Class). |

**Pre-condicoes:**

1. AST ingestion executada (Code nodes existem)
2. Diff enrichment executado (Commits tem `symbols_added`, `symbols_modified`)

**Fluxo Principal:**

1. O ciclo `/learn` ou `sleep.py` executa `phase_connect`
2. **Pass 4 (Commit → Module via file paths):**
   - Para cada Commit com lista de `files`, busca Module nodes com `file_path` correspondente
   - Cria edge `MODIFIES_SAME` (Commit → Module) com peso 0.5
3. **Pass 5 (Commit → Function/Class via diff symbols):**
   - Para cada Commit com `symbols_modified`/`symbols_added`/`symbols_deleted`
   - Busca Code nodes por nome do simbolo
   - Cria edge `MODIFIES` (Commit → Function/Class) com peso 0.7
4. O sistema reporta quantidade de edges criados

**Pos-condicoes:**

1. Commits conectados a Modules que tocam
2. Commits conectados a Functions/Classes que modificam
3. Navegacao bidirecional: "quem mexeu nesta funcao?" ↔ "o que este commit mudou?"
4. Spreading activation agora propaga de Code → Commit e vice-versa

**Exemplo de saida:**

```text
Phase [connect]...
  -> {"references": 0, "informed_by": 0, "applies": 0,
      "same_scope": 0, "modifies_same": 0,
      "commit_module": 4, "commit_symbol": 3}
```

---

### UC-INT-02: Rastrear Impacto de um Commit no Codigo

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-INT-02 |
| **Nome** | Rastrear Impacto de um Commit no Codigo |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | `recall.py`, Cerebro Organizacional |
| **Descricao** | O ator investiga um commit especifico para entender seu impacto: quais funcoes mudaram, quais modulos foram afetados, e o que outros commits tambem mexeram nas mesmas areas. |

**Pre-condicoes:**

1. AST + Diff integracoes executadas (UC-AST-01, UC-DIFF-01, UC-INT-01)

**Fluxo Principal:**

1. O ator busca o commit no cerebro:

   ```bash
   python3 .claude/brain/recall.py "feat brain fallback" --type commit
   ```

2. O resultado inclui:
   - `change_shape`: ex. `feature_add`
   - `symbols_added`: ex. `["class:FallbackGraph", "function:add_node"]`
   - `diff_summary`: resumo estruturado
3. O ator navega pelas **conexoes** do commit:
   - `MODIFIES` → Function/Class nodes que foram modificados
   - `MODIFIES_SAME` → Module nodes cujos arquivos foram tocados
   - `SAME_SCOPE` → Outros commits na mesma area
4. A partir de um Function node, o ator pode ver:
   - `MEMBER_OF` → Classe pai
   - `DEFINES` ← Module que contem a funcao
   - `MODIFIES` ← Outros commits que tambem mexeram nesta funcao

**Pos-condicoes:**

1. Ator entende o impacto completo do commit
2. Ator pode identificar mudancas acopladas (commits que sempre mexem nos mesmos arquivos)
3. Debug facilitado: se algo quebrou, os commits que mexeram na mesma area sao suspeitos

---

## Diagnostico

### UC-DIAG-01: Verificar Cobertura de Codigo e Diffs

| Campo | Valor |
| ------- | ------- |
| **ID** | UC-DIAG-01 |
| **Nome** | Verificar Cobertura de Codigo e Diffs |
| **Ator Principal** | Desenvolvedor Solo, CI/CD |
| **Atores Secundarios** | `cognitive.py` |
| **Descricao** | O ator executa health check e verifica: quantos Code nodes existem, qual a cobertura de modulos/classes/funcoes, e que percentual dos commits foi enriquecido com diff analysis. |

**Pre-condicoes:**

1. Cerebro inicializado

**Fluxo Principal:**

1. O ator executa `python3 .claude/brain/cognitive.py health`
2. O sistema retorna metricas tradicionais (health_score, nodes, edges, embeddings) **mais** duas secoes novas:
   - **code_coverage**: total de Code nodes, breakdown por tipo (modules, classes, functions, interfaces)
   - **diff_enrichment**: total de commits, commits enriquecidos, percentual de cobertura
3. O sistema gera recomendacoes automaticas:
   - Se 0 Code nodes: "Rode `populate.py ast` para ingerir estrutura do codigo"
   - Se <50% dos commits enriquecidos: "Rode `populate.py diffs --unenriched` para enriquecer"

**Pos-condicoes:**

1. Ator tem visibilidade da cobertura de codigo e diffs
2. Recomendacoes acionaveis para melhorar a cobertura

**Exemplo de saida:**

```json
{
  "health_score": 0.99,
  "status": "healthy",
  "code_coverage": {
    "modules": 13,
    "classes": 2,
    "functions": 103,
    "interfaces": 0,
    "total_code_nodes": 118
  },
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

## Referencia de CLI

### AST Ingestion

```bash
# Ingerir codebase inteiro
python3 .claude/brain/populate.py ast

# Diretorio especifico
python3 .claude/brain/populate.py ast ./src

# Filtrar linguagens
python3 .claude/brain/populate.py ast --lang py,ts

# Preview sem gravar
python3 .claude/brain/populate.py ast --dry-run

# Combinado
python3 .claude/brain/populate.py ast ./src --lang py --dry-run
```

### Diff Enrichment

```bash
# Ultimos 20 commits (padrao)
python3 .claude/brain/populate.py diffs

# Backfill por data
python3 .claude/brain/populate.py diffs --since 2025-01-01

# Limitar quantidade
python3 .claude/brain/populate.py diffs --max 500

# Somente nao processados
python3 .claude/brain/populate.py diffs --unenriched

# Combinado
python3 .claude/brain/populate.py diffs --since 2025-06-01 --max 200
```

### Recall com tipos de codigo

```bash
# Buscar funcoes
python3 .claude/brain/recall.py "autenticacao" --type function

# Buscar classes
python3 .claude/brain/recall.py "service" --type class

# Buscar modulos
python3 .claude/brain/recall.py "parser" --type module

# Buscar interfaces
python3 .claude/brain/recall.py "handler" --type interface

# Buscar qualquer codigo
python3 .claude/brain/recall.py "brain" --type code
```

### Refresh (automatico no /learn)

```bash
# Refresh padrao: commits + diffs + cross-refs
python3 .claude/brain/populate.py refresh

# Refresh com mais commits
python3 .claude/brain/populate.py refresh 50
```

### Standalone Parsers (debug/teste)

```bash
# Testar diff parser em um commit
python3 .claude/brain/diff_parser.py <commit_hash>

# Testar AST parser em um diretorio
python3 .claude/brain/ast_parser.py ./src --lang py

# AST parser dry run
python3 .claude/brain/ast_parser.py ./src --dry-run
```

---

## Arquivos Envolvidos

### Novos

| Arquivo | Linhas | Proposito |
| --------- | -------- | ----------- |
| `.claude/brain/ast_parser.py` | ~700 | Motor de AST multi-linguagem (tree-sitter + regex fallback) |
| `.claude/brain/diff_parser.py` | ~450 | Parser de unified diff + classificador de mudancas |

### Modificados

| Arquivo | Mudancas |
| --------- | ---------- |
| `.claude/brain/populate.py` | `populate_ast()`, `populate_diffs()`, CLI `ast`/`diffs`, diff no `refresh` |
| `.claude/brain/brain_sqlite.py` | `update_node_content()`, `node_id` param em `add_memory()`, Code decay rate, Code em `_primary_type()` |
| `.claude/brain/sleep.py` | `phase_connect` passes 4-5 (Commit↔Code), sampling estratificado em `phase_relate` |
| `.claude/brain/recall.py` | Novos tipos no `type_map` (code, module, class, function, interface), Code em `type_priority` |
| `.claude/brain/cognitive.py` | Health check com `code_coverage` e `diff_enrichment`, novas recomendacoes |

### Linguagens Suportadas (AST Parser)

| Linguagem | Extensoes | tree-sitter | Regex Fallback |
| ----------- | ----------- | ------------- | ---------------- |
| Python | `.py` | Sim | Sim (classes, funcoes, imports) |
| JavaScript | `.js`, `.jsx` | Sim | Sim (classes, funcoes, arrow functions) |
| TypeScript | `.ts`, `.tsx` | Sim | Sim (classes, funcoes, interfaces, types) |
| Ruby | `.rb` | Sim | Sim (classes, modules, funcoes) |
| Go | `.go` | Sim | Sim (structs, interfaces, funcs) |
| Java | `.java` | Sim | Sim (classes, interfaces, metodos) |
| Rust | `.rs` | Sim | Sim (structs, traits, enums, funcs) |
| PHP | `.php` | Sim | Sim (classes, interfaces, funcoes) |

### Padroes Arquiteturais Detectados

O AST parser detecta padroes arquiteturais por convencao de nomes:

| Sufixo | Padrao Detectado |
| -------- | ------------------ |
| `*Controller` | Controller |
| `*Service` | Service |
| `*Repository` | Repository |
| `*Factory` | Factory |
| `*Handler` | Handler |
| `*Middleware` | Middleware |
| `*Validator` | Validator |
| `*UseCase` | UseCase |
| `*Gateway` | Gateway |
| `*DTO` | DTO |
| `*Model` | Model |
| `*Entity` | Entity |
| `*Test` / `*Spec` | Test |

---

## Escala (Projeto 10+ Anos)

| Metrica | Estimativa | Mitigacao |
| --------- | ----------- | ----------- |
| 10k+ arquivos | tree-sitter parsea ~1MB/s, batch SQLite transactions | OK em <5 min |
| 50k+ simbolos | IDs de 16 chars (sem colisao ate bilhoes) | OK |
| 500 commits recentes | `git log -p` streaming, skip enriched | OK em <3 min |
| phase_relate O(n^2) | Sampling estratificado, cap 500 | Funcional |
| Re-runs | `body_hash` skip para AST, `diff_enriched_at` skip para diffs | O(mudancas) |
