# Experience Library
> Última atualização: 2026-02-04 (/learn commit c7a67be)
> Soluções reutilizáveis descobertas durante o trabalho

## EXP-001: Validar Componente Antes de Registrar
- **Contexto**: Componente criado manualmente tinha erros no frontmatter
- **Stack**: Python scripts, manifest.json
- **Padrão**: PAT-007
- **Abordagem**: SEMPRE rodar validate.py antes de register.py. Corrigir todos os erros reportados. Só então registrar.
- **Resultado**: Sucesso — evita componentes inválidos no sistema
- **Data**: 2026-02-03

---

## EXP-002: Debugar Script Python do Engram
- **Contexto**: Script não estava funcionando como esperado
- **Stack**: Python 3, scripts do Engram
- **Abordagem**: Rodar com output explícito. Verificar se path está correto. Checar se Python 3.8+ está instalado.
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-003: Verificar Saúde do Sistema
- **Contexto**: Dúvida se Engram está funcionando corretamente
- **Stack**: /doctor, doctor.py
- **Abordagem**: Rodar `/doctor` ou `python3 doctor.py --project-dir .`. Score 90%+ = saudável.
- **Resultado**: Sucesso — diagnóstico rápido com sugestões de fix
- **Data**: 2026-02-03

---

## EXP-004: Ver Uso de Componentes
- **Contexto**: Não sei quais skills estão sendo usados
- **Stack**: track_usage.py
- **Abordagem**: Três reports disponíveis: health (completo), stale (obsoletos), summary (rápido).
- **Resultado**: Sucesso — visibilidade de métricas
- **Data**: 2026-02-03

---

## EXP-005: Criar Skill Customizado
- **Contexto**: Preciso de um skill novo para tarefa repetitiva
- **Stack**: genesis scripts
- **Padrão**: PAT-002
- **Abordagem**: generate_component.py → editar SKILL.md → validate.py → register.py
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-006: Atualizar Engram Sem Perder Customizações
- **Contexto**: Nova versão do Engram disponível
- **Stack**: setup.sh
- **Abordagem**: `./setup.sh --update /projeto` preserva knowledge e skills customizados
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-007: Listar Todos os Componentes
- **Contexto**: Quero ver tudo que está instalado
- **Stack**: register.py
- **Abordagem**: `register.py --list --project-dir .`
- **Resultado**: Sucesso — lista com versão, uso, source
- **Data**: 2026-02-03

---

## EXP-008: Ciclo Completo /init-engram + /learn + /commit
- **Contexto**: Primeira inicialização completa do Engram em um projeto
- **Stack**: /init-engram, /learn, /commit
- **Abordagem**: 1) /init-engram popula knowledge files 2) Gera skills específicos 3) /commit com mensagem semântica 4) /learn registra uso e evolui
- **Resultado**: Sucesso — health 100%, 61 arquivos commitados, tracking funcionando
- **Data**: 2026-02-03

---

## EXP-009: Registrar Co-ativações de Skills
- **Contexto**: Quero saber quais skills são usados juntos para detectar oportunidades de composição
- **Stack**: co_activation.py
- **Abordagem**: `co_activation.py --log-session --skills skill1,skill2,skill3 --project-dir .`
- **Resultado**: Sucesso — sessão registrada para análise futura
- **Data**: 2026-02-03

---

## EXP-010: Analisar Arquitetura de Subagentes vs Paralelismo
- **Contexto**: Questão se o Engram deveria ter execução paralela com context windows isoladas
- **Stack**: Arquitetura Engram v2, orquestração
- **Abordagem**: Usar agente Explore para análise profunda. Documentar vantagens do modelo atual antes de propor mudanças.
- **Descoberta**: Modelo sequencial é vantagem deliberada: (1) evita race conditions em knowledge files, (2) permite detecção confiável de co-ativações, (3) 3x mais barato em tokens, (4) skills gerados em sequência evitam redundância
- **Resultado**: Decisão de manter modelo sequencial — paralelismo quebraria premissas do sistema de evolução
- **Data**: 2026-02-03

---

## EXP-011: Implementar Sistema de Migração de Backups
- **Contexto**: /init-engram não tinha lógica para migrar backups criados pelo setup.sh
- **Stack**: Python, engram-genesis scripts
- **Padrão**: PAT-011
- **Abordagem**: 1) Analisar como setup.sh cria backups 2) Criar migrate_backup.py com --detect, --analyze, --migrate, --cleanup 3) Atualizar init-engram.md com Fase 0 e Fase 6
- **Descoberta**: Merge semântico é melhor que sobrescrita — preserva EXP entries, PAT entries, ADRs únicos
- **Resultado**: Sucesso — testado com backups simulados, todas as fases funcionam
- **Data**: 2026-02-03

---

## EXP-012: Limpar __pycache__ do Histórico Git
- **Contexto**: Arquivos __pycache__ foram commitados acidentalmente antes do .gitignore
- **Stack**: Git, .gitignore
- **Abordagem**: 1) Criar .gitignore robusto 2) `git rm -r --cached **/__pycache__/` 3) Commit de cleanup
- **Descoberta**: Remover do cache (--cached) preserva arquivos locais mas remove do tracking
- **Resultado**: Sucesso — 22 binários removidos do histórico, repositório mais limpo
- **Data**: 2026-02-03

---

## EXP-013: Estruturar Commit Fundacional de Sistema
- **Contexto**: Criar base completa de sistema metacircular (Engram v2.0.0)
- **Stack**: Git, bash, Python, Markdown
- **Padrão**: PAT-017
- **Abordagem**: Incluir em commit atômico:
  1. Estrutura de diretórios (.claude/ com subpastas)
  2. Schemas de validação (skill.schema.md, agent.schema.md, etc)
  3. Motors core (engram-genesis/, engram-evolution/)
  4. Seeds universais (6 skills que funcionam em qualquer projeto)
  5. Knowledge files populados (não templates vazios)
  6. Documentação de design (proposals em docs/)
- **Resultado**: 61 arquivos, 6002 linhas, Health Score 100%
- **Data**: 2026-02-03 (commit 264072a6)

---

## EXP-014: Extrair Conhecimento de Commit Antigo via /learn
- **Contexto**: Analisar commit específico para documentar padrões retroativamente
- **Stack**: Git, /learn skill
- **Abordagem**: 1) `git show <sha> --stat` para ver scope 2) `git diff <sha>^..<sha>` para diff completo 3) Analisar mudanças e extrair padrões 4) Atualizar knowledge files
- **Descoberta**: Commits fundacionais contêm muitos padrões implícitos que valem documentar
- **Resultado**: 3 novos padrões (PAT-017, PAT-018, PAT-019) extraídos do commit 264072a6
- **Data**: 2026-02-04

---

## EXP-015: Documentar Arquitetura v3.0 Git-Native (commit 5da6535c)
- **Contexto**: Extrair e consolidar decisões arquiteturais de commit fundacional de arquitetura
- **Stack**: Git, brain.py, populate.py, /learn
- **Abordagem**: 1) `git show 5da6535c --stat` 2) Identificar ADRs novos 3) Popular cérebro com commits recentes 4) Criar memórias conceituais (Git-Native Architecture, Wikilinks Pattern)
- **Descoberta**: 4 ADRs (008-011) definem escalabilidade para 10 devs x 5 anos (~$0.20/sessão vs $37)
- **Padrões Extraídos**: Estado por dev evita conflitos, wikilinks criam grafo emergente, camadas HOT/WARM/COLD controlam tokens
- **Resultado**: Cérebro: 93 nós, 145 arestas. Health Score: 100%
- **Data**: 2026-02-04

---

## EXP-016: Major Version Upgrade (cb64fd73 - v3.0.0)
- **Contexto**: Analisar commit de upgrade de versao major para extrair padroes
- **Stack**: Git, /learn skill, knowledge files
- **Abordagem**: 1) `git show cb64fd73 --stat` (24 files, 1410 insertions) 2) Analisar diff completo 3) Identificar componentes novos (5 seeds) 4) Extrair metricas do cerebro (68 nos, 106 arestas) 5) Documentar padroes (PAT-020, 021, 022)
- **Descoberta**:
  - cognitive-log.jsonl registra hubs de conhecimento (person-engram = 49 conexoes, principal hub)
  - Seeds faltantes causavam instalacao incompleta
  - Diagrama ASCII do ciclo metacircular documenta arquitetura visualmente
- **Padroes Extraidos**: Major upgrade checklist (PAT-020), Seeds universais (PAT-021), Cognitive log (PAT-022)
- **Resultado**: Cerebro v3 completo, health 100%, 26 verificacoes passando
- **Data**: 2026-02-04

---

## EXP-017: Implementar /recall para Consulta ao Cerebro (5db29c67)
- **Contexto**: Criar interface human-friendly para consultar cerebro organizacional
- **Stack**: Python, argparse, brain.py, embeddings.py, commands
- **Abordagem**:
  1. Criar recall.py com busca semantica + spreading activation
  2. Implementar fallback gracioso quando deps nao estao disponiveis
  3. Dual output: JSON para scripts, human-readable para devs
  4. Criar command em .claude/commands/ E core/commands/
  5. Atualizar CLAUDE.md com instrucoes de quando usar /recall
- **Padroes Aplicados**: PAT-023 (Fallback), PAT-024 (Hibrido), PAT-025 (Dual Output), PAT-026 (Dois Locais), PAT-027 (Spreading)
- **Descoberta**: recall.py usa type_map para traduzir tipos amigaveis ("adr") para labels do grafo (["ADR", "Decision"])
- **Resultado**: 4 arquivos, 575 linhas. Interface: `/recall "query" --type ADR --depth 3`
- **Data**: 2026-02-03 (commit 5db29c67)

---

## EXP-018: Implementar Cerebro Organizacional Completo (d94adec)
- **Contexto**: Commit massivo (66 arquivos, 5429 linhas) implementando sistema de memoria com grafo
- **Stack**: Python, NetworkX, sentence-transformers, numpy
- **Abordagem**:
  1. brain.py (1060 linhas): grafo DiGraph + spreading activation + decay
  2. embeddings.py (233 linhas): busca semantica com provider configuravel
  3. cognitive.py (244 linhas): processos periodicos (consolidate, decay, archive, health)
  4. populate.py (527 linhas): popular com ADRs, patterns, commits existentes
  5. maintain.sh (67 linhas): wrapper para cron/CI
  6. Integrar em /init-engram (Fase 5) e /learn (Fase 4)
- **Padroes Extraidos**: PAT-020 (Grafo NetworkX com FallbackGraph), PAT-021 (Decay diferenciado Decision<Episode), PAT-022 (Spreading activation), PAT-023 (Provider local/openai), PAT-024 (Jobs periodicos), PAT-025 (Conteudo .md + grafo .json)
- **Resultado**: Estado inicial: 61 nos, 97 arestas, 61 embeddings. Agora: 108 nos, 169 arestas
- **Data**: 2026-02-04 (analise do commit d94adec de 2026-02-03)

---

## EXP-019: Analisar Commit Fundacional para Documentar Design Decisions (bbcc8777)
- **Contexto**: Commit inicial de repositório contém decisões implícitas valiosas
- **Stack**: Git, /learn, knowledge files
- **Abordagem**:
  1. `git show <sha> --stat` para escopo (77 arquivos, 8137 linhas)
  2. Ler documentos de design (`Engram_self_bootstrap_analysis.md`, guia de uso)
  3. Identificar inspirações (Voyager, DGM, BOSS)
  4. Extrair ADR-000 com justificativas de cada feature
  5. Documentar padrões fundacionais (PAT-028 a PAT-031)
- **Descoberta**: Commit inicial contém "DNA conceitual" - pesquisa de mercado + gap analysis + proposta arquitetural = base para todas as decisões futuras
- **Resultado**: 1 ADR, 4 padrões, 8 termos de glossário extraídos
- **Data**: 2026-02-04

## EXP-020: Reverter Feature para Restaurar Single Responsibility (setup.sh)
- **Contexto**: setup.sh acumulou batch logic (+175 linhas), violando SRP
- **Stack**: Bash, Git
- **Abordagem**:
  1. `git log --follow setup.sh` para encontrar commit antes da feature
  2. Comparar versões (`git show <sha>:setup.sh | wc -l`)
  3. Avaliar o que se perde (batch) vs o que se ganha (simplicidade)
  4. `git checkout <sha> -- setup.sh` para revert cirúrgico
  5. Criar wrapper separado (`batch-setup.sh`) com a lógica extraída
  6. Atualizar README para refletir separação
- **Descoberta**: Revert cirúrgico de arquivo + criação de wrapper é melhor que refatorar in-place
- **Resultado**: setup.sh -175 linhas, batch-setup.sh 177 linhas, README corrigido
- **Data**: 2026-02-04

---

## Regras da Library
- Maximo 50 experiencias (descartar as mais antigas se necessario)
- Cada experiencia: maximo 10 linhas
- Foco na abordagem, nao no codigo especifico
- Experiencias mais recentes tem prioridade
- Populado pelo /learn quando interacoes sao bem-sucedidas
