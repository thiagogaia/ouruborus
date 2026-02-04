---
name: domain-expert
description: Descoberta e gestão de conhecimento de domínio e negócio. Use
  quando encontrar termos do negócio, regras de negócio implícitas no código,
  restrições legais ou operacionais, ou quando precisar entender o "porquê"
  por trás de uma feature. Alimenta o DOMAIN.md.
---

# Domain Expert

Descobre, organiza e mantém o conhecimento de domínio do projeto.

## Workflow de Descoberta

### 1. Fontes de Conhecimento de Domínio
Extrair de (em ordem de confiabilidade):
- Código-fonte (nomes de entidades, validações, enums, constantes)
- Schema do banco de dados (tabelas, relações, constraints)
- Testes (cenários revelam regras de negócio)
- Comentários e documentação inline
- README e docs/
- Mensagens de commit que mencionam "regra", "requisito", "negócio"

### 2. O Que Registrar em DOMAIN.md

**Glossário**: Termos específicos do domínio
```
- **Lead**: Potencial cliente que demonstrou interesse. Não confundir com "contato".
- **Churn rate**: Percentual de clientes que cancelam por período.
```

**Regras de Negócio**: Invariantes que o código DEVE respeitar
```
- RN-001: Pedido só pode ser cancelado se status != "enviado"
- RN-002: Desconto máximo de 30% sem aprovação de gerente
```

**Entidades**: Mapa do domínio
```
Cliente → possui → Pedidos → contém → Itens → referencia → Produto
```

**Restrições**: Limites externos
```
- LGPD: dados pessoais devem ser anonimizáveis
- API externa: rate limit de 100 req/min
```

### 3. Validação com o Dev
Quando descobrir regra implícita no código:
- Apresentar ao dev: "Detectei que [código] implementa [regra]. Está correto?"
- Se confirmado → registrar em DOMAIN.md
- Se incorreto → pode ser bug, registrar em PRIORITY_MATRIX.md

## Regras
- NUNCA invente regras de negócio — só registre o que está no código ou foi confirmado
- SEMPRE use os termos do glossário ao se referir a entidades do domínio
- Se encontrar inconsistência entre código e domínio, reporte como possível bug
- Mantenha glossário em ordem alfabética
- Regras de negócio têm identificador único (RN-NNN)
