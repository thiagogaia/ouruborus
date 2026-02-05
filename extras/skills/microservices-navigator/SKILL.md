---
name: microservices-navigator
description: Navegador de ecossistemas de microservicos. Use quando precisar mapear
  dependencias entre servicos, detectar comunicacao (REST, Kafka, SQS, gRPC),
  identificar duplicidades, entender fluxos de orquestracao, ou debugar
  problemas de integracao entre servicos. Tambem para onboarding em projetos
  com muitos repositorios.
---

# Microservices Navigator

## Proposito

Navegar e mapear ecossistemas complexos de microservicos. Em projetos com 10+ servicos,
entender quem chama quem, por qual protocolo, e qual o papel de cada servico vira
o maior gargalo de produtividade. Este skill resolve isso.

## Workflow

### 1. Mapear Servicos

Para cada repositorio/servico do ecossistema:

```
| Servico | Stack | Tipo | Responsabilidade |
|---------|-------|------|------------------|
```

**Tipos de servico:**
- **Orquestrador**: coordena fluxos entre servicos (ex: recebe request, chama N servicos)
- **Dominio**: dono de uma entidade/recurso (ex: orders, payments, users)
- **Processador**: consome filas/eventos e executa logica (workers, consumers)
- **Gateway**: ponto de entrada externo (API gateway, BFF)
- **Legado**: servico antigo mantido por compatibilidade
- **Infraestrutura**: bridge, webhook relay, cache, logging

### 2. Detectar Comunicacao

Analisar codigo para identificar como servicos se comunicam:

**REST (sincrono)**
- Buscar HTTP clients (axios, fetch, HttpService, Guzzle)
- Mapear base URLs e endpoints chamados
- Identificar service discovery (DNS interno, env vars)

**Mensageria (assincrono)**
- Kafka: buscar producers/consumers, topicos, consumer groups
- SQS: buscar envio/consumo de filas
- RabbitMQ: exchanges, queues, bindings

**Eventos**
- Event emitters internos
- Webhooks (inbound/outbound)
- Schedulers e CronJobs

**Resultado:**
```
| De | Para | Protocolo | Canal/Rota | Descricao |
|----|------|-----------|------------|-----------|
| conductor | order | REST | POST /orders | Criar pedido |
| establishment | bridge | Kafka | establishment.created | Novo EC |
| webhook | payment-processor | SQS | acquirer-webhooks | Notificacao adquirente |
```

### 3. Identificar Padroes de Orquestracao

Classificar como os servicos se coordenam:

- **Orchestration**: um servico central coordena o fluxo (conductor pattern)
- **Choreography**: servicos reagem a eventos de outros (pub/sub)
- **Saga**: transacoes distribuidas com compensacao
- **CQRS**: separacao de leitura/escrita em servicos diferentes
- **Event Sourcing**: estado derivado de sequencia de eventos

### 4. Mapear Dependencias

Gerar grafo de dependencias:

```
Servico A
  ├── depende de: B (REST), C (Kafka)
  ├── depende dele: D, E
  └── banco: PostgreSQL (schema_a)
```

**Identificar:**
- Servicos criticos (muitos dependentes)
- Single points of failure
- Dependencias circulares
- Servicos isolados (sem dependencias = possivel dead code)

### 5. Detectar Problemas

**Duplicidades:**
- Mesmo endpoint implementado em 2+ servicos
- Mesma entidade gerenciada por servicos diferentes
- Logica de negocio replicada (ex: calculo de taxa em 3 servicos)

**Anti-patterns:**
- Chatty communication (servico A chama B 10x por request)
- Distributed monolith (deploy independente mas acoplamento forte)
- Shared database (2+ servicos acessando mesmo schema)
- Sync over async (usando REST onde deveria ser evento)

### 6. Gerar Documentacao

Produzir SERVICE_MAP.md atualizado com:
- Tabela de servicos
- Mapa de comunicacao
- Diagrama de dependencias (ASCII ou Mermaid)
- Bancos de dados por servico
- Dependencias externas (APIs de terceiros)

## Regras

- NUNCA assumir comunicacao sem evidencia no codigo
- Diferenciar comunicacao sincrona (REST) de assincrona (Kafka/SQS)
- Registrar servicos legados separadamente — eles tem regras diferentes
- Ao encontrar duplicidade, reportar COM os arquivos/linhas especificos
- Atualizar SERVICE_MAP.md quando descobrir novos fluxos
- Considerar workers/consumers como servicos (eles tem dependencias proprias)

## Output Esperado

```
Mapa de Microservicos
=====================

Servicos: X ativos, Y legados
Comunicacao: Z fluxos (W sync, V async)
Bancos: N schemas

Fluxo Principal:
  Client → Gateway → Orchestrator → [Service A, Service B] → Response

Problemas Detectados:
  - [duplicidade/anti-pattern com localizacao]

Recomendacoes:
  1. [acao concreta]
```
