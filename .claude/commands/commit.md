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

5. Se a mudança é relevante para o knowledge, sugerir: "Quer rodar /learn para registrar?"

## Regras
- Mensagem SEMPRE em inglês
- Primeira linha: max 72 caracteres
- Escopo reflete o módulo/área afetada
- Se múltiplas mudanças não-relacionadas: sugerir commits separados
