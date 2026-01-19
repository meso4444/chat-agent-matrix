#!/bin/bash
# setup_config.sh
# Chat Agent Matrix 互動式設定精靈

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# 載入現有設定 (如果有的話)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

echo "========================================================"
echo "☀️🌙 Chat Agent Matrix 設定精靈"
echo "========================================================"
echo ""

# 1. 設定 ngrok Authtoken
echo "--------------------------------------------------------"
echo "🔑 設定 1/3: ngrok Authtoken"
echo "--------------------------------------------------------"
echo "請至 https://dashboard.ngrok.com/get-started/your-authtoken 取得"
echo "如果您已經設定過，可以直接按 Enter 跳過。"
echo ""
read -p "請輸入 ngrok Authtoken: " INPUT_NGROK_TOKEN

if [ -n "$INPUT_NGROK_TOKEN" ]; then
    if command -v ngrok &> /dev/null; then
        ngrok config add-authtoken "$INPUT_NGROK_TOKEN"
        echo "✅ ngrok Token 設定完成"
    else
        echo "⚠️  ngrok 未安裝，將跳過設定 (請先執行 install_dependencies.sh)"
    fi
else
    echo "⏭️  保留現有 ngrok 設定"
fi
echo ""

# 2. 設定 Telegram Bot Token
echo "--------------------------------------------------------"
echo "🤖 設定 2/3: Telegram Bot Token"
echo "--------------------------------------------------------"
echo "請至 Telegram 搜尋 @BotFather 創建機器人並取得 Token。"
echo "目前設定: ${TELEGRAM_BOT_TOKEN:-未設定}"
echo ""
read -p "請輸入 Bot Token (按 Enter 保留原值): " INPUT_BOT_TOKEN

if [ -n "$INPUT_BOT_TOKEN" ]; then
    BOT_TOKEN="$INPUT_BOT_TOKEN"
else
    BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
fi
echo ""

# 3. 設定 Chat ID
echo "--------------------------------------------------------"
echo "👤 設定 3/3: Telegram Chat ID"
echo "--------------------------------------------------------"
echo "這是您的個人 ID，用於驗證身份。"

# 定義自動獲取函數
get_chat_id_from_api() {
    export PY_BOT_TOKEN="$1"
    python3 -c "
import requests, sys, time, os

try:
    token = os.environ['PY_BOT_TOKEN']
    
    # 1. 刪除 Webhook
    requests.post(f'https://api.telegram.org/bot{token}/deleteWebhook')
    
    # 2. 輪詢 (Polling) 等待訊息
    print('   ⏳ 正在等待訊息抵達 (最多 30 秒)...', file=sys.stderr)
    for i in range(10):
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        res = requests.get(url, timeout=5).json()
        
        if not res.get('ok'):
            print(f\"API Error: {res.get('description')}\", file=sys.stderr)
            sys.exit(2)
            
        if res['result']:
            # 成功抓到！
            print(res['result'][-1]['message']['chat']['id'])
            sys.exit(0)
        
        # 沒抓到，等待 3 秒重試
        time.sleep(3)
        
    sys.exit(1) # 超時無訊息
except Exception as e:
    print(f\"Error: {e}\", file=sys.stderr)
    sys.exit(2)
"
}

# 嘗試自動獲取
DETECTED_CHAT_ID=""
if [ -n "$BOT_TOKEN" ]; then
    echo "🔄 正在嘗試自動獲取您的 Chat ID..."
    # 這裡移除 2>/dev/null 以便顯示 Python 的錯誤輸出，但我們只抓 stdout 給變數
    # 為了美觀，我們將 stderr 暫存
    ERR_LOG=$(mktemp)
    DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")
    
    if [ -z "$DETECTED_CHAT_ID" ]; then
        echo "⚠️  目前無法自動獲取"
        
        # 強制先刪除 Webhook，進入手動拉取模式
        python3 -c "import requests; requests.post(f'https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook')" > /dev/null 2>&1
        
        echo "👉 系統已切換至偵測模式。請「現在」傳送一則訊息 (如 /start) 給您的 Bot。"
        read -p "   發送後，請按 Enter 鍵重試..." dummy
        
        echo "🔄 正在讀取..."
        # 這裡的函數內部也會再做一次 deleteWebhook 以策萬全，但關鍵是上面的那次
        DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")
    fi
    
    rm -f "$ERR_LOG"
    
    if [ -n "$DETECTED_CHAT_ID" ]; then
        echo "✅ 成功獲取 Chat ID: $DETECTED_CHAT_ID"
    else
        echo "❌ 仍無法自動獲取。您可以稍後手動填寫。"
    fi
fi

CURRENT_ID="${TELEGRAM_CHAT_ID:-$DETECTED_CHAT_ID}"
echo "目前設定: ${CURRENT_ID:-未設定}"
echo ""
read -p "請輸入 Chat ID (按 Enter 使用 [${DETECTED_CHAT_ID:-保留原值}]): " INPUT_CHAT_ID

if [ -n "$INPUT_CHAT_ID" ]; then
    CHAT_ID="$INPUT_CHAT_ID"
elif [ -n "$DETECTED_CHAT_ID" ]; then
    CHAT_ID="$DETECTED_CHAT_ID"
else
    CHAT_ID="$TELEGRAM_CHAT_ID"
fi

# 寫入 .env 檔案
echo "--------------------------------------------------------"
echo "💾 正在儲存設定..."

# 如果 .env 不存在，從 example 複製
if [ ! -f "$ENV_FILE" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
fi

# 使用 sed 更新 .env (如果檔案存在)
# 若檔案不存在則直接建立
if [ ! -f "$ENV_FILE" ]; then
    echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" > "$ENV_FILE"
    echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> "$ENV_FILE"
else
    # 更新 BOT_TOKEN
    if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
        # 使用 | 作為分隔符避免內容衝突
        sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$BOT_TOKEN|" "$ENV_FILE"
    else
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"
    fi
    
    # 更新 CHAT_ID
    if grep -q "TELEGRAM_CHAT_ID=" "$ENV_FILE"; then
        sed -i "s|TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=$CHAT_ID|" "$ENV_FILE"
    else
        echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> "$ENV_FILE"
    fi
fi

echo "✅ 設定已儲存至 .env"
echo ""
echo "🎉 設定完成！您可以執行 ./start_all_services.sh 啟動服務了。"
echo ""
