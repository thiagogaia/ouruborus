# Projeto: ouroborusclaudegram_v2_final

## Identidade
Idioma padrão: Português brasileiro. Código e commits em inglês.

## Princípio Central: Auto-Alimentação (Ouroboros)
Este projeto usa Engram v3.0.0 — um sistema metacircular de retroalimentação com cérebro organizacional.
Toda decisão, padrão, erro corrigido ou insight DEVE ser registrado **direto no cérebro** via `brain.add_memory()`.
O sistema evolui a si mesmo: gera skills sob demanda, versiona mudanças, aposenta o inútil.

## Workflow Obrigatório

### Antes de Codificar
1. **O que mudou recentemente**: `python3 .claude/brain/recall.py --recent 7d --type Commit --top 10 --format json`
2. **Conhecimento relevante**: `python3 .claude/brain/recall.py "<tema da tarefa>" --top 10 --format json`
3. **Saúde do cérebro** (se necessário): `python3 .claude/brain/cognitive.py health`
4. Só leia os `.md` de knowledge se o recall não cobrir

O cérebro é a **fonte primária e única**. O recall retorna conteúdo completo (campo `content`) e suporta **busca temporal** (`--recent Nd`, `--since YYYY-MM-DD`, `--sort date`). Os `.md` de knowledge são mantidos em sincronia como fallback, para git diffs e leitura humana.

> **Nota**: Os knowledge files (CURRENT_STATE.md, ADR_LOG.md, PATTERNS.md, DOMAIN.md, EXPERIENCE_LIBRARY.md) são genesis-only — criados no setup e populados no /init-engram. Após o cérebro ser populado, não são mais atualizados. O recall os substitui. Único .md ativo: PRIORITY_MATRIX.md.

### Ao Codificar
- Validação de input em todas as APIs
- Error handling em todas as rotas

### Depois de Codificar
1. Registre padrões, decisões, experiências e domínio **direto no cérebro** via `brain.add_memory()`
2. Reavalie `PRIORITY_MATRIX.md` (único .md ativamente atualizado)
3. Execute `/learn` para consolidar

## Stack

## Auto-Geração (Metacircular)
O Engram gera seus próprios componentes:
- `/init-engram` — Análise profunda + geração de skills/agents para o projeto
- `/create [tipo] [nome]` — Gerar componente sob demanda
- `/doctor` — Health check do sistema
- `/learn` — Retroalimentação + evolução

DNA em `.claude/dna/`. Manifest em `.claude/manifest.json`.

## Skills Disponíveis
Consulte `.claude/skills/` — cada skill tem SKILL.md com instruções.
Skills são gerados sob demanda pelo `engram-genesis`.

## Subagentes
Definidos em `.claude/agents/`. Gerados pelo `/init-engram`.
Subagentes NÃO podem invocar outros subagentes.

## Orquestração Inteligente
O Claude cria subagents e skills sob demanda DURANTE o trabalho.
Se uma tarefa exige expertise que nenhum componente existente cobre:

1. **Detectar**: listar agents/skills, verificar se algum cobre
2. **Anunciar**: informar ao dev o que vai criar e por quê
3. **Gerar**: usar engram-genesis (scaffold → customizar → validar → registrar)
4. **Usar**: delegar a tarefa ao componente recém-criado
5. **Reportar**: informar o que foi criado ao final

Consulte `.claude/skills/engram-factory/SKILL.md` para o protocolo completo.
Referência detalhada em `.claude/skills/engram-factory/references/orchestration-protocol.md`.

Regras: anunciar antes de criar, máximo 2 por sessão, nunca duplicar, source=runtime.

## Cérebro Organizacional

O cérebro em `.claude/brain/` é a **fonte primária de conhecimento** — um grafo de conhecimento auto-alimentado.
Todo conteúdo é armazenado in-graph (props.content). Não depende de .md files para conteúdo.
- **Conexões entre nós**: quais commits mexeram nos mesmos arquivos, quais patterns se complementam, quais ADRs motivaram quais patterns
- **Busca semântica**: encontra conhecimento por significado, não só por texto
- **Spreading activation**: a partir de um resultado, navega conexões para encontrar conhecimento relacionado indiretamente

### IMPORTANTE: O Cérebro é a Fonte Única de Verdade

**O recall retorna conteúdo completo.** Não precisa ler .md files — o cérebro contém tudo. O recall já retorna o campo `content` com texto completo de cada memória.

```bash
# Busca semântica — output JSON parseável
python3 .claude/brain/recall.py "<pergunta>" --top 10 --format json

# Busca temporal — o que mudou recentemente
python3 .claude/brain/recall.py --recent 7d --type Commit --top 10 --format json

# Combinado — busca semântica filtrada por período
python3 .claude/brain/recall.py "<pergunta>" --since 2026-02-01 --sort date --format json

# Ver conexões semânticas de forma legível
python3 .claude/brain/recall.py "<pergunta>"
```

### Quando Consultar o Cérebro

Use `python3 .claude/brain/recall.py` automaticamente quando:
- **Qualquer tarefa nova**: buscar padrões, ADRs e experiências relacionadas
- Pergunta sobre arquitetura: "como funciona X?", "por que Y foi feito assim?"
- Pergunta sobre domínio: "o que é X?", "qual a regra de Y?"
- Antes de decisões: verificar se já existe ADR relacionado
- Debug de problemas: encontrar soluções anteriores similares
- Refactoring: encontrar commits que mexeram nos mesmos arquivos

### Quando Usar Domain-Expert Automaticamente

O Claude DEVE invocar `domain-analyst` ou seguir `domain-expert` quando:
1. **Termo desconhecido**: Encontrar termo de negócio NÃO documentado no DOMAIN.md
2. **Regra implícita**: Descobrir validação/constraint que revela regra de negócio
3. **Estados de negócio**: Ver enum/constante que define estados ou transições
4. **Comentário "por quê"**: Encontrar comentário explicando motivação (não implementação)
5. **Pergunta de negócio**: Usuário perguntar sobre regras, fluxos ou entidades
6. **Lógica condicional complexa**: Analisar código com if/switch em status, permissões, etc.

**Workflow de Descoberta Automática:**
```
1. Detectar → é conhecimento de domínio?
2. Verificar → já está no DOMAIN.md?
3. Se não está → extrair e propor registro
4. Se inconsistente → reportar possível bug
5. Validar → confirmar com dev antes de registrar
```

**Atalho:** Use `/domain [termo ou pergunta]` para análise sob demanda.

### Exemplo de Uso

```bash
# Busca semântica — retorna nós + conexões
python3 .claude/brain/recall.py "autenticação" --format json

# Filtrar por tipo
python3 .claude/brain/recall.py "setup" --type ADR --top 5

# O que mudou nos últimos 7 dias (substitui "O Que Mudou Recentemente" do antigo CURRENT_STATE.md)
python3 .claude/brain/recall.py --recent 7d --type Commit --top 10

# Busca temporal com query semântica
python3 .claude/brain/recall.py "bug" --since 2026-02-01 --sort date --top 5

# Ver saúde do cérebro
python3 .claude/brain/cognitive.py health
```

### O que as Conexões Semânticas Revelam

O campo `connections` nos resultados do recall mostra relações que os .md não contêm:
- `SAME_SCOPE`: commits que trabalharam na mesma área — se um quebrou algo, os outros são suspeitos
- `MODIFIES_SAME`: commits que tocaram os mesmos arquivos — mudanças acopladas
- `RELATED_TO`: nós semanticamente similares — patterns complementares, conceitos relacionados
- `BELONGS_TO_THEME`: commits agrupados por tema — mostra áreas de atividade
- `REFERENCES`: referências cruzadas explícitas entre ADRs, patterns e experiências

### Quando Alimentar o Cérebro

O cérebro é alimentado automaticamente via `/learn`. Execute ao final de cada sessão.
O `/learn` roda: brain.add_memory() (direto, com embeddings inline) → refresh (commits) → sleep (8 fases de inteligência) → health check.

O loop de auto-alimentação funciona assim:
1. `/recall` busca → reforça memórias acessadas → **persiste** (brain.save())
2. Trabalho acontece → novas memórias via `brain.add_memory()` (embeddings gerados inline)
3. `/learn` consolida → sleep (connect, relate, themes, calibrate, promote, insights, gaps, decay)
4. Próximo recall acha resultados melhores (memórias reforçadas + novas conexões + promoções + insights)

## Regras de Ouro
- NUNCA pule o workflow de retroalimentação
- Priorize legibilidade sobre cleverness
- Pergunte antes de mudar arquitetura
- Registre TUDO que pode ser útil no futuro
- Se não existe skill para algo repetitivo: crie com `/create`
- **Cérebro é a fonte primária** — rode recall primeiro, .md como fallback e espelho legível
