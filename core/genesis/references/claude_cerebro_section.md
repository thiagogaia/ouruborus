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
.claude/brain/.venv/bin/python3 .claude/brain/recall.py "<pergunta>" --top 10 --format json

# Busca temporal — o que mudou recentemente
.claude/brain/.venv/bin/python3 .claude/brain/recall.py --recent 7d --type Commit --top 10 --format json

# Combinado — busca semântica filtrada por período
.claude/brain/.venv/bin/python3 .claude/brain/recall.py "<pergunta>" --since 2026-02-01 --sort date --format json

# Ver conexões semânticas de forma legível
.claude/brain/.venv/bin/python3 .claude/brain/recall.py "<pergunta>"
```

### Quando Consultar o Cérebro

Use `.claude/brain/.venv/bin/python3 .claude/brain/recall.py` automaticamente quando:
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
