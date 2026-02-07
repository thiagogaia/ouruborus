#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# 🐍 Engram — Extras Installer
#    Instala agents e skills opcionais (nicho/domínio)
# ═══════════════════════════════════════════════════════════════
# Uso:
#   ./install_extras.sh                → instala no diretório atual
#   ./install_extras.sh /meu/projeto   → instala no diretório especificado
#   ./install_extras.sh --list         → mostra extras disponíveis
#   ./install_extras.sh --help         → mostra ajuda
#
# Pré-requisito: Engram já instalado via setup.sh
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/VERSION")
EXTRAS_DIR="$SCRIPT_DIR/extras"

# ── Colors ────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_step() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}▸${NC} $1"; }
print_done() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}✓${NC} $1"; }
print_warn() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${YELLOW}⚠${NC} $1"; }

# ── Argument handling ─────────────────────────────────────────

show_help() {
    echo ""
    echo "🐍 Engram v${VERSION} — Extras Installer"
    echo ""
    echo "Instala agents e skills opcionais de nicho/domínio."
    echo "Rode após ./setup.sh ter instalado o Engram no projeto."
    echo ""
    echo "Usage:"
    echo "  ./install_extras.sh [OPTIONS] [TARGET_DIR]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help"
    echo "  -v, --version  Show version"
    echo "  -l, --list     List available extras without installing"
    echo "  --force        Overwrite existing extras (default: skip)"
    echo ""
    echo "Examples:"
    echo "  ./install_extras.sh                  # Install extras in current dir"
    echo "  ./install_extras.sh /path/to/project # Install extras in specific dir"
    echo "  ./install_extras.sh --list           # See what's available"
    echo ""
    exit 0
}

show_version() {
    echo "Engram Extras Installer v${VERSION}"
    exit 0
}

list_extras() {
    echo ""
    echo -e "${BOLD}🐍 Engram v${VERSION} — Available Extras${NC}"
    echo ""

    if [[ -d "$EXTRAS_DIR/agents" ]]; then
        echo -e "  ${BOLD}Agents:${NC}"
        for agent in "$EXTRAS_DIR/agents/"*.md; do
            [[ -f "$agent" ]] || continue
            local name=$(basename "$agent" .md)
            local desc=$(sed -n 's/^description: *//p' "$agent" | head -1 | cut -c1-70)
            echo -e "    ${GREEN}•${NC} ${BOLD}$name${NC} — $desc"
        done
        echo ""
    fi

    if [[ -d "$EXTRAS_DIR/skills" ]]; then
        echo -e "  ${BOLD}Skills:${NC}"
        for skill_dir in "$EXTRAS_DIR/skills"/*/; do
            [[ -d "$skill_dir" ]] || continue
            local name=$(basename "$skill_dir")
            local skill_file="$skill_dir/SKILL.md"
            local desc=""
            [[ -f "$skill_file" ]] && desc=$(sed -n 's/^description: *//p' "$skill_file" | head -1 | cut -c1-70)
            echo -e "    ${GREEN}•${NC} ${BOLD}$name${NC} — $desc"
        done
        echo ""
    fi

    exit 0
}

MODE="install"
FORCE=false
TARGET_DIR=""

for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help ;;
        -v|--version) show_version ;;
        -l|--list) list_extras ;;
        --force) FORCE=true ;;
        *) TARGET_DIR="$arg" ;;
    esac
done

TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# ── Validation ────────────────────────────────────────────────

CLAUDE_DIR="$TARGET_DIR/.claude"

if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo -e "${RED}Erro: Engram não está instalado em $TARGET_DIR${NC}"
    echo -e "${RED}Rode ./setup.sh primeiro.${NC}"
    exit 1
fi

if [[ ! -d "$EXTRAS_DIR" ]]; then
    echo -e "${RED}Erro: Pasta extras/ não encontrada em $SCRIPT_DIR${NC}"
    exit 1
fi

# ── Install ───────────────────────────────────────────────────

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  🐍 Engram v${VERSION} — Installing Extras${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
print_step "Projeto: ${BOLD}$TARGET_DIR${NC}"
echo ""

agents_installed=0
agents_skipped=0
skills_installed=0
skills_skipped=0

# Install extra agents
if [[ -d "$EXTRAS_DIR/agents" ]]; then
    for agent in "$EXTRAS_DIR/agents/"*.md; do
        [[ -f "$agent" ]] || continue
        local_name=$(basename "$agent")
        dest="$CLAUDE_DIR/agents/$local_name"

        if [[ -f "$dest" ]] && ! $FORCE; then
            print_warn "Agent já existe, pulando: $local_name (use --force para sobrescrever)"
            ((agents_skipped++)) || true
        else
            cp "$agent" "$dest"
            print_done "Agent instalado: ${BOLD}${local_name%.md}${NC}"
            ((agents_installed++)) || true
        fi
    done
fi

# Install extra skills
if [[ -d "$EXTRAS_DIR/skills" ]]; then
    for skill_dir in "$EXTRAS_DIR/skills"/*/; do
        [[ -d "$skill_dir" ]] || continue
        local_name=$(basename "$skill_dir")
        dest="$CLAUDE_DIR/skills/$local_name"

        if [[ -d "$dest" ]] && ! $FORCE; then
            print_warn "Skill já existe, pulando: $local_name (use --force para sobrescrever)"
            ((skills_skipped++)) || true
        else
            cp -r "${skill_dir%/}" "$dest"
            print_done "Skill instalado: ${BOLD}$local_name${NC}"
            ((skills_installed++)) || true
        fi
    done
fi

# ── Register in manifest ─────────────────────────────────────

MANIFEST="$CLAUDE_DIR/manifest.json"

if [[ -f "$MANIFEST" ]] && command -v python3 &>/dev/null; then
    python3 - "$MANIFEST" "$EXTRAS_DIR" << 'PYEOF'
import json, sys, os
from datetime import datetime

manifest_path = sys.argv[1]
extras_dir = sys.argv[2]

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

now = datetime.now().astimezone().isoformat()
skills = manifest.setdefault('components', {}).setdefault('skills', {})
agents = manifest.setdefault('components', {}).setdefault('agents', {})

# Register extra skills
skills_dir = os.path.join(extras_dir, 'skills')
if os.path.isdir(skills_dir):
    for name in os.listdir(skills_dir):
        if os.path.isdir(os.path.join(skills_dir, name)) and name not in skills:
            skills[name] = {
                "version": "1.0.0",
                "source": "extras",
                "created_at": now,
                "updated_at": now,
                "activations": 0,
                "last_used": None,
                "health": "active"
            }

# Register extra agents
agents_dir = os.path.join(extras_dir, 'agents')
if os.path.isdir(agents_dir):
    for f in os.listdir(agents_dir):
        if f.endswith('.md'):
            name = f[:-3]
            if name not in agents:
                agents[name] = {
                    "version": "1.0.0",
                    "source": "extras",
                    "created_at": now,
                    "updated_at": now,
                    "activations": 0,
                    "last_used": None,
                    "health": "active"
                }

manifest['last_updated'] = now

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write('\n')
PYEOF
    print_done "manifest.json atualizado"
fi

# ── Summary ───────────────────────────────────────────────────

total=$((agents_installed + skills_installed))
skipped=$((agents_skipped + skills_skipped))

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
if [[ $total -gt 0 ]]; then
    echo -e "${BOLD}  ✅ Extras instalados: $agents_installed agent(s), $skills_installed skill(s)${NC}"
else
    echo -e "${BOLD}  ℹ️  Nenhum extra novo para instalar${NC}"
fi
[[ $skipped -gt 0 ]] && echo -e "  ${YELLOW}Pulados: $skipped (já existiam)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
