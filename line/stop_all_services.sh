#!/bin/bash
# 停止所有 LINE 服務 (Chat Agent Matrix)

# 從 Python config 讀取設定
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# 載入環境變數
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")

echo "🛑 停止 LINE 系統服務..."

# 檢查 tmux 是否安裝
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux 未安裝"
    exit 1
fi

# 檢查 session 是否存在
if ! tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "⚠️ 未找到 session '$TMUX_SESSION_NAME'，服務可能已經停止"
    exit 0
fi

echo "🔄 正在停止所有服務..."

# 逐個停止 window (給服務時間正常關閉)
echo "停止 Cloudflare Tunnel..."
tmux send-keys -t "$TMUX_SESSION_NAME:cloudflared" C-c 2>/dev/null
sleep 1

echo "停止 LINE Webhook API..."
tmux send-keys -t "$TMUX_SESSION_NAME:line_api" C-c 2>/dev/null
sleep 1

# 強制終止整個 session (包含所有 Agent)
echo "終止 tmux session..."
tmux kill-session -t "$TMUX_SESSION_NAME"

echo "🎉 LINE 所有服務已停止"
