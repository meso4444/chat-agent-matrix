#!/bin/bash
# start_ngrok.sh (Secure Version)
# 啟動 ngrok 並自動配置 Telegram Webhook (使用動態密鑰)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
RUNTIME_STATE_FILE="$SCRIPT_DIR/.runtime_state"
NGROK_LOG="$SCRIPT_DIR/ngrok.log"

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

echo "🚀 正在啟動 ngrok (Port $FLASK_PORT)..."

# 清理舊進程
pkill -f "ngrok http $FLASK_PORT"
rm -f "$NGROK_LOG"

# 啟動 ngrok
nohup ngrok http $FLASK_PORT > "$NGROK_LOG" 2>&1 &
NGROK_PID=$!

echo "⏳ 等待 ngrok 建立連線並獲取 URL..."

# 輪詢 (Polling) 獲取公網 URL
PUBLIC_URL=""
for i in {1..10}; do
    echo "   ▸ 嘗試獲取網址 ($i/10)..."
    
    if command -v jq &> /dev/null; then
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    else
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4 | head -1)
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
echo "{\"ngrok_url\": \"$PUBLIC_URL\"}" > "$RUNTIME_STATE_FILE"
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