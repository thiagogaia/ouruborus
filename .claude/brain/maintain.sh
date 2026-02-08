#!/bin/bash
# maintain.sh - Script de manutencao do cerebro organizacional
#
# Uso:
#   ./maintain.sh daily     # Roda decay (diario)
#   ./maintain.sh weekly    # Roda consolidate (semanal)
#   ./maintain.sh monthly   # Roda archive (mensal)
#   ./maintain.sh health    # Verifica saude
#   ./maintain.sh full      # Roda tudo (sleep + consolidate + health)
#
# Fluxo vs /learn:
#   /learn        = fluxo principal (encode + sleep + health) — rode ao fim de cada sessao
#   maintain.sh   = cron para periodos sem /learn (ex: projeto ocioso, ferias)
#   maintain.sh full = manutenção completa para uso manual ou menos frequente

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

# Use brain venv when available (ensures chromadb, sentence-transformers, etc.)
PYTHON="$SCRIPT_DIR/.venv/bin/python3"
[[ -x "$PYTHON" ]] || PYTHON="python3"

case "${1:-health}" in
    daily|decay)
        echo "=== Running Daily Decay ==="
        "$PYTHON" .claude/brain/cognitive.py decay
        ;;

    weekly|consolidate)
        echo "=== Running Weekly Consolidation ==="
        "$PYTHON" .claude/brain/cognitive.py consolidate
        ;;

    monthly|archive)
        echo "=== Running Monthly Archive ==="
        "$PYTHON" .claude/brain/cognitive.py archive
        ;;

    sleep)
        echo "=== Running Sleep Cycle ==="
        "$PYTHON" .claude/brain/sleep.py ${@:2}
        ;;

    health)
        echo "=== Brain Health Check ==="
        "$PYTHON" .claude/brain/cognitive.py health
        ;;

    full)
        echo "=== Full Maintenance ==="
        "$PYTHON" .claude/brain/sleep.py
        "$PYTHON" .claude/brain/cognitive.py consolidate
        "$PYTHON" .claude/brain/cognitive.py health
        ;;

    *)
        echo "Usage: $0 {daily|weekly|monthly|sleep|health|full}"
        echo ""
        echo "Commands:"
        echo "  daily    - Run memory decay (Ebbinghaus curve)"
        echo "  weekly   - Run connection consolidation"
        echo "  monthly  - Archive weak memories"
        echo "  sleep    - Run sleep cycle (semantic consolidation)"
        echo "  health   - Check brain health status"
        echo "  full     - Run all processes (sleep + consolidate + health)"
        exit 1
        ;;
esac
