# Proposta: Armazenar Trechos de Código no Cérebro

> Exploration de como incluir código real nos nós Code para recall semântico mais útil.

---

## Estado Atual

O `generate_content_text()` em `ast_parser.py` gera apenas **metadata** para embeddings:

```
# Function (hoje)
def authenticate(user_id: str) -> User
  File: src/auth/service.ts:45-89 (45 lines)
  Docstring: Validates user credentials and returns session
  Complexity: moderate
```

O cérebro **não** armazena o corpo da função. O recall encontra "authenticate" por similaridade semântica (assinatura + docstring) mas não retorna *como* está implementado.

---

## Objetivo

Quando o usuário pergunta "como funciona a autenticação?", o recall poderia retornar o trecho relevante em vez de só "leia src/auth/service.ts".

**Benefício:** Menos tokens — em vez de carregar o arquivo inteiro, o recall devolve só o trecho necessário.

---

## Desafios

| Desafio | Descrição |
|---------|-----------|
| **Tamanho** | Função pode ter 200+ linhas. Classe pode ter 500+. Inviável armazenar tudo. |
| **Embeddings** | Mais conteúdo = embeddings maiores. ChromaDB indexa por embedding; chunks grandes podem diluir a busca. |
| **Recall overflow** | top-10 resultados × 200 linhas cada = 2000 linhas = ~5k tokens. Pode exceder o que queremos retornar. |
| **Atualização** | Código muda. body_hash já existe para skip; precisamos re-parsear quando arquivo muda. |
| **Duplicação** | Commit diffs já trazem symbols_added/modified. Code nodes trazem estrutura. Body seria camada extra. |

---

## Abordagens Possíveis

### A. Body Preview (primeiras N linhas)

**Ideia:** Para cada Function/Class, adicionar primeiras 20–30 linhas do corpo ao `content`.

```python
# generate_content_text(fn) passaria a incluir:
def authenticate(user_id: str) -> User
  File: src/auth/service.ts:45-89
  Docstring: ...
  ---
  Body (first 25 lines):
  const user = await db.users.findById(user_id)
  if (!user) throw new AuthError('User not found')
  const session = await createSession(user)
  ...
```

**Prós:** Simples, tamanho previsível, dá "gosto" da implementação.  
**Contras:** Funções longas truncam no meio; lógica-chave pode estar no final.

**Implementação:** 
- `ast_parser` já tem `lines` e `line_start`/`line_end`. Adicionar `body_preview = lines[line_start:line_start+25]` ao parse.
- Ou: `generate_content_text` recebe `file_content` e extrai o range.

**Custo:** ~25 linhas × ~40 chars = ~1000 chars = ~250 tokens por nó. Com 400 Functions, +100k tokens no grafo. Embeddings: +400 vetores.

---

### B. Body Opcional por Tamanho

**Ideia:** Só incluir body para funções/classes **pequenas** (< 40 linhas). Grandes ficam só com metadata.

```
if (line_end - line_start) <= 40:
    content += "\n---\n" + body
else:
    content += "\n  (body omitted, 127 lines)"
```

**Prós:** Foco em trechos úteis; funções grandes raramente cabem no contexto de qualquer forma.  
**Contras:** Implementações complexas (ex.: auth com muitos branches) podem ficar de fora.

---

### C. Chunks por Função (full body, truncado)

**Ideia:** Armazenar corpo completo até um limite (ex.: 50 linhas). Acima disso, truncar com elipse.

```python
MAX_BODY_LINES = 50
body = lines[line_start:line_end]
if len(body) > MAX_BODY_LINES:
    body = body[:25] + ["  # ... truncated ..."] + body[-15:]
```

**Prós:** Início + fim muitas vezes basta (setup + return).  
**Contras:** Lógica central pode estar no meio.

---

### D. Recall com Modo `--compact` vs `--expand`

**Ideia:** O problema não é só armazenar, é **retornar**. 

- **Compact (default):** Recall retorna só `title` + `summary` (ou metadata). ~50 tokens/nó.
- **Expand:** Com flag `--include-code`, retorna `content` completo (com body).

Assim o cérebro pode armazenar body, mas o recall só inclui quando o usuário/cliente pede. Economia de tokens no caso comum.

**Implementação:** `recall.py` já retorna `content`. Adicionar `--compact` que omita `content` ou retorne só primeiros 200 chars.

---

### E. Prop Separado (não embarcar no embedding)

**Ideia:** Manter `content` para embedding como hoje (metadata). Adicionar `props.body_snippet` que não entra no embedding.

- Busca semântica usa só metadata (como hoje).
- Quando o nó é retornado, o cliente pode pedir `body_snippet` se existir.

**Prós:** Embeddings não incham; busca continua precisa.  
**Contras:** Precisa de mecanismo para "expandir" após a busca (ex.: segundo request ou flag).

---

### F. Só em Nodes "Interessantes"

**Ideia:** Heurística para incluir body só em nós considerados relevantes:

- Funções com docstring (já documentadas)
- Funções com nomes que batem com padrões: `*handler`, `*service`, `*auth*`, `*validate*`
- Classes com `detected_pattern` (Controller, Service, etc.)

**Prós:** Menos nós, menos armazenamento.  
**Contras:** Heurística pode errar; código importante pode ficar de fora.

---

## Recomendação: Abordagem Híbrida (A + B + D)

1. **Estender `generate_content_text`** para incluir body preview quando:
   - Function/Class com ≤ 40 linhas: body completo
   - Function/Class com > 40 linhas: primeiras 25 linhas + `"... (N more lines)"`

2. **Limite de tamanho no content:** Cap total em ~1500 chars (~375 tokens) por nó. Evita outliers.

3. **Recall `--compact`:** Novo modo que retorna só `title` + `summary` (sem `content`). Ou `--max-content-chars 500` para truncar.

4. **Manter compatibilidade:** `populate ast` já usa `body_hash` para incremental. Ao adicionar body ao content, o hash do arquivo muda → re-parse → content atualizado. Nada extra.

---

## Rascunho de Implementação

### 1. `ast_parser.py` — `generate_content_text`

```python
def generate_content_text(item, file_lines: List[str] = None) -> str:
    # ... existing metadata ...
    
    if file_lines and hasattr(item, 'line_start') and hasattr(item, 'line_end'):
        start, end = item.line_start - 1, item.line_end  # 0-based
        body = file_lines[start:end]
        max_lines = 40 if len(body) <= 40 else 25
        body_preview = body[:max_lines]
        if len(body) > max_lines:
            body_preview.append(f"  # ... ({len(body) - max_lines} more lines)")
        body_text = '\n'.join(body_preview)
        # Cap total
        if len(body_text) > 1200:
            body_text = body_text[:1200] + "\n  # ... truncated"
        parts.append(f"\n---\n{body_text}")
    
    return '\n'.join(parts)
```

O parser precisa passar `file_lines` ao gerar o content. O `ParseResult` ou o loop em `populate_ast` já tem acesso ao conteúdo do arquivo (é lido para o parse).

### 2. `populate.py` — passar linhas

O `scan_directory` retorna `ParseResult`. O conteúdo do arquivo é lido dentro do parser. Precisamos que `generate_content_text` receba as linhas. Opções:

- **a)** Adicionar `file_content: str` ao `ParseResult` (ou ao `ModuleInfo`) — o parse já lê o arquivo.
- **b)** Em `populate_ast`, antes de chamar `generate_content_text`, ler o arquivo: `lines = Path(mod.file_path).read_text().splitlines()`.

A opção (b) é mais simples e não mexe no parser. Custo: um read por arquivo, que já está sendo lido no parse. Na verdade o parse recebe `content` — está em `parse_file` ou similar. Verificar onde o arquivo é lido.

O `scan_directory` provavelmente chama `parse_file(file_path)` que lê o conteúdo. O `ParseResult` não guarda o conteúdo. Então precisamos ou guardar no parse ou ler de novo no populate. Ler de novo é O(1) por arquivo, aceitável.

### 3. `recall.py` — modo compacto

```python
parser.add_argument("--compact", action="store_true", help="Omit full content to save tokens")
# ao montar resultados:
if args.compact:
    for r in results:
        r["content"] = r.get("summary", r["content"][:300])  # truncar
```

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| brain.db e ChromaDB crescem | Limitar body a 40 linhas ou 1200 chars; só Functions/Classes, não Modules |
| Recall retorna muito | `--compact` ou `--max-content-chars` |
| Busca semântica piora | Testar: embeddings de metadata vs metadata+body. Se piorar, usar prop separado (E) |
| Performance do parse | body é extração de slice de lista; custo desprezível |

---

## Próximos Passos

1. **Spike:** Implementar (A+B) em um branch, só para Functions. Medir:
   - Crescimento de brain.db e ChromaDB
   - Qualidade do recall ("como funciona X?" com e sem body)
2. **Benchmark:** Comparar tokens retornados: recall com body vs ler arquivo completo.
3. **Decisão:** Se economia for significativa e qualidade boa, mergear. Caso contrário, avaliar prop separado (E) ou apenas recall `--expand` sob demanda.
