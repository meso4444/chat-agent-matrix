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

# 0. 設定 Port (避免與其他服務衝突)
echo "--------------------------------------------------------"
echo "🔌 設定 1/4: Port 配置"
echo "--------------------------------------------------------"
echo "請設定服務通訊埠，以避免與其他應用程式衝突。"
echo ""
echo "預設值:"
echo "  • Flask Webhook Port: 5000"
echo "  • Ngrok API Port: 4040"
echo ""

read -p "Flask Webhook Port [預設: 5000]: " INPUT_FLASK_PORT
FLASK_PORT="${INPUT_FLASK_PORT:-5000}"

read -p "Ngrok API Port [預設: 4040]: " INPUT_NGROK_API_PORT
NGROK_API_PORT="${INPUT_NGROK_API_PORT:-4040}"

echo "✅ Port 已設定: Flask=$FLASK_PORT, Ngrok API=$NGROK_API_PORT"
echo ""

# 1. 設定 ngrok Authtoken
echo "--------------------------------------------------------"
echo "🔑 設定 2/4: ngrok Authtoken"
echo "--------------------------------------------------------"
echo "請至 https://dashboard.ngrok.com/get-started/your-authtoken 取得"
echo "目前設定: ${NGROK_AUTHTOKEN:-未設定}"
echo ""
read -p "請輸入 ngrok Authtoken (按 Enter 保留原值): " INPUT_NGROK_TOKEN

if [ -n "$INPUT_NGROK_TOKEN" ]; then
    NGROK_AUTHTOKEN="$INPUT_NGROK_TOKEN"
    echo "✅ ngrok Authtoken 已記錄"
else
    NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN"
    echo "⏭️  保留現有 ngrok 設定"
fi
echo ""

# 2. 設定 Telegram Bot Token
echo "--------------------------------------------------------"
echo "🤖 設定 3/4: Telegram Bot Token"
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
echo "👤 設定 4/4: Telegram Chat ID"
echo "--------------------------------------------------------"
echo "這是您的個人 ID，用於驗證身份。"
echo "💡 系統將自動偵測，需要您傳送一條訊息給 Bot（例如 /start）。"
echo ""

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

# 物理生成 .env 檔案（簡化模式，不涉及 Multi-Bot 註冊）
cat > "$ENV_FILE" << EOF
NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

echo "✅ 設定已儲存至 .env"
echo ""

# 更新 config.yaml 中的 Port 配置
echo "💾 正在更新 Port 配置到 config.yaml..."
CONFIG_YAML="$SCRIPT_DIR/config.yaml"

if [ -f "$CONFIG_YAML" ]; then
    # 使用 Python 更新 YAML 中的 Port（保留原有縮排和格式）
    python3 << PYTHON_EOF
import re

with open('$CONFIG_YAML', 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查是否已有 server 段落
if 'server:' in content:
    # 更新現有 port
    content = re.sub(r'(\s+)port:\s*\d+', r'\1port: $FLASK_PORT', content)
    # 如果沒有 ngrok_api_port，則添加
    if 'ngrok_api_port:' not in content:
        content = re.sub(r'(server:.*?\n\s+port:.*?\n)', r'\1  ngrok_api_port: $NGROK_API_PORT\n', content, flags=re.DOTALL)
    else:
        content = re.sub(r'(\s+)ngrok_api_port:\s*\d+', r'\1ngrok_api_port: $NGROK_API_PORT', content)
else:
    # 如果沒有 server 段落，添加到文件末尾
    if not content.endswith('\n'):
        content += '\n'
    content += f'server:\n  port: $FLASK_PORT\n  ngrok_api_port: $NGROK_API_PORT\n'

with open('$CONFIG_YAML', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Port 已更新到 config.yaml:")
print("   • Flask Port: $FLASK_PORT")
print("   • Ngrok API Port: $NGROK_API_PORT")
PYTHON_EOF
else
    echo "⚠️  config.yaml 不存在，將在首次啟動時生成"
fi

echo ""
echo "🎉 設定完成！您可以執行 ./start_all_services.sh 啟動服務了。"
echo ""
