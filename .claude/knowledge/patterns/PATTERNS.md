# Padrões do Projeto
> Última atualização: 2026-02-03 (/init-engram)

## Padrões Aprovados

### PAT-001: Feedback Loop do Engram
- **Contexto**: ao final de qualquer tarefa
- **Solução**: executar /learn para registrar mudanças, padrões e decisões
- **Descoberto em**: 2026-02-03

### PAT-002: Estrutura de Skill
- **Contexto**: ao criar um novo skill
- **Solução**: seguir schema em `.claude/schemas/skill.schema.md`
  - Diretório kebab-case com SKILL.md obrigatório
  - Frontmatter YAML com name + description (50-500 chars)
  - Scripts em scripts/ com shebang e permissão executável
  - References em references/ para docs sob demanda
- **Exemplo**: `.claude/skills/engram-genesis/`
- **Descoberto em**: 2026-02-03

### PAT-003: Estrutura de Agent
- **Contexto**: ao criar um novo agent
- **Solução**: seguir schema em `.claude/schemas/agent.schema.md`
  - Arquivo único .md em .claude/agents/
  - Frontmatter YAML com name, description, tools
  - Body com responsabilidades, regras, output esperado
- **Exemplo**: `.claude/agents/architect.md`
- **Descoberto em**: 2026-02-03

### PAT-004: Estrutura de Command
- **Contexto**: ao criar um novo slash command
- **Solução**: seguir schema em `.claude/schemas/command.schema.md`
  - Arquivo único .md em .claude/commands/
  - SEM frontmatter (diferente de skills/agents)
  - Instruções diretas para o Claude
- **Exemplo**: `.claude/commands/commit.md`
- **Descoberto em**: 2026-02-03

### PAT-005: Scripts Python Padrão
- **Contexto**: ao criar scripts para skills
- **Solução**:
  - Shebang `#!/usr/bin/env python3`
  - Docstring com usage
  - argparse para CLI
  - Funções isoladas e testáveis
  - main() no final com if __name__ == "__main__"
- **Exemplo**: `core/genesis/scripts/validate.py`
- **Descoberto em**: 2026-02-03

### PAT-006: Registro em Manifest
- **Contexto**: ao criar/modificar componentes
- **Solução**: usar register.py para manter manifest.json sincronizado
  - `python3 register.py --type skill --name nome --source genesis`
  - Sources válidos: core, seed, genesis, manual, evolution, runtime
- **Descoberto em**: 2026-02-03

### PAT-007: Validação Antes de Registro
- **Contexto**: antes de registrar componente
- **Solução**: rodar validate.py primeiro
  - `python3 validate.py --type skill --path .claude/skills/nome/`
  - Corrigir todos os erros antes de registrar
- **Descoberto em**: 2026-02-03

### PAT-008: Knowledge Files Organization
- **Contexto**: ao organizar conhecimento persistente
- **Solução**:
  - context/CURRENT_STATE.md → estado vivo do projeto
  - priorities/PRIORITY_MATRIX.md → ICE Score
  - patterns/PATTERNS.md → padrões aprovados (este arquivo)
  - decisions/ADR_LOG.md → decisões arquiteturais
  - domain/DOMAIN.md → glossário + regras de negócio
  - experiences/EXPERIENCE_LIBRARY.md → soluções reutilizáveis
- **Descoberto em**: 2026-02-03

### PAT-009: Versionamento de Componentes
- **Contexto**: ao evoluir um componente existente
- **Solução**:
  - archive.py faz backup em .claude/versions/
  - Incrementar versão no manifest
  - Registrar mudança no evolution-log.md
- **Descoberto em**: 2026-02-03

### PAT-010: Runtime Component Creation
- **Contexto**: quando Claude precisa de expertise inexistente durante tarefa
- **Solução**:
  - Anunciar ao dev o que vai criar e por quê
  - Usar genesis para gerar scaffold
  - Customizar para o caso específico
  - Registrar com source=runtime
  - Avaliar no próximo /learn
- **Descoberto em**: 2026-02-03

### PAT-011: Migração Inteligente de Backups
- **Contexto**: ao reinstalar Engram em projeto com instalação anterior
- **Solução**: migrate_backup.py com estratégia smart
  - Fase 0 do /init-engram: detectar → analisar → apresentar → migrar
  - Preservar skills/commands/agents customizados (não-core)
  - Merge de permissões no settings.json
  - Merge semântico de knowledge files (append entries únicos)
  - Cleanup na Fase 6 após sucesso
- **Descoberto em**: 2026-02-03

### PAT-012: Venv Isolado para Brain
- **Contexto**: dependências Python pesadas (torch, sentence-transformers)
- **Solução**: criar venv em `.claude/brain/.venv`
  - setup.sh cria e instala deps automaticamente
  - Scripts do brain ativam venv antes de executar
  - Evita conflitos com Python do sistema
  - Permite embeddings locais sem cloud
- **Exemplo**: `source .claude/brain/.venv/bin/activate && python3 brain.py stats`
- **Descoberto em**: 2026-02-03

### PAT-013: Integração de Features em Commands Existentes
- **Contexto**: nova feature que complementa workflow existente
- **Solução**: adicionar fase ao command existente em vez de criar novo
  - /init-engram: Fase 5 para popular cérebro
  - /learn: Fase 4 para criar memórias
  - Mantém fluxo único e intuitivo
- **Descoberto em**: 2026-02-03

## Anti-Padrões

### ANTI-001: Pular Feedback Loop
- **Problema**: conhecimento se perde entre sessões
- **Solução**: SEMPRE rodar /learn ao final de tarefa significativa
- **Descoberto em**: 2026-02-03

### ANTI-002: Skills Muito Grandes
- **Problema**: SKILL.md com mais de 500 linhas fica difícil de manter
- **Solução**: mover detalhes para references/, usar composes para orquestrar
- **Descoberto em**: 2026-02-03

### ANTI-003: Duplicar Componentes
- **Problema**: skills/agents redundantes confundem e desperdiçam tokens
- **Solução**: verificar com /curriculum antes de criar, considerar merge
- **Descoberto em**: 2026-02-03

### ANTI-004: Ignorar Validação
- **Problema**: componentes inválidos quebram o sistema
- **Solução**: SEMPRE validar antes de registrar
- **Descoberto em**: 2026-02-03

### ANTI-005: Manifest Dessincronizado
- **Problema**: componentes existem mas não estão no manifest (ou vice-versa)
- **Solução**: usar register.py, rodar /doctor periodicamente
- **Descoberto em**: 2026-02-03
