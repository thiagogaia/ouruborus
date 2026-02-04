#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# 🐍 Engram v3 — Batch Installer
#    Instala Engram em múltiplos projetos de uma vez
# ═══════════════════════════════════════════════════════════════
# Uso:
#   ./batch-setup.sh proj1 proj2 proj3     → instala em múltiplos diretórios
#   ./batch-setup.sh -y proj1 proj2        → modo batch (sem confirmações)
#   ./batch-setup.sh --update proj1 proj2  → atualiza múltiplos projetos
#   ./batch-setup.sh --uninstall proj1     → remove de múltiplos projetos
#
# Este script é um wrapper que chama ./setup.sh para cada diretório.
# Para instalar em um único projeto, use diretamente: ./setup.sh
# ═══════════════════════════════════════════════════════════════

VERSION="3.0.0"
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
    echo -e "${BOLD}  🐍 Engram v${VERSION} — Batch Installer${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_progress() { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${BOLD}[$1/$2]${NC} $3"; }
print_done() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}✓${NC} $1"; }
print_error() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${RED}✗${NC} $1"; }
print_warn() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${YELLOW}⚠${NC} $1"; }

# ── Argument handling ─────────────────────────────────────────

show_help() {
    echo ""
    echo "🐍 Engram v${VERSION} — Batch Installer"
    echo ""
    echo "Usage:"
    echo "  ./batch-setup.sh [OPTIONS] DIR1 [DIR2 DIR3 ...]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help"
    echo "  -v, --version       Show version"
    echo "  -y, --yes, --batch  Non-interactive mode (auto-confirm backups)"
    echo "  --update            Update core without touching knowledge"
    echo "  --uninstall         Remove Engram from projects"
    echo ""
    echo "Examples:"
    echo "  ./batch-setup.sh proj1 proj2 proj3        # Install in multiple dirs"
    echo "  ./batch-setup.sh -y ~/proj1 ~/proj2       # Batch install (no prompts)"
    echo "  ./batch-setup.sh --update proj1 proj2     # Update multiple projects"
    echo "  ./batch-setup.sh --uninstall proj1 proj2  # Remove from multiple"
    echo ""
    echo "Note: For single project, use ./setup.sh directly."
    echo ""
    exit 0
}

show_version() {
    echo "Engram Batch Installer v${VERSION}"
    exit 0
}

MODE=""
BATCH_MODE=false
TARGET_DIRS=()

for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help ;;
        -v|--version) show_version ;;
        -y|--yes|--batch) BATCH_MODE=true ;;
        --update) MODE="--update" ;;
        --uninstall) MODE="--uninstall" ;;
        *) TARGET_DIRS+=("$arg") ;;
    esac
done

# ── Validation ────────────────────────────────────────────────

if [[ ${#TARGET_DIRS[@]} -eq 0 ]]; then
    echo -e "${RED}Erro: Nenhum diretório especificado.${NC}"
    echo ""
    echo "Uso: ./batch-setup.sh proj1 proj2 proj3"
    echo "     ./batch-setup.sh --help"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/setup.sh" ]]; then
    echo -e "${RED}Erro: setup.sh não encontrado em $SCRIPT_DIR${NC}"
    exit 1
fi

# ── Main ──────────────────────────────────────────────────────

print_header

total=${#TARGET_DIRS[@]}
success=0
failed=0
current=0

echo -e "  ${BOLD}Processando $total projeto(s)...${NC}"
echo ""

for target in "${TARGET_DIRS[@]}"; do
    ((current++)) || true
    print_progress "$current" "$total" "Processando: ${BOLD}$target${NC}"

    # Validate directory exists
    if [[ ! -d "$target" ]]; then
        print_error "Diretório não existe: $target"
        ((failed++)) || true
        echo ""
        continue
    fi

    # Build command
    CMD=("$SCRIPT_DIR/setup.sh")
    [[ -n "$MODE" ]] && CMD+=("$MODE")
    CMD+=("$target")

    # Run setup.sh
    # In batch mode, we auto-confirm by piping "y" to stdin
    if $BATCH_MODE; then
        if echo "y" | "${CMD[@]}" 2>&1; then
            ((success++)) || true
        else
            print_error "Falha em: $target"
            ((failed++)) || true
        fi
    else
        if "${CMD[@]}"; then
            ((success++)) || true
        else
            print_error "Falha ou cancelado: $target"
            ((failed++)) || true
        fi
    fi

    echo ""
done

# ── Summary ───────────────────────────────────────────────────

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
if [[ $failed -eq 0 ]]; then
    echo -e "${BOLD}  ✅ Concluído: ${success}/${total} projetos${NC}"
else
    echo -e "${BOLD}  ⚠️  Parcial: ${success} sucesso, ${failed} falha(s)${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [[ -z "$MODE" ]] && [[ $success -gt 0 ]]; then
    echo -e "  ${BOLD}${YELLOW}Próximo passo:${NC}"
    echo ""
    echo -e "  ${CYAN}  cd <projeto>${NC}"
    echo -e "  ${CYAN}  claude${NC}"
    echo -e "  ${CYAN}  /init-engram${NC}"
    echo ""
fi

[[ $failed -gt 0 ]] && exit 1
exit 0
