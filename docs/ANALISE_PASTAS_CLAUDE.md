# Análise: Pastas em `.claude/` na Instalação

> Origem das pastas archive, consolidated, docs, memory, templates durante setup.sh e init-engram.

## Resumo

| Pasta | Criada por | Usada pelo Brain v4? | Observação |
|-------|------------|---------------------|------------|
| **archive** | — | ❌ Não | Removida do setup (ADR-024) |
| **consolidated** | — | ❌ Não | Removida do setup (ADR-024) |
| **memory** | — | ❌ Não | Removida do setup (ADR-024) |
| **templates** | setup.sh | — | Staging: removida no init-engram Fase 7 |
| **docs** | — | — | Não criada por setup nem init-engram |

---

## 1. setup.sh — O que cria

Em `install_core()` (linhas 379–390):

```bash
# 10. Install brain (organizational memory)
if [[ -d "$SCRIPT_DIR/.claude/brain" ]]; then
    mkdir -p "$CLAUDE_DIR/brain/state"
    # memory/, consolidated/, archive/ — deprecated (ADR-024), removidas em v4.1
    cp "$SCRIPT_DIR/.claude/brain/"*.py ...
```

**Atualizado (ADR-024):** memory/, consolidated/ e archive/ não são mais criadas.

E em linhas 251–255 (skill templates):

```bash
if [[ -d "$SCRIPT_DIR/templates/skills" ]]; then
    mkdir -p "$CLAUDE_DIR/templates/skills"
    cp -r "$SCRIPT_DIR/templates/skills/"* "$CLAUDE_DIR/templates/skills/"
```

**Pastas criadas pelo setup.sh:**
- `brain/state/`
- `templates/skills/`
- ~~`memory/`~~ ~~`consolidated/`~~ ~~`archive/`~~ — removidas (ADR-024)

---

## 2. init-engram — O que altera

Na **Fase 7** (Cleanup):

```bash
rm -rf .claude/templates/
```

O init-engram remove `templates/` após o genesis. É só área de staging.

---

## 3. Uso atual (Brain v4)

O Brain v4 usa **SQLite** (`brain.db`) + **ChromaDB** como store. Não usa mais:

- `memory/` — antes o `brain.py` (JSON) gravava um .md por memória
- `consolidated/` — nunca usada no código atual
- `archive/` — `cognitive.py archive` apenas marca nós como `Archived` no grafo; não grava em disco

O `brain_sqlite.py` define `self.memory_path = self.base_path.parent / "memory"` (linha 165), mas **não usa** esse atributo em nenhum lugar.

---

## 4. Pasta `docs`

Não há criação de `.claude/docs/` nem no setup nem no init-engram. Possíveis origens:

- `docs/` na raiz do projeto (documentação do Engram)
- Algum subdiretório, por ex. `skills/*/references/`

---

## 5. Decisão (ADR-024)

**Aplicado 2026-02-08:**
- ✅ Removido do setup.sh: criação de memory/, consolidated/, archive/
- ✅ ADR-024: Deprecar essas pastas, remoção completa em v4.1
- Pendente v4.1: remover `memory_path` de brain_sqlite.py/brain.py se ainda existir
