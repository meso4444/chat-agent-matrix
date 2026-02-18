#!/bin/bash
# ============================================================================
# Chat Agent Matrix - [Entrypoint] Simplified Delegation Version
# ============================================================================
set -e

echo "🧬 [Entrypoint] Container awakening..."

# 1. Environment variable setup
export SCRIPT_DIR="/app/telegram"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
cd "$SCRIPT_DIR"

# 2. Core power delegation: call start_all_services.sh
# This ensures 100% loading of config.yaml mounted in container (aligns with ISC architecture)
if [ -f "./start_all_services.sh" ]; then
    echo "🚀 Startup script detected, delegating startup task..."
    bash ./start_all_services.sh
else
    echo "❌ Fatal error: /app/telegram/start_all_services.sh not found"
    exit 1
fi

echo "🏁 [Entrypoint] Startup sequence complete. Container entering daemon mode."
# Keep container running
tail -f /dev/null
