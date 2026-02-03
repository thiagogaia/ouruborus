---
name: python-scripts
description: Validação e teste de scripts Python do Engram. Use quando criar, modificar ou debugar scripts em core/ ou .claude/skills/*/scripts/. Verifica shebang, docstring, argparse, funções isoladas, e execução sem erros.
---

# Python Scripts Validator

Validar e testar scripts Python internos do Engram.

## Propósito

Os scripts Python do Engram (genesis e evolution) são críticos para o funcionamento do sistema metacircular. Este skill garante que todos os scripts seguem os padrões do projeto e funcionam corretamente.

## Quando Ativar
- Ao criar novo script em `scripts/`
- Ao modificar script existente
- Ao debugar erro em script
- Antes de commit com mudanças em `.py`

## Workflow

1. **Identificar scripts alterados**
   ```bash
   git diff --name-only | grep '\.py$'
   ```

2. **Verificar estrutura do script** (para cada arquivo)
   - [ ] Shebang: `#!/usr/bin/env python3`
   - [ ] Docstring com description e usage
   - [ ] argparse para CLI (se aceita argumentos)
   - [ ] Funções isoladas e testáveis
   - [ ] `main()` no final
   - [ ] Guard `if __name__ == "__main__":`

3. **Verificar sintaxe**
   ```bash
   python3 -m py_compile path/to/script.py
   ```

4. **Testar execução básica**
   ```bash
   python3 path/to/script.py --help
   ```

5. **Verificar sem dependências externas**
   - Apenas stdlib Python 3.8+
   - Imports: json, os, sys, argparse, datetime, pathlib, re

## Regras

- NUNCA adicionar dependências externas (pip install)
- SEMPRE manter compatibilidade com Python 3.8+
- SEMPRE incluir docstring com usage
- Funções devem ser puras quando possível
- Erros devem ter mensagens claras

## Checklist de Validação

```
□ Shebang presente
□ Docstring com usage
□ argparse para CLI
□ main() com guard
□ Sintaxe OK (py_compile)
□ --help funciona
□ Imports são stdlib only
□ Mensagens de erro claras
```

## Output Esperado

```
✅ script.py
  ├── Shebang: OK
  ├── Docstring: OK
  ├── argparse: OK
  ├── Sintaxe: OK
  ├── --help: OK
  └── Imports: stdlib only

❌ outro.py
  ├── Shebang: FALTANDO
  └── Fix: Adicionar #!/usr/bin/env python3 na linha 1
```

## Scripts do Projeto

### Genesis (`core/genesis/scripts/` e `.claude/skills/engram-genesis/scripts/`)
- `analyze_project.py` — detecta stack do projeto
- `generate_component.py` — gera scaffolds
- `validate.py` — valida componentes contra schemas
- `register.py` — registra no manifest
- `compose.py` — compõe skills

### Evolution (`core/evolution/scripts/` e `.claude/skills/engram-evolution/scripts/`)
- `track_usage.py` — relatórios de uso
- `doctor.py` — health check
- `archive.py` — arquiva componentes
- `curriculum.py` — análise de cobertura
- `co_activation.py` — padrões de co-ativação
- `global_memory.py` — memória global entre projetos
