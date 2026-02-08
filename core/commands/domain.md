---
name: domain
description: Analisar e registrar conhecimento de domínio. Use para descobrir regras
  de negócio, mapear entidades, ou atualizar o glossário.
args: "[termo, pergunta ou 'analyze' para análise completa]"
---

# /domain - Análise de Domínio

Você é o Domain Expert. Analise conhecimento de domínio e registre no cérebro via `brain.add_memory()`. DOMAIN.md é genesis-only.

## Entrada do Usuário
$ARGUMENTS

## Workflow

### Se argumento é um termo ou pergunta específica:
1. **Buscar no cérebro**: `.claude/brain/.venv/bin/python3 .claude/brain/recall.py "$ARGUMENTS" --type concept --top 5`
2. **Verificar DOMAIN.md**: O termo já está documentado?
3. **Se não está**: Buscar no código (grep por uso, validações, comentários)
4. **Propor definição** ao usuário para validação
5. **Se validado**: Registrar no cérebro via `brain.add_memory(labels=["Concept", "Glossary"])`

### Se argumento é "analyze" ou vazio:
1. **Invocar domain-analyst** via Task tool para análise completa do codebase
2. **Comparar** descobertas com DOMAIN.md atual
3. **Listar gaps**: termos usados no código mas não documentados
4. **Propor atualizações** para aprovação do usuário

## O Que Registrar

### Glossário (ordem alfabética)
```markdown
- **Termo**: Definição clara. Contexto de uso se necessário.
```

### Regras de Negócio (RN-NNN)
```markdown
- **RN-XXX**: Descrição da invariante que o código DEVE respeitar.
  - Fonte: arquivo:linha ou "confirmado pelo dev"
```

### Entidades
```markdown
EntidadeA → relação → EntidadeB → relação → EntidadeC
```

### Restrições
```markdown
- Tipo (legal/técnica/operacional): descrição do limite
```

## Regras
- NUNCA invente regras — só registre o que está no código ou foi confirmado
- SEMPRE valide com o usuário antes de registrar
- Use terminologia consistente com o glossário existente
- Inconsistências código/domínio podem indicar bugs — reporte

## Output
Após análise, mostre:
1. **Descobertas**: O que foi encontrado
2. **Proposta**: O que será registrado no cérebro
3. **Ação**: Aguardar confirmação do usuário antes de editar

## Exemplos de Uso
```bash
/domain Lead                    # O que é Lead neste projeto?
/domain regra de cancelamento   # Qual a regra para cancelar pedido?
/domain analyze                 # Análise completa do codebase
/domain                         # Mesmo que analyze
```
