#!/bin/bash
# start_ngrok.sh (Precise Process Management Version)
# 啟動 ngrok 並自動配置 Telegram Webhook (使用動態密鑰 + PID 精確管理)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
RUNTIME_STATE_FILE="$SCRIPT_DIR/.runtime_state"
NGROK_LOG="$SCRIPT_DIR/ngrok.log"
NGROK_PID_FILE="$SCRIPT_DIR/.ngrok.pid"

# 支援獨立的 Ngrok Config 路徑
#NGROK_CONFIG_PATH="${NGROK_CONFIG_PATH:-}"
#if [[ -z "$NGROK_CONFIG_PATH" ]]; then
#    # 檢查是否存在 ngrok_dev.yml (用於 Dev 環境)
#    if [ -f "$SCRIPT_DIR/ngrok_dev.yml" ]; then
#        NGROK_CONFIG_PATH="$SCRIPT_DIR/ngrok_dev.yml"
#    else
#        # 預設配置 (如果存在)
#        NGROK_CONFIG_PATH=""
#    fi
#fi

cd "$SCRIPT_DIR"

# 載入環境變數
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ 錯誤: 環境變數 TELEGRAM_BOT_TOKEN 未設定"
    exit 1
fi

BOT_TOKEN="$TELEGRAM_BOT_TOKEN"

# 讀取動態 Secret
if [ ! -f "$SECRET_FILE" ]; then
    echo "❌ 錯誤: 找不到 Webhook Secret，請先執行 start_all_services.sh"
    exit 1
fi
WEBHOOK_SECRET=$(cat "$SECRET_FILE")

# 讀取 Port
FLASK_PORT=$(python3 -c "import sys; sys.path.append('.'); from config import FLASK_PORT; print(FLASK_PORT)")
NGROK_API_PORT=$(python3 -c "import sys; sys.path.append('.'); from config import NGROK_API_PORT; print(NGROK_API_PORT)" 2>/dev/null || echo "4040")

# ============================================================================
# 驗證與設置 ngrok Authtoken
# ============================================================================
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "❌ 錯誤: 環境變數 NGROK_AUTHTOKEN 未設定"
    exit 1
fi

# 確保 ngrok 配置目錄存在（ngrok 3 使用 ~/.config/ngrok）
mkdir -p ~/.config/ngrok

# 設置 ngrok 配置文件（包含 authtoken 和 web_addr）
NGROK_CONFIG_FILE="$HOME/.config/ngrok/ngrok.yml"
cat > "$NGROK_CONFIG_FILE" << EOF
version: "3"
agent:
    authtoken: $NGROK_AUTHTOKEN
    web_addr: 127.0.0.1:$NGROK_API_PORT
EOF

echo "🔐 ngrok 配置已設置:"
echo "   • Authtoken: ✅"
echo "   • Web API 端口: 127.0.0.1:$NGROK_API_PORT"

echo "🚀 正在啟動 ngrok (Port $FLASK_PORT)..."

# ============================================================================
# 精確清理：使用 PID 檔案而非 pkill 模式匹配
# ============================================================================
if [ -f "$NGROK_PID_FILE" ]; then
    OLD_NGROK_PID=$(cat "$NGROK_PID_FILE")
    if kill -0 "$OLD_NGROK_PID" 2>/dev/null; then
        echo "🔄 清理舊 ngrok 進程 (PID: $OLD_NGROK_PID)..."
        kill "$OLD_NGROK_PID" 2>/dev/null || true
        sleep 1
        # 如果進程仍在執行，強制殺死
        if kill -0 "$OLD_NGROK_PID" 2>/dev/null; then
            kill -9 "$OLD_NGROK_PID" 2>/dev/null || true
        fi
    fi
    rm -f "$NGROK_PID_FILE"
fi

rm -f "$NGROK_LOG"

# 啟動 ngrok
if [[ -n "$NGROK_CONFIG_PATH" && -f "$NGROK_CONFIG_PATH" ]]; then
    echo "📋 使用配置檔: $NGROK_CONFIG_PATH"
    nohup ngrok start --config "$NGROK_CONFIG_PATH" --all > "$NGROK_LOG" 2>&1 &
else
    echo "📋 使用默認配置 (Flask Port $FLASK_PORT)"
    # ngrok 3+ 不支持 --api 參數，使用默認的 ngrok http 命令
    # ngrok 3 的 API 服務器默認監聽在 unix socket 或其他方式
    nohup ngrok http $FLASK_PORT > "$NGROK_LOG" 2>&1 &
fi

NGROK_PID=$!
echo "📝 ngrok PID: $NGROK_PID"
echo "$NGROK_PID" > "$NGROK_PID_FILE"

echo "⏳ 等待 ngrok 建立連線並獲取 URL..."

# 輪詢 (Polling) 獲取公網 URL
# ngrok 3 配置了 web_addr，應該監聽在指定的 NGROK_API_PORT
PUBLIC_URL=""

for i in {1..10}; do
    echo "   ▸ 嘗試獲取網址 ($i/10)..."

    if command -v jq &> /dev/null; then
        PUBLIC_URL=$(curl -s http://localhost:$NGROK_API_PORT/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)
    else
        PUBLIC_URL=$(curl -s http://localhost:$NGROK_API_PORT/api/tunnels 2>/dev/null | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4 | head -1)
    fi

    # 檢查是否成功獲取有效 URL
    if [[ -n "$PUBLIC_URL" && "$PUBLIC_URL" != "null" && "$PUBLIC_URL" == http* ]]; then
        echo "✅ 成功獲取新網址: $PUBLIC_URL"
        break
    fi

    sleep 3
done

if [[ -z "$PUBLIC_URL" || "$PUBLIC_URL" == "null" ]]; then
    echo "❌ 獲取 ngrok URL 失敗 (超時 30 秒)"
    echo "📋 最近的 ngrok 日誌:"
    tail -n 5 "$NGROK_LOG"
    exit 1
fi

# 寫入運行時狀態檔 (供其他程式讀取)
echo "{\"ngrok_url\": \"$PUBLIC_URL\", \"ngrok_pid\": $NGROK_PID}" > "$RUNTIME_STATE_FILE"
echo "📝 已更新運行時狀態: $RUNTIME_STATE_FILE"

# 通知 Telegram 更新 Webhook (帶上 Secret Token)
WEBHOOK_URL="$PUBLIC_URL/telegram_webhook"
echo "🔄 正在更新 Telegram Webhook 到: $WEBHOOK_URL"

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
     -d "url=$WEBHOOK_URL" \
     -d "secret_token=$WEBHOOK_SECRET")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook 設定成功 (已啟用 Secret Token 驗證)"
else
    echo "❌ Webhook 設定失敗"
    echo "   回應: $RESPONSE"
fi

echo ""
echo "🎉 ngrok 啟動與配置完成！"
