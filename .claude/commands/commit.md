Criar um git commit com mensagem semântica.

1. Execute `git status` e `git diff --stat` para ver o que mudou

2. Analise as mudanças e gere uma mensagem de commit seguindo Conventional Commits:

```
tipo(escopo): descrição curta em inglês

corpo opcional explicando o "porquê"
```

Tipos: feat, fix, refactor, docs, test, chore, style, perf, ci, build

3. Apresente a mensagem proposta ao dev e pergunte se quer ajustar

4. Execute:
```bash
git add -A
git commit -m "mensagem"
```

5. **Atualizar CHANGELOG.md** se algum arquivo em `core/` foi modificado:
   - Leia o `CHANGELOG.md` da raiz
   - Adicione a mudança na seção `[Unreleased]`, na categoria correta:
     - **Added** — funcionalidade nova
     - **Changed** — mudança em funcionalidade existente
     - **Deprecated** — funcionalidade marcada para remoção
     - **Removed** — funcionalidade removida
     - **Fixed** — correção de bug
   - Formato da entrada: `- Descrição curta em inglês (\`hash curto\`)`
   - Stage e amend o commit para incluir o CHANGELOG:
     ```bash
     git add CHANGELOG.md
     git commit --amend --no-edit
     ```
   - Se nenhum arquivo em `core/` mudou, pular este passo

6. Se a mudança é relevante para o knowledge, sugerir: "Quer rodar /learn para registrar?"

## Regras
- Mensagem SEMPRE em inglês
- Primeira linha: max 72 caracteres
- Escopo reflete o módulo/área afetada
- Se múltiplas mudanças não-relacionadas: sugerir commits separados
- CHANGELOG.md só rastreia mudanças em `core/` (o DNA do Engram)
