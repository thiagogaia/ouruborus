# Knowledge Schema v1.0

Define a estrutura dos arquivos de conhecimento persistente do Engram.
Knowledge files são a memória do projeto — alimentados pelo `/learn`.

## Estrutura

```
knowledge/
├── context/
│   └── CURRENT_STATE.md        # Estado vivo do projeto
├── priorities/
│   └── PRIORITY_MATRIX.md      # Tarefas com ICE Score
├── patterns/
│   └── PATTERNS.md             # Padrões e anti-padrões
├── decisions/
│   └── ADR_LOG.md              # Architectural Decision Records
├── domain/
│   └── DOMAIN.md               # Glossário + regras de negócio
└── experiences/
    └── EXPERIENCE_LIBRARY.md   # Interações bem-sucedidas reutilizáveis
```

## Regras Gerais

1. Todos os knowledge files são Markdown
2. Todos DEVEM ter um header H1 como título
3. Todos DEVEM ter campo "Última atualização" no topo
4. Conteúdo é acumulativo — nunca deletar, apenas marcar como obsoleto
5. Cada entrada DEVE ter data de registro
6. Knowledge files são git-tracked (versionados com o projeto)

## CURRENT_STATE.md

O arquivo mais consultado. Estado atual do projeto.

### Seções Obrigatórias
- **Status Geral**: fase, saúde (🟢🟡🔴), próximo marco
- **O Que Mudou Recentemente**: últimas N mudanças com data e impacto
- **Stack**: tecnologias em uso
- **Bloqueios Conhecidos**: o que está impedindo progresso
- **Contexto Para Próxima Sessão**: o que o Claude precisa saber

## PRIORITY_MATRIX.md

Tarefas priorizadas com ICE Score.

### Formato de Entrada
```
| # | Tarefa | Impacto | Confiança | Esforço | ICE | Status |
```
ICE = Impacto × Confiança / Esforço (1-10 cada)

### Seções Obrigatórias
- **Ativas**: tarefas em andamento
- **Backlog**: priorizadas mas não iniciadas
- **Cemitério**: despriorizadas com justificativa

## PATTERNS.md

Padrões descobertos durante o desenvolvimento.

### Formato de Entrada
```
### PAT-NNN: Nome do Padrão
- **Contexto**: quando usar
- **Solução**: como implementar
- **Exemplo**: código ou referência
- **Descoberto em**: data
```

### Seções Obrigatórias
- **Padrões Aprovados**: usar sempre
- **Anti-Padrões**: nunca usar, com justificativa

## ADR_LOG.md

Registro de decisões arquiteturais.

### Formato de Entrada
```
### ADR-NNN: Título da Decisão
- **Status**: proposta | aceita | depreciada | substituída por ADR-XXX
- **Data**: YYYY-MM-DD
- **Contexto**: por que a decisão era necessária
- **Decisão**: o que foi decidido
- **Alternativas**: o que foi considerado
- **Consequências**: trade-offs aceitos
```

## DOMAIN.md

Conhecimento de domínio / negócio.

### Seções Obrigatórias
- **Glossário**: termos do domínio com definição
- **Regras de Negócio**: invariantes que o código deve respeitar
- **Entidades**: mapa das entidades principais e relações
- **Restrições**: limites externos (legais, técnicos, de negócio)

## EXPERIENCE_LIBRARY.md (novo em v2)

Interações bem-sucedidas que podem ser reutilizadas como exemplos.

### Formato de Entrada
```
### EXP-NNN: Título Descritivo
- **Contexto**: qual tarefa foi resolvida
- **Stack**: tecnologias envolvidas
- **Padrão aplicado**: referência a PATTERNS.md (se aplicável)
- **Abordagem**: resumo da solução (3-5 linhas)
- **Resultado**: sucesso/parcial + observações
- **Data**: YYYY-MM-DD
```

### Regras
- Máximo 50 experiências (descartar as mais antigas/menos relevantes)
- Cada experiência tem máximo 10 linhas
- Foco em abordagem, não em código específico
