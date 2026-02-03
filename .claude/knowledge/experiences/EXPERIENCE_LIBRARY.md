# Experience Library
> Última atualização: 2026-02-03 (/init-engram)
> Soluções reutilizáveis descobertas durante o trabalho

## EXP-001: Validar Componente Antes de Registrar
- **Contexto**: Componente criado manualmente tinha erros no frontmatter
- **Stack**: Python scripts, manifest.json
- **Padrão**: PAT-007
- **Abordagem**: SEMPRE rodar validate.py antes de register.py. Corrigir todos os erros reportados. Só então registrar.
- **Resultado**: Sucesso — evita componentes inválidos no sistema
- **Data**: 2026-02-03

---

## EXP-002: Debugar Script Python do Engram
- **Contexto**: Script não estava funcionando como esperado
- **Stack**: Python 3, scripts do Engram
- **Abordagem**: Rodar com output explícito. Verificar se path está correto. Checar se Python 3.8+ está instalado.
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-003: Verificar Saúde do Sistema
- **Contexto**: Dúvida se Engram está funcionando corretamente
- **Stack**: /doctor, doctor.py
- **Abordagem**: Rodar `/doctor` ou `python3 doctor.py --project-dir .`. Score 90%+ = saudável.
- **Resultado**: Sucesso — diagnóstico rápido com sugestões de fix
- **Data**: 2026-02-03

---

## EXP-004: Ver Uso de Componentes
- **Contexto**: Não sei quais skills estão sendo usados
- **Stack**: track_usage.py
- **Abordagem**: Três reports disponíveis: health (completo), stale (obsoletos), summary (rápido).
- **Resultado**: Sucesso — visibilidade de métricas
- **Data**: 2026-02-03

---

## EXP-005: Criar Skill Customizado
- **Contexto**: Preciso de um skill novo para tarefa repetitiva
- **Stack**: genesis scripts
- **Padrão**: PAT-002
- **Abordagem**: generate_component.py → editar SKILL.md → validate.py → register.py
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-006: Atualizar Engram Sem Perder Customizações
- **Contexto**: Nova versão do Engram disponível
- **Stack**: setup.sh
- **Abordagem**: `./setup.sh --update /projeto` preserva knowledge e skills customizados
- **Resultado**: Sucesso
- **Data**: 2026-02-03

---

## EXP-007: Listar Todos os Componentes
- **Contexto**: Quero ver tudo que está instalado
- **Stack**: register.py
- **Abordagem**: `register.py --list --project-dir .`
- **Resultado**: Sucesso — lista com versão, uso, source
- **Data**: 2026-02-03

---

## EXP-008: Ciclo Completo /init-engram + /learn + /commit
- **Contexto**: Primeira inicialização completa do Engram em um projeto
- **Stack**: /init-engram, /learn, /commit
- **Abordagem**: 1) /init-engram popula knowledge files 2) Gera skills específicos 3) /commit com mensagem semântica 4) /learn registra uso e evolui
- **Resultado**: Sucesso — health 100%, 61 arquivos commitados, tracking funcionando
- **Data**: 2026-02-03

---

## EXP-009: Registrar Co-ativações de Skills
- **Contexto**: Quero saber quais skills são usados juntos para detectar oportunidades de composição
- **Stack**: co_activation.py
- **Abordagem**: `co_activation.py --log-session --skills skill1,skill2,skill3 --project-dir .`
- **Resultado**: Sucesso — sessão registrada para análise futura
- **Data**: 2026-02-03

---

## Regras da Library
- Máximo 50 experiências (descartar as mais antigas se necessário)
- Cada experiência: máximo 10 linhas
- Foco na abordagem, não no código específico
- Experiências mais recentes têm prioridade
- Populado pelo /learn quando interações são bem-sucedidas
