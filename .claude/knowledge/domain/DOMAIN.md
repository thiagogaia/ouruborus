# Conhecimento de Domínio
> Última atualização: 2026-02-04 (/domain analyze)

## Glossário

- **ADR**: Architecture Decision Record. Registro formal de decisão arquitetural com contexto, opções e consequências.

- **Agent**: Especialista invocado via Task tool. Arquivo .md com instruções e tools permitidas. NÃO pode invocar outros agents.

- **Automatic Curriculum**: Conceito do Voyager - sistema que propõe tarefas baseado no nível atual. Roadmap futuro para Engram.

- **Batch Mode**: Modo de instalação sem prompts interativos (--batch ou -y). Confirma backups automaticamente.

- **BOSS (Bootstrap Your Own Skills)**: Pesquisa USC/Google de bootstrapping bottom-up de skills. Skills emergem de prática, não de design top-down. Inspiração para pattern detection do /learn.

- **Brain (Cérebro Organizacional)**: Sistema de memória com grafo de conhecimento em `.claude/brain/`. Usa NetworkX para nós e arestas, embeddings para busca semântica.

- **Cognitive Job**: Processo periódico de manutenção do cérebro. Três tipos: consolidate (semanal), decay (diário), archive (sob demanda).

- **Command**: Atalho para invocar skill ou sequência de ações. Arquivo .md em .claude/commands/. Usuário digita /nome.

- **Consolidação**: Processo cognitivo semanal. Fortalece conexões entre nós co-acessados, detecta padrões emergentes.

- **Content Type**: Classificação do tipo de conteúdo baseado nos labels. Valores: "episodes", "concepts", "patterns", "decisions", "people", "domains".

- **Curva de Ebbinghaus**: Modelo de esquecimento. strength = e^(-decay_rate × dias). Memórias menos acessadas enfraquecem gradualmente.

- **Darwin Gödel Machine (DGM)**: Agente Sakana AI que reescreve seu próprio código-fonte. Mantém arquivo evolutivo. Inspiração para capacidade metacircular do Engram.

- **Decay (Esquecimento)**: Processo cognitivo diário. Aplica curva de Ebbinghaus, marca memórias fracas para possível arquivo.

- **Domain Keywords**: Dicionário de palavras-chave para inferir domínio automático. Domínios: auth, payments, database, api, frontend, infra, testing.

- **Embeddings**: Representação vetorial de texto para busca semântica. Usa sentence-transformers (local) ou OpenAI API.

- **Engram**: Traço físico de memória armazenado no cérebro. No contexto deste projeto, representa o sistema de memória persistente para Claude Code.

- **Evolution**: Motor de evolução. Rastreia uso de componentes, detecta padrões, propõe melhorias, aposenta componentes obsoletos.

- **Experience Replay**: Técnica de ML - reusar experiências passadas como exemplos. No Engram: EXPERIENCE_LIBRARY.md.

- **FallbackGraph**: Implementação simplificada de grafo quando NetworkX não está disponível. Fornece operações básicas (add_node, add_edge, successors, predecessors) sem dependências externas.

- **Feedback Loop**: Ciclo de retroalimentação. No Engram: trabalhar → registrar aprendizado → consultar na próxima vez.

- **Frontmatter**: Metadados YAML no início de arquivos Markdown (entre ---). Contém name, description, tools, etc.

- **Genesis**: Motor de auto-geração. Analisa projetos, gera scaffolds de componentes, valida contra schemas, registra no manifest.

- **Health Score**: Métrica de saúde do cérebro: 1.0 - (weak_count / total_nodes). Status: healthy (>=0.8), needs_attention (>=0.5), critical (<0.5).

- **Health Status**: Estado de saúde de componente baseado em uso. Ícones: verde (ativo), amarelo (stale), caixa (archived), branco (nunca usado).

- **ICE Score**: Método de priorização. ICE = (Impacto × Confiança) / Esforço. Cada fator de 1-10.

- **Knowledge File**: Arquivo markdown em .claude/knowledge/ que persiste entre sessões. Seis tipos: context, priorities, patterns, decisions, domain, experiences.

- **Manifest**: Registro central de todos os componentes (.claude/manifest.json). Rastreia versão, uso, saúde.

- **Memory Labels**: Tipos de memória no grafo: Episode (episódica), Concept (semântica), Pattern (procedural), Decision (ADR), Person, Domain.

- **Memory State**: Estado de uma memória no grafo, contendo: strength (força), access_count (vezes acessada), last_accessed (último acesso), created_at (criação), decay_rate (taxa de esquecimento).

- **Metacircular**: Sistema que pode gerar a si mesmo. O Engram usa genesis para gerar skills, e genesis pode gerar versões atualizadas de si mesmo.

- **Monorepo**: Projeto com múltiplos pacotes/workspaces em um repositório. Detectado via pnpm-workspace.yaml ou lerna.json.

- **Ouroboros**: Símbolo da serpente que morde a própria cauda. Representa o ciclo de retroalimentação do sistema — cada sessão consome conhecimento da anterior e produz conhecimento para a próxima.

- **Progressive Disclosure**: Técnica de UX onde informação é revelada gradualmente. Skills são carregados só quando necessários.

- **Protected Labels**: Labels de nós que não são arquivados mesmo com baixa strength: Person, Domain, Decision.

- **Reinforce**: Processo de fortalecimento de memória acessada. Incrementa access_count, atualiza last_accessed, aumenta strength em 5% (capped em 1.0).

- **Runtime Component**: Componente criado durante uma sessão de trabalho (source=runtime). Avaliado no próximo /learn.

- **Scaffold**: Estrutura inicial gerada para um componente. Contém placeholders [TODO:] para customização.

- **Schema**: Definição formal da estrutura de um componente. Usado por genesis e validate.py para garantir componentes corretos.

- **Seed**: Skill universal que vem com toda instalação. Não depende de stack específica.

- **Self-Verification**: Conceito do Voyager - só commita skill se verificou sucesso. No Engram: validate.py obrigatório antes de register.py.

- **Skill**: Capacidade especializada do Claude. Diretório com SKILL.md + scripts opcionais. Carregado sob demanda (progressive disclosure).

- **Skill Library**: Conceito do Voyager - coleção de skills indexados por embedding semântico. No Engram: `.claude/skills/` + manifest.json.

- **Spreading Activation**: Técnica de busca em grafos. A partir de nós semente, propaga ativação pelos vizinhos com decay. Encontra conhecimento relacionado indiretamente.

- **Stack Detection**: Processo de detecção automática da stack do projeto via package.json, requirements.txt, Cargo.toml, etc.

- **Stale Threshold**: Número de dias sem uso após o qual um componente é considerado stale. Default: 14 dias.

- **Template Stack**: Arquivo `.skill.tmpl` em `templates/skills/` que serve como ponto de partida para geração de skill customizado por framework.

- **Voyager**: Projeto NVIDIA/MineDojo de agente que joga Minecraft e constrói sua própria biblioteca de skills. Inspiração para skill library composicional do Engram.

- **WeakMemory**: Label adicionado a nós com strength < 0.3. Indica memória candidata a consolidação ou arquivo.

## Regras de Negócio

### Componentes (RN-001 a RN-010)

- **RN-001**: Todo componente DEVE seguir seu schema correspondente
- **RN-002**: Skills DEVEM ter description com 50-500 caracteres incluindo trigger explícito
- **RN-003**: Agents NÃO PODEM invocar outros agents (evita loops)
- **RN-004**: Componentes runtime são avaliados no próximo /learn
- **RN-005**: Máximo 2 componentes runtime por sessão (evita explosão)
- **RN-006**: Componentes nunca usados após 14 dias são candidatos a archive
- **RN-007**: Knowledge files devem ser atualizados após cada tarefa significativa
- **RN-008**: Decisões arquiteturais DEVEM ser registradas em ADR_LOG.md
- **RN-009**: Padrões repetidos DEVEM virar skills (DRY para prompts)
- **RN-010**: Backups de componentes vão para .claude/versions/

### Validação (RN-011 a RN-019)

- **RN-011**: Nome de skill DEVE corresponder ao nome do diretório
  - Fonte: `validate.py:98-99`
- **RN-012**: Scripts dentro de skill DEVEM ter linha shebang (#!)
  - Fonte: `validate.py:123-124`
- **RN-013**: Scripts DEVEM ter permissão de execução (chmod +x)
  - Fonte: `validate.py:125-126`
- **RN-014**: Arquivos proibidos em skill: README.md, CHANGELOG.md, INSTALLATION.md, INSTALL.md, QUICK_REFERENCE.md
  - Fonte: `validate.py:135-138`
- **RN-015**: Body de agent DEVE conter seção "Regras" ou "Rules"
  - Fonte: `validate.py:184-185`
- **RN-016**: Body de agent NÃO DEVE exceder 300 linhas
  - Fonte: `validate.py:188-189`
- **RN-017**: Commands NÃO DEVEM ter frontmatter YAML
  - Fonte: `validate.py:206-207`
- **RN-018**: Commands DEVEM ter conteúdo mínimo de 20 caracteres
  - Fonte: `validate.py:210-211`
- **RN-019**: Commands NÃO DEVEM exceder 200 linhas
  - Fonte: `validate.py:214-215`

### Brain/Memória (RN-020 a RN-027)

- **RN-020**: Taxa de decay varia por tipo de memória: Decision=0.001, Pattern=0.005, Concept=0.003, Episode=0.01, Person=0.0001
  - Fonte: `brain.py:433-446`
- **RN-021**: ID de pessoa DEVE seguir formato "person-{username}"
  - Fonte: `brain.py:454`
- **RN-022**: ID de domínio DEVE seguir formato "domain-{nome_lowercase}"
  - Fonte: `brain.py:487`
- **RN-023**: Threshold para memória fraca (WeakMemory): strength < 0.3
  - Fonte: `brain.py:868`
- **RN-024**: Threshold para arquivo (archive): strength < 0.1
  - Fonte: `brain.py:864`
- **RN-025**: Spreading activation usa decay de 0.5 por nível (default)
  - Fonte: `brain.py:605`
- **RN-026**: Nós in-edges recebem 50% da ativação de out-edges
  - Fonte: `brain.py:655`
- **RN-027**: Top 10 resultados de retrieve() são reforçados automaticamente
  - Fonte: `brain.py:732`

### Manifest/Lifecycle (RN-028 a RN-030)

- **RN-028**: Sources válidos para componentes: genesis, seed, manual, evolution, runtime, core
  - Fonte: `register.py:156`
- **RN-029**: Componentes novos iniciam com activations=0, last_used=null, health=active
  - Fonte: `register.py:81-89`
- **RN-030**: Unregister marca health=archived (não remove fisicamente)
  - Fonte: `register.py:101`

### Doctor/Health (RN-031 a RN-034)

- **RN-031**: Knowledge files com idade > 14 dias geram warning
  - Fonte: `doctor.py:140-144`
- **RN-032**: Knowledge files com tamanho < 50 bytes são considerados vazios
  - Fonte: `doctor.py:132-134`
- **RN-033**: Core skills obrigatórios: engram-genesis, engram-evolution
  - Fonte: `doctor.py:96-103`
- **RN-034**: Health score: >=90%=verde, >=70%=amarelo, <70%=vermelho
  - Fonte: `doctor.py:341-345`

## Entidades Principais

### Manifest e Componentes

```
Manifest
    └── registra → Components (skills, agents, commands)
                       │
                       ├── Skills
                       │   ├── têm → SKILL.md (obrigatório)
                       │   ├── têm → scripts/ (opcional)
                       │   ├── têm → references/ (opcional)
                       │   └── seguem → skill.schema.md
                       │
                       ├── Agents
                       │   ├── são → arquivo .md único
                       │   ├── declaram → tools permitidas
                       │   └── seguem → agent.schema.md
                       │
                       └── Commands
                           ├── são → arquivo .md único
                           └── seguem → command.schema.md

Knowledge Files
    ├── CURRENT_STATE.md → estado vivo
    ├── PRIORITY_MATRIX.md → tarefas priorizadas
    ├── PATTERNS.md → padrões aprovados
    ├── ADR_LOG.md → decisões arquiteturais
    ├── DOMAIN.md → glossário (este arquivo)
    └── EXPERIENCE_LIBRARY.md → soluções reutilizáveis
```

### Brain (Cérebro Organizacional)

```
Brain (Cérebro)
    └── contém → Nodes (Nós)
                   │
                   ├── Episode → memória episódica (commits, eventos)
                   ├── Concept → memória semântica (glossário, definições)
                   ├── Pattern → memória procedural (padrões de código)
                   ├── Decision → ADRs
                   ├── Person → autores (mapeados de git config)
                   └── Domain → domínios técnicos (auth, api, database, etc)

    └── contém → Edges (Arestas)
                   │
                   ├── AUTHORED_BY → Node → Person
                   ├── REFERENCES → Node → Node
                   └── BELONGS_TO → Node → Domain

    └── executa → Cognitive Processes
                   │
                   ├── Consolidate (semanal)
                   ├── Decay (diário)
                   └── Archive (sob demanda)
```

### Ciclo de Vida de Componente

```
Componente (Skill | Agent | Command)
    │
    ├── state: nascimento
    │     └── source: genesis | seed | runtime | core | manual
    │
    ├── state: ativo
    │     └── metrics: activations, last_used
    │
    ├── state: stale
    │     └── trigger: 14 dias sem uso
    │
    └── state: archived
          └── trigger: manual ou health=archived
```

### Processo de Instalação

```
Instalação (setup.sh)
    │
    ├── detect_stack → identifica framework/ORM/DB/etc
    │
    ├── install_core → schemas + genesis + evolution + seeds + commands
    │
    ├── install_brain_deps → cria venv + pip install networkx numpy sentence-transformers
    │
    ├── generate_claude_md → CLAUDE.md customizado pela stack
    │
    └── initialize_knowledge → templates para 6 knowledge files
```

## Restrições

### Técnicas
- Scripts devem rodar com Python 3.8+ (sem dependências externas no core)
- setup.sh deve funcionar em macOS e Linux (bash 4+)
- Cada skill deve carregar em < 1 segundo
- SKILL.md não deve exceder 500 linhas
- Agent body não deve exceder 300 linhas
- Command não deve exceder 200 linhas

### De Design
- Simplicidade > completude (não over-engineer)
- Componentes devem ser auto-documentados
- Prefira composição a herança (composes field)
- Evite abstrações prematuras

### Valores Hardcoded (candidatos a config)
| Valor | Onde | Descrição |
|-------|------|-----------|
| 14 dias | track_usage.py, doctor.py | Threshold para stale |
| 0.1 | cognitive.py | Threshold para archive |
| 0.3 | brain.py | Threshold para WeakMemory |
| 500 linhas | validate.py | Max body de skill |
| 300 linhas | validate.py | Max body de agent |
| 200 linhas | validate.py | Max body de command |
