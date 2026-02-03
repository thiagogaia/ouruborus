# Architecture Decision Records
> Última atualização: 2026-02-03 (/init-engram)

## ADR-001: Sistema Metacircular
**Data**: 2026-02-03
**Status**: ✅ Aceito
**Decisores**: Design inicial

### Contexto
Engram v1 tinha skills fixos. Adicionar novos exigia edição manual. Cada projeto tinha os mesmos skills, mesmo que a stack fosse diferente.

### Decisão
Implementar sistema metacircular onde genesis gera skills sob demanda baseado na stack detectada, e evolution rastreia uso para propor melhorias.

### Consequências
- ✅ Skills customizados por projeto
- ✅ Sistema se auto-evolui
- ✅ Menos manutenção manual
- ⚠️ Maior complexidade inicial
- ⚠️ Requer schemas bem definidos

---

## ADR-002: Skills com Frontmatter YAML
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Precisamos de metadados estruturados (name, description) para validação e registro, mas queremos manter markdown legível.

### Decisão
Usar frontmatter YAML (delimitado por ---) no início de SKILL.md. Body continua markdown puro.

### Alternativas Consideradas
1. ❌ JSON separado — dois arquivos, mais complexo
2. ❌ Tudo YAML — menos legível para humanos
3. ✅ Frontmatter YAML — padrão da indústria (Jekyll, Hugo, MDX)

### Consequências
- ✅ Validação automática via parse simples
- ✅ Legível por humanos
- ✅ Compatível com editores markdown
- ⚠️ Parser YAML básico (sem recursos avançados)

---

## ADR-003: Agents Não Invocam Outros Agents
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Task tool permite invocar subagents. Se agents pudessem invocar outros agents, poderíamos ter loops infinitos ou explosão de contexto.

### Decisão
Agents são terminais — podem usar tools (Read, Grep, etc) mas NUNCA Task. Orquestração fica com o Claude principal.

### Consequências
- ✅ Sem risco de loops infinitos
- ✅ Controle de contexto previsível
- ✅ Debug mais simples
- ⚠️ Composição requer skill intermediário

---

## ADR-004: Progressive Disclosure
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Carregar todos os skills no início desperdiça tokens e sobrecarrega o contexto.

### Decisão
Skills são carregados sob demanda quando o Claude detecta necessidade (via triggers na description) ou quando invocados explicitamente.

### Consequências
- ✅ Menor uso de tokens
- ✅ Contexto mais focado
- ✅ Escalável para muitos skills
- ⚠️ Descriptions devem ter triggers claros

---

## ADR-005: Python para Scripts Internos
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Scripts de genesis/evolution precisam manipular JSON, parsear markdown, validar estruturas.

### Decisão
Usar Python 3 sem dependências externas. Funciona em qualquer máquina com Python instalado.

### Alternativas Consideradas
1. ❌ Node.js — requer npm install
2. ❌ Bash puro — muito verboso para JSON/parsing
3. ✅ Python stdlib — universal, expressivo, sem deps

### Consequências
- ✅ Zero dependências
- ✅ Funciona em macOS, Linux, WSL
- ✅ Fácil de manter
- ⚠️ Requer Python 3.8+

---

## ADR-006: Manifest como Source of Truth
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Precisamos saber quais componentes existem, suas versões, uso, saúde.

### Decisão
manifest.json é o registro central. register.py mantém sincronizado. doctor.py detecta dessincronização.

### Consequências
- ✅ Single source of truth
- ✅ Métricas de uso automáticas
- ✅ Health tracking
- ⚠️ Precisa manter sincronizado

---

## ADR-007: Adoção do Engram (Bootstrap)
**Data**: 2026-02-03
**Status**: ✅ Aceito

### Contexto
Este projeto É o próprio Engram — um caso metacircular onde o sistema gerencia a si mesmo.

### Decisão
Usar Engram para desenvolver Engram, demonstrando o conceito de auto-alimentação (ouroboros).

### Consequências
- ✅ Dogfooding — usamos o que construímos
- ✅ Bugs encontrados mais rápido
- ✅ Demonstra viabilidade do sistema
- ⚠️ Bootstrap paradox (precisamos do sistema para melhorar o sistema)

---

## Template para Novas Decisões

```markdown
## ADR-NNN: Título
**Data**: YYYY-MM-DD
**Status**: 🟡 Proposto | ✅ Aceito | ❌ Rejeitado | ⚠️ Superseded

### Contexto
[Qual problema estamos resolvendo?]

### Decisão
[O que decidimos fazer?]

### Alternativas Consideradas
1. ❌ Alternativa A — [motivo rejeição]
2. ❌ Alternativa B — [motivo rejeição]
3. ✅ Escolhida — [motivo escolha]

### Consequências
- ✅ Benefício 1
- ✅ Benefício 2
- ⚠️ Trade-off 1
```
