Executar code review dos arquivos alterados.

## Escopo

1. Identificar arquivos alterados:
   - Se $ARGUMENTS especifica arquivos: revisar esses
   - Senão: `git diff --name-only HEAD` para uncommitted
   - Se nada uncommitted: `git diff --name-only HEAD~1` para último commit

2. Ativar skill `code-reviewer` e executar o pipeline completo:
   - Camada 1: Correção
   - Camada 2: Padrões (consultando PATTERNS.md)
   - Camada 3: Segurança
   - Camada 4: Performance

3. Apresentar resultado para cada arquivo revisado.

4. Se encontrar padrão novo durante a review: registrar em PATTERNS.md.

5. Veredito final:
   - ✅ APROVADO — pode commitar
   - ⚠️ COM SUGESTÕES — pode commitar mas considere melhorias
   - ❌ REQUER MUDANÇAS — corrigir antes de commitar
