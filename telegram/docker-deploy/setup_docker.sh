#!/bin/bash
# setup_docker.sh - Chat Agent Matrix Docker Deployment Configuration Wizard
# Purpose: Setup Docker instance with credentials and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_GENERATOR="$SCRIPT_DIR/generate_config.py"

echo "=========================================="
echo "🐳 Chat Agent Matrix - Docker 實例設置精靈"
echo "=========================================="
echo ""

# Step 1: 實例命名
echo "步驟 1/3：實例命名"
echo "----------------------------------------"
echo "實例名稱用於區分不同的部署環境或測試場景"
echo ""
echo "💡 命名建議範例："
echo "   • 技術環境：dev, staging, production, test, sandbox"
echo "   • 應用場景：travel_planner, investment_advisor, meditation_coach"
echo "   • 專案代號：gupta, chod, omega, alpha, nexus"
echo "   • 個人用途：work, hobby, research, learning, experiment"
echo "   • 創意組合：anything_goes（只要符合規範即可）"
echo ""
echo "⚠️  限制：只允許字母、數字和下劃線（不含空格或特殊符號）"
echo ""

# 實例名稱驗證函數
validate_instance_name() {
  local name="$1"
  if [[ ! "$name" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ 無效的實例名稱：'$name'"
    echo "   允許的字符：字母、數字、下劃線"
    return 1
  fi
  return 0
}

# 循環讀取直到有效
while true; do
  read -p "請輸入實例名稱: " INSTANCE_NAME
  if validate_instance_name "$INSTANCE_NAME"; then
    break
  fi
done

echo "✓ 實例已鎖定：$INSTANCE_NAME"
echo ""

ENV_FILE="$SCRIPT_DIR/.env.${INSTANCE_NAME}"

# Step 2: ngrok 憑證
echo "步驟 2/3：ngrok 認證令牌"
echo "----------------------------------------"
read -p "請輸入 Authtoken: " INPUT_NGROK_TOKEN
NGROK_AUTHTOKEN="${INPUT_NGROK_TOKEN:-}"
echo "✓ ngrok 已記錄"
echo ""

# Step 3: Telegram 設置
echo "步驟 3/3：Telegram 設置"
echo "----------------------------------------"
read -p "請輸入 Bot Token: " BOT_TOKEN
echo "✓ Telegram Bot 已記錄"
echo ""

# --- 自動獲取 Chat ID 函數 ---
get_chat_id_from_api() {
    export PY_BOT_TOKEN="$1"
    python3 -c "
import requests, sys, time, os
try:
    token = os.environ['PY_BOT_TOKEN']
    requests.post(f'https://api.telegram.org/bot{token}/deleteWebhook')
    for i in range(10):
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        res = requests.get(url, timeout=5).json()
        if res.get('ok') and res['result']:
            print(res['result'][-1]['message']['chat']['id'])
            sys.exit(0)
        time.sleep(3)
    sys.exit(1)
except: sys.exit(2)
"
}

# Telegram Chat ID (自動偵測)
echo "Telegram Chat ID（自動偵測）"
echo "----------------------------------------"
DETECTED_CHAT_ID=""
if [ -n "$BOT_TOKEN" ]; then
    echo "🔄 正在嘗試自動獲取您的 Chat ID..."
    echo "👉 請傳送一則訊息 (如 /start) 給您的 Bot。"
    DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN") || echo ""
    
    if [ -n "$DETECTED_CHAT_ID" ]; then
        echo "✅ 成功獲取 Chat ID: $DETECTED_CHAT_ID"
    else
        echo "⚠️  自動獲取失敗，請手動輸入。"
    fi
fi

read -p "請輸入 Chat ID [預設: ${DETECTED_CHAT_ID}]: " INPUT_CHAT_ID
CHAT_ID="${INPUT_CHAT_ID:-$DETECTED_CHAT_ID}"
echo "✓ Chat ID 已記錄: $CHAT_ID"
echo ""

# 物理生成 .env 檔案
# 【注意】
#   - Port 信息不應寫入 .env，而是寫入 config.yaml（由 generate_config.py 處理）
#   - INSTANCE_NAME 在 docker-compose environment 部分被顯式設置，會覆蓋 .env 中的值，故不需寫入
cat > "$ENV_FILE" << EOF
NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

# Agent 配置（選擇性）
echo "=========================================="
echo "🤖 Agent 配置（選擇性）"
echo "=========================================="
echo ""
read -p "是否為此實例定義專屬 Agent? [y/N]: " DEFINE_AGENTS

AGENTS_DATA=""
if [[ "$DEFINE_AGENTS" =~ ^[Yy]$ ]]; then
    agent_count=0
    add_agent="Y"
    while [[ "$add_agent" =~ ^[Yy]$ ]]; do
        agent_count=$((agent_count + 1))
        echo ""
        echo "Agent #$agent_count 配置"
        read -p "  名稱 (例如 Index): " AGENT_NAME
        if [ -z "$AGENT_NAME" ]; then break; fi
        read -p "  引擎 (gemini/claude) [gemini]: " ENGINE
        ENGINE="${ENGINE:-gemini}"
        read -p "  職責 (usecase): " USECASE
        read -p "  描述 (description): " DESCRIPTION
        AGENTS_DATA="${AGENTS_DATA}|||${AGENT_NAME}:${ENGINE}:${USECASE}:${DESCRIPTION}"
        read -p "繼續建立下一個? [y/N]: " add_agent
        add_agent="${add_agent:-N}"
    done
    if [ -n "$AGENTS_DATA" ]; then AGENTS_DATA="${AGENTS_DATA:3}"; fi
fi

echo ""
echo "⚙️  正在調用生成器物理落地配置..."

# 調用外部生成器產生 config.yaml
python3 "$CONFIG_GENERATOR" "config" "$INSTANCE_NAME" "$AGENTS_DATA" "$SCRIPT_DIR"

# 調用外部生成器產生 docker-compose override
python3 "$CONFIG_GENERATOR" "compose" "$INSTANCE_NAME" "" "$SCRIPT_DIR"

# 建立容器憑證持久化目錄
echo "📁 正在建立容器憑證存儲目錄..."
mkdir -p "$SCRIPT_DIR/container_home/$INSTANCE_NAME"
chmod 750 "$SCRIPT_DIR/container_home/$INSTANCE_NAME"
echo "✅ 憑證目錄已建立: $SCRIPT_DIR/container_home/$INSTANCE_NAME"

echo ""
echo "=========================================="
echo "✅ 實例設置完成！"
echo ""
echo "生成的文件："
echo "  • .env.${INSTANCE_NAME}"
echo "  • config.${INSTANCE_NAME}.yaml"
echo "  • docker-compose.${INSTANCE_NAME}.yml"
echo "  • container_home/${INSTANCE_NAME}/ (認證存儲)"
echo ""
echo "標準流程（手動執行）："
echo "  1️⃣  設置 AI Agent 認證："
echo "     bash ../agent_credential_wizard.sh"
echo ""
echo "  2️⃣  構建鏡像："
echo "     docker compose -f docker-compose.${INSTANCE_NAME}.yml build bot"
echo ""
echo "  3️⃣  啟動容器："
echo "     docker compose -f docker-compose.${INSTANCE_NAME}.yml up -d bot"
echo ""
echo "  4️⃣  檢查狀態："
echo "     docker ps -a | grep chat-agent-${INSTANCE_NAME}"
echo ""
echo "=========================================="
echo ""
