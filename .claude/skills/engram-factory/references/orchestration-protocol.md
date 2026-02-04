# Protocolo de Orquestração Runtime

Referência detalhada para o Claude decidir quando e como auto-criar
componentes durante uma sessão de trabalho.

## Decision Tree

```
Dev pede uma tarefa
│
├─ É trivial / conhecimento geral?
│  SIM → resolver diretamente, sem componente
│  NÃO ↓
│
├─ Listar agents em .claude/agents/ e skills em .claude/skills/
│  Algum cobre a expertise necessária?
│  SIM → ativar o componente existente
│  PARCIALMENTE → ativar + complementar inline (avaliar evolução no /learn)
│  NÃO ↓
│
├─ Existe na memória global (~/.engram/)?
│  SIM → importar via global_memory.py, adaptar, usar
│  NÃO ↓
│
├─ Existe template de stack em templates/stacks/?
│  SIM → usar como base, customizar, instalar
│  NÃO ↓
│
├─ Criar componente runtime
│  │
│  ├─ Será reutilizável?
│  │  NÃO → resolver inline, anotar para /learn
│  │  SIM ↓
│  │
│  ├─ Precisa de persona + julgamento?
│  │  SIM → criar AGENT
│  │  NÃO → criar SKILL
│  │
│  └─ Executar: anunciar → gerar → customizar → validar → registrar → usar
│
└─ Reportar no final da tarefa
```

## Critérios de "Expertise Necessária"

Um componente é necessário quando a tarefa exige:

### Criar Agent (persona especialista)
- Conhecimento profundo de uma tecnologia específica (ex: Oracle, Kubernetes, Redis)
- Capacidade de julgamento com trade-offs (ex: security auditor, performance tuner)
- Perspectiva de role diferente (ex: QA tester, UX reviewer, legal compliance)
- A resposta muda significativamente dependendo de quem "é" o respondente

### Criar Skill (processo repetível)
- Workflow com steps definidos que se aplica múltiplas vezes
- Padrões de código específicos de uma tecnologia/lib
- Templates ou scaffolds que seguem um formato fixo
- Checklists ou validações com critérios objetivos

### NÃO criar (resolver inline)
- Perguntas factuais simples ("qual o tipo de retorno de X?")
- Tarefas pequenas e pontuais sem reuso
- Coisas que o conhecimento base do Claude já cobre bem
- Tasks que levam < 5 minutos e não vão se repetir

## Fluxo Detalhado: Criação de Agent Runtime

### Exemplo: "Migrar autenticação de Lucia para Better Auth"

```
1. DETECTAR
   Claude avalia: "preciso de expertise profunda em Better Auth,
   migração de auth providers, e session management. O db-expert
   cobre banco mas não auth. Nenhum agent de auth existe."

2. ANUNCIAR
   "⚡ Esta tarefa exige expertise em migração de auth providers que
    nenhum agent atual cobre. Vou criar o agent `auth-migration-expert`
    para guiar a migração de Lucia → Better Auth."

3. GERAR
   python3 .claude/skills/engram-genesis/scripts/generate_component.py \
     --type agent --name auth-migration-expert --project-dir .

4. CUSTOMIZAR (Claude edita o scaffold)

   ---
   name: auth-migration-expert
   description: Especialista em migração de sistemas de autenticação.
     Invoque para migrar entre providers de auth, preservar sessões
     existentes, e garantir zero-downtime na transição.
   tools:
     - Read
     - Grep
     - Glob
   ---

   Você é um especialista em migração de sistemas de autenticação.

   ## Contexto desta Migração
   - De: Lucia (session-based, SQLite adapter)
   - Para: Better Auth (session-based, Prisma adapter)
   - Prioridade: preservar sessões ativas dos usuários

   ## Checklist de Migração
   1. Mapear schema de sessões: Lucia vs Better Auth
   2. Criar migration de schema (adicionar campos Better Auth)
   3. Script de data migration (converter sessões existentes)
   4. Atualizar middleware de auth
   5. Atualizar Server Actions que usam getSession()
   6. Atualizar Client Components que usam useSession()
   7. Testar: login, logout, refresh, protected routes
   8. Remover dependências de Lucia

   ## Regras
   - NUNCA dropar tabelas de sessão antes de migrar dados
   - SEMPRE manter backward compatibility durante transição
   - Testar com usuário existente E usuário novo
   - Registrar decisão em ADR_LOG.md

5. VALIDAR
   python3 .claude/skills/engram-genesis/scripts/validate.py \
     --type agent --path .claude/agents/auth-migration-expert.md

6. REGISTRAR
   python3 .claude/skills/engram-genesis/scripts/register.py \
     --type agent --name auth-migration-expert --source runtime --project-dir .

7. USAR
   Claude delega a tarefa ao agent recém-criado.

8. REPORTAR
   "🐍 Criei agent 'auth-migration-expert' para guiar a migração
    Lucia → Better Auth. Ele está em .claude/agents/auth-migration-expert.md.
    O /learn vai avaliar se vale manter para futuras migrações de auth."
```

## Fluxo Detalhado: Criação de Skill Runtime

### Exemplo: "Implementar upload de imagens com S3"

```
1. DETECTAR
   Claude avalia: "preciso de workflow de upload S3 com presigned URLs,
   resize, e integração com o form. Nenhum skill cobre storage/upload."

2. ANUNCIAR
   "⚡ Nenhum skill cobre integração com S3. Vou criar `s3-upload-patterns`
    com o workflow completo para o projeto."

3. GERAR + CUSTOMIZAR

   ---
   name: s3-upload-patterns
   description: Padrões de upload de arquivos com AWS S3. Use quando
     implementar upload de imagens, documentos ou qualquer arquivo
     que vai para S3, incluindo presigned URLs e resize.
   ---

   # S3 Upload Patterns

   ## Workflow de Upload
   1. Client solicita presigned URL via Server Action
   2. Server Action gera URL com AWS SDK (expiração: 5min)
   3. Client faz PUT direto no S3 (não passa pelo server)
   4. Client confirma upload via Server Action
   5. Server valida: arquivo existe? tipo correto? tamanho ok?
   6. Server registra no banco (url, tipo, tamanho, uploadedBy)

   ## Resize de Imagem
   - Usar sharp no Server Action de confirmação
   - Gerar: thumb (150x150), medium (600x600), original
   - Padrão de nomes: {id}/thumb.webp, {id}/medium.webp, {id}/original.webp

   ## Segurança
   - Presigned URLs com expiração curta (300s)
   - Validar Content-Type no presigned URL
   - Limitar tamanho máximo (10MB imagem, 50MB documento)
   - Bucket privado, acesso via CloudFront com signed cookies

   ## Regras
   - NUNCA fazer upload passando pelo servidor Node (memória)
   - SEMPRE validar tipo e tamanho no server DEPOIS do upload
   - SEMPRE gerar webp para imagens (menor, melhor quality/size)

4-8. (mesmos steps: validar, registrar, usar, reportar)
```

## Rastreamento de Componentes Runtime

Componentes criados em runtime são marcados com `source: runtime` no manifest.
Isso permite que o `/learn` os avalie especificamente:

### No /learn, para cada componente runtime:

```
1. Foi usado durante a sessão que o criou? (deveria ser sim)
2. O dev editou depois? (sinal de que precisa refinamento)
3. É reutilizável para futuras sessões?
   SIM → manter, source evolui para "genesis" no próximo /learn
   NÃO → avaliar archive
4. Pode ser mergeado com componente existente?
   SIM → evoluir o existente, arquivar o runtime
```

## Limites

- Máximo 2 componentes criados por sessão (se precisar de mais, agrupar)
- Se o mesmo tipo de componente runtime é criado em 3+ projetos → exportar para global
- Se criou agent e nunca mais usou → /learn propõe archive
- Não criar componente para tarefa que leva < 5min e não se repete
