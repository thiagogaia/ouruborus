# Command Schema v1.0

Define a estrutura de slash commands Engram.
Commands são atalhos que o dev invoca como `/comando [args]`.

## Estrutura

```
commands/
└── command-name.md         # Nome = o que o dev digita após /
```

Opcionalmente, subdiretórios para comandos com namespace:
```
commands/
└── workflow/
    ├── plan.md             # /workflow:plan
    └── execute.md          # /workflow:execute
```

## Formato do Arquivo

Commands são Markdown puro — sem frontmatter YAML.
O conteúdo é a instrução que o Claude executa quando o dev invoca `/command`.

### Variáveis Disponíveis
- `$ARGUMENTS` — texto após o nome do comando
  Exemplo: `/plan autenticação OAuth` → $ARGUMENTS = "autenticação OAuth"

## Regras de Validação

1. Arquivo DEVE ser `.md` dentro de `.claude/commands/`
2. Nome do arquivo DEVE ser kebab-case
3. Conteúdo DEVE ser instruções executáveis (não documentação)
4. DEVE conter pelo menos uma ação concreta
5. PODE referenciar skills, agents e knowledge files
6. NÃO DEVE ter frontmatter YAML (diferente de skills e agents)
7. NÃO DEVE ter mais de 200 linhas

## Boas Práticas

- Comece com o contexto mínimo necessário
- Referencie knowledge files para estado persistente
- Use skills sob demanda (não carregue tudo)
- Termine com output visível (relatório, confirmação, etc)
- Se o command modifica knowledge, termine registrando a mudança

## Exemplo Mínimo Válido

```markdown
Analise o estado atual do projeto:

1. Consulte o cérebro: `python3 .claude/brain/recall.py --recent 7d --top 10`
2. Leia `.claude/knowledge/priorities/PRIORITY_MATRIX.md`
3. Resuma: status geral, próxima prioridade, bloqueios
4. Sugira a próxima ação concreta

Se o $ARGUMENTS contiver um tópico específico, foque nele.
```
