# Padrões do Projeto
> Última atualização: 2026-02-04 (/learn commit c7a67be)

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

### PAT-014: Higienização de Repositório com .gitignore
- **Contexto**: primeiro commit ou limpeza de repositório
- **Solução**: criar .gitignore robusto ANTES de commitar
  - Python: `**/__pycache__/`, `*.py[cod]`, `*.so`, `.eggs/`
  - IDE: `.idea/`, `.vscode/`, `*.swp`
  - OS: `.DS_Store`, `Thumbs.db`
  - Environment: `.env`, `.env.local`, `.env.*.local`
  - Engram backups: `.claude.bak/`, `CLAUDE.md.bak`
- **Exemplo**: commit 774b6c58 removeu 22 arquivos __pycache__ do histórico
- **Descoberto em**: 2026-02-03

### PAT-017: Execução Sequencial como Vantagem Arquitetural
- **Contexto**: questionamento sobre se orquestração deveria ser paralela
- **Solução**: manter modelo sequencial deliberadamente
  - Evita race conditions em knowledge files
  - Permite detecção de co-ativações para propor composições
  - 3x mais barato em tokens (contexto compartilhado)
  - Skills gerados em sequência evitam redundância
- **Anti-pattern**: paralelismo com context windows isoladas quebraria rastreamento de evolução
- **Referência**: [[EXP-010]], commit 6d7c3077
- **Descoberto em**: 2026-02-04

## Anti-Padrões

### ANTI-006: Paralelismo em Sistema de Evolução
- **Problema**: context windows isoladas quebram rastreamento de uso
- **Consequências**: sem co-ativações detectáveis, não há dados para propor composições
- **Solução**: usar modelo sequencial com contexto compartilhado
- **Descoberto em**: 2026-02-04

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

### ANTI-006: Commitar Arquivos Binários Python
- **Problema**: `__pycache__/` e `*.pyc` poluem histórico git, crescem o repo, causam conflitos
- **Solução**: SEMPRE adicionar ao .gitignore antes do primeiro commit Python
- **Corrigido**: commit 774b6c58 (removeu 22 binários do histórico)
- **Descoberto em**: 2026-02-03

---

## Padrões de DevOps

### PAT-015: Auto-Instalação de Dependências do Sistema
- **Contexto**: setup.sh precisa de dependências que podem não estar instaladas
- **Solução**: Fallback progressivo com detecção de plataforma
  1. Detectar sistema operacional (Debian/Ubuntu vs outros)
  2. Tentar instalar automaticamente se possível
  3. Fallback: passwordless sudo → sudo com senha → instruções manuais
  4. Mensagens claras indicando próximos passos
- **Exemplo**: `python3.X-venv` em Debian/Ubuntu (commit 367a4c1)
  - Detecta se é Debian: `[[ -f /etc/debian_version ]]`
  - Obtém versão Python dinamicamente: `python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'`
  - Tenta: `sudo apt install python3.X-venv`
  - Se falha: mostra comando manual com instruções claras
- **Benefícios**: UX melhorada, funciona em WSL, graceful degradation
- **Descoberto em**: 2026-02-04

### PAT-016: Commit de Documentação Arquitetural Estruturado
- **Contexto**: registrar análises arquiteturais e modelo de orquestração
- **Solução**: commit estruturado com múltiplos componentes:
  1. Atualizar PRIORITY_MATRIX.md (mover concluídas para cemitério)
  2. Criar memórias no cérebro (episódicas, conceituais ou procedurais)
  3. Rodar consolidação do grafo (fortalece conexões)
  4. Registrar ativações no manifest.json
- **Exemplo**: Commit 7f7f221 - "docs(knowledge): record architectural analysis on orchestration model"
  - Criou 3 memórias: milestone v3.0, fix seeds, conceito metacircular
  - Consolidou 111 conexões no grafo
  - Registrou 4 tarefas no cemitério
  - Atualizou ativações do engram-genesis
- **Benefício**: Rastreabilidade completa de decisões e estado do sistema
- **Descoberto em**: 2026-02-04 (extraído via /learn do commit 7f7f221)

### PAT-017: Commit Fundacional Completo
- **Contexto**: ao criar a base de um sistema novo (v1.0.0, v2.0.0)
- **Solução**: incluir em um único commit atômico:
  - Estrutura de diretórios completa
  - Schemas de validação (definições formais)
  - Componentes core (motors/engines)
  - Seeds (componentes universais)
  - Knowledge files populados com dados reais
  - Documentação inicial
- **Exemplo**: commit 264072a6 do Engram v2.0.0
  - 61 arquivos, 6002 linhas adicionadas
  - 4 skills, 3 agents, 13 commands, 4 schemas
  - 6 knowledge files com conteúdo real
  - 550 linhas de proposta de semantic search
- **Benefício**: checkout de qualquer commit gera sistema funcional
- **Descoberto em**: 2026-02-04 (análise retrospectiva)

### PAT-018: Separação Motor vs Produto
- **Contexto**: ao estruturar sistema metacircular/auto-gerativo
- **Solução**: separar claramente em 3 camadas:
  - **Motor de geração** (engram-genesis) - cria componentes
  - **Motor de evolução** (engram-evolution) - rastreia uso, propõe melhorias
  - **Produtos gerados** (skills, agents, commands) - usados pelo dev
- **Estrutura de cada motor**:
  - SKILL.md com instruções do processo
  - scripts/ com implementação em Python
  - references/ com documentação adicional
- **Descoberto em**: 2026-02-04 (análise do commit 264072a6)

### PAT-019: Documentação por Proximidade
- **Contexto**: ao organizar schemas, references, documentação técnica
- **Solução**: documentação fica próxima ao código que documenta
  - Schemas em `.claude/schemas/` (junto ao manifest)
  - References de skill em `skill/references/`
  - Proposals/RFCs em `docs/` (documentos longos de design)
- **Exemplo**: `docs/semantic_search_proposal.md` (550 linhas de design doc)
- **Descoberto em**: 2026-02-04

### PAT-020: Major Version Upgrade com Brain Integration (v3.0.0)
- **Contexto**: upgrade de versao major com integracao de sistema de memoria
- **Solucao**: commit atomico com todos os componentes sincronizados
  1. Atualizar `.engram-version` (2.0.0 -> 3.0.0)
  2. Adicionar seeds faltantes ao sistema (5 novos skills)
  3. Sincronizar `manifest.json` com 9 skills registrados
  4. Atualizar `CURRENT_STATE.md` com diagrama metacircular
  5. Popular cerebro: 68 nos, 106 arestas, 61 embeddings
  6. Criar cognitive-log.jsonl para auditoria
  7. Rodar health check (26 verificacoes = 100%)
- **Exemplo**: commit cb64fd73 (Engram v3.0.0)
- **Descoberto em**: 2026-02-04 (extraido via /learn do commit cb64fd73)

### PAT-021: Skills Seeds Universais
- **Contexto**: skills que devem existir em toda instalacao do Engram
- **Solucao**: garantir 6 seeds completos com source=seed
  - **knowledge-manager**: gerencia feedback loop e knowledge files
  - **domain-expert**: descoberta de glossario e regras de negocio
  - **priority-engine**: priorizacao com ICE Score
  - **code-reviewer**: review em 4 camadas (correcao, padroes, seguranca, performance)
  - **engram-factory**: orquestracao runtime e criacao sob demanda
  - **project-analyzer**: analise profunda de codebase
- **Exemplo**: commit cb64fd73 corrigiu instalacao adicionando 5 seeds faltantes
- **Descoberto em**: 2026-02-04 (extraido via /learn do commit cb64fd73)

### PAT-022: Cognitive Log como Append-Only Journal
- **Contexto**: rastrear operacoes cognitivas do cerebro organizacional
- **Solucao**: arquivo JSONL (uma linha JSON por operacao)
  - Registra: edges_strengthened, patterns_detected, summaries_created
  - Lista hubs ordenados por conexoes (centralidade)
  - Timestamp da execucao para auditoria
  - Format: `.claude/brain/cognitive-log.jsonl`
- **Beneficio**: permite debugging e analise de evolucao do grafo
- **Exemplo**: consolidacao com 106 arestas fortalecidas, hub principal "person-engram" com 49 conexoes
- **Descoberto em**: 2026-02-04 (extraido via /learn do commit cb64fd73)

---

## Padroes de Busca e Interface (commit 5db29c67)

### PAT-023: Interface de Consulta com Fallback Gracioso
- **Contexto**: script Python depende de modulos que podem nao estar instalados
- **Solucao**: implementar try/except no import com variavel HAS_DEPS
  - Se dependencias ausentes: retornar erro informativo + sugestao de fallback
  - Nunca crashar silenciosamente
  - Fornecer caminho alternativo (ex: "consulte .claude/knowledge/ diretamente")
- **Exemplo**: recall.py retorna fallback quando Brain/embeddings nao carregam
- **Descoberto em**: 2026-02-03 (commit 5db29c67)

### PAT-024: Busca Hibrida (Embeddings + Texto)
- **Contexto**: busca semantica requer embeddings, que podem falhar
- **Solucao**: tentar embedding primeiro, fallback para busca textual
  - Gerar embedding da query
  - Se falhar: usar parametro query= em vez de query_embedding=
  - Avisar em stderr que esta usando modo degradado
- **Exemplo**: recall.py tenta embeddings.get_embedding(), fallback para brain.retrieve(query=...)
- **Descoberto em**: 2026-02-03 (commit 5db29c67)

### PAT-025: Formato de Output Dual (JSON + Human)
- **Contexto**: CLIs precisam servir tanto scripts quanto humanos
- **Solucao**: argparse com --format (json|human)
  - JSON para pipelines e integracao
  - Human para leitura direta com formatacao visual
  - Mesma estrutura de dados, apresentacao diferente
- **Exemplo**: recall.py --format json vs recall.py --format human
- **Descoberto em**: 2026-02-03 (commit 5db29c67)

### PAT-026: Command File em Dois Locais
- **Contexto**: commands do Engram devem estar no projeto E no core para propagacao
- **Solucao**: manter copia em .claude/commands/ (projeto) e core/commands/ (template)
  - Projeto usa .claude/commands/
  - setup.sh copia de core/commands/ para novos projetos
  - Alteracoes devem ser feitas em ambos ou apenas no core
- **Descoberto em**: 2026-02-03 (commit 5db29c67)

### PAT-027: Spreading Activation para Busca em Grafo
- **Contexto**: buscar conhecimento relacionado em grafo de conhecimento
- **Solucao**: spreading activation com depth configuravel
  - Buscar nos iniciais por similaridade
  - Expandir para nos conectados ate depth niveis
  - Combinar scores de similaridade + conexao
  - Ranquear resultados finais
- **Exemplo**: recall.py --depth 3 expande busca por 3 niveis de conexao
- **Descoberto em**: 2026-02-03 (commit 5db29c67)

---

## Padrões Fundacionais (commit bbcc8777 - inicial)

### PAT-028: Análise de Mercado como Base para Decisões Arquiteturais
- **Contexto**: antes de criar sistema novo, entender o que existe
- **Solução**: pesquisa estruturada com 4 dimensões:
  1. **Panorama de Mercado**: projetos similares (acadêmicos + indústria)
  2. **Gap Analysis**: o que falta no sistema atual vs mercado
  3. **Arquitetura Proposta**: síntese do melhor de cada inspiração
  4. **Roadmap**: sprints com features priorizadas
- **Exemplo**: `Engram_self_bootstrap_analysis.md` (704 linhas)
  - Analisou: Voyager, DGM, BOSS, Claude Memory Bank, Self-Improving CLAUDE.md
  - Identificou 9 gaps (sem auto-geração, sem composição, sem verificação...)
  - Propôs 4 fases: Bootstrap → Gênese → Uso → Reflexão
- **Benefício**: decisões fundamentadas, não arbitrárias
- **Descoberto em**: 2026-02-03 (commit bbcc8777)

### PAT-029: Templates por Stack como Progressive Customization
- **Contexto**: skills precisam ser customizados por framework/linguagem
- **Solução**: biblioteca de templates em `templates/skills/`:
  ```
  templates/skills/
  ├── nextjs/nextjs-patterns.skill.tmpl
  ├── django/django-patterns.skill.tmpl
  ├── fastapi/fastapi-patterns.skill.tmpl
  ├── laravel/laravel-patterns.skill.tmpl
  ├── express/express-patterns.skill.tmpl
  ├── react/react-patterns.skill.tmpl
  └── vue/vue-patterns.skill.tmpl
  ```
  - Template é ponto de partida (não produto final)
  - Genesis customiza para o projeto específico
  - Stack detection em analyze_project.py determina qual template usar
- **Exemplo**: Next.js 14 → template nextjs-patterns → skill customizado com padrões do projeto
- **Descoberto em**: 2026-02-03 (commit bbcc8777)

### PAT-030: Documentação de Uso como Guia de Adoção
- **Contexto**: sistema complexo precisa de guia prático
- **Solução**: documento separado (`Engram_v2_guia_de_uso.md`) com:
  1. Ciclo de vida (instalação → inicialização → uso diário)
  2. Metodologia diária (/status → trabalho → /learn)
  3. Exemplos concretos por stack (Next.js, Django)
  4. Cenários de auto-geração e evolução
  5. Referência rápida (tabela de commands)
- **Estrutura**: 742 linhas, 8 seções, flow diagrams ASCII
- **Benefício**: onboarding rápido, reduz curva de aprendizado
- **Descoberto em**: 2026-02-03 (commit bbcc8777)

### PAT-031: Organização de Extras vs Core
- **Contexto**: alguns skills são universais, outros são de nicho
- **Solução**: separar em `core/` (instalado sempre) e `extras/` (opcional)
  ```
  core/
  ├── seeds/          ← skills universais
  ├── agents/         ← agents base
  └── commands/       ← commands essenciais

  extras/
  ├── skills/         ← skills de nicho (n8n, sales-funnel)
  └── agents/         ← agents especializados (prompt-engineer)
  ```
  - Core é copiado pelo setup.sh automaticamente
  - Extras requer cópia manual ou flag específica
- **Exemplo**: n8n-agent-builder é extra (poucos projetos usam n8n)
- **Descoberto em**: 2026-02-03 (commit bbcc8777)

### PAT-032: Instrução Proativa para Skills
- **Contexto**: skill existe mas não está sendo usado automaticamente pelo Claude
- **Solução**: adicionar seção "Quando Usar X Automaticamente" no CLAUDE.md
  - Definir triggers claros (lista de situações que ativam o skill)
  - Definir workflow estruturado (passos a seguir)
  - Opcionalmente criar /command como atalho
- **Exemplo**: domain-expert → seção "Quando Usar Domain-Expert Automaticamente" com 6 triggers
  ```markdown
  O Claude DEVE invocar domain-analyst quando:
  1. Termo desconhecido: não documentado no DOMAIN.md
  2. Regra implícita: validação/constraint revela regra
  3. Estados de negócio: enum/constante define estados
  ...
  ```
- **Anti-padrão**: skill definido mas sem instrução de quando usar (fica dormindo)
- **Descoberto em**: 2026-02-04 (commit bfc9ef1 - /domain)

### PAT-033: Single Responsibility para Scripts Shell
- **Contexto**: script shell acumula funcionalidades além do propósito original
- **Solução**: cada script faz uma coisa bem feita (Unix philosophy)
  - Script principal: operação unitária (ex: `setup.sh` instala UM projeto)
  - Script wrapper: orquestra múltiplas chamadas (ex: `batch-setup.sh` chama setup.sh N vezes)
  - Nunca misturar lógica de loop/batch com lógica de negócio
- **Anti-padrão**: feature creep em scripts core (adicionar batch, arrays, progress ao setup.sh)
- **Exemplo**: `setup.sh` revertido de 958 → 783 linhas; `batch-setup.sh` criado com 177 linhas
- **Descoberto em**: 2026-02-04 (commit bbcf725 - refactor setup)
