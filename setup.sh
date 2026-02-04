#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# 🐍 Engram v3 — Auto-Installer (Metacircular)
#    Sistema de memória persistente para Claude Code
#    Com Cérebro Organizacional (grafo + embeddings)
# ═══════════════════════════════════════════════════════════════
# Uso:
#   ./setup.sh                  → instala no diretório atual
#   ./setup.sh /meu/projeto     → instala no diretório especificado
#   ./setup.sh --help           → mostra ajuda
#   ./setup.sh --update /proj   → atualiza core sem tocar knowledge
#   ./setup.sh --uninstall /proj → remove Engram
#
# O que faz (v3 — com cérebro organizacional):
#   1. Detecta a stack do projeto automaticamente
#   2. Instala o DNA (schemas) + Genesis (motor de auto-geração)
#   3. Instala seeds universais + Evolution (motor de evolução)
#   4. Instala Brain (cérebro organizacional com grafo + embeddings)
#   5. Gera CLAUDE.md customizado e settings.json
#   6. O /init-engram popula o cérebro e gera componentes sob demanda
# ═══════════════════════════════════════════════════════════════

VERSION="3.0.0"

# ── Argument handling ─────────────────────────────────────────

show_help() {
    echo ""
    echo "🐍 Engram v${VERSION} — Persistent Memory for Claude Code"
    echo ""
    echo "Usage:"
    echo "  ./setup.sh [OPTIONS] [TARGET_DIR]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help"
    echo "  -v, --version     Show version"
    echo "  --update          Update core without touching knowledge/customizations"
    echo "  --uninstall       Remove Engram from project"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh                    # Install in current directory"
    echo "  ./setup.sh /path/to/project   # Install in specific directory"
    echo "  ./setup.sh --update .         # Update core in current directory"
    echo ""
    exit 0
}

show_version() {
    echo "Engram v${VERSION}"
    exit 0
}

MODE="install"
TARGET_DIR=""

for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help ;;
        -v|--version) show_version ;;
        --update) MODE="update" ;;
        --uninstall) MODE="uninstall" ;;
        *) TARGET_DIR="$arg" ;;
    esac
done

TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Colors ────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  🐍 Engram v${VERSION} — Persistent Memory for Claude Code${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}▸${NC} $1"; }
print_warn() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${YELLOW}⚠${NC} $1"; }
print_done() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}✓${NC} $1"; }

# ── Uninstall ─────────────────────────────────────────────────

do_uninstall() {
    print_header
    echo -e "  ${YELLOW}⚠ Removendo Engram de: ${BOLD}$TARGET_DIR${NC}"
    echo ""
    read -p "  Tem certeza? Isso remove .claude/ e CLAUDE.md (S/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "  Cancelado."
        exit 0
    fi
    [[ -d "$TARGET_DIR/.claude" ]] && rm -rf "$TARGET_DIR/.claude" && print_done "Removido .claude/"
    [[ -f "$TARGET_DIR/CLAUDE.md" ]] && rm "$TARGET_DIR/CLAUDE.md" && print_done "Removido CLAUDE.md"
    print_done "Engram removido."
    exit 0
}

[[ "$MODE" == "uninstall" ]] && do_uninstall

# ═══════════════════════════════════════════════════════════════
# STACK DETECTION (same as v1, reused)
# ═══════════════════════════════════════════════════════════════

detect_stack() {
    print_step "Analisando projeto em: ${BOLD}$TARGET_DIR${NC}"
    echo ""

    LANG_NODE=false; LANG_PYTHON=false; LANG_PHP=false
    LANG_RUST=false; LANG_GO=false; LANG_RUBY=false

    [[ -f "$TARGET_DIR/package.json" ]] && LANG_NODE=true
    [[ -f "$TARGET_DIR/requirements.txt" || -f "$TARGET_DIR/pyproject.toml" || -f "$TARGET_DIR/Pipfile" ]] && LANG_PYTHON=true
    [[ -f "$TARGET_DIR/composer.json" ]] && LANG_PHP=true
    [[ -f "$TARGET_DIR/Cargo.toml" ]] && LANG_RUST=true
    [[ -f "$TARGET_DIR/go.mod" ]] && LANG_GO=true
    [[ -f "$TARGET_DIR/Gemfile" ]] && LANG_RUBY=true

    FRAMEWORK=""; FRAMEWORK_VERSION=""
    if $LANG_NODE && [[ -f "$TARGET_DIR/package.json" ]]; then
        PKG=$(cat "$TARGET_DIR/package.json")
        echo "$PKG" | grep -q '"next"' && FRAMEWORK="nextjs"
        echo "$PKG" | grep -q '"nuxt"' && FRAMEWORK="nuxt"
        echo "$PKG" | grep -q '"@angular/core"' && FRAMEWORK="angular"
        echo "$PKG" | grep -q '"svelte"' && FRAMEWORK="sveltekit"
        echo "$PKG" | grep -q '"vue"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="vue"
        echo "$PKG" | grep -q '"react"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="react"
        echo "$PKG" | grep -q '"express"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="express"
        [[ "$FRAMEWORK" == "nextjs" ]] && FRAMEWORK_VERSION=$(echo "$PKG" | grep -oP '"next":\s*"[^"]*"' | grep -oP '[\d.]+' | head -1) || true
    fi
    $LANG_PYTHON && [[ -f "$TARGET_DIR/manage.py" ]] && FRAMEWORK="django"
    $LANG_PYTHON && grep -ql "fastapi" "$TARGET_DIR/requirements.txt" 2>/dev/null && FRAMEWORK="fastapi"

    ORM=""; DB=""
    [[ -d "$TARGET_DIR/prisma" || -f "$TARGET_DIR/prisma/schema.prisma" ]] && ORM="prisma"
    if $LANG_NODE && [[ -f "$TARGET_DIR/package.json" ]]; then
        echo "$PKG" | grep -q '"drizzle-orm"' && ORM="drizzle"
        echo "$PKG" | grep -q '"typeorm"' && ORM="typeorm"
        echo "$PKG" | grep -q '"mongoose"' && ORM="mongoose" && DB="mongodb"
    fi
    [[ -f "$TARGET_DIR/.env.example" ]] && grep -qi "postgres" "$TARGET_DIR/.env.example" 2>/dev/null && DB="postgresql"

    HAS_TAILWIND=false; HAS_SHADCN=false; UI_FRAMEWORK=""; AUTH=""
    HAS_TYPESCRIPT=false; TEST_FRAMEWORK=""
    HAS_DOCKER=false; PKG_MANAGER="npm"; IS_MONOREPO=false

    [[ -f "$TARGET_DIR/tsconfig.json" ]] && HAS_TYPESCRIPT=true
    [[ -f "$TARGET_DIR/Dockerfile" || -f "$TARGET_DIR/docker-compose.yml" ]] && HAS_DOCKER=true
    [[ -f "$TARGET_DIR/pnpm-lock.yaml" ]] && PKG_MANAGER="pnpm"
    [[ -f "$TARGET_DIR/yarn.lock" ]] && PKG_MANAGER="yarn"
    [[ -f "$TARGET_DIR/bun.lockb" || -f "$TARGET_DIR/bun.lock" ]] && PKG_MANAGER="bun"

    if $LANG_NODE && [[ -f "$TARGET_DIR/package.json" ]]; then
        echo "$PKG" | grep -q '"tailwindcss"' && HAS_TAILWIND=true
        [[ -f "$TARGET_DIR/components.json" ]] && HAS_SHADCN=true && UI_FRAMEWORK="shadcn"
        echo "$PKG" | grep -q '"vitest"' && TEST_FRAMEWORK="vitest"
        echo "$PKG" | grep -q '"jest"' && [[ -z "$TEST_FRAMEWORK" ]] && TEST_FRAMEWORK="jest"
        echo "$PKG" | grep -q '"next-auth\|@auth/core"' && AUTH="nextauth"
        echo "$PKG" | grep -q '"better-auth"' && AUTH="better-auth"
    fi

    echo -e "  ${BOLD}Stack Detectada:${NC}"
    $LANG_NODE && echo -e "    ${GREEN}✓${NC} Node.js (${PKG_MANAGER})"
    $LANG_PYTHON && echo -e "    ${GREEN}✓${NC} Python"
    $LANG_PHP && echo -e "    ${GREEN}✓${NC} PHP"
    $LANG_RUST && echo -e "    ${GREEN}✓${NC} Rust"
    $LANG_GO && echo -e "    ${GREEN}✓${NC} Go"
    $LANG_RUBY && echo -e "    ${GREEN}✓${NC} Ruby"
    [[ -n "$FRAMEWORK" ]] && echo -e "    ${GREEN}✓${NC} Framework: ${BOLD}$FRAMEWORK${NC} ${FRAMEWORK_VERSION:+v$FRAMEWORK_VERSION}"
    [[ -n "$ORM" ]] && echo -e "    ${GREEN}✓${NC} ORM: $ORM"
    [[ -n "$DB" ]] && echo -e "    ${GREEN}✓${NC} Database: $DB"
    $HAS_TYPESCRIPT && echo -e "    ${GREEN}✓${NC} TypeScript"
    $HAS_DOCKER && echo -e "    ${GREEN}✓${NC} Docker"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# INSTALL CORE (DNA + Genesis + Seeds) — the v2 approach
# ═══════════════════════════════════════════════════════════════

install_core() {
    print_step "Instalando core (DNA + Genesis + Seeds)..."

    local CLAUDE_DIR="$TARGET_DIR/.claude"
    mkdir -p "$CLAUDE_DIR"/{skills,agents,commands,knowledge/{context,priorities,patterns,decisions,domain,experiences},schemas,versions}

    # 1. Schemas (DNA)
    cp -r "$SCRIPT_DIR/core/schemas/"* "$CLAUDE_DIR/schemas/"
    print_done "Schemas instalados (DNA do sistema)"

    # 2. Genesis skill (motor de auto-geração)
    cp -r "$SCRIPT_DIR/core/genesis" "$CLAUDE_DIR/skills/engram-genesis"
    chmod +x "$CLAUDE_DIR/skills/engram-genesis/scripts/"*.py 2>/dev/null || true
    print_done "Genesis skill instalado (motor de auto-geração)"

    # 3. Evolution skill (motor de evolução)
    cp -r "$SCRIPT_DIR/core/evolution" "$CLAUDE_DIR/skills/engram-evolution"
    chmod +x "$CLAUDE_DIR/skills/engram-evolution/scripts/"*.py 2>/dev/null || true
    print_done "Evolution skill instalado (motor de evolução)"

    # 4. Seeds (skills universais) — if they exist
    if [[ -d "$SCRIPT_DIR/core/seeds" ]]; then
        for seed in "$SCRIPT_DIR/core/seeds"/*/; do
            [[ -d "$seed" ]] && cp -r "$seed" "$CLAUDE_DIR/skills/"
        done
        print_done "Seeds universais instalados"
    fi

    # 5. Agents (universal templates)
    if [[ -d "$SCRIPT_DIR/core/agents" ]]; then
        cp "$SCRIPT_DIR/core/agents/"*.md "$CLAUDE_DIR/agents/" 2>/dev/null || true
        print_done "Agents universais instalados"
    fi

    # 6. Commands
    cp "$SCRIPT_DIR/core/commands/"*.md "$CLAUDE_DIR/commands/" 2>/dev/null || true
    print_done "Commands instalados (13 commands)"

    # 7. Knowledge templates
    local TODAY=$(date +%Y-%m-%d)
    for tmpl in "$SCRIPT_DIR/templates/knowledge/"*.tmpl; do
        [[ -f "$tmpl" ]] || continue
        local BASENAME=$(basename "$tmpl" .md.tmpl)
        local SUBDIR=""
        case "$BASENAME" in
            CURRENT_STATE) SUBDIR="context" ;;
            PRIORITY_MATRIX) SUBDIR="priorities" ;;
            PATTERNS) SUBDIR="patterns" ;;
            ADR_LOG) SUBDIR="decisions" ;;
            DOMAIN) SUBDIR="domain" ;;
            EXPERIENCE_LIBRARY) SUBDIR="experiences" ;;
        esac
        if [[ -n "$SUBDIR" ]]; then
            local DEST="$CLAUDE_DIR/knowledge/$SUBDIR/$BASENAME.md"
            if [[ ! -f "$DEST" ]]; then
                sed "s/\${DATE}/$TODAY/g" "$tmpl" > "$DEST"
            fi
        fi
    done
    print_done "Knowledge templates inicializados (6 arquivos)"

    # 8. Initialize manifest
    if [[ ! -f "$CLAUDE_DIR/manifest.json" ]]; then
        cat > "$CLAUDE_DIR/manifest.json" << MANIFEST_EOF
{
  "engram_version": "${VERSION}",
  "installed_at": "$(date -Iseconds)",
  "last_updated": "$(date -Iseconds)",
  "components": {
    "skills": {
      "engram-genesis": {
        "version": "1.0.0",
        "source": "core",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "engram-evolution": {
        "version": "1.0.0",
        "source": "core",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "project-analyzer": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "knowledge-manager": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "domain-expert": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "priority-engine": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "code-reviewer": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      },
      "engram-factory": {
        "version": "1.0.0",
        "source": "seed",
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)",
        "activations": 0,
        "last_used": null,
        "health": "active"
      }
    },
    "agents": {},
    "commands": {}
  },
  "evolution": {
    "total_generations": 0,
    "total_evolutions": 0,
    "total_archived": 0
  }
}
MANIFEST_EOF
        print_done "Manifest inicializado"
    fi

    # 9. Save version
    echo "$VERSION" > "$CLAUDE_DIR/.engram-version"

    # 10. Install brain (organizational memory)
    if [[ -d "$SCRIPT_DIR/.claude/brain" ]]; then
        mkdir -p "$CLAUDE_DIR/brain/state"
        mkdir -p "$CLAUDE_DIR/memory"/{episodes,concepts,patterns,decisions,people,domains}
        mkdir -p "$CLAUDE_DIR/consolidated"
        mkdir -p "$CLAUDE_DIR/archive"
        cp "$SCRIPT_DIR/.claude/brain/"*.py "$CLAUDE_DIR/brain/" 2>/dev/null || true
        cp "$SCRIPT_DIR/.claude/brain/"*.sh "$CLAUDE_DIR/brain/" 2>/dev/null || true
        cp "$SCRIPT_DIR/.claude/brain/"*.md "$CLAUDE_DIR/brain/" 2>/dev/null || true
        cp "$SCRIPT_DIR/.claude/brain/"*.json "$CLAUDE_DIR/brain/" 2>/dev/null || true
        chmod +x "$CLAUDE_DIR/brain/"*.py "$CLAUDE_DIR/brain/"*.sh 2>/dev/null || true
        print_done "Brain instalado (cérebro organizacional)"
    fi
}

# ═══════════════════════════════════════════════════════════════
# INSTALL BRAIN DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

install_brain_deps() {
    local CLAUDE_DIR="$TARGET_DIR/.claude"
    local VENV_DIR="$CLAUDE_DIR/brain/.venv"

    if [[ ! -d "$CLAUDE_DIR/brain" ]]; then
        return  # Brain not installed
    fi

    print_step "Instalando dependências do Brain..."

    # Check if python3 is available
    if ! command -v python3 &>/dev/null; then
        print_warn "Python3 não encontrado. Dependências do Brain não instaladas."
        print_warn "Instale Python3 e execute novamente, ou instale manualmente:"
        print_warn "  pip install networkx numpy sentence-transformers"
        return
    fi

    # Get Python version for venv package name
    local PYTHON_VERSION
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")

    # Function to check if we're on Debian/Ubuntu (includes WSL)
    is_debian_based() {
        [[ -f /etc/debian_version ]] || [[ -f /etc/lsb-release ]] || grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null
    }

    # Function to install python3-venv on Debian/Ubuntu
    install_venv_package() {
        local PKG="python${PYTHON_VERSION}-venv"
        print_step "Tentando instalar ${PKG} automaticamente..."

        if command -v sudo &>/dev/null; then
            # Try with sudo
            if sudo -n true 2>/dev/null; then
                # Passwordless sudo available
                sudo apt-get update -qq 2>/dev/null
                sudo apt-get install -y -qq "$PKG" 2>/dev/null && return 0
            else
                # Need password - ask user
                print_step "Precisamos de permissão para instalar ${PKG}..."
                sudo apt-get update -qq 2>/dev/null
                sudo apt-get install -y "$PKG" 2>/dev/null && return 0
            fi
        fi

        # Try without sudo (rootless container or already root)
        if [[ $EUID -eq 0 ]]; then
            apt-get update -qq 2>/dev/null
            apt-get install -y -qq "python${PYTHON_VERSION}-venv" 2>/dev/null && return 0
        fi

        return 1
    }

    # Create venv if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        # First attempt to create venv
        if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
            # Failed - check if we're on Debian/Ubuntu and try to install venv package
            if is_debian_based; then
                print_warn "python3-venv não instalado. Tentando instalar..."

                if install_venv_package; then
                    print_done "python${PYTHON_VERSION}-venv instalado com sucesso"
                    # Retry venv creation
                    if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
                        print_warn "Ainda não foi possível criar venv após instalação."
                        print_warn "Execute manualmente: sudo apt install python${PYTHON_VERSION}-venv"
                        return
                    fi
                else
                    print_warn "Não foi possível instalar python${PYTHON_VERSION}-venv automaticamente."
                    print_warn "Execute manualmente:"
                    print_warn "  sudo apt update && sudo apt install python${PYTHON_VERSION}-venv"
                    print_warn "E depois execute o setup.sh novamente."
                    return
                fi
            else
                # Not Debian-based, give generic instructions
                print_warn "Não foi possível criar venv."
                print_warn "Instale o pacote venv do seu sistema e execute novamente."
                print_warn "Ou instale as dependências globalmente:"
                print_warn "  pip install networkx numpy sentence-transformers"
                return
            fi
        fi
    fi

    print_done "Virtual environment criado"

    # Install dependencies in venv
    (
        source "$VENV_DIR/bin/activate" 2>/dev/null || . "$VENV_DIR/bin/activate"
        pip install --quiet --upgrade pip 2>/dev/null || true
        pip install --quiet networkx numpy 2>/dev/null && print_done "networkx + numpy instalados"
        pip install --quiet sentence-transformers 2>/dev/null && print_done "sentence-transformers instalado"
    ) || {
        print_warn "Algumas dependências podem não ter sido instaladas."
        print_warn "Execute: source .claude/brain/.venv/bin/activate && pip install networkx numpy sentence-transformers"
    }
}

# ═══════════════════════════════════════════════════════════════
# BACKUP (same as v1)
# ═══════════════════════════════════════════════════════════════

HAS_PREVIOUS_CONFIG=false

backup_existing_config() {
    local HAS_CLAUDE_DIR=false
    local HAS_CLAUDE_MD=false

    [[ -d "$TARGET_DIR/.claude" ]] && HAS_CLAUDE_DIR=true
    [[ -f "$TARGET_DIR/CLAUDE.md" ]] && HAS_CLAUDE_MD=true

    if ! $HAS_CLAUDE_DIR && ! $HAS_CLAUDE_MD; then return; fi

    echo -e "  ${YELLOW}📋 Configuração existente detectada${NC}"
    echo -e "  O Engram vai fazer ${BOLD}backup${NC} e instalar por cima."
    echo ""
    read -p "  Continuar? (S/n): " -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Nn]$ ]] && echo -e "  ${RED}Cancelado.${NC}" && exit 0

    $HAS_CLAUDE_DIR && cp -r "$TARGET_DIR/.claude" "$TARGET_DIR/.claude.bak" && print_done "Backup: .claude/ → .claude.bak/"
    $HAS_CLAUDE_MD && cp "$TARGET_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md.bak" && print_done "Backup: CLAUDE.md → CLAUDE.md.bak"
    HAS_PREVIOUS_CONFIG=true
}

# ═══════════════════════════════════════════════════════════════
# GENERATE CLAUDE.md (enhanced for v2)
# ═══════════════════════════════════════════════════════════════

generate_claude_md() {
    print_step "Gerando CLAUDE.md..."

    PROJECT_NAME=""
    if [[ -f "$TARGET_DIR/package.json" ]]; then
        PROJECT_NAME=$(node -e "console.log(require('$TARGET_DIR/package.json').name||'')" 2>/dev/null) || true
    fi
    [[ -z "$PROJECT_NAME" ]] && PROJECT_NAME=$(basename "$TARGET_DIR")

    STACK_LINES=""
    [[ -n "$FRAMEWORK" ]] && STACK_LINES+="- Framework: ${FRAMEWORK}${FRAMEWORK_VERSION:+ $FRAMEWORK_VERSION}"$'\n'
    [[ -n "$DB" ]] && STACK_LINES+="- Banco: ${DB}${ORM:+ + $ORM}"$'\n'
    $HAS_TYPESCRIPT && STACK_LINES+="- TypeScript: strict mode"$'\n'
    $HAS_DOCKER && STACK_LINES+="- Infra: Docker"$'\n'
    $LANG_NODE && STACK_LINES+="- Package Manager: ${PKG_MANAGER}"$'\n'

    RULES=""
    $HAS_TYPESCRIPT && RULES+="- Use TypeScript strict, nunca \`any\`"$'\n'
    [[ "$FRAMEWORK" == "nextjs" ]] && RULES+="- Server Components por padrão, Client Components só quando necessário"$'\n'
    RULES+="- Validação de input em todas as APIs"$'\n'
    RULES+="- Error handling em todas as rotas"$'\n'

    cat > "$TARGET_DIR/CLAUDE.md" << CLAUDE_EOF
# Projeto: ${PROJECT_NAME}

## Identidade
Idioma padrão: Português brasileiro. Código e commits em inglês.

## Princípio Central: Auto-Alimentação (Ouroboros)
Este projeto usa Engram v${VERSION} — um sistema metacircular de retroalimentação.
Toda decisão, padrão, erro corrigido ou insight DEVE ser registrado em \`.claude/knowledge/\`.
O sistema evolui a si mesmo: gera skills sob demanda, versiona mudanças, aposenta o inútil.

## Workflow Obrigatório

### Antes de Codificar
1. Leia \`.claude/knowledge/context/CURRENT_STATE.md\`
2. Consulte \`.claude/knowledge/priorities/PRIORITY_MATRIX.md\`
3. Verifique \`.claude/knowledge/patterns/PATTERNS.md\`
4. Se decisão arquitetural: consulte \`ADR_LOG.md\`
5. Se lógica de negócio: consulte \`DOMAIN.md\`
6. Se tarefa similar já resolvida: consulte \`EXPERIENCE_LIBRARY.md\`

### Ao Codificar
${RULES}
### Depois de Codificar
1. Atualize \`CURRENT_STATE.md\`
2. Registre padrões novos em \`PATTERNS.md\`
3. Registre decisões em \`ADR_LOG.md\`
4. Reavalie \`PRIORITY_MATRIX.md\`
5. Registre aprendizados de domínio em \`DOMAIN.md\`

## Stack
${STACK_LINES}
## Auto-Geração (Metacircular)
O Engram gera seus próprios componentes:
- \`/init-engram\` — Análise profunda + geração de skills/agents para o projeto
- \`/create [tipo] [nome]\` — Gerar componente sob demanda
- \`/doctor\` — Health check do sistema
- \`/learn\` — Retroalimentação + evolução

Schemas em \`.claude/schemas/\`. Manifest em \`.claude/manifest.json\`.

## Skills Disponíveis
Consulte \`.claude/skills/\` — cada skill tem SKILL.md com instruções.
Skills são gerados sob demanda pelo \`engram-genesis\`.

## Subagentes
Definidos em \`.claude/agents/\`. Gerados pelo \`/init-engram\`.
Subagentes NÃO podem invocar outros subagentes.

## Orquestração Inteligente
O Claude cria subagents e skills sob demanda DURANTE o trabalho.
Se uma tarefa exige expertise que nenhum componente existente cobre:

1. **Detectar**: listar agents/skills, verificar se algum cobre
2. **Anunciar**: informar ao dev o que vai criar e por quê
3. **Gerar**: usar engram-genesis (scaffold → customizar → validar → registrar)
4. **Usar**: delegar a tarefa ao componente recém-criado
5. **Reportar**: informar o que foi criado ao final

Consulte \`.claude/skills/engram-factory/SKILL.md\` para o protocolo completo.
Referência detalhada em \`.claude/skills/engram-factory/references/orchestration-protocol.md\`.

Regras: anunciar antes de criar, máximo 2 por sessão, nunca duplicar, source=runtime.

## Regras de Ouro
- NUNCA pule o workflow de retroalimentação
- Priorize legibilidade sobre cleverness
- Pergunte antes de mudar arquitetura
- Registre TUDO que pode ser útil no futuro
- Se não existe skill para algo repetitivo: crie com \`/create\`
CLAUDE_EOF

    print_done "CLAUDE.md gerado"
}

# ═══════════════════════════════════════════════════════════════
# SETTINGS.JSON (same logic as v1)
# ═══════════════════════════════════════════════════════════════

customize_settings() {
    print_step "Gerando settings.json..."

    local EXTRA=""
    $LANG_PYTHON && EXTRA+='      "Bash(pip:*)",'$'\n''      "Bash(python:*)",'$'\n''      "Bash(python3:*)",'$'\n'
    [[ "$PKG_MANAGER" == "pnpm" ]] && EXTRA+='      "Bash(pnpm:*)",'$'\n'
    [[ "$PKG_MANAGER" == "yarn" ]] && EXTRA+='      "Bash(yarn:*)",'$'\n'
    [[ "$PKG_MANAGER" == "bun" ]] && EXTRA+='      "Bash(bun:*)",'$'\n'

    cat > "$TARGET_DIR/.claude/settings.json" << SETTINGS_EOF
{
  "permissions": {
    "allow": [
      "Bash(${PKG_MANAGER} run:*)",
      "Bash(npx:*)",
      "Bash(docker compose:*)",
      "Bash(git add:*)", "Bash(git status:*)", "Bash(git commit:*)",
      "Bash(git log:*)", "Bash(git diff:*)", "Bash(git branch:*)",
      "Bash(cat:*)", "Bash(ls:*)", "Bash(find:*)", "Bash(grep:*)",
      "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(mkdir:*)",
      "Bash(echo:*)", "Bash(python3:*)",
${EXTRA}      "Read", "Write", "Edit", "Glob", "Grep"
    ],
    "deny": [
      "Bash(rm -rf /)*",
      "Read(.env)", "Read(.env.local)", "Read(.env.production)"
    ]
  }
}
SETTINGS_EOF

    print_done "settings.json customizado"
}

# ═══════════════════════════════════════════════════════════════
# INITIALIZE CURRENT_STATE.md
# ═══════════════════════════════════════════════════════════════

initialize_knowledge() {
    print_step "Inicializando knowledge..."

    local TODAY=$(date +%Y-%m-%d)
    local STATE_FILE="$TARGET_DIR/.claude/knowledge/context/CURRENT_STATE.md"

    cat > "$STATE_FILE" << STATE_EOF
# Estado Atual do Projeto
> Última atualização: ${TODAY} (auto-detectado pelo setup.sh)

## Status Geral
- **Fase**: Engram: onboarding
- **Saúde**: 🟡 Pendente análise profunda (rode /init-engram)
- **Próximo Marco**: Completar inicialização com /init-engram

## O Que Mudou Recentemente
- [${TODAY}] Engram v${VERSION} instalado via setup.sh | Impacto: ALTO

## Stack Detectada
${STACK_LINES}
## Contexto Para Próxima Sessão
Rode \`/init-engram\` para completar a inicialização.
O Claude vai analisar o projeto, gerar skills customizados via genesis,
popular knowledge files, e configurar agents e commands.
STATE_EOF

    print_done "Knowledge inicializado"
}

# ═══════════════════════════════════════════════════════════════
# UPDATE MODE
# ═══════════════════════════════════════════════════════════════

do_update() {
    print_header
    print_step "Atualizando core do Engram..."

    # Update schemas
    cp -r "$SCRIPT_DIR/core/schemas/"* "$TARGET_DIR/.claude/schemas/"
    print_done "Schemas atualizados"

    # Update genesis (preserving custom skills)
    cp -r "$SCRIPT_DIR/core/genesis" "$TARGET_DIR/.claude/skills/engram-genesis"
    chmod +x "$TARGET_DIR/.claude/skills/engram-genesis/scripts/"*.py 2>/dev/null || true
    print_done "Genesis atualizado"

    # Update evolution
    cp -r "$SCRIPT_DIR/core/evolution" "$TARGET_DIR/.claude/skills/engram-evolution"
    chmod +x "$TARGET_DIR/.claude/skills/engram-evolution/scripts/"*.py 2>/dev/null || true
    print_done "Evolution atualizado"

    # Update seeds (universal skills)
    if [[ -d "$SCRIPT_DIR/core/seeds" ]]; then
        for seed in "$SCRIPT_DIR/core/seeds"/*/; do
            [[ -d "$seed" ]] && cp -r "$seed" "$TARGET_DIR/.claude/skills/"
        done
        print_done "Seeds atualizados"
    fi

    # Update agents
    if [[ -d "$SCRIPT_DIR/core/agents" ]]; then
        cp "$SCRIPT_DIR/core/agents/"*.md "$TARGET_DIR/.claude/agents/" 2>/dev/null || true
        print_done "Agents atualizados"
    fi

    # Update commands
    cp "$SCRIPT_DIR/core/commands/"*.md "$TARGET_DIR/.claude/commands/" 2>/dev/null || true
    print_done "Commands atualizados"

    echo "$VERSION" > "$TARGET_DIR/.claude/.engram-version"
    print_done "Engram atualizado para v${VERSION} (knowledge preservado)"
    exit 0
}

[[ "$MODE" == "update" ]] && do_update

# ═══════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════

verify_installation() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  ✅ Engram v${VERSION} Instalado!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    local FILE_COUNT=$(find "$TARGET_DIR/.claude" -type f | wc -l)
    echo -e "  ${GREEN}📁 Arquivos instalados:${NC} $FILE_COUNT"
    echo ""
    echo -e "  ${BOLD}Estrutura (metacircular):${NC}"
    echo -e "  ${GREEN}├── CLAUDE.md${NC}                        (customizado)"
    echo -e "  ${GREEN}├── .claude/${NC}"
    echo -e "  ${GREEN}│   ├── schemas/${NC}                     (DNA do sistema)"
    echo -e "  ${GREEN}│   ├── manifest.json${NC}                (registro de componentes)"
    echo -e "  ${GREEN}│   ├── settings.json${NC}                (permissões)"
    echo -e "  ${GREEN}│   ├── skills/${NC}                      (8 skills: genesis + evolution + 6 seeds)"
    echo -e "  ${GREEN}│   ├── agents/${NC}                      (3 agents: architect, domain-analyst, db-expert)"
    echo -e "  ${GREEN}│   ├── commands/${NC}                    (13 commands)"
    echo -e "  ${GREEN}│   └── knowledge/${NC}                   (6 knowledge files)"
    echo ""

    $HAS_PREVIOUS_CONFIG && echo -e "  ${YELLOW}📋 Backup em .claude.bak/ — /init-engram vai mergear${NC}" && echo ""

    echo -e "  ${BOLD}${YELLOW}Próximo passo:${NC}"
    echo ""
    echo -e "  ${CYAN}  cd $TARGET_DIR${NC}"
    echo -e "  ${CYAN}  claude${NC}"
    echo -e "  ${CYAN}  /init-engram${NC}"
    echo ""
    echo -e "  O Claude vai usar ${BOLD}genesis${NC} para gerar skills, agents"
    echo -e "  e commands customizados para o seu projeto."
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

main() {
    print_header

    if [[ ! -d "$SCRIPT_DIR/core" ]]; then
        echo -e "${RED}Erro: Pasta core/ não encontrada em $SCRIPT_DIR${NC}"
        exit 1
    fi

    detect_stack
    backup_existing_config
    install_core
    install_brain_deps
    generate_claude_md
    customize_settings
    initialize_knowledge
    verify_installation
}

main "$@"
