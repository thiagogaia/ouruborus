Inicializar o Engram para este projeto usando o sistema de auto-geração.

## Fase 1: Análise do Projeto

1. Execute o analisador de projeto:
```bash
python3 .claude/skills/engram-genesis/scripts/analyze_project.py --project-dir . --output json
```

2. Leia o resultado e entenda a stack detectada e sugestões de componentes.

3. Se existir `.claude.bak/` ou `CLAUDE.md.bak`, leia para migrar configurações anteriores:
   - Commands customizados → preservar
   - Regras de coding → incorporar no CLAUDE.md
   - Knowledge files → mesclar com templates novos
   - Settings.json → mesclar permissões

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

### CURRENT_STATE.md
- Analisar o codebase em profundidade
- Mapear módulos, dependências, estado de cada área
- Identificar dívidas técnicas
- Listar bloqueios conhecidos

### PATTERNS.md
- Inspecionar código existente
- Detectar padrões recorrentes (naming, estrutura, error handling)
- Registrar como padrões aprovados

### DOMAIN.md
- Analisar nomes de entidades, variáveis, tabelas
- Extrair glossário do domínio
- Mapear regras de negócio implícitas no código

### PRIORITY_MATRIX.md
- Buscar TODOs no código
- Identificar issues/bugs óbvios
- Priorizar com ICE Score

### EXPERIENCE_LIBRARY.md
- Criar vazia (será populada pelo /learn)

## Fase 5: Health Check

Executar `/doctor` para validar a instalação completa.

## Fase 6: Relatório Final

Apresentar resumo do que foi gerado, populado e validado.
Sugerir próximos passos concretos baseado nas prioridades detectadas.
