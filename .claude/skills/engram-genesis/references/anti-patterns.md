# Anti-Patterns — O que NÃO Fazer

## AP-1: Skill Genérico Demais
❌ "Ajuda a resolver problemas de código"
✅ "Valida endpoints REST contra padrões do projeto, incluindo input validation, error handling e tipagem"

**Problema:** Description vago não ativa o skill no momento certo.

## AP-2: Skill Gigante
❌ SKILL.md com 800+ linhas cobrindo tudo
✅ SKILL.md com ~100 linhas + references/ para detalhes

**Problema:** Consome contexto desnecessário toda vez que ativa.

## AP-3: Documentação ao Invés de Instrução
❌ "Este skill foi criado para... A história por trás dele..."
✅ "1. Leia o schema. 2. Valide os campos. 3. Reporte erros."

**Problema:** Claude precisa de instrução, não de backstory.

## AP-4: Hardcoded para Uma Stack
❌ "Use `npx prisma migrate dev` para criar migration"
✅ "Execute o comando de migration do ORM detectado no projeto"

**Problema:** Skill fica inútil se o projeto mudar de ORM.
**Exceção:** Skills em `templates/stacks/` são propositalmente específicos.

## AP-5: Sem Guardrails
❌ Skill que não tem seção "Regras"
✅ "NUNCA execute migration em produção sem backup"

**Problema:** Sem limites, o skill pode causar dano.

## AP-6: Duplicação de Knowledge
❌ Repetir no SKILL.md informação que está em PATTERNS.md
✅ "Consulte PATTERNS.md seção 'API Patterns' para padrões aprovados"

**Problema:** Informação duplicada diverge com o tempo.

## AP-7: Arquivos Extraneous
❌ README.md, CHANGELOG.md, INSTALLATION.md dentro do skill
✅ Apenas SKILL.md + scripts/ + references/ + assets/

**Problema:** Poluição, confusão, desperdício de tokens.

## AP-8: Skills que Invocam Agents
❌ "Invoque o agent architect para avaliar"
✅ Skill faz o trabalho ou declara composição com outros skills

**Problema:** Agents executam em fork isolado, não podem ser invocados por skills.

## AP-9: Sem Conexão com Knowledge
❌ Skill que não consulta nem atualiza knowledge files
✅ "Registre padrão descoberto em PATTERNS.md"

**Problema:** Quebra o ciclo de retroalimentação (princípio central do Engram).
