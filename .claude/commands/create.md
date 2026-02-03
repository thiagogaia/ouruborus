Criar um novo componente Engram sob demanda.

Uso: `/create [tipo] [nome]`
Exemplos:
- `/create skill api-validator`
- `/create agent performance-expert`
- `/create command deploy`

## Workflow

1. Interpretar $ARGUMENTS:
   - Primeiro argumento: tipo (skill | agent | command)
   - Segundo argumento: nome (kebab-case)
   - Se argumentos insuficientes, perguntar ao dev

2. Validar que o nome é kebab-case e não existe ainda

3. Ativar skill `engram-genesis`:
   - Consultar schema correspondente
   - Gerar scaffold via `generate_component.py`
   - Perguntar ao dev o propósito e triggers
   - Customizar o conteúdo gerado
   - Validar via `validate.py`
   - Registrar via `register.py`

4. Confirmar criação e mostrar:
   - Onde o arquivo foi criado
   - O que o dev deve customizar
   - Como testar
