---
name: execution-pipeline
description: Pipeline estruturado de execucao de tarefas em 7 estagios. Use quando
  precisar mapear demandas em tarefas executaveis, definir cenarios de teste,
  orquestrar implementacao com loop de correcao, ou gerenciar releases com
  documentacao rastreavel. Integra com /plan, /review e /commit.
---

# Execution Pipeline

## Proposito

Metodologia para transformar demandas em entregas testadas e documentadas.
Divide o trabalho em estagios claros com artefatos rastreaveis, loop de correcao,
e separacao de responsabilidades (quem planeja != quem implementa != quem testa).

## Visao Geral

```
Mapeamento → Planejamento → Implementacao → Teste → Avaliacao → Docs → Release
                                              ↑         |
                                              └── NOT OK ┘ (loop de correcao)
```

## Fase 0: Mapeamento de Demanda

Transforma uma demanda (Jira, issue, conversa) em tarefas executaveis.

### Etapa 1: Ler a Fonte

1. Acessar demandas na fonte (Jira, GitHub Issues, etc.)
2. Listar todas: epicos, features, tarefas
3. Identificar hierarquia (epico → features → tarefas)
4. Mapear status atual (backlog, em andamento, etc.)

**Output:** `01-mapeamento-demandas.md`

### Etapa 2: Analisar Dependencias

1. Identificar dependencias entre tarefas
2. Criar grafo de dependencias
3. Definir camadas de execucao (o que vem antes do que)

**Output:** `02-dependencias-priorizacao.md`

### Etapa 3: Avaliar Servico

1. Acessar repositorio do servico
2. Analisar estrutura atual (modulos, entidades, endpoints)
3. Comparar com requisitos da demanda
4. Identificar gaps (o que existe vs o que falta)

**Output:** `03-avaliacao-{servico}.md`

### Etapa 4: Criar Quebra de Tarefas

Estrutura de pastas:
```
tasks/{DEMANDA}/
├── README.md                    # Visao geral, links, criterios
├── 01-{primeira-tarefa}.md      # Requisitos funcionais
├── 02-{segunda-tarefa}.md
└── ...
```

Cada arquivo de tarefa:
```markdown
# Tarefa XX: {Nome}

**Servico:** {nome}
**Tipo:** Desenvolvimento | DevOps
**Dependencia:** Tarefa XX | Nenhuma

## Objetivo
{O que deve ser feito}

## Requisitos Funcionais
### RF01 - {Nome do requisito}
{Descricao, endpoint se aplicavel, resposta esperada}

## Criterios de Aceite
- [ ] {Criterio 1}
- [ ] {Criterio 2}

## Duvidas em Aberto
{Listar, nao assumir}
```

### Regras do Mapeamento

- **Nao inventar termos** — usar apenas termos da fonte
- **Nao inventar requisitos** — se nao sabe, perguntar
- **Delegar avaliacoes tecnicas** — usar agentes especializados
- **Documentar duvidas** — registrar no arquivo, nao assumir
- **NUNCA** entrar na Etapa 4 sem finalizar todas as anteriores

## Estagio 1: Planejamento

1. Ler arquivo da tarefa (requisitos funcionais)
2. Avaliar o que precisa ser feito
3. Verificar ambiente Docker (OBRIGATORIO):
   - Existe `docker-compose.yml` com app + banco + deps?
   - Se NAO: marcar criacao como PRE-REQUISITO
4. Definir cenarios de teste
5. Documentar cenarios

**Output:** `{task-id}-cenarios-teste.md`

Conteudo obrigatorio:
- Como subir o ambiente
- Pre-requisitos (migrations, seeds)
- Lista de cenarios com comandos especificos
- Criterio de sucesso de cada cenario

## Estagio 2: Implementacao

1. Ler arquivo da tarefa
2. Se nao existe docker-compose: criar PRIMEIRO
3. Implementar requisitos
4. Garantir: test, lint, build passando

**Importante:** Ambiente Docker deve ser COMPLETO e ISOLADO (portas unicas para rodar em paralelo).

## Estagio 3: Teste

1. Subir ambiente via docker-compose (OBRIGATORIO)
2. Executar cada cenario de teste definido no Estagio 1
3. Registrar resultado de cada cenario
4. Gerar arquivo de resultado
5. Derrubar ambiente (docker-compose down)

**NUNCA** subir app/banco manualmente. Sempre docker-compose.

**Output:** `{task-id}-resultado-teste.md`

## Estagio 4: Avaliacao

1. Ler resultado do teste
2. Avaliar se todos os cenarios passaram

**Se OK:** proximo estagio.

**Se NAO OK:**
1. Alocar correcao
2. Corrigir E validar cenarios que falharam
3. LIMPAR resultado anterior
4. Re-testar TODOS os cenarios (nao so os que falharam)
5. Voltar para avaliacao (loop ate OK)

**Limite:** maximo 3 tentativas antes de escalar para humano.

## Estagio 5: Documentacao API

1. Verificar se o projeto tem Swagger/OpenAPI
2. Se nao tem: criar com implementacao adequada a stack
3. Se tem: atualizar com novos endpoints/alteracoes

## Estagio 6: Release

1. Verificar/criar branch `{DEMANDA}` no projeto
2. Commit com mensagem descritiva referenciando a tarefa
3. Cada tarefa = 1 commit isolado

```
feat({servico}): {descricao} - {DEMANDA}/{tarefa}
```

**NAO fazer push automatico** — aguardar revisao se necessario.

## Estagio 7: Documentacao Wiki

1. Verificar se o projeto tem wiki
2. Se nao: criar
3. Se tem: atualizar com nova versao/changelog

## Estrutura Final

```
tasks/{DEMANDA}/
├── README.md
├── 01-{tarefa}.md
├── 01-{tarefa}-cenarios-teste.md
├── 01-{tarefa}-resultado-teste.md    ← OK
├── 02-{tarefa}.md
├── 02-{tarefa}-cenarios-teste.md
├── 02-{tarefa}-resultado-teste.md    ← OK
└── ...
```

## Integracao com Engram

- `/plan` → usar para Estagio 1 (planejamento)
- `/review` → usar antes do Estagio 6 (release)
- `/commit` → usar no Estagio 6 (commit semantico)
- `/learn` → usar apos cada demanda completa

## Regras

- NUNCA pular estagios (sequencia e obrigatoria)
- NUNCA assumir requisitos — se nao esta no arquivo, perguntar
- SEMPRE ter docker-compose antes de implementar
- SEMPRE testar TODOS os cenarios no re-teste (nao so os que falharam)
- SEMPRE limpar resultado anterior antes de re-testar
- Maximo 3 tentativas no loop de correcao
- Cada tarefa = 1 commit isolado
- Documentar duvidas no arquivo, nao no chat

## Output Esperado

Ao iniciar uma demanda:
```
Pipeline de Execucao — {DEMANDA}
=================================

Tarefas: X (Y em sequencia, Z paralelizaveis)
Servicos afetados: [lista]
Dependencias: [grafo]

Estagio atual: [1-7]
Progresso: [X/Y tarefas concluidas]
```
