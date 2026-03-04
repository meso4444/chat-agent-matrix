#!/bin/bash
# Chat Agent Matrix (LINE) - 系統狀態檢查

# 從 Python config 讀取設定
SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="$SCRIPT_DIR/.env"

# 載入環境變數
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "📊 Chat Agent Matrix (LINE) 系統狀態"
echo "⏰ 檢查時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==========================================="

# 1. 檢查 tmux
echo "1️⃣  tmux Session:"
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "   ✅ 運行中 ($TMUX_SESSION_NAME)"
    echo "   📋 視窗狀態:"
    tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name} (#{?window_active,⭐ 活躍,背景})"
else
    echo "   ❌ 未運行"
    echo "   💡 請執行: ./start_all_services.sh"
    exit 1
fi
echo ""

# 2. 檢查 Flask 與 Agent 活躍狀態
echo "2️⃣  API 伺服器狀態:"
API_DATA=$(curl -s --max-time 2 "http://127.0.0.1:$FLASK_PORT/status" || echo "failed")

if [ "$API_DATA" != "failed" ]; then
    echo "   ✅ Flask 正常 (Port $FLASK_PORT)"
    
    # 解析 JSON 顯示活躍 Agent
    ACTIVE=$(echo "$API_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('active_agent', 'Unknown'))" 2>/dev/null)
    echo "   ⭐ 當前活躍 Agent: $ACTIVE"
    
    # 簡單列出 Agent 狀態 (紅綠燈)
    echo "$API_DATA" | python3 -c "
import sys, json
try:
    agents = json.load(sys.stdin).get('agents', {})
    status_line = '   🤖 Agent 狀態: '
    for name, status in agents.items():
        icon = '🟢' if status else '🔴'
        status_line += f'{icon} {name}  '
    print(status_line)
except: pass
"
else
    echo "   ❌ 無法連接 API (Connection Refused)"
    echo "   💡 建議查看日誌: tmux capture-pane -t $TMUX_SESSION_NAME:line_api -p | tail -n 20"
fi
echo ""

# 3. 檢查 Cloudflare Tunnel
echo "3️⃣  隧道狀態 (Cloudflare):"
# 檢查 cloudflared 是否在 tmux 中運行
if tmux list-windows -t "$TMUX_SESSION_NAME" | grep -q "cloudflared"; then
    # 檢查是否有錯誤日誌
    TUNNEL_LOG=$(tmux capture-pane -t "$TMUX_SESSION_NAME:cloudflared" -p 2>/dev/null | tail -n 5)
    if [[ "$TUNNEL_LOG" == *"ERR"* || "$TUNNEL_LOG" == *"error"* ]]; then
        echo "   ⚠️  運行中但可能有錯誤:"
        echo "$TUNNEL_LOG"
    else
        echo "   ✅ 運行中"
        echo "   🌍 固定網址: (請參考 config.yaml 或 setup_cloudflare_fixed_url.sh 輸出)"
    fi
else
    echo "   ❌ 未啟動"
fi
echo ""

echo "🔧 管理命令:"
echo "   • 進入終端: tmux attach -t $TMUX_SESSION_NAME"
echo "   • 重啟服務: ./stop_all_services.sh && ./start_all_services.sh"