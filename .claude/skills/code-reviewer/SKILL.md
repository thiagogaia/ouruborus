---
name: code-reviewer
description: Review de código seguindo pipeline de qualidade. Use quando
  executar /review, antes de commits, ou quando pedir para revisar código.
  Pipeline sequencial — correção → padrões → segurança → performance.
---

# Code Reviewer

Review sistemático de código em 4 camadas.

## Pipeline de Review

Executar em SEQUÊNCIA — não avançar se a camada anterior tem ❌ críticos.

### Camada 1: Correção
O código faz o que deveria?
- [ ] Lógica correta (edge cases cobertos?)
- [ ] Tipagem correta (se TypeScript/Python typed)
- [ ] Error handling (exceções tratadas?)
- [ ] Null/undefined safety
- [ ] Testes existem e passam?

### Camada 2: Padrões
O código segue os padrões do projeto?
- [ ] Consultar `PATTERNS.md` para padrões aprovados
- [ ] Naming conventions consistentes
- [ ] Estrutura de arquivos no lugar certo
- [ ] Imports organizados
- [ ] Sem código duplicado (DRY)
- [ ] Componentes no tamanho certo (não muito grandes)

### Camada 3: Segurança
O código é seguro?
- [ ] Input validation em todas as entradas externas
- [ ] Sem secrets hardcoded
- [ ] SQL injection / XSS / CSRF prevenidos
- [ ] Auth/authz checks nas rotas protegidas
- [ ] Rate limiting em endpoints públicos
- [ ] Dados sensíveis não logados

### Camada 4: Performance
O código é eficiente?
- [ ] Sem queries N+1 (loops com DB calls)
- [ ] Índices de banco para queries frequentes
- [ ] Sem re-renders desnecessários (React)
- [ ] Assets otimizados (images, bundles)
- [ ] Caching onde apropriado

## Output

Para cada arquivo revisado:
```
📝 [arquivo]
  ✅ Camada 1: Correção — OK
  ⚠️  Camada 2: Padrões — 1 sugestão
     → Extrair lógica do handler para service (PAT-003)
  ✅ Camada 3: Segurança — OK
  ❌ Camada 4: Performance — 1 problema
     → Query N+1 na linha 45: usar include/join

Veredito: ⚠️ APROVADO COM SUGESTÕES
```

## Regras
- SEMPRE consulte PATTERNS.md antes de comentar sobre padrões
- Se encontrar padrão novo durante review: registrar em PATTERNS.md
- ❌ = blocker (deve corrigir antes de merge)
- ⚠️ = sugestão (pode mergear mas deveria corrigir)
- ✅ = aprovado
- Veredito possíveis: ✅ APROVADO | ⚠️ APROVADO COM SUGESTÕES | ❌ REQUER MUDANÇAS
