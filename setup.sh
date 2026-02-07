#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# 🐍 Engram v4 — Auto-Installer (Metacircular)
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
# O que faz (v4 — brain-only architecture):
#   1. Detecta a stack do projeto automaticamente
#   2. Instala o DNA + Genesis (motor de auto-geração)
#   3. Instala seeds universais + Evolution (motor de evolução)
#   4. Instala Brain (cérebro organizacional com grafo + embeddings)
#   5. Gera CLAUDE.md customizado e settings.json
#   6. O /init-engram popula o cérebro e gera componentes sob demanda
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/VERSION")

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
    echo "  --force           Skip confirmation prompts (still creates backups)"
    echo "  --regenerate      Regenerate CLAUDE.md and settings.json (use with --update)"
    echo "  --uninstall       Remove Engram from project"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh                              # Install in current directory"
    echo "  ./setup.sh /path/to/project             # Install in specific directory"
    echo "  ./setup.sh --update .                   # Update core in current directory"
    echo "  ./setup.sh --update --force .           # Update without prompts"
    echo "  ./setup.sh --update --regenerate .      # Update and regenerate configs"
    echo ""
    exit 0
}

show_version() {
    echo "Engram v${VERSION}"
    exit 0
}

MODE="install"
FORCE=false
REGENERATE=false
TARGET_DIR=""

for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help ;;
        -v|--version) show_version ;;
        --update) MODE="update" ;;
        --uninstall) MODE="uninstall" ;;
        --force) FORCE=true ;;
        --regenerate) REGENERATE=true ;;
        *) TARGET_DIR="$arg" ;;
    esac
done

TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

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
        echo "$PKG" | grep -q '"@nestjs/core"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="nestjs"
        echo "$PKG" | grep -q '"nuxt"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="nuxt"
        echo "$PKG" | grep -q '"@angular/core"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="angular"
        echo "$PKG" | grep -q '"svelte"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="sveltekit"
        echo "$PKG" | grep -q '"vue"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="vue"
        echo "$PKG" | grep -q '"react"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="react"
        echo "$PKG" | grep -q '"express"' && [[ -z "$FRAMEWORK" ]] && FRAMEWORK="express"
        [[ "$FRAMEWORK" == "nextjs" ]] && FRAMEWORK_VERSION=$(echo "$PKG" | sed -n 's/.*"next"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | sed 's/[\^~>=<]//g' | head -1) || true
    fi
    if $LANG_PHP && [[ -f "$TARGET_DIR/composer.json" ]]; then
        COMPOSER=$(cat "$TARGET_DIR/composer.json")
        echo "$COMPOSER" | grep -q '"laravel/framework"' && FRAMEWORK="laravel"
    fi
    $LANG_PYTHON && [[ -f "$TARGET_DIR/manage.py" ]] && FRAMEWORK="django"
    $LANG_PYTHON && grep -ql "fastapi" "$TARGET_DIR/requirements.txt" 2>/dev/null && FRAMEWORK="fastapi"

    ORM=""; DB=""
    [[ -d "$TARGET_DIR/prisma" || -f "$TARGET_DIR/prisma/schema.prisma" ]] && ORM="prisma"
    if $LANG_NODE && [[ -f "$TARGET_DIR/package.json" ]]; then
        echo "$PKG" | grep -q '"drizzle-orm"' && ORM="drizzle"
        echo "$PKG" | grep -q '"typeorm"' && ORM="typeorm"
        echo "$PKG" | grep -q '"sequelize"' && [[ -z "$ORM" ]] && ORM="sequelize"
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
    mkdir -p "$CLAUDE_DIR"/{skills,agents,commands,knowledge,dna,versions}

    # 1. Schemas (DNA)
    cp -r "$SCRIPT_DIR/core/dna/"* "$CLAUDE_DIR/dna/"
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
            [[ -d "$seed" ]] || continue
            local SEED_NAME
            SEED_NAME=$(basename "$seed")
            cp -r "${seed%/}" "$CLAUDE_DIR/skills/$SEED_NAME"
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

    # 7. Skill templates (staging area — /init-engram will evaluate and prune)
    if [[ -d "$SCRIPT_DIR/templates/skills" ]]; then
        mkdir -p "$CLAUDE_DIR/templates/skills"
        cp -r "$SCRIPT_DIR/templates/skills/"* "$CLAUDE_DIR/templates/skills/" 2>/dev/null || true
        local SKILL_TMPL_COUNT=$(find "$CLAUDE_DIR/templates/skills" -name "*.skill.tmpl" -type f | wc -l | tr -d ' ')
        print_done "Skill templates copiados para staging ($SKILL_TMPL_COUNT templates)"
    fi

    # 8. Knowledge templates (mirror copy — folder structure matches destination)
    local TODAY=$(date +%Y-%m-%d)
    local TMPL_COUNT=0
    while IFS= read -r tmpl; do
        local REL="${tmpl#$SCRIPT_DIR/templates/knowledge/}"
        local DEST="$CLAUDE_DIR/knowledge/${REL%.tmpl}"
        mkdir -p "$(dirname "$DEST")"
        if [[ ! -f "$DEST" ]]; then
            sed "s/\${DATE}/$TODAY/g" "$tmpl" > "$DEST"
            ((TMPL_COUNT++)) || true
        fi
    done < <(find "$SCRIPT_DIR/templates/knowledge" -name "*.tmpl" -type f)
    print_done "Knowledge templates inicializados ($TMPL_COUNT arquivos)"

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
      },
      "base-ingester": {
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
        # NOT copying *.json — each project starts with an empty brain (brain.db created on first load)
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
                print_warn "  pip install networkx numpy sentence-transformers chromadb pydantic-settings"
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
        pip install --quiet chromadb pydantic-settings 2>/dev/null && print_done "chromadb + pydantic-settings instalados"

        # Patch ChromaDB for Python 3.14+ compatibility (pydantic.v1 crash)
        # See: https://github.com/chroma-core/chroma/issues/5996
        local PATCH_SCRIPT="$CLAUDE_DIR/brain/patch_chromadb.py"
        if [[ -f "$PATCH_SCRIPT" ]]; then
            python3 "$PATCH_SCRIPT" 2>/dev/null && print_done "ChromaDB patched para Python $(python3 --version 2>&1 | awk '{print $2}')" || true
        fi
    ) || {
        print_warn "Algumas dependências podem não ter sido instaladas."
        print_warn "Execute: source .claude/brain/.venv/bin/activate && pip install networkx numpy sentence-transformers chromadb pydantic-settings"
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
Toda decisão, padrão, erro corrigido ou insight DEVE ser registrado **direto no cérebro** via \`brain.add_memory()\`.
O sistema evolui a si mesmo: gera skills sob demanda, versiona mudanças, aposenta o inútil.

## Workflow Obrigatório

### Antes de Codificar
1. **O que mudou recentemente**: \`python3 .claude/brain/recall.py --recent 7d --type Commit --top 10 --format json\`
2. **Conhecimento relevante**: \`python3 .claude/brain/recall.py "<tema da tarefa>" --top 10 --format json\`
3. **Prioridades**: consulte \`PRIORITY_MATRIX.md\` (único .md ativamente atualizado)
4. Só leia os \`.md\` de knowledge se o recall não cobrir

> **Nota**: Os knowledge files (.md) são genesis-only — criados no setup e populados no /init-engram. Após o cérebro ser populado, não são mais atualizados. O recall os substitui.

### Ao Codificar
${RULES}
### Depois de Codificar
1. Registre padrões, decisões e experiências **direto no cérebro** via \`brain.add_memory()\`
2. Reavalie \`PRIORITY_MATRIX.md\` (único .md ativamente atualizado)
3. Execute \`/learn\` para consolidar

## Stack
${STACK_LINES}
## Auto-Geração (Metacircular)
O Engram gera seus próprios componentes:
- \`/init-engram\` — Análise profunda + geração de skills/agents para o projeto
- \`/create [tipo] [nome]\` — Gerar componente sob demanda
- \`/doctor\` — Health check do sistema
- \`/learn\` — Retroalimentação + evolução

DNA em \`.claude/dna/\`. Manifest em \`.claude/manifest.json\`.

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
# UPDATE HELPERS
# ═══════════════════════════════════════════════════════════════

backup_for_update() {
    local CLAUDE_DIR="$TARGET_DIR/.claude"
    local TIMESTAMP
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    local BACKUP_DIR="$TARGET_DIR/.claude.update-backup.${TIMESTAMP}"

    if ! $FORCE; then
        echo ""
        echo -e "  ${YELLOW}Um backup será criado antes de atualizar.${NC}"
        echo -e "  ${YELLOW}Backup em: ${BOLD}${BACKUP_DIR}/${NC}"
        echo ""
        read -p "  Continuar? (S/n): " -n 1 -r
        echo ""
        [[ $REPLY =~ ^[Nn]$ ]] && echo -e "  ${RED}Cancelado.${NC}" && exit 0
    fi

    cp -r "$CLAUDE_DIR" "$BACKUP_DIR"
    print_done "Backup criado: $(basename "$BACKUP_DIR")/"
    UPDATE_BACKUP_DIR="$BACKUP_DIR"
}

update_manifest_json() {
    local CLAUDE_DIR="$TARGET_DIR/.claude"
    local MANIFEST="$CLAUDE_DIR/manifest.json"

    if [[ ! -f "$MANIFEST" ]]; then
        print_warn "manifest.json não encontrado — será criado no próximo install"
        return
    fi

    python3 - "$MANIFEST" "$VERSION" "$SCRIPT_DIR" << 'PYEOF'
import json, sys, os, glob
from datetime import datetime

manifest_path = sys.argv[1]
version = sys.argv[2]
script_dir = sys.argv[3]

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

# Update version and timestamp
manifest['engram_version'] = version
manifest['last_updated'] = datetime.now().astimezone().isoformat()

# Discover seeds from source
seeds_dir = os.path.join(script_dir, 'core', 'seeds')
if os.path.isdir(seeds_dir):
    existing_skills = manifest.get('components', {}).get('skills', {})
    for seed_name in os.listdir(seeds_dir):
        seed_path = os.path.join(seeds_dir, seed_name)
        if os.path.isdir(seed_path) and seed_name not in existing_skills:
            # Add new seed — never overwrite existing entries
            existing_skills[seed_name] = {
                "version": "1.0.0",
                "source": "seed",
                "created_at": datetime.now().astimezone().isoformat(),
                "updated_at": datetime.now().astimezone().isoformat(),
                "activations": 0,
                "last_used": None,
                "health": "active"
            }
    manifest.setdefault('components', {})['skills'] = existing_skills

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write('\n')

print(f"  manifest.json: version={version}, seeds checked")
PYEOF

    if [[ $? -eq 0 ]]; then
        print_done "manifest.json atualizado"
    else
        print_warn "Falha ao atualizar manifest.json — atualize manualmente"
    fi
}

# ═══════════════════════════════════════════════════════════════
# UPDATE MODE
# ═══════════════════════════════════════════════════════════════

do_update() {
    print_header
    local CLAUDE_DIR="$TARGET_DIR/.claude"

    # ── 1. Pre-flight: verify Engram is installed ──
    if [[ ! -d "$CLAUDE_DIR" ]]; then
        echo -e "  ${RED}Erro: Engram não está instalado em $TARGET_DIR${NC}"
        echo -e "  ${RED}Use ./setup.sh $TARGET_DIR para instalar.${NC}"
        exit 1
    fi

    print_step "Atualizando core do Engram em: ${BOLD}$TARGET_DIR${NC}"

    # ── 2. Version comparison (gap 8) ──
    # Compare: $SCRIPT_DIR/VERSION (source of truth) vs $TARGET_DIR/.claude/.engram-version (installed)
    local INSTALLED_VERSION=""
    [[ -f "$CLAUDE_DIR/.engram-version" ]] && INSTALLED_VERSION=$(cat "$CLAUDE_DIR/.engram-version")

    echo ""
    echo -e "  ${BOLD}Engram (source):${NC}  v${VERSION}  ← ${SCRIPT_DIR}/VERSION"
    if [[ -n "$INSTALLED_VERSION" ]]; then
        echo -e "  ${BOLD}Projeto (local):${NC}  v${INSTALLED_VERSION}  ← ${TARGET_DIR}/.claude/.engram-version"

        if [[ "$INSTALLED_VERSION" == "$VERSION" ]]; then
            echo ""
            echo -e "  ${YELLOW}Projeto já está na mesma versão do Engram (v${VERSION}).${NC}"
            if ! $FORCE; then
                read -p "  Atualizar mesmo assim? (s/N): " -n 1 -r
                echo ""
                [[ ! $REPLY =~ ^[Ss]$ ]] && echo -e "  ${GREEN}Nenhuma alteração feita.${NC}" && exit 0
            else
                print_step "Forçando atualização (--force)"
            fi
        else
            echo ""
            echo -e "  ${GREEN}Atualizando projeto: v${INSTALLED_VERSION} → v${VERSION}${NC}"
        fi
    else
        echo -e "  ${BOLD}Projeto (local):${NC}  ${YELLOW}sem versão (.engram-version ausente)${NC}"
        echo ""
        echo -e "  ${YELLOW}Gravando versão v${VERSION} no projeto${NC}"
    fi

    # ── 3. Timestamped backup (gap 7) ──
    backup_for_update

    # ── 4. Update schemas, genesis, evolution ──
    cp -r "$SCRIPT_DIR/core/dna/"* "$CLAUDE_DIR/dna/"
    print_done "Schemas atualizados"

    cp -r "$SCRIPT_DIR/core/genesis" "$CLAUDE_DIR/skills/engram-genesis"
    chmod +x "$CLAUDE_DIR/skills/engram-genesis/scripts/"*.py 2>/dev/null || true
    print_done "Genesis atualizado"

    cp -r "$SCRIPT_DIR/core/evolution" "$CLAUDE_DIR/skills/engram-evolution"
    chmod +x "$CLAUDE_DIR/skills/engram-evolution/scripts/"*.py 2>/dev/null || true
    print_done "Evolution atualizado"

    # ── 5. Update seeds with customization warning (gap 6) ──
    if [[ -d "$SCRIPT_DIR/core/seeds" ]]; then
        local SEED_WARNINGS=()
        for seed in "$SCRIPT_DIR/core/seeds"/*/; do
            [[ ! -d "$seed" ]] && continue
            local SEED_NAME
            SEED_NAME=$(basename "$seed")
            local DEST_SEED="$CLAUDE_DIR/skills/$SEED_NAME"

            # Detect local-only files that would be overwritten
            if [[ -d "$DEST_SEED" ]]; then
                local LOCAL_EXTRAS=()
                while IFS= read -r local_file; do
                    local REL="${local_file#$DEST_SEED/}"
                    if [[ ! -f "$seed/$REL" ]]; then
                        LOCAL_EXTRAS+=("$REL")
                    fi
                done < <(find "$DEST_SEED" -type f 2>/dev/null)
                if [[ ${#LOCAL_EXTRAS[@]} -gt 0 ]]; then
                    SEED_WARNINGS+=("$SEED_NAME: ${#LOCAL_EXTRAS[@]} arquivo(s) local(is) preservado(s)")
                fi
            fi

            cp -r "${seed%/}" "$CLAUDE_DIR/skills/$SEED_NAME"
        done
        print_done "Seeds atualizados"
        for warn in "${SEED_WARNINGS[@]:-}"; do
            [[ -n "$warn" ]] && print_warn "$warn"
        done
    fi

    # ── 6. Update agents, commands, skill templates ──
    if [[ -d "$SCRIPT_DIR/core/agents" ]]; then
        cp "$SCRIPT_DIR/core/agents/"*.md "$CLAUDE_DIR/agents/" 2>/dev/null || true
        print_done "Agents atualizados"
    fi

    cp "$SCRIPT_DIR/core/commands/"*.md "$CLAUDE_DIR/commands/" 2>/dev/null || true
    print_done "Commands atualizados"

    if [[ -d "$SCRIPT_DIR/templates/skills" ]]; then
        mkdir -p "$CLAUDE_DIR/templates/skills"
        cp -r "$SCRIPT_DIR/templates/skills/"* "$CLAUDE_DIR/templates/skills/" 2>/dev/null || true
        print_done "Skill templates atualizados"
    fi

    # ── 7. Update brain scripts — code only, never data (gap 1) ──
    if [[ -d "$SCRIPT_DIR/.claude/brain" ]]; then
        mkdir -p "$CLAUDE_DIR/brain/state"
        # Copy code files: .py, .sh, .md
        cp "$SCRIPT_DIR/.claude/brain/"*.py "$CLAUDE_DIR/brain/" 2>/dev/null || true
        cp "$SCRIPT_DIR/.claude/brain/"*.sh "$CLAUDE_DIR/brain/" 2>/dev/null || true
        cp "$SCRIPT_DIR/.claude/brain/"*.md "$CLAUDE_DIR/brain/" 2>/dev/null || true
        chmod +x "$CLAUDE_DIR/brain/"*.py "$CLAUDE_DIR/brain/"*.sh 2>/dev/null || true
        # NEVER copy data: graph.json, embeddings.npz, *.jsonl
        print_done "Brain scripts atualizados (dados preservados)"
    fi

    # ── 8. Verify/install brain deps (gap 2) ──
    local VENV_DIR="$CLAUDE_DIR/brain/.venv"
    if [[ -d "$CLAUDE_DIR/brain" ]]; then
        if [[ ! -d "$VENV_DIR" ]] || $FORCE; then
            install_brain_deps
        else
            print_done "Brain deps: .venv já existe (use --force para reinstalar)"
        fi
    fi

    # ── 9. Update manifest.json (gap 5) ──
    update_manifest_json

    # ── 10. Advisory about CLAUDE.md / settings.json (gaps 3-4) ──
    if ! $REGENERATE; then
        echo ""
        print_warn "CLAUDE.md e settings.json NÃO foram alterados (customizações preservadas)"
        print_warn "Use --regenerate para regenerá-los com backup"
    fi

    # ── 11. Regenerate if --regenerate (gaps 3-4) ──
    if $REGENERATE; then
        echo ""
        print_step "Regenerando CLAUDE.md e settings.json (--regenerate)..."

        # Backup existing files
        [[ -f "$TARGET_DIR/CLAUDE.md" ]] && cp "$TARGET_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md.pre-update.bak"
        [[ -f "$CLAUDE_DIR/settings.json" ]] && cp "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/settings.json.pre-update.bak"

        # Need stack detection for generation
        detect_stack
        generate_claude_md
        customize_settings

        print_warn "Templates regenerados — customizações manuais podem ter sido perdidas"
        print_warn "Backup em CLAUDE.md.pre-update.bak e settings.json.pre-update.bak"
    fi

    # ── 12. Save version ──
    echo "$VERSION" > "$CLAUDE_DIR/.engram-version"

    # ── 13. Summary ──
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  ✅ Engram atualizado para v${VERSION}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}✓${NC} Core (dna, genesis, evolution, seeds)"
    echo -e "  ${GREEN}✓${NC} Brain scripts (dados preservados)"
    echo -e "  ${GREEN}✓${NC} Agents, commands, templates"
    echo -e "  ${GREEN}✓${NC} manifest.json (versão e seeds)"
    [[ -n "${UPDATE_BACKUP_DIR:-}" ]] && echo -e "  ${GREEN}✓${NC} Backup em: $(basename "$UPDATE_BACKUP_DIR")/"
    $REGENERATE && echo -e "  ${GREEN}✓${NC} CLAUDE.md e settings.json regenerados"
    ! $REGENERATE && echo -e "  ${YELLOW}—${NC} CLAUDE.md e settings.json preservados"
    echo ""
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
    echo -e "  ${GREEN}│   ├── dna/${NC}                          (DNA do sistema)"
    echo -e "  ${GREEN}│   ├── manifest.json${NC}                (registro de componentes)"
    echo -e "  ${GREEN}│   ├── settings.json${NC}                (permissões)"
    echo -e "  ${GREEN}│   ├── skills/${NC}                      (9 skills: genesis + evolution + 7 seeds)"
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
