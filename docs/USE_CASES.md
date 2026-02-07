# Engram v4 (Ouroboros) — Casos de Uso

> Documento gerado em 2026-02-07. Descreve os casos de uso completos do sistema.

---

## Sumario

- [Atores](#atores)
- [Diagrama de Contexto](#diagrama-de-contexto)
- [Mapa de Casos de Uso](#mapa-de-casos-de-uso)
- **Instalacao & Setup**
  - [UC-01: Instalar Engram em um Projeto](#uc-01-instalar-engram-em-um-projeto)
  - [UC-02: Instalar Engram em Multiplos Projetos](#uc-02-instalar-engram-em-multiplos-projetos)
  - [UC-03: Inicializar o Sistema com Genesis](#uc-03-inicializar-o-sistema-com-genesis)
- **Workflow Diario**
  - [UC-04: Iniciar Sessao de Trabalho](#uc-04-iniciar-sessao-de-trabalho)
  - [UC-05: Consultar o Cerebro Organizacional](#uc-05-consultar-o-cerebro-organizacional)
  - [UC-06: Implementar uma Feature](#uc-06-implementar-uma-feature)
  - [UC-07: Fazer Code Review](#uc-07-fazer-code-review)
  - [UC-08: Criar Commit Semantico](#uc-08-criar-commit-semantico)
  - [UC-09: Registrar Aprendizado da Sessao](#uc-09-registrar-aprendizado-da-sessao)
- **Gestao de Conhecimento**
  - [UC-10: Descobrir e Registrar Conhecimento de Dominio](#uc-10-descobrir-e-registrar-conhecimento-de-dominio)
  - [UC-11: Registrar Decisao Arquitetural](#uc-11-registrar-decisao-arquitetural)
  - [UC-12: Planejar Implementacao de Feature](#uc-12-planejar-implementacao-de-feature)
- **Auto-Evolucao**
  - [UC-13: Criar Componente sob Demanda](#uc-13-criar-componente-sob-demanda)
  - [UC-14: Orquestrar Componente em Runtime](#uc-14-orquestrar-componente-em-runtime)
  - [UC-15: Diagnosticar Saude do Sistema](#uc-15-diagnosticar-saude-do-sistema)
  - [UC-16: Evoluir o Sistema via Aprendizado](#uc-16-evoluir-o-sistema-via-aprendizado)
- **Priorizacao**
  - [UC-17: Gerenciar Prioridades com ICE Score](#uc-17-gerenciar-prioridades-com-ice-score)
- **Multi-Projeto & Compartilhamento**
  - [UC-18: Exportar Skill para Memoria Global](#uc-18-exportar-skill-para-memoria-global)
  - [UC-19: Importar Skill da Memoria Global](#uc-19-importar-skill-da-memoria-global)
- **Manutencao**
  - [UC-20: Executar Manutencao Cognitiva do Cerebro](#uc-20-executar-manutencao-cognitiva-do-cerebro)
  - [UC-21: Fazer Onboarding de Novo Desenvolvedor](#uc-21-fazer-onboarding-de-novo-desenvolvedor)

---

## Atores

| Ator | Descricao | Exemplos de Interacao |
|------|-----------|----------------------|
| **Desenvolvedor Solo** | Desenvolvedor individual usando Claude Code + Engram no dia a dia. Ator principal. | Codifica, consulta cerebro, registra aprendizado, faz commits |
| **Tech Lead / Arquiteto** | Responsavel por decisoes arquiteturais. Quer preservar e recuperar decisoes e padroes. | Registra ADRs, define padroes, revisa codigo, consulta historico de decisoes |
| **Dev Novo** | Desenvolvedor recem-chegado ao projeto. Precisa entender decisoes, padroes e dominio existentes. | Consulta cerebro, navega conexoes semanticas, aprende regras de negocio |
| **CI/CD / Automacao** | Sistemas automatizados (pipelines, cron, hooks) que interagem com o Engram. | Batch install, manutencao cognitiva agendada, health checks automaticos |

---

## Diagrama de Contexto

```
                        ┌─────────────────────────────────┐
                        │         Engram v4 (Ouroboros)    │
                        │                                 │
  Desenvolvedor Solo ──→│  Cerebro Organizacional         │
                        │    ├── Grafo de Conhecimento    │
  Tech Lead ──────────→│    ├── Busca Semantica          │
                        │    ├── Processos Cognitivos     │
  Dev Novo ───────────→│    └── Memoria Persistente      │
                        │                                 │
  CI/CD ──────────────→│  Motor Metacircular             │
                        │    ├── Genesis (auto-geracao)   │
                        │    ├── Evolution (auto-evolucao)│
                        │    └── Factory (orquestracao)   │
                        │                                 │
                        │  Componentes                    │
                        │    ├── Skills (capacidades)     │
                        │    ├── Agents (especialistas)   │
                        │    └── Commands (interface)     │
                        └─────────────────────────────────┘
                                       │
                                       ▼
                              Repositorio Git
                              (toda memoria versionada)
```

---

## Mapa de Casos de Uso

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ENGRAM v3                                    │
│                                                                      │
│  ┌─ Instalacao ──────────────────────────────────────────────────┐   │
│  │  UC-01: Instalar em projeto                                   │   │
│  │  UC-02: Instalar em multiplos projetos                        │   │
│  │  UC-03: Inicializar com genesis                               │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─ Workflow Diario ─────────────────────────────────────────────┐   │
│  │  UC-04: Iniciar sessao ──→ UC-05: Consultar cerebro          │   │
│  │  UC-06: Implementar feature ──→ UC-07: Code review           │   │
│  │  UC-08: Commit semantico ──→ UC-09: Registrar aprendizado    │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─ Gestao de Conhecimento ──────────────────────────────────────┐   │
│  │  UC-10: Conhecimento de dominio                               │   │
│  │  UC-11: Decisao arquitetural (ADR)                            │   │
│  │  UC-12: Planejar feature                                      │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─ Auto-Evolucao ──────────────────────────────────────────────┐   │
│  │  UC-13: Criar componente       UC-14: Orquestrar runtime     │   │
│  │  UC-15: Diagnosticar saude     UC-16: Evoluir via /learn     │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─ Priorizacao / Multi-Projeto / Manutencao ────────────────────┐   │
│  │  UC-17: ICE Score   UC-18/19: Export/Import   UC-20: Cognitiva│   │
│  │  UC-21: Onboarding                                            │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Instalacao & Setup

### UC-01: Instalar Engram em um Projeto

| Campo | Valor |
|-------|-------|
| **ID** | UC-01 |
| **Nome** | Instalar Engram em um Projeto |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | — |
| **Descricao** | O desenvolvedor instala o Engram em um projeto existente, preparando a estrutura de diretorios, DNA, seeds, cerebro e dependencias Python. |

**Pre-condicoes:**
1. O projeto-alvo e um repositorio git valido
2. O repositorio Engram foi clonado localmente
3. Python 3.10+ esta instalado no sistema

**Fluxo Principal:**
1. O desenvolvedor navega ate o diretorio do Engram clonado
2. O desenvolvedor executa `./setup.sh /caminho/do/projeto`
3. O sistema detecta a stack do projeto (linguagem, framework, ORM, banco, UI, auth, testes)
4. O sistema exibe o plano de instalacao e pede confirmacao
5. O desenvolvedor confirma
6. O sistema cria a estrutura `.claude/` com DNA, seeds, agents, commands e knowledge templates
7. O sistema cria o ambiente virtual Python (`.claude/brain/.venv/`)
8. O sistema instala dependencias (sentence-transformers, chromadb, networkx, etc.)
9. O sistema inicializa o banco SQLite do cerebro (`brain.db`)
10. O sistema gera/atualiza o `CLAUDE.md` com instrucoes do projeto
11. O sistema exibe resumo da instalacao com proximos passos

**Fluxos Alternativos:**

- **FA-01: Instalacao ja existente**
  - No passo 4, o sistema detecta `.claude/` existente
  - O sistema faz backup em `.claude.bak/`
  - O sistema pergunta se deseja sobrescrever ou atualizar (--update)
  - O desenvolvedor escolhe; fluxo continua no passo 6

- **FA-02: Stack nao reconhecida**
  - No passo 3, o sistema nao identifica framework especifico
  - O sistema instala apenas os seeds universais (sem templates de stack)
  - O `/init-engram` gerara skills customizados via analise com IA

- **FA-03: Dependencias Python falham**
  - No passo 8, pip falha ao instalar alguma dependencia
  - O sistema exibe erro e sugere instalar manualmente
  - A instalacao conclui parcialmente (cerebro nao funcional ate resolver)

**Pos-condicoes:**
1. Diretorio `.claude/` criado com toda a estrutura
2. Cerebro inicializado (banco vazio, pronto para popular)
3. 6 seed skills, 3 agents, 15 commands instalados
4. `CLAUDE.md` atualizado com instrucoes especificas do projeto
5. Manifest (`manifest.json`) criado com registro de componentes

---

### UC-02: Instalar Engram em Multiplos Projetos

| Campo | Valor |
|-------|-------|
| **ID** | UC-02 |
| **Nome** | Instalar Engram em Multiplos Projetos |
| **Ator Principal** | CI/CD / Automacao |
| **Atores Secundarios** | Desenvolvedor Solo |
| **Descricao** | O sistema ou desenvolvedor instala o Engram em varios projetos simultaneamente, usando o script batch. |

**Pre-condicoes:**
1. Todos os projetos-alvo sao repositorios git validos
2. O repositorio Engram foi clonado localmente
3. Python 3.10+ esta instalado

**Fluxo Principal:**
1. O ator executa `./batch-setup.sh /proj1 /proj2 /proj3`
2. O sistema valida que todos os caminhos existem e sao diretorios git
3. Para cada projeto, o sistema executa o fluxo do UC-01 sequencialmente
4. O sistema exibe progresso: "Instalando em proj1... OK", "Instalando em proj2... OK"
5. Ao final, exibe resumo consolidado: projetos instalados, falhas, proximos passos

**Fluxos Alternativos:**

- **FA-01: Modo CI/CD (sem prompts)**
  - O ator executa com flag `-y`: `./batch-setup.sh -y /proj1 /proj2`
  - O sistema pula todas as confirmacoes interativas
  - Instalacoes existentes sao sobrescritas automaticamente (com backup)

- **FA-02: Um projeto falha**
  - No passo 3, a instalacao de um projeto falha
  - O sistema registra o erro e continua com os proximos projetos
  - No resumo final, lista projetos com falha e motivos

**Pos-condicoes:**
1. Todos os projetos validos tem `.claude/` instalado
2. Cada projeto tem cerebro independente
3. Resumo de batch disponivel no terminal

---

### UC-03: Inicializar o Sistema com Genesis

| Campo | Valor |
|-------|-------|
| **ID** | UC-03 |
| **Nome** | Inicializar o Sistema com Genesis |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | Apos a instalacao fisica (UC-01), o desenvolvedor roda `/init-engram` dentro do Claude Code para que a IA analise o projeto em profundidade e gere componentes customizados. |

**Pre-condicoes:**
1. UC-01 concluido (`.claude/` existe com seeds e cerebro vazio)
2. O desenvolvedor esta dentro do Claude Code no diretorio do projeto

**Fluxo Principal:**
1. O desenvolvedor executa `/init-engram`
2. **Fase 0 — Backup**: o sistema detecta instalacao anterior e faz backup se necessario
3. **Fase 1 — Analise**: Claude analisa o codebase (estrutura, dependencias, patterns existentes, commits)
4. **Fase 2 — Plano**: Claude apresenta o plano de geracao (skills, agents, knowledge) e pede aprovacao
5. O desenvolvedor aprova o plano
6. **Fase 3 — Genesis**: Claude gera skills customizados para a stack detectada (ex: nextjs-patterns, prisma-helper)
7. **Fase 4 — Knowledge**: Claude popula os knowledge files iniciais (CURRENT_STATE, PATTERNS, ADR_LOG, DOMAIN, PRIORITY_MATRIX, EXPERIENCE_LIBRARY)
8. **Fase 5 — Cerebro**: Claude popula o cerebro com commits, ADRs, patterns e regras de negocio via `brain.add_memory()`
9. **Fase 6 — Health Check**: Claude verifica saude do cerebro recem-populado
10. **Fase 7 — Cleanup**: Claude remove scaffolds temporarios e apresenta relatorio final

**Fluxos Alternativos:**

- **FA-01: Projeto novo (sem historico)**
  - Na Fase 1, Claude nao encontra commits ou patterns
  - O cerebro inicia com poucos nos (apenas seeds e conceitos basicos)
  - Claude sugere comecar a trabalhar e rodar `/learn` apos os primeiros commits

- **FA-02: Projeto grande (muitos commits)**
  - Na Fase 5, Claude limita a populacao aos 200 commits mais recentes
  - Commits mais antigos podem ser importados depois via `populate.py commits N`

- **FA-03: Dev rejeita o plano**
  - No passo 5, o desenvolvedor pede ajustes
  - Claude revisa o plano (adiciona/remove skills) e apresenta novamente
  - Fluxo retorna ao passo 5

**Pos-condicoes:**
1. Cerebro populado com ~100-200 nos e conexoes semanticas
2. Skills customizados gerados e registrados no manifest
3. Knowledge files preenchidos com estado inicial
4. Sistema pronto para o ciclo diario (UC-04 em diante)

---

## Workflow Diario

### UC-04: Iniciar Sessao de Trabalho

| Campo | Valor |
|-------|-------|
| **ID** | UC-04 |
| **Nome** | Iniciar Sessao de Trabalho |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O desenvolvedor abre uma nova sessao no Claude Code. O sistema consulta automaticamente o cerebro para recuperar contexto da sessao anterior e apresentar estado + prioridades. |

**Pre-condicoes:**
1. Engram inicializado (UC-03 concluido)
2. O desenvolvedor esta no Claude Code no diretorio do projeto

**Fluxo Principal:**
1. O desenvolvedor executa `/status`
2. Claude consulta o cerebro: `recall --recent 7d --type Commit --top 10`
3. Claude le o `PRIORITY_MATRIX.md` para prioridades atuais
4. Claude verifica saude do cerebro via `cognitive.py health`
5. Claude apresenta:
   - Fase do projeto e health score do cerebro
   - Ultimos commits relevantes
   - Top 3-5 prioridades com ICE Score
   - Bloqueios identificados
   - Sugestao concreta de proxima acao

**Fluxos Alternativos:**

- **FA-01: Primeira sessao apos /init-engram**
  - No passo 2, o cerebro tem poucos nos
  - Claude apresenta estado inicial e sugere a primeira tarefa do PRIORITY_MATRIX

- **FA-02: Cerebro com saude critica**
  - No passo 4, health < 0.7
  - Claude alerta e sugere rodar `/doctor` antes de trabalhar
  - Inclui UC-15 como sub-fluxo

- **FA-03: Sem prioridades definidas**
  - No passo 3, PRIORITY_MATRIX esta vazio
  - Claude sugere rodar `/priorities` para definir prioridades iniciais
  - Inclui UC-17 como sub-fluxo

**Pos-condicoes:**
1. Desenvolvedor tem visao clara do estado do projeto
2. Proxima acao identificada
3. Contexto da sessao anterior recuperado pelo cerebro

---

### UC-05: Consultar o Cerebro Organizacional

| Campo | Valor |
|-------|-------|
| **ID** | UC-05 |
| **Nome** | Consultar o Cerebro Organizacional |
| **Ator Principal** | Desenvolvedor Solo, Dev Novo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | Qualquer ator consulta o cerebro para recuperar conhecimento: decisoes, padroes, regras de negocio, bugs anteriores, ou qualquer informacao registrada. |

**Pre-condicoes:**
1. Cerebro populado com nos (UC-03 ou UC-09 executados)

**Fluxo Principal:**
1. O ator executa `/recall [pergunta]` (ex: `/recall como funciona a autenticacao`)
2. O sistema gera embedding da pergunta
3. O sistema busca por similaridade semantica no grafo
4. O sistema aplica spreading activation — expande para nos conectados (3 niveis)
5. O sistema retorna resultados rankeados com:
   - Score de relevancia (0 a 1)
   - Tipo do no (ADR, Pattern, Concept, Episode)
   - Conteudo completo (campo `content`)
   - Conexoes semanticas (RELATED_TO, SAME_SCOPE, etc.)
6. O sistema reforca os nos acessados (+5% forca) — auto-alimentacao
7. O ator usa a informacao para tomar decisoes ou entender contexto

**Fluxos Alternativos:**

- **FA-01: Busca temporal**
  - O ator quer ver mudancas recentes: `/recall --recent 7d --type Commit`
  - O sistema filtra por data e tipo em vez de busca semantica
  - Util para "o que mudou desde a ultima sessao?"

- **FA-02: Busca filtrada por tipo**
  - O ator quer apenas ADRs: `/recall autenticacao --type ADR --top 5`
  - O sistema restringe busca ao tipo solicitado

- **FA-03: Nenhum resultado relevante**
  - No passo 3, o sistema nao encontra nos com score > 0.3
  - O sistema informa que nao ha conhecimento registrado sobre o tema
  - Sugere que o ator registre apos trabalhar no tema (UC-09)

- **FA-04: Consulta automatica pelo Claude**
  - O ator faz uma pergunta natural: "como funciona X?" ou "por que Y?"
  - Claude detecta que e uma pergunta de conhecimento e roda recall automaticamente
  - O ator nao precisa usar `/recall` explicitamente

**Pos-condicoes:**
1. Ator tem informacao relevante para tomar decisao ou entender contexto
2. Nos acessados foram reforcados no cerebro (mais fortes para futuras buscas)
3. Conexoes semanticas expostas podem revelar relacoes nao-obvias

---

### UC-06: Implementar uma Feature

| Campo | Valor |
|-------|-------|
| **ID** | UC-06 |
| **Nome** | Implementar uma Feature |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA), Tech Lead (opcional) |
| **Descricao** | O desenvolvedor implementa uma feature, usando o Engram para consultar conhecimento, seguir patterns e tomar decisoes informadas. |

**Pre-condicoes:**
1. Sessao iniciada (UC-04)
2. Feature identificada (possivelmente via PRIORITY_MATRIX)

**Fluxo Principal:**
1. O desenvolvedor descreve a feature para o Claude
2. Claude executa `/recall` automaticamente para buscar padroes, ADRs e experiencias relacionadas
3. Claude verifica se existe skill especifico para a stack/tarefa
4. Claude apresenta abordagem baseada em:
   - Patterns aprovados encontrados no cerebro
   - ADRs que restringem ou orientam a decisao
   - Experiencias anteriores similares (bugs, solucoes)
5. O desenvolvedor aprova a abordagem
6. Claude implementa seguindo os patterns do projeto
7. Durante a implementacao, se encontrar termo de dominio nao documentado, aciona UC-10
8. Se uma decisao arquitetural nova for necessaria, aciona UC-11
9. A implementacao e concluida

**Fluxos Alternativos:**

- **FA-01: Feature complexa — planejar antes**
  - No passo 2, Claude identifica que a feature e complexa
  - Claude sugere `/plan [feature]` primeiro (UC-12)
  - Apos plano aprovado, retorna ao passo 6

- **FA-02: Expertise nao coberta**
  - No passo 3, nenhum skill ou agent cobre a necessidade
  - Claude aciona UC-14 (orquestracao runtime) para criar componente sob demanda
  - Retorna ao passo 6 com o novo componente disponivel

- **FA-03: Conflito com ADR existente**
  - No passo 4, a abordagem ideal conflita com uma ADR registrada
  - Claude alerta e propoe: (a) seguir ADR, (b) revisar/atualizar ADR, (c) registrar excecao
  - O desenvolvedor decide; fluxo continua

**Pos-condicoes:**
1. Feature implementada seguindo patterns do projeto
2. Decisoes documentadas (se houver ADR nova)
3. Conhecimento de dominio descoberto e registrado
4. Codigo pronto para review (UC-07)

---

### UC-07: Fazer Code Review

| Campo | Valor |
|-------|-------|
| **ID** | UC-07 |
| **Nome** | Fazer Code Review |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O ator solicita review de codigo. Claude executa um pipeline de 4 camadas baseado no cerebro do projeto (patterns, ADRs, regras). |

**Pre-condicoes:**
1. Existem alteracoes no working tree ou staged (arquivos modificados)
2. Skill `code-reviewer` disponivel

**Fluxo Principal:**
1. O ator executa `/review`
2. Claude identifica os arquivos alterados (`git diff`)
3. Claude consulta o cerebro para buscar patterns e ADRs aplicaveis aos arquivos
4. Claude executa o pipeline de 4 camadas:
   - **Camada 1 — Correcao**: bugs logicos, off-by-one, null refs, race conditions
   - **Camada 2 — Padroes**: aderencia a patterns aprovados, naming, estrutura
   - **Camada 3 — Seguranca**: injection, XSS, exposicao de dados, OWASP Top 10
   - **Camada 4 — Performance**: queries N+1, loops desnecessarios, alocacoes
5. Claude emite veredito: APROVADO, SUGESTOES (nao-bloqueante), ou REQUER MUDANCAS
6. Se REQUER MUDANCAS, Claude lista os itens com localizacao e sugestao de correcao
7. O ator corrige ou aceita as sugestoes

**Fluxos Alternativos:**

- **FA-01: Nenhum arquivo alterado**
  - No passo 2, `git diff` esta vazio
  - Claude informa que nao ha alteracoes para revisar

- **FA-02: Pattern desconhecido**
  - Na Camada 2, Claude encontra pattern nao registrado no cerebro
  - Claude sugere registrar como novo pattern (UC-09 na proxima /learn)

- **FA-03: Vulnerabilidade critica**
  - Na Camada 3, Claude detecta vulnerabilidade critica (injection, leak de credenciais)
  - Claude emite REQUER MUDANCAS com prioridade maxima e instrucoes de correcao
  - O commit e bloqueado ate a correcao

**Pos-condicoes:**
1. Codigo revisado nas 4 dimensoes
2. Veredito registrado
3. Se APROVADO, pronto para commit (UC-08)
4. Feedback do review alimenta o cerebro na proxima /learn

---

### UC-08: Criar Commit Semantico

| Campo | Valor |
|-------|-------|
| **ID** | UC-08 |
| **Nome** | Criar Commit Semantico |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O desenvolvedor usa `/commit` para que Claude gere automaticamente uma mensagem de commit semantica baseada no diff. |

**Pre-condicoes:**
1. Existem alteracoes staged ou unstaged para commitar
2. Preferencialmente, review executado (UC-07)

**Fluxo Principal:**
1. O desenvolvedor executa `/commit`
2. Claude analisa o diff completo (staged + unstaged)
3. Claude gera mensagem no padrao Conventional Commits:
   ```
   tipo(escopo): descricao curta em ingles

   corpo opcional explicando o "porque"
   ```
4. Claude apresenta a mensagem para aprovacao
5. O desenvolvedor aprova (ou ajusta)
6. Claude executa o `git commit`
7. Claude sugere: "Quer rodar /learn para registrar o aprendizado?"

**Fluxos Alternativos:**

- **FA-01: Dev ajusta a mensagem**
  - No passo 5, o desenvolvedor pede alteracoes
  - Claude regenera ou edita conforme solicitado
  - Retorna ao passo 4

- **FA-02: Multiplas preocupacoes no diff**
  - No passo 2, o diff mistura features, fixes e refactoring
  - Claude sugere dividir em commits atomicos
  - O desenvolvedor escolhe: commit unico ou dividido

- **FA-03: Pre-commit hook falha**
  - No passo 6, um hook de pre-commit rejeita
  - Claude analisa o erro, sugere correcao, e tenta novamente
  - Cria um NOVO commit (nunca amend)

**Pos-condicoes:**
1. Commit criado com mensagem semantica padronizada
2. Historico git limpo e legivel
3. Commit sera processado pelo cerebro na proxima /learn

---

### UC-09: Registrar Aprendizado da Sessao

| Campo | Valor |
|-------|-------|
| **ID** | UC-09 |
| **Nome** | Registrar Aprendizado da Sessao |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O desenvolvedor executa `/learn` ao final da sessao. Claude reflete sobre o trabalho feito, registra tudo no cerebro, roda processos cognitivos e propoe evolucoes. Este e o coracao do Ouroboros. |

**Pre-condicoes:**
1. Trabalho foi realizado na sessao (commits, decisoes, descobertas)

**Fluxo Principal:**
1. O desenvolvedor executa `/learn`
2. **Fase 1 — Coleta**: Claude analisa `git diff` e `git log` para identificar o que mudou
3. **Fase 2 — Introspeccao**: Claude reflete sobre:
   - Patterns usados ou criados
   - Decisoes arquiteturais tomadas
   - Problemas resolvidos e como
   - Conhecimento de dominio descoberto
4. **Fase 3 — Encode no Cerebro**: para cada item, Claude chama `brain.add_memory()`:
   - ADRs → labels `[ADR, Decision]`
   - Patterns → labels `[Pattern, ApprovedPattern]`
   - Experiencias → labels `[Episode, Experience]`
   - Conceitos → labels `[Concept, Glossary]`
   - Bug fixes → labels `[Episode, BugFix]`
5. **Fase 4 — Consolidar**: Claude roda processos cognitivos:
   - `populate.py refresh` — importa commits recentes
   - `sleep.py` — 5 fases (dedup, connect, relate, themes, calibrate)
   - `cognitive.py health` — verifica saude
6. **Fase 5 — Evolucao**: Claude analisa uso de componentes:
   - Skills usados → incrementa contadores
   - Co-ativacoes → detecta skills usados juntos
   - Componentes stale → propoe arquivo/aposentadoria
7. **Fase 6 — Resumo**: Claude apresenta:
   - Nos criados, arestas semanticas novas
   - Health score atualizado
   - Sugestoes evolutivas
   - Proxima acao recomendada

**Fluxos Alternativos:**

- **FA-01: Sessao sem trabalho significativo**
  - Na Fase 1, nao ha commits nem alteracoes relevantes
  - Claude informa que nao ha o que registrar
  - Ainda roda consolidacao (Fase 4) para manter saude

- **FA-02: Cerebro com problemas durante encode**
  - Na Fase 3, falha ao adicionar memoria (erro Python)
  - Claude registra o erro, tenta as memorias restantes
  - Reporta falhas no resumo final

- **FA-03: Health critico apos consolidacao**
  - Na Fase 4, health < 0.7
  - Claude executa acoes de recuperacao adicionais (embeddings.py build)
  - Sugere rodar `/doctor` para diagnostico completo

**Pos-condicoes:**
1. Todo conhecimento da sessao registrado no cerebro
2. Conexoes semanticas criadas pelo sono
3. PRIORITY_MATRIX.md atualizado
4. Metricas de evolucao atualizadas
5. Proxima sessao (UC-04) tera acesso a tudo que foi registrado

---

## Gestao de Conhecimento

### UC-10: Descobrir e Registrar Conhecimento de Dominio

| Campo | Valor |
|-------|-------|
| **ID** | UC-10 |
| **Nome** | Descobrir e Registrar Conhecimento de Dominio |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA), Agent `domain-analyst` |
| **Descricao** | Durante o trabalho, um termo de negocio, regra implicita ou estado e descoberto. O sistema extrai, propoe registro e alimenta o cerebro com conhecimento de dominio. |

**Pre-condicoes:**
1. Cerebro inicializado
2. Skill `domain-expert` e agent `domain-analyst` disponiveis

**Fluxo Principal:**
1. Claude detecta conhecimento de dominio (gatilhos automaticos):
   - Termo de negocio nao documentado no cerebro
   - Regra implicita em validacao/constraint
   - Enum/constante que define estados ou transicoes
   - Comentario explicando motivacao (nao implementacao)
   - Logica condicional complexa (if/switch em status, permissoes)
2. Claude verifica no cerebro se o conceito ja esta registrado: `recall "<termo>" --type Concept`
3. Se NAO esta registrado, Claude extrai e propoe ao desenvolvedor:
   - Termo/conceito com definicao
   - Regra de negocio com pre-condicoes e excecoes
   - Entidade com atributos e relacoes
4. O desenvolvedor valida ou corrige
5. Claude registra no cerebro via `brain.add_memory()` com labels `[Concept, Domain]`
6. Se inconsistente com registro existente, Claude reporta possivel bug

**Fluxos Alternativos:**

- **FA-01: Uso explicito pelo desenvolvedor**
  - O desenvolvedor executa `/domain [termo]`
  - Claude analisa o codebase em busca de usos do termo
  - Propoe definicao baseada no codigo encontrado

- **FA-02: Conceito ja registrado mas incompleto**
  - No passo 3, o conceito existe mas com informacao parcial
  - Claude propoe enriquecimento (mais contexto, relacoes, exemplos)
  - O desenvolvedor aprova a atualizacao

- **FA-03: Termo ambiguo**
  - No passo 3, o termo tem multiplos significados no codebase
  - Claude lista os contextos e pede ao dev para distinguir
  - Cada significado e registrado como conceito separado

**Pos-condicoes:**
1. Conhecimento de dominio registrado no cerebro com conexoes
2. Termos acessiveis via `/recall` para qualquer ator
3. Dev Novo podera entender o dominio consultando o cerebro (UC-21)

---

### UC-11: Registrar Decisao Arquitetural

| Campo | Valor |
|-------|-------|
| **ID** | UC-11 |
| **Nome** | Registrar Decisao Arquitetural (ADR) |
| **Ator Principal** | Tech Lead / Arquiteto |
| **Atores Secundarios** | Claude Code (IA), Agent `architect` |
| **Descricao** | Uma decisao arquitetural e tomada e registrada como ADR no cerebro, preservando contexto, alternativas avaliadas e trade-offs para consulta futura. |

**Pre-condicoes:**
1. Uma decisao arquitetural precisa ser tomada ou foi tomada
2. Cerebro inicializado

**Fluxo Principal:**
1. O Tech Lead descreve o problema/decisao ao Claude
2. Claude consulta o cerebro para ADRs existentes relacionadas: `recall "<tema>" --type ADR`
3. Claude apresenta ADRs anteriores que podem influenciar a decisao
4. O Tech Lead discute trade-offs com Claude (opcionalmente delega ao agent `architect`)
5. A decisao e tomada
6. Claude estrutura a ADR:
   - Titulo: `ADR-NNN: [Descricao]`
   - Contexto: problema que motivou
   - Decisao: o que foi decidido
   - Alternativas: opcoes avaliadas e por que foram descartadas
   - Consequencias: trade-offs aceitos
   - Status: aceita / superada / revisada
7. Claude registra no cerebro via `brain.add_memory()` com labels `[ADR, Decision]`
8. O sono (sleep.py) cria conexoes automaticas com patterns, commits e conceitos relacionados

**Fluxos Alternativos:**

- **FA-01: ADR contradiz decisao anterior**
  - No passo 3, Claude encontra ADR que contradiz a nova decisao
  - Claude alerta explicitamente e mostra as implicacoes
  - O Tech Lead decide: (a) manter a nova (marcar anterior como "superada"), (b) respeitar a anterior

- **FA-02: Decisao emergente (nao planejada)**
  - Durante implementacao (UC-06), uma decisao arquitetural e tomada implicitamente
  - Claude detecta e propoe registro como ADR
  - Fluxo inicia no passo 5 (decisao ja tomada)

**Pos-condicoes:**
1. ADR registrada no cerebro com conexoes semanticas
2. Decisao rastreavel via `/recall` para todos os atores
3. Proximas implementacoes consideram a ADR automaticamente
4. Dev Novo encontrara a ADR ao consultar o tema (UC-21)

---

### UC-12: Planejar Implementacao de Feature

| Campo | Valor |
|-------|-------|
| **ID** | UC-12 |
| **Nome** | Planejar Implementacao de Feature |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA), Agent `architect` |
| **Descricao** | Antes de implementar uma feature complexa, o ator cria um plano de implementacao informado pelo cerebro: ADRs, patterns, experiencias anteriores. |

**Pre-condicoes:**
1. Feature identificada (possivelmente via PRIORITY_MATRIX)
2. Cerebro populado com conhecimento do projeto

**Fluxo Principal:**
1. O ator executa `/plan [descricao da feature]`
2. Claude consulta o cerebro para reunir contexto:
   - ADRs que restringem/orientam a implementacao
   - Patterns aprovados para a stack
   - Experiencias anteriores (features similares, bugs relacionados)
   - Regras de dominio aplicaveis
3. Claude analisa o codebase para identificar:
   - Arquivos que serao afetados
   - Dependencias entre componentes
   - Pontos de integracao
4. Claude gera plano de implementacao:
   - Objetivo e escopo
   - Passos numerados com arquivos e funcoes
   - Dependencias entre passos
   - Riscos identificados e mitigacoes
   - Estimativa de complexidade
5. O ator revisa e aprova (ou ajusta)
6. O plano fica disponivel como referencia durante a implementacao (UC-06)

**Fluxos Alternativos:**

- **FA-01: Feature com impacto arquitetural**
  - No passo 2, Claude identifica que a feature exige decisao arquitetural
  - Claude sugere registrar ADR primeiro (UC-11)
  - Apos ADR, retorna ao passo 3 com a restricao incorporada

- **FA-02: Feature depende de componente inexistente**
  - No passo 3, Claude identifica necessidade de skill/agent que nao existe
  - Claude inclui no plano: "Passo 0 — Criar componente X via /create"

**Pos-condicoes:**
1. Plano de implementacao detalhado e disponivel
2. Riscos mapeados antes de comecar
3. Contexto do cerebro incorporado na estrategia
4. Desenvolvedor pode executar UC-06 com confianca

---

## Auto-Evolucao

### UC-13: Criar Componente sob Demanda

| Campo | Valor |
|-------|-------|
| **ID** | UC-13 |
| **Nome** | Criar Componente sob Demanda |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA), Skill `engram-genesis` |
| **Descricao** | O ator identifica uma necessidade recorrente que nenhum componente existente cobre e cria um novo skill, agent ou command via `/create`. |

**Pre-condicoes:**
1. Engram inicializado (UC-03 concluido)
2. Necessidade identificada (tarefa repetitiva, expertise faltante)

**Fluxo Principal:**
1. O ator executa `/create [tipo] [nome]` (ex: `/create skill api-testing`)
2. Claude verifica se componente similar ja existe (manifest + cerebro)
3. Claude analisa o codebase para entender o contexto de uso
4. Claude gera o componente seguindo o DNA (schema correspondente):
   - Skill: SKILL.md com triggers, steps, patterns, exemplos
   - Agent: agent.md com persona, tools, restricoes
   - Command: command.md com prompt e argumentos
5. Claude valida contra o schema (DNA)
6. Claude registra no manifest.json com metadados (source=user, version, created_at)
7. Claude apresenta resumo: o que foi criado, como usar, onde vive

**Fluxos Alternativos:**

- **FA-01: Componente similar ja existe**
  - No passo 2, Claude encontra componente com 70%+ de sobreposicao
  - Claude propoe: (a) estender o existente, (b) compor (usar os dois), (c) criar novo mesmo assim
  - O ator decide

- **FA-02: Schema validation falha**
  - No passo 5, o componente gerado nao passa no schema
  - Claude corrige automaticamente e revalida
  - Se persistir, reporta ao ator e gera com aviso

**Pos-condicoes:**
1. Componente novo disponivel em `.claude/skills/`, `.claude/agents/` ou `.claude/commands/`
2. Registrado no manifest com metricas de uso zeradas
3. Disponivel para uso imediato
4. Sera rastreado pelo engram-evolution para avaliar utilidade

---

### UC-14: Orquestrar Componente em Runtime

| Campo | Valor |
|-------|-------|
| **ID** | UC-14 |
| **Nome** | Orquestrar Componente em Runtime |
| **Ator Principal** | Claude Code (IA) |
| **Atores Secundarios** | Desenvolvedor Solo |
| **Descricao** | Durante o trabalho, Claude detecta que precisa de expertise nao coberta por nenhum componente existente e cria um skill ou agent sob demanda, sem interromper o fluxo. |

**Pre-condicoes:**
1. Tarefa em andamento que requer expertise especifica
2. Nenhum componente existente cobre a necessidade
3. Menos de 2 componentes runtime ja criados nesta sessao

**Fluxo Principal:**
1. Claude lista agents e skills existentes
2. Claude verifica que nenhum cobre a expertise necessaria
3. Claude **anuncia** ao desenvolvedor: "Vou criar [tipo] [nome] porque [motivo]"
4. O desenvolvedor aprova
5. Claude usa engram-genesis para gerar o componente (scaffold → customizar → validar → registrar)
6. Claude registra com `source=runtime` no manifest
7. Claude delega a tarefa ao componente recem-criado
8. Claude reporta ao desenvolvedor o que foi criado

**Fluxos Alternativos:**

- **FA-01: Limite de 2 por sessao atingido**
  - No passo 2, ja existem 2 componentes runtime nesta sessao
  - Claude informa e adapta usando componentes existentes
  - Sugere criar na proxima sessao via `/create`

- **FA-02: Dev rejeita a criacao**
  - No passo 4, o desenvolvedor prefere nao criar
  - Claude adapta usando os componentes existentes (melhor esforco)

- **FA-03: Componente runtime reutilizado**
  - O componente runtime e usado em sessoes subsequentes
  - Na proxima /learn, engram-evolution detecta e propoe promover de `runtime` para `permanent`

**Pos-condicoes:**
1. Componente criado e operacional
2. Tarefa concluida com a expertise necessaria
3. Componente rastreado para avaliacao na proxima /learn
4. Maximo de 2 componentes runtime por sessao respeitado

---

### UC-15: Diagnosticar Saude do Sistema

| Campo | Valor |
|-------|-------|
| **ID** | UC-15 |
| **Nome** | Diagnosticar Saude do Sistema |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O ator executa `/doctor` para verificar a saude completa do Engram: cerebro, componentes, manifest, dependencias e integridade geral. |

**Pre-condicoes:**
1. Engram instalado (UC-01 concluido)

**Fluxo Principal:**
1. O ator executa `/doctor`
2. Claude verifica integridade do cerebro:
   - `cognitive.py health` — score, weak memories, connectivity, embedding coverage
   - Verifica se brain.db existe e e valido
   - Verifica se embeddings estao atualizados
3. Claude verifica componentes:
   - Todos os skills referenciados no manifest existem no disco?
   - Skills tem SKILL.md valido contra o DNA?
   - Agents tem formato correto?
4. Claude verifica dependencias:
   - Python venv existe e funciona?
   - Pacotes necessarios instalados?
5. Claude verifica integridade:
   - CLAUDE.md esta atualizado?
   - Manifest sincronizado com disco?
6. Claude emite diagnostico:
   - Score geral (healthy / needs_attention / critical)
   - Lista de problemas encontrados
   - Acoes recomendadas para cada problema

**Fluxos Alternativos:**

- **FA-01: Cerebro corrompido**
  - No passo 2, brain.db esta corrompido
  - Claude recomenda: `populate.py all` para reconstruir a partir dos .md
  - Oferece executar automaticamente se o dev aprovar

- **FA-02: Componente orfao**
  - No passo 3, skill existe no disco mas nao no manifest
  - Claude propoe registrar ou remover
  - Dev decide

- **FA-03: Dependencias faltantes**
  - No passo 4, pacotes Python nao instalados
  - Claude oferece instalar automaticamente
  - Dev aprova; Claude roda `pip install`

**Pos-condicoes:**
1. Estado de saude do sistema documentado
2. Problemas identificados com acoes claras
3. Se acoes executadas, sistema mais saudavel

---

### UC-16: Evoluir o Sistema via Aprendizado

| Campo | Valor |
|-------|-------|
| **ID** | UC-16 |
| **Nome** | Evoluir o Sistema via Aprendizado |
| **Ator Principal** | Claude Code (IA) |
| **Atores Secundarios** | Desenvolvedor Solo |
| **Descricao** | O skill `engram-evolution` analisa padroes de uso, detecta componentes subutilizados, identifica co-ativacoes recorrentes e propoe evolucoes (criar, compor, aposentar). |

**Pre-condicoes:**
1. Historico de uso de componentes acumulado (varias sessoes de /learn)
2. Manifest com metricas de uso

**Fluxo Principal:**
1. Durante `/learn` (UC-09), a Fase 5 aciona o engram-evolution
2. O sistema analisa metricas de uso:
   - Quais skills foram usados nesta sessao
   - Co-ativacoes: skills usados juntos com frequencia
   - Skills nao usados ha mais de N sessoes (stale)
3. O sistema detecta oportunidades:
   - **Composicao**: skills A e B sempre usados juntos → propor merge
   - **Aposentadoria**: skill C nao usado ha 10+ sessoes → propor archive
   - **Criacao**: padrao recorrente sem skill → propor novo skill
4. O sistema apresenta propostas ao desenvolvedor
5. O desenvolvedor aprova, rejeita ou adapta cada proposta
6. Propostas aprovadas sao executadas (merge, archive ou create)
7. Manifest atualizado com novas metricas e versoes

**Fluxos Alternativos:**

- **FA-01: Nenhuma evolucao necessaria**
  - No passo 3, nao ha oportunidades detectadas
  - O sistema reporta "Sem evolucoes sugeridas. Sistema estavel."

- **FA-02: Componente runtime promovido**
  - No passo 3, componente criado com `source=runtime` (UC-14) mostra uso recorrente
  - O sistema propoe promover para `source=permanent`
  - Dev aprova; manifest atualizado

**Pos-condicoes:**
1. Sistema evoluido com componentes mais relevantes
2. Componentes inuteis aposentados (menos ruido)
3. Composicoes criadas reduzem redundancia
4. Manifest e evolution-log.md atualizados

---

## Priorizacao

### UC-17: Gerenciar Prioridades com ICE Score

| Campo | Valor |
|-------|-------|
| **ID** | UC-17 |
| **Nome** | Gerenciar Prioridades com ICE Score |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA), Skill `priority-engine` |
| **Descricao** | O ator reavalia prioridades do projeto usando o framework ICE (Impact x Confidence x Ease). O PRIORITY_MATRIX.md e o unico knowledge file ativamente mantido. |

**Pre-condicoes:**
1. Tarefas existem (definidas ou descobertas durante o trabalho)
2. Skill `priority-engine` disponivel

**Fluxo Principal:**
1. O ator executa `/priorities`
2. Claude consulta o cerebro para contextualizar:
   - Commits recentes (o que ja foi feito)
   - ADRs (restricoes e direcoes)
   - Experiencias (dificuldades anteriores que afetam confianca)
3. Claude le o PRIORITY_MATRIX.md atual
4. Para cada tarefa, Claude avalia ou reavalia:
   - **Impact** (1-5): quanto impacto a tarefa tem no projeto
   - **Confidence** (1-5): quao confiante estamos que vai funcionar
   - **Ease** (1-5): quao facil e implementar
   - **ICE Score** = Impact × Confidence × Ease
5. Claude reordena a matriz por ICE Score decrescente
6. Claude apresenta a matriz atualizada e sugere as top 3 prioridades
7. O ator ajusta se necessario
8. Claude salva o PRIORITY_MATRIX.md atualizado

**Fluxos Alternativos:**

- **FA-01: Nova tarefa descoberta**
  - O ator menciona uma tarefa nova durante a sessao
  - Claude adiciona a matriz e avalia ICE imediatamente
  - Reordena e apresenta nova posicao

- **FA-02: Tarefa concluida**
  - O ator informa que uma tarefa foi concluida
  - Claude marca como done no PRIORITY_MATRIX e remove da lista ativa
  - Recalcula posicoes das restantes

- **FA-03: Mudanca de contexto**
  - Novas informacoes (bug critico, mudanca de requisitos) alteram drasticamente os scores
  - Claude reavalia todos os ICE Scores com o novo contexto
  - Alerta se a prioridade #1 mudou

**Pos-condicoes:**
1. PRIORITY_MATRIX.md atualizado com ICE Scores vigentes
2. Top prioridades identificadas
3. Proxima sessao (UC-04) mostrara prioridades atualizadas

---

## Multi-Projeto & Compartilhamento

### UC-18: Exportar Skill para Memoria Global

| Campo | Valor |
|-------|-------|
| **ID** | UC-18 |
| **Nome** | Exportar Skill para Memoria Global |
| **Ator Principal** | Desenvolvedor Solo, Tech Lead |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O ator identifica um skill generico o suficiente para ser util em outros projetos e exporta para a memoria global (`~/.engram/`). |

**Pre-condicoes:**
1. Skill existe e esta funcional no projeto atual
2. Skill e generico o suficiente para outros projetos

**Fluxo Principal:**
1. O ator executa `/export [nome-do-skill]`
2. Claude verifica que o skill existe e esta registrado no manifest
3. Claude analisa se o skill contem dependencias especificas do projeto
4. Claude copia o skill para `~/.engram/skills/[nome]/`
5. Claude adiciona metadados de exportacao (projeto de origem, data, versao)
6. Claude confirma a exportacao

**Fluxos Alternativos:**

- **FA-01: Skill com dependencias do projeto**
  - No passo 3, o skill referencia caminhos ou configs especificas
  - Claude alerta e propoe: (a) generalizar antes de exportar, (b) exportar com aviso
  - Dev decide

- **FA-02: Skill ja exportado**
  - No passo 4, ja existe versao em `~/.engram/`
  - Claude compara versoes e propoe: (a) sobrescrever, (b) manter versao anterior
  - Dev decide

**Pos-condicoes:**
1. Skill disponivel em `~/.engram/skills/` para importacao em qualquer projeto
2. Metadados de rastreabilidade registrados
3. Outros projetos podem usar via `/import` (UC-19)

---

### UC-19: Importar Skill da Memoria Global

| Campo | Valor |
|-------|-------|
| **ID** | UC-19 |
| **Nome** | Importar Skill da Memoria Global |
| **Ator Principal** | Desenvolvedor Solo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | O ator importa um skill da memoria global (`~/.engram/`) para o projeto atual, reutilizando conhecimento de outros projetos. |

**Pre-condicoes:**
1. Skill existe em `~/.engram/skills/`
2. Engram inicializado no projeto de destino

**Fluxo Principal:**
1. O ator executa `/import [nome-do-skill]`
2. Claude lista skills disponiveis em `~/.engram/skills/`
3. Claude verifica compatibilidade com o projeto atual (stack, dependencias)
4. Claude copia o skill para `.claude/skills/[nome]/`
5. Claude registra no manifest.json com `source=imported`
6. Claude adapta paths ou configs especificos se necessario
7. Claude confirma a importacao e mostra como usar

**Fluxos Alternativos:**

- **FA-01: Conflito com skill existente**
  - No passo 4, skill com mesmo nome ja existe no projeto
  - Claude propoe: (a) sobrescrever, (b) renomear, (c) cancelar
  - Dev decide

- **FA-02: Incompatibilidade de stack**
  - No passo 3, skill foi criado para stack diferente
  - Claude alerta: "Este skill foi criado para Next.js, seu projeto usa Django"
  - Dev decide se importa mesmo assim

**Pos-condicoes:**
1. Skill disponivel e funcional no projeto atual
2. Registrado no manifest
3. Rastreado pelo engram-evolution para avaliar utilidade

---

## Manutencao

### UC-20: Executar Manutencao Cognitiva do Cerebro

| Campo | Valor |
|-------|-------|
| **ID** | UC-20 |
| **Nome** | Executar Manutencao Cognitiva do Cerebro |
| **Ator Principal** | CI/CD / Automacao |
| **Atores Secundarios** | Desenvolvedor Solo (manual) |
| **Descricao** | Processos cognitivos de manutencao sao executados periodicamente para manter o cerebro saudavel: decay (esquecimento), consolidacao, sono e archive. |

**Pre-condicoes:**
1. Cerebro populado com nos
2. Scripts Python funcionais (venv configurado)

**Fluxo Principal:**
1. O sistema executa manutencao conforme agendamento:
   - **Diario**: `python3 .claude/brain/cognitive.py decay` — aplica curva de Ebbinghaus
   - **Semanal**: `python3 .claude/brain/cognitive.py consolidate` — fortalece conexoes usadas
   - **Mensal**: `python3 .claude/brain/cognitive.py archive` — move memorias fracas (< 0.1)
2. Cada processo gera log em `cognitive-log.jsonl`
3. O health score e recalculado apos cada operacao

**Fluxos Alternativos:**

- **FA-01: Execucao manual**
  - O desenvolvedor roda manualmente quando percebe lentidao ou resultados pobres
  - Pode rodar comandos individuais ou `cognitive.py daily` / `cognitive.py weekly`

- **FA-02: Via cron (recomendado para projetos ativos)**
  ```
  0 2 * * * cd /projeto && python3 .claude/brain/cognitive.py decay
  0 3 * * 0 cd /projeto && python3 .claude/brain/cognitive.py consolidate
  ```

- **FA-03: Cerebro muito grande**
  - Archive move muitas memorias fracas
  - Memorias arquivadas sao preservadas (nao deletadas) mas nao aparecem em buscas
  - Podem ser restauradas se necessario

**Pos-condicoes:**
1. Memorias fracas decairam (esquecimento natural)
2. Conexoes frequentes fortalecidas (consolidacao)
3. Memorias irrelevantes arquivadas (menos ruido)
4. Health score atualizado
5. Proximos recalls retornam resultados mais relevantes

---

### UC-21: Fazer Onboarding de Novo Desenvolvedor

| Campo | Valor |
|-------|-------|
| **ID** | UC-21 |
| **Nome** | Fazer Onboarding de Novo Desenvolvedor |
| **Ator Principal** | Dev Novo |
| **Atores Secundarios** | Claude Code (IA) |
| **Descricao** | Um novo desenvolvedor chega ao projeto e usa o cerebro organizacional para entender decisoes, padroes, dominio e historico sem depender de documentacao manual ou explicacoes da equipe. |

**Pre-condicoes:**
1. Engram inicializado e com historico no cerebro (varias sessoes de /learn)
2. Dev Novo tem acesso ao repositorio e ao Claude Code

**Fluxo Principal:**
1. O Dev Novo abre o Claude Code no projeto
2. O Dev Novo executa `/status` — ve o estado atual, prioridades e saude
3. O Dev Novo faz perguntas naturais ao Claude:
   - "Como funciona a autenticacao?" → Claude roda `/recall` e responde com ADRs, patterns
   - "Por que usamos Redis?" → Claude encontra ADR com contexto, alternativas e trade-offs
   - "O que significa 'idempotencia' neste contexto?" → Claude encontra conceito de dominio
   - "Que bugs ja tiveram no checkout?" → Claude busca episodes de bug fix
4. Claude usa spreading activation para revelar conexoes nao-obvias:
   - "A ADR de Redis tambem influenciou o pattern de cache que voce vai encontrar em X"
5. O Dev Novo consulta padroes aprovados: `/recall patterns de API`
6. O Dev Novo entende o dominio: `/domain pagamento` ou `/recall regras de negocio`
7. O Dev Novo comeca a trabalhar seguindo UC-04 em diante

**Fluxos Alternativos:**

- **FA-01: Cerebro com pouco historico**
  - O projeto e recente e tem poucas sessoes de /learn
  - Claude complementa com analise direta do codebase
  - Sugere que a equipe rode mais `/learn` para enriquecer

- **FA-02: Pergunta sem resposta no cerebro**
  - O Dev Novo pergunta algo que nao esta registrado
  - Claude responde com base no codigo (sem contexto historico)
  - Claude sugere registrar a resposta no cerebro para futuros devs

- **FA-03: Navegacao guiada**
  - O Dev Novo pede: "Me de um tour pelo projeto"
  - Claude monta um roteiro baseado no cerebro:
    1. Visao geral (CURRENT_STATE)
    2. Decisoes-chave (top ADRs por peso)
    3. Padroes obrigatorios (top Patterns)
    4. Dominio (Conceitos com mais conexoes)
    5. Historico recente (ultimos commits)

**Pos-condicoes:**
1. Dev Novo entende arquitetura, decisoes e dominio do projeto
2. Tempo de onboarding drasticamente reduzido
3. Conhecimento institucional preservado independente de turnover
4. Dev Novo pode contribuir seguindo patterns existentes

---

## Matriz de Rastreabilidade

| Caso de Uso | Dev Solo | Tech Lead | Dev Novo | CI/CD |
|-------------|:--------:|:---------:|:--------:|:-----:|
| UC-01: Instalar Engram | X | | | |
| UC-02: Instalar Multiplos | | | | X |
| UC-03: Inicializar Genesis | X | | | |
| UC-04: Iniciar Sessao | X | | | |
| UC-05: Consultar Cerebro | X | X | X | |
| UC-06: Implementar Feature | X | | | |
| UC-07: Code Review | X | X | | |
| UC-08: Commit Semantico | X | | | |
| UC-09: Registrar Aprendizado | X | | | |
| UC-10: Conhecimento Dominio | X | X | | |
| UC-11: Decisao Arquitetural | | X | | |
| UC-12: Planejar Feature | X | X | | |
| UC-13: Criar Componente | X | X | | |
| UC-14: Orquestrar Runtime | | | | |
| UC-15: Diagnosticar Saude | X | | | |
| UC-16: Evoluir Sistema | | | | |
| UC-17: Gerenciar Prioridades | X | X | | |
| UC-18: Exportar Skill | X | X | | |
| UC-19: Importar Skill | X | | | |
| UC-20: Manutencao Cognitiva | | | | X |
| UC-21: Onboarding | | | X | |

> **Nota:** UC-14 e UC-16 tem como ator principal o Claude Code (IA) — sao acionados automaticamente.

---

## Dependencias entre Casos de Uso

```
UC-01 ──→ UC-03 ──→ UC-04 ──→ UC-05
  │                    │         │
  │                    ▼         ▼
  │                  UC-06 ──→ UC-07 ──→ UC-08 ──→ UC-09
  │                    │                              │
  │                    ├──→ UC-10                      ├──→ UC-16
  │                    ├──→ UC-11                      └──→ UC-17
  │                    ├──→ UC-12
  │                    └──→ UC-14 (runtime)
  │
UC-02 (batch, alternativa ao UC-01)

UC-13 (sob demanda, qualquer momento apos UC-03)
UC-15 (diagnostico, qualquer momento apos UC-01)
UC-18 / UC-19 (compartilhamento, qualquer momento apos UC-03)
UC-20 (manutencao, agendado, apos UC-03)
UC-21 (onboarding, apos historico acumulado via UC-09)
```

---

## Glossario

| Termo | Definicao |
|-------|-----------|
| **ADR** | Architecture Decision Record — registro de decisao arquitetural com contexto, alternativas e trade-offs |
| **Cerebro** | Grafo de conhecimento em `.claude/brain/` — fonte primaria de informacao do projeto |
| **DNA** | Schemas formais que definem a estrutura valida de skills, agents, commands e knowledge |
| **Engram** | Traco fisico de uma memoria armazenada no cerebro (termo da neurociencia) |
| **Genesis** | Motor de auto-geracao que analisa o projeto e gera componentes customizados |
| **ICE Score** | Framework de priorizacao: Impact × Confidence × Ease |
| **Manifest** | Registro central de componentes (`.claude/manifest.json`) com metricas de uso |
| **Ouroboros** | Serpente que come a propria cauda — simboliza o ciclo de retroalimentacao do sistema |
| **Recall** | Interface de busca do cerebro com busca semantica e spreading activation |
| **Sleep** | Processo de consolidacao semantica com 5 fases (dedup, connect, relate, themes, calibrate) |
| **Spreading Activation** | Tecnica de busca em grafo que propaga ativacao pelos vizinhos para encontrar nos indiretamente relevantes |
