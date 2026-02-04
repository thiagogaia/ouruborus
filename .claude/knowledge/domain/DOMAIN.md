# Conhecimento de Domínio
> Última atualização: 2026-02-03 (/init-engram)

## Glossário

- **Engram**: Traço físico de memória armazenado no cérebro. No contexto deste projeto, representa o sistema de memória persistente para Claude Code.

- **Ouroboros**: Símbolo da serpente que morde a própria cauda. Representa o ciclo de retroalimentação do sistema — cada sessão consome conhecimento da anterior e produz conhecimento para a próxima.

- **Metacircular**: Sistema que pode gerar a si mesmo. O Engram usa genesis para gerar skills, e genesis pode gerar versões atualizadas de si mesmo.

- **Genesis**: Motor de auto-geração. Analisa projetos, gera scaffolds de componentes, valida contra schemas, registra no manifest.

- **Evolution**: Motor de evolução. Rastreia uso de componentes, detecta padrões, propõe melhorias, aposenta componentes obsoletos.

- **Skill**: Capacidade especializada do Claude. Diretório com SKILL.md + scripts opcionais. Carregado sob demanda (progressive disclosure).

- **Agent**: Especialista invocado via Task tool. Arquivo .md com instruções e tools permitidas. NÃO pode invocar outros agents.

- **Command**: Atalho para invocar skill ou sequência de ações. Arquivo .md em .claude/commands/. Usuário digita /nome.

- **Seed**: Skill universal que vem com toda instalação. Não depende de stack específica.

- **Schema**: Definição formal da estrutura de um componente. Usado por genesis e validate.py para garantir componentes corretos.

- **Manifest**: Registro central de todos os componentes (.claude/manifest.json). Rastreia versão, uso, saúde.

- **Knowledge File**: Arquivo markdown em .claude/knowledge/ que persiste entre sessões. Seis tipos: context, priorities, patterns, decisions, domain, experiences.

- **ICE Score**: Método de priorização. ICE = (Impacto × Confiança) / Esforço. Cada fator de 1-10.

- **ADR**: Architecture Decision Record. Registro formal de decisão arquitetural com contexto, opções e consequências.

- **Runtime Component**: Componente criado durante uma sessão de trabalho (source=runtime). Avaliado no próximo /learn.

- **Progressive Disclosure**: Técnica de UX onde informação é revelada gradualmente. Skills são carregados só quando necessários.

- **Feedback Loop**: Ciclo de retroalimentação. No Engram: trabalhar → registrar aprendizado → consultar na próxima vez.

- **Brain (Cérebro Organizacional)**: Sistema de memória com grafo de conhecimento em `.claude/brain/`. Usa NetworkX para nós e arestas, embeddings para busca semântica.

- **Spreading Activation**: Técnica de busca em grafos. A partir de nós semente, propaga ativação pelos vizinhos com decay. Encontra conhecimento relacionado indiretamente.

- **Curva de Ebbinghaus**: Modelo de esquecimento. strength = e^(-decay_rate × dias). Memórias menos acessadas enfraquecem gradualmente.

- **Embeddings**: Representação vetorial de texto para busca semântica. Usa sentence-transformers (local) ou OpenAI API.

- **Consolidação**: Processo cognitivo semanal. Fortalece conexões entre nós co-acessados, detecta padrões emergentes.

- **Decay (Esquecimento)**: Processo cognitivo diário. Aplica curva de Ebbinghaus, marca memórias fracas para possível arquivo.

- **Memory Labels**: Tipos de memória no grafo: Episode (episódica), Concept (semântica), Pattern (procedural), Decision (ADR), Person, Domain.

## Regras de Negócio

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

## Entidades Principais

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

## Restrições

### Técnicas
- Scripts devem rodar com Python 3.8+ (sem dependências externas)
- setup.sh deve funcionar em macOS e Linux (bash 4+)
- Cada skill deve carregar em < 1 segundo
- SKILL.md não deve exceder 500 linhas

### De Design
- Simplicidade > completude (não over-engineer)
- Componentes devem ser auto-documentados
- Prefira composição a herança (composes field)
- Evite abstrações prematuras
