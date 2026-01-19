#!/bin/bash
# stop_telegram_services.sh (ngrok edition)

SCRIPT_DIR="$(dirname "$0")"
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "🛑 Stopping Telegram → AI System (ngrok)"

# 1. Kill tmux session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    tmux kill-session -t "$TMUX_SESSION_NAME"
    echo "✅ tmux session '$TMUX_SESSION_NAME' terminated"
else
    echo "⚠️  tmux session does not exist"
fi

# 2. Kill ngrok
if pgrep -f "ngrok http $FLASK_PORT" > /dev/null; then
    pkill -f "ngrok http $FLASK_PORT"
    echo "✅ ngrok process terminated"
else
    echo "ℹ️  ngrok not running"
fi

# 3. Kill any remaining Flask process
if pgrep -f "telegram_webhook_server.py" > /dev/null; then
    pkill -f "telegram_webhook_server.py"
    echo "✅ Residual Flask server terminated"
fi

# 4. Clean up logs
rm -f "$SCRIPT_DIR/ngrok.log"

echo "🎉 All services stopped"
