#!/bin/bash
# Stop all LINE services (Chat Agent Matrix)

# Read configuration from Python config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")

echo "🛑 Stopping all LINE system services..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not installed"
    exit 1
fi

# Check if session exists
if ! tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "⚠️ Session '$TMUX_SESSION_NAME' not found, services may already be stopped"
    exit 0
fi

echo "🔄 Stopping all services..."

# Stop windows individually (give services time to shut down gracefully)
echo "Stopping Cloudflare Tunnel..."
tmux send-keys -t "$TMUX_SESSION_NAME:cloudflared" C-c 2>/dev/null
sleep 1

echo "Stopping LINE Webhook API..."
tmux send-keys -t "$TMUX_SESSION_NAME:line_api" C-c 2>/dev/null
sleep 1

# Force terminate entire session (including all Agents)
echo "Terminating tmux session..."
tmux kill-session -t "$TMUX_SESSION_NAME"

echo "🎉 All LINE services stopped"
