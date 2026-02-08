Inicializar o Engram para este projeto usando o sistema de auto-geração.

## Fase 0: Migração de Backup (se existir)

O setup.sh cria backups quando já existe configuração anterior.
Esta fase detecta, analisa e migra conteúdo customizado.

1. Execute a detecção de backups:
```bash
python3 .claude/skills/engram-genesis/scripts/migrate_backup.py --project-dir . --detect --output json
```

2. Se backups forem encontrados (`found: true`), execute análise completa:
```bash
python3 .claude/skills/engram-genesis/scripts/migrate_backup.py --project-dir . --analyze --output json
```

3. Apresente ao dev o que foi encontrado:
```
🔄 Backup Detectado — Análise de Migração
═════════════════════════════════════════

Componentes customizados encontrados:
  📦 Skills: [listar se houver]
  📦 Commands: [listar se houver]
  📦 Agents: [listar se houver]

Knowledge com conteúdo útil:
  📚 [arquivo]: [X linhas de conteúdo]

Permissões customizadas:
  ⚙️  [X] permissões adicionais detectadas

Recomendações:
  🔴 [alta prioridade]
  🟡 [média prioridade]

Estratégia: SMART (mesclar inteligentemente)
Continuar com migração? (perguntar ao dev)
```

4. Se aprovado, execute a migração:
```bash
python3 .claude/skills/engram-genesis/scripts/migrate_backup.py --project-dir . --migrate --strategy smart
```

5. **NÃO apague os backups ainda** — isso será feito na Fase Final.

Se não houver backups, pule para Fase 1.

## Fase 1: Análise do Projeto

1. Execute o analisador de projeto:
```bash
python3 .claude/skills/engram-genesis/scripts/analyze_project.py --project-dir . --output json
```

2. Leia o resultado e entenda a stack detectada e sugestões de componentes.

## Fase 2: Apresentar Plano

Apresente ao dev o plano de geração ANTES de executar:

```
🐍 Engram Init — Plano de Geração
═══════════════════════════════════

Stack detectada: [listar]

Skills a gerar:
  🔴 [nome] — [razão]
  🟡 [nome] — [razão]

Agents a gerar:
  🔴 [nome] — [razão]

Seeds universais (já instalados):
  ✅ project-analyzer
  ✅ knowledge-manager
  ✅ domain-expert
  ✅ priority-engine
  ✅ code-reviewer

[Se houve migração na Fase 0:]
Migrados do backup:
  ✅ [componentes preservados]

Continuar? (perguntar ao dev)
```

## Fase 3: Auto-Geração via Genesis

Ativar o skill `engram-genesis`. Para cada componente aprovado:

1. Gerar scaffold via `generate_component.py`
2. **Customizar o conteúdo** para este projeto específico:
   - Skills: preencher workflow com padrões reais da stack
   - Agents: configurar tools e skills relevantes
   - Commands: adaptar para o package manager e scripts do projeto
3. Validar via `validate.py`
4. Registrar via `register.py`

## Fase 4: Popular Knowledge

Preencher knowledge files com dados reais:

### CURRENT_STATE.md + Cérebro (população inicial)
A análise profunda vai para **ambos** — é a única vez que CURRENT_STATE.md é populado:
- Analisar o codebase em profundidade
- Mapear módulos, dependências, estado de cada área
- Identificar dívidas técnicas
- Listar bloqueios conhecidos

**Escrever no CURRENT_STATE.md** (snapshot legível para git e leitura humana):
- Status geral, fase, saúde, stack, bloqueios, próximo marco

**Registrar no cérebro** via `brain.add_memory()` (fonte primária a partir daqui):
```python
import sys
sys.path.insert(0, '.claude/brain')
from brain_sqlite import BrainSQLite as Brain

brain = Brain()
brain.load()
dev = {"author": "@engram"}  # ou get_current_developer() se disponível

# Estado inicial do projeto
brain.add_memory(
    title="Estado Inicial: [nome do projeto]",
    content="## Status\n[fase, saúde, stack]\n\n## Módulos\n[...]\n\n## Dívidas Técnicas\n[...]\n\n## Bloqueios\n[...]",
    labels=["State", "Genesis"],
    author=dev["author"],
    props={"phase": "genesis", "date": "[YYYY-MM-DD]"}
)

brain.save()
```

**Nota**: após o genesis, CURRENT_STATE.md não é mais atualizado — o cérebro assume via recall temporal (`--recent 7d`)

### PATTERNS.md
- Inspecionar código existente
- Detectar padrões recorrentes (naming, estrutura, error handling)
- Registrar como padrões aprovados
- **Se houve migração**: verificar se padrões do backup ainda são válidos

### DOMAIN.md
- Analisar nomes de entidades, variáveis, tabelas
- Extrair glossário do domínio
- Mapear regras de negócio implícitas no código
- **Se houve migração**: mesclar termos do backup

### PRIORITY_MATRIX.md
- Buscar TODOs no código
- Identificar issues/bugs óbvios
- Priorizar com ICE Score

### EXPERIENCE_LIBRARY.md
- **Se houve migração**: manter experiências do backup
- Caso contrário: criar vazia (será populada pelo /learn)

## Fase 5: Popular Cérebro Organizacional

O cérebro em `.claude/brain/` deve ser populado com conhecimento existente.

### 5.1 Verificar venv do Brain
```bash
# Verifica se venv existe e ativa
if [[ -d ".claude/brain/.venv" ]]; then
    source .claude/brain/.venv/bin/activate
fi
```

### 5.2 Popular com conhecimento existente

Processar ADRs, conceitos de domínio, patterns e commits:
```bash
python3 .claude/brain/populate.py all
```

Isso irá:
- Extrair ADRs do ADR_LOG.md
- Extrair conceitos do DOMAIN.md (glossário, regras, entidades)
- Extrair patterns do PATTERNS.md
- Processar últimos 7000 commits do git (memória episódica)
- **Ingerir estrutura do código via AST** (módulos, classes, funções, interfaces)
- **Enriquecer commits com análise de diff** (símbolos adicionados/modificados, change shape)

### 5.3 Gerar Embeddings para Busca Semântica
```bash
python3 .claude/brain/embeddings.py build
```

Isso irá:
- Usar ChromaDB HNSW como vector store primário (instalado pelo setup.sh)
- Auto-migrar embeddings.npz existentes se ChromaDB estiver vazio
- Fallback para npz se ChromaDB não estiver disponível
- Modelo local: `all-MiniLM-L6-v2` (384 dims, offline, gratuito)

### 5.4 Verificar Saúde do Cérebro
```bash
python3 .claude/brain/cognitive.py health
```

Se `status: healthy`, continuar. Se não, seguir recomendações.
Verificar que `vector_backend: chromadb` — se mostrar `npz`, reinstalar deps:
```bash
source .claude/brain/.venv/bin/activate && pip install chromadb pydantic-settings
python3 .claude/brain/patch_chromadb.py
```

### 5.5 Reportar ao Dev
```
🧠 Cérebro Organizacional Populado
══════════════════════════════════

Memórias criadas:
  📋 [X] ADRs (decisões arquiteturais)
  📚 [Y] Conceitos (glossário + regras)
  🔄 [Z] Patterns (padrões aprovados)
  📝 [W] Commits (memória episódica)

Total: [N] nós, [M] arestas
Grau médio: [G] (conectividade)
Embeddings: [E] vetores gerados
Vector store: [chromadb | npz]

Status: 🟢 Saudável
```

---

## Fase 6: Health Check

Executar `/doctor` para validar a instalação completa.

## Fase 7: Cleanup e Relatório Final

1. **Se houve backup na Fase 0**, execute cleanup:
```bash
python3 .claude/skills/engram-genesis/scripts/migrate_backup.py --project-dir . --cleanup
```

2. Remover staging de templates (se existir):
```bash
rm -rf .claude/templates/
```

3. Apresentar resumo do que foi:
   - Gerado (novos componentes)
   - Migrado (do backup)
   - Populado (knowledge files)
   - Validado (health check)

3. Sugerir próximos passos concretos baseado nas prioridades detectadas.

```
🐍 Engram Init — Concluído!
═══════════════════════════════════

✅ Componentes gerados: X skills, Y agents
✅ Migrados do backup: Z items
✅ Knowledge populado: 6 arquivos
✅ Cérebro populado: N nós, M arestas, E embeddings
✅ Health check: PASSED

🗑️  Backups removidos (migração concluída)

Próximos passos sugeridos:
  1. [baseado em PRIORITY_MATRIX]
  2. [baseado em PRIORITY_MATRIX]
  3. [baseado em PRIORITY_MATRIX]

Use /status para ver o estado atual.
Use /learn após cada sessão para retroalimentar.
Use .claude/brain/maintain.sh health para ver saúde do cérebro.
```
