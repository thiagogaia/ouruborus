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

### CURRENT_STATE.md
- Analisar o codebase em profundidade
- Mapear módulos, dependências, estado de cada área
- Identificar dívidas técnicas
- Listar bloqueios conhecidos

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

## Fase 5: Health Check

Executar `/doctor` para validar a instalação completa.

## Fase 6: Cleanup e Relatório Final

1. **Se houve backup na Fase 0**, execute cleanup:
```bash
python3 .claude/skills/engram-genesis/scripts/migrate_backup.py --project-dir . --cleanup
```

2. Apresentar resumo do que foi:
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
✅ Health check: PASSED

🗑️  Backups removidos (migração concluída)

Próximos passos sugeridos:
  1. [baseado em PRIORITY_MATRIX]
  2. [baseado em PRIORITY_MATRIX]
  3. [baseado em PRIORITY_MATRIX]

Use /status para ver o estado atual.
Use /learn após cada sessão para retroalimentar.
```
