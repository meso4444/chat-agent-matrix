#!/bin/bash
# stop_telegram_services.sh (ngrok 版)

SCRIPT_DIR="$(dirname "$0")"
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "🛑 停止 Telegram → AI 系統 (ngrok)"

# 1. 殺掉 tmux session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    tmux kill-session -t "$TMUX_SESSION_NAME"
    echo "✅ tmux session '$TMUX_SESSION_NAME' 已終止"
else
    echo "⚠️  tmux session 不存在"
fi

# 2. 殺掉 ngrok
if pgrep -f "ngrok http $FLASK_PORT" > /dev/null; then
    pkill -f "ngrok http $FLASK_PORT"
    echo "✅ ngrok 進程已終止"
else
    echo "ℹ️  ngrok 未運行"
fi

# 3. 殺掉可能殘留的 Flask process
if pgrep -f "telegram_webhook_server.py" > /dev/null; then
    pkill -f "telegram_webhook_server.py"
    echo "✅ 殘留的 Flask 伺服器已終止"
fi

# 4. 清理 log
rm -f "$SCRIPT_DIR/ngrok.log"

echo "🎉 所有服務已停止"
