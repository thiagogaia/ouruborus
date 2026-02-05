---
name: fintech-domain
description: Dominio de pagamentos e fintech. Use quando trabalhar com entidades de
  pagamento (Client, Payment Operator, Merchant), fluxos transacionais
  (Order, Charge, Transaction, Settlement), compliance (CERC, PCI, PLD, KYC),
  integracao com adquirentes, split de pagamento, antifraude ou chargeback.
---

# Fintech Domain

## Proposito

Guia de dominio para projetos de pagamentos/fintech. Documenta entidades, fluxos,
regras de negocio e compliance regulatorio. Essencial para entender o "porque"
por tras de validacoes, estados e restricoes que parecem arbitrarias mas vem
de regulacao financeira.

## Entidades Fundamentais

### Hierarquia

```
Client (CNPJ/marca)
└── Payment Operator (1:N)
    └── Business Operator (1:N)
        ├── Seller/Merchant (1:N)
        └── Commissioned Partner (1:N)
```

### Client
- Entidade comercial/juridica (CNPJ, marca)
- Agrupamento logico — nao opera diretamente
- Ex: holding, grupo empresarial

### Payment Operator
- Entidade que OPERA pagamentos
- Responsabilidades:
  - Contratos com adquirentes (credenciais, taxas)
  - Liquidacao financeira
  - Conformidade regulatoria (PCI, PLD, CERC)
  - Gerenciamento de risco e chargebacks
- Regra: adquirentes pertencem APENAS ao Payment Operator

### Business Operator
- Entidade que opera o contexto COMERCIAL
- Responsabilidades:
  - Integracao via API
  - Criacao de pedidos / checkout
  - Regras comerciais (precos, split)
  - Isolamento de saldo
- Regra: vinculado a um unico Payment Operator

### Seller (Merchant)
- Dono do produto/servico vendido
- Responsavel por entrega e relacao com consumidor
- Cadastro requer: CNPJ/CPF, dados bancarios, MCC (codigo de atividade)

### Commissioned Partner
- Participante financeiro do split SEM propriedade do produto
- Ex: afiliados, influenciadores, parceiros comerciais

## Modos de Operacao

### Gateway (Basic)
- Cliente atua como Payment Operator proprio
- Apenas transaciona e retorna
- Cobranca via fatura mensal (nao desconta na venda)
- Sem controle de saldo, regulatorio ou antifraude

### Subadquirente (Pro)
- Plataforma atua como Payment Operator
- Cliente atua como Business Operator
- Stack completa: saldo, regulatorio, antifraude, KYC
- Taxas por pedido, possibilidade de desconto na liquidacao

## Fluxo Transacional

### Fluxo Principal (Pedido → Pagamento)

```
1. Business Operator cria Order (pedido)
2. Order gera Charge (cobranca)
3. Charge envia para Orquestrador
4. Orquestrador roteia para Adquirente correto
5. Adquirente processa (autoriza/captura)
6. Transaction registrada
7. Webhook notifica resultado
8. Settlement (liquidacao) na data programada
```

### Estados de Transacao

```
pending → authorized → captured → settled
                    → cancelled
                    → refunded (parcial ou total)
       → declined
       → error
```

### Meios de Pagamento

- **Cartao de Credito**: autorizar → capturar → liquidar
- **PIX**: pagamento instantaneo (sem captura separada)
- **Boleto**: emitir → aguardar pagamento → confirmar
- **Wallet**: debito de saldo interno

Cada meio tem adquirentes diferentes e fluxos proprios.

## Split de Pagamento

Distribuicao do valor entre participantes:

```
Valor total: R$ 100,00
├── Seller: R$ 70,00
├── Afiliado: R$ 15,00
├── Plataforma (Business Op): R$ 10,00
└── Payment Operator (taxa): R$ 5,00
```

Regras:
- Soma das partes DEVE ser igual ao total
- Payment Operator desconta taxa ANTES do repasse
- Saldo de cada participante e isolado por Business Operator
- Split definido no momento da criacao do pedido

## Compliance e Regulatorio

### CERC (Centralizadora de Recebiveis)
- Registro obrigatorio de agenda de recebiveis
- Layouts padrao: AP001 (opt-in), AP002 (unidades recebiveis), AP024 (protocolo), AP025 (liquidacao)
- Workers dedicados processam filas de cada layout
- Conciliacao periodica (a cada 15min + semanal)

### PCI DSS
- Dados de cartao NUNCA em texto plano
- Tokenizacao obrigatoria (nunca armazenar PAN completo)
- Credenciais de adquirentes criptografadas (Fernet + Secrets Manager)
- Logs NAO podem conter dados de cartao

### KYC (Know Your Customer)
- Validacao de CPF/CNPJ obrigatoria no cadastro
- Consulta a bureaus (BigBoost, ABECS)
- Validacao de MCC (Merchant Category Code)
- Score de risco influencia limites transacionais

### PLD (Prevencao a Lavagem de Dinheiro)
- Monitoramento de transacoes atipicas
- Reportes obrigatorios ao COAF
- Limites de transacao por perfil de risco

### Antifraude
- Analise pre-autorizacao (antes de enviar ao adquirente)
- Decision Manager (aprovado, rejeitado, revisao pendente)
- Inputs: historico do comprador, device fingerprint, dados do pedido
- Servico deve ser NON-BLOCKING para nao travar checkout

## Chargeback

```
Comprador contesta → Adquirente notifica → Chargeback criado
    → Analise interna → Contestar OU Aceitar
    → Se contestar: enviar evidencias ao adquirente
    → Resolucao final: mantido OU revertido
```

Regras:
- Validar duplicidade (mesmo cartao + valor + periodo)
- Prazo para contestacao: varia por bandeira (30-120 dias)
- Impacto financeiro: debitar do saldo do Seller
- Taxa de chargeback alta = risco de descredenciamento

## Integracao com Adquirentes

### Multi-adquirente
Roteamento inteligente baseado em:
- Tipo de transacao (credito, pix, boleto)
- Bandeira do cartao
- Taxa do adquirente
- Disponibilidade (fallback)

### Adquirentes Comuns
- **Credito**: Adyen, Cielo, MercadoPago, PagSeguro, Yuno, WorldPay
- **PIX**: Iugu, Adyen, Bradesco, BV
- **Boleto**: Bradesco (mTLS)

### Webhook de Adquirentes
- Cada adquirente tem formato proprio de webhook
- Servico unificado recebe → normaliza → encaminha para fila (SQS)
- Idempotencia obrigatoria (mesmo webhook pode vir N vezes)

## Regras

- NUNCA logar dados de cartao (PAN, CVV, validade)
- SEMPRE validar idempotencia em transacoes (idempotency key)
- Tratar valores financeiros como inteiros (centavos), NUNCA float
- Split deve somar 100% do valor — validar ANTES de processar
- Chargeback: verificar duplicidade ANTES de criar
- KYC/Antifraude: non-blocking (nao travar o fluxo principal)
- Credenciais de adquirentes: sempre criptografadas, nunca em env vars

## Output Esperado

Ao analisar logica de pagamentos, reportar:
```
Entidade: [qual entidade de dominio]
Fluxo: [em qual ponto do fluxo transacional]
Regra de Negocio: [qual regra se aplica e por que]
Compliance: [se ha impacto regulatorio]
Risco: [se ha risco financeiro/operacional]
```
