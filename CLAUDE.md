# Projeto: ouroborusclaudegram_v2_final

## Identidade
Idioma padrão: Português brasileiro. Código e commits em inglês.

## Princípio Central: Auto-Alimentação (Ouroboros)
Este projeto usa Engram v2.0.0 — um sistema metacircular de retroalimentação.
Toda decisão, padrão, erro corrigido ou insight DEVE ser registrado em `.claude/knowledge/`.
O sistema evolui a si mesmo: gera skills sob demanda, versiona mudanças, aposenta o inútil.

## Workflow Obrigatório

### Antes de Codificar
1. Leia `.claude/knowledge/context/CURRENT_STATE.md`
2. Consulte `.claude/knowledge/priorities/PRIORITY_MATRIX.md`
3. Verifique `.claude/knowledge/patterns/PATTERNS.md`
4. Se decisão arquitetural: consulte `ADR_LOG.md`
5. Se lógica de negócio: consulte `DOMAIN.md`
6. Se tarefa similar já resolvida: consulte `EXPERIENCE_LIBRARY.md`

### Ao Codificar
- Validação de input em todas as APIs
- Error handling em todas as rotas

### Depois de Codificar
1. Atualize `CURRENT_STATE.md`
2. Registre padrões novos em `PATTERNS.md`
3. Registre decisões em `ADR_LOG.md`
4. Reavalie `PRIORITY_MATRIX.md`
5. Registre aprendizados de domínio em `DOMAIN.md`

## Stack

## Auto-Geração (Metacircular)
O Engram gera seus próprios componentes:
- `/init-engram` — Análise profunda + geração de skills/agents para o projeto
- `/create [tipo] [nome]` — Gerar componente sob demanda
- `/doctor` — Health check do sistema
- `/learn` — Retroalimentação + evolução

Schemas em `.claude/schemas/`. Manifest em `.claude/manifest.json`.

## Skills Disponíveis
Consulte `.claude/skills/` — cada skill tem SKILL.md com instruções.
Skills são gerados sob demanda pelo `engram-genesis`.

## Subagentes
Definidos em `.claude/agents/`. Gerados pelo `/init-engram`.
Subagentes NÃO podem invocar outros subagentes.

## Orquestração Inteligente
O Claude cria subagents e skills sob demanda DURANTE o trabalho.
Se uma tarefa exige expertise que nenhum componente existente cobre:

1. **Detectar**: listar agents/skills, verificar se algum cobre
2. **Anunciar**: informar ao dev o que vai criar e por quê
3. **Gerar**: usar engram-genesis (scaffold → customizar → validar → registrar)
4. **Usar**: delegar a tarefa ao componente recém-criado
5. **Reportar**: informar o que foi criado ao final

Consulte `.claude/skills/engram-factory/SKILL.md` para o protocolo completo.
Referência detalhada em `.claude/skills/engram-factory/references/orchestration-protocol.md`.

Regras: anunciar antes de criar, máximo 2 por sessão, nunca duplicar, source=runtime.

## Regras de Ouro
- NUNCA pule o workflow de retroalimentação
- Priorize legibilidade sobre cleverness
- Pergunte antes de mudar arquitetura
- Registre TUDO que pode ser útil no futuro
- Se não existe skill para algo repetitivo: crie com `/create`
