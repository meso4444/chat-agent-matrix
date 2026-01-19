#!/bin/bash
# status_telegram_services.sh (Multi-Agent 版)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"

# 讀取配置
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "📊 Chat Agent Matrix 系統狀態 (Multi-Agent)"
echo "⏰ 檢查時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==========================================="

# 1. 檢查 tmux
echo "1️⃣  tmux Session:"
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "   ✅ 運行中 ($TMUX_SESSION_NAME)"
    echo "   📋 視窗狀態:"
    tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
else
    echo "   ❌ 未運行"
fi
echo ""

# 2. 檢查 Flask 與 Agent 活躍狀態
echo "2️⃣  API 伺服器狀態:"
API_DATA=$(curl -s "http://localhost:$FLASK_PORT/status" || echo "failed")
if [ "$API_DATA" != "failed" ]; then
    echo "   ✅ Flask 正常 (Port $FLASK_PORT)"
    ACTIVE=$(echo "$API_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['active_agent'])")
    echo "   ⭐ 當前活躍 Agent: $ACTIVE"
else
    echo "   ❌ 無法連接 API 服務"
fi
echo ""

# 3. 檢查 ngrok
echo "3️⃣  隧道狀態 (ngrok):"
if pgrep -f "ngrok http $FLASK_PORT" > /dev/null; then
    echo "   ✅ 運行中"
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data['tunnels'] else 'N/A')" 2>/dev/null)
    echo "   🌍 公網位址: $PUBLIC_URL"
else
    echo "   ❌ 未啟動"
fi
echo ""