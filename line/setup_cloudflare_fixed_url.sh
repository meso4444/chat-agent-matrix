#!/bin/bash
# 設定 Cloudflare Tunnel 固定 URL

# 從 Python config 讀取設定
SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="$SCRIPT_DIR/.env"

# 載入環境變數 (避免 config.py 報錯)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "🔐 已載入 .env 環境變數"
fi

TUNNEL_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_TUNNEL_NAME; print(CLOUDFLARE_TUNNEL_NAME)")
CUSTOM_DOMAIN=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_CUSTOM_DOMAIN; print(CLOUDFLARE_CUSTOM_DOMAIN)")
LOCAL_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

# 檢查域名是否為 None
if [ "$CUSTOM_DOMAIN" == "None" ] || [ -z "$CUSTOM_DOMAIN" ]; then
    echo "❌ 錯誤: 未設定自訂域名 (CLOUDFLARE_CUSTOM_DOMAIN)"
    echo "💡 請先執行 ./setup_config.sh 進行設定"
    exit 1
fi

echo "🧬 設定 Cloudflare Tunnel 固定 URL"
echo "📋 Tunnel 名稱: $TUNNEL_NAME"
echo "🌐 自訂域名: $CUSTOM_DOMAIN"
echo "📍 本地端口: $LOCAL_PORT"
echo ""

# 檢查 cloudflared 是否安裝
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared 未安裝，請先執行: ./install_dependencies.sh"
    exit 1
fi

# 步驟 1: 登入 Cloudflare
echo "🔐 步驟 1: 登入 Cloudflare"

# 檢查是否已經登入
echo "🔍 檢查 Cloudflare 登入狀態..."
if cloudflared tunnel list > /dev/null 2>&1; then
    echo "✅ 已經登入 Cloudflare，跳過登入步驟"
else
    echo "即將自動開啟瀏覽器進行 Cloudflare 登入..."
    echo ""
    echo "📋 登入步驟:"
    echo "1. 瀏覽器會自動開啟 Cloudflare 授權頁面"
    echo "2. 請在瀏覽器中登入你的 Cloudflare 帳號"
    echo "3. 點擊 'Authorize' 或 '授權' 按鈕"
    echo "4. 看到 'You have successfully logged in' 後回到此終端"
    echo ""
    echo "⚠️ 如果瀏覽器沒有自動開啟，請手動複製以下 URL："
    echo ""

    # 在背景執行登入命令，並設定超時
    timeout 120 cloudflared tunnel login &
    LOGIN_PID=$!
    
    echo "⏳ 等待瀏覽器授權中..."
    echo "💡 如果超過 2 分鐘未完成，將會自動取消"
    
    # 等待登入完成或超時
    if wait $LOGIN_PID; then
        echo "✅ Cloudflare 登入成功"
    else
        echo "❌ 登入超時或失敗"
        echo ""
        echo "🔧 請嘗試手動登入："
        echo "1. 開啟新終端"
        echo "2. 執行: cloudflared tunnel login"
        echo "3. 完成授權後按任意鍵繼續..."
        read -p ""
        
        # 再次檢查登入狀態
        if cloudflared tunnel list > /dev/null 2>&1; then
            echo "✅ 確認登入成功"
        else
            echo "❌ 仍未登入，請檢查網路連線或 Cloudflare 帳號狀態"
            exit 1
        fi
    fi
fi

# 步驟 2: 建立 tunnel
echo "🚀 步驟 2: 建立 tunnel"

# 檢查是否已存在
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "⚠️  Tunnel '$TUNNEL_NAME' 已存在"
    read -p "是否要刪除舊設定並重新建立? (y/N): " reset_choice
    
    if [[ "$reset_choice" =~ ^[Yy]$ ]]; then
        echo "🗑️ 正在清理舊設定..."
        
        # 嘗試清理 DNS
        cloudflared tunnel route dns delete $CUSTOM_DOMAIN 2>/dev/null
        
        # 刪除 Tunnel
        if cloudflared tunnel delete "$TUNNEL_NAME"; then
            echo "✅ 舊 Tunnel 已刪除"
        else
            echo "❌ 無法刪除舊 Tunnel (可能權限不足或不存在)"
        fi
        
        # 建立新的
        echo "🆕 建立新 tunnel: $TUNNEL_NAME"
        if cloudflared tunnel create "$TUNNEL_NAME"; then
            echo "✅ Tunnel 建立成功"
        else
            echo "❌ Tunnel 建立失敗"
            exit 1
        fi
    else
        echo "⏩ 保留現有 Tunnel 設定"
        
        # 檢查 credentials 文件是否存在
        EXISTING_TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        CREDENTIALS_FILE="$HOME/.cloudflared/$EXISTING_TUNNEL_ID.json"
        
        if [ ! -f "$CREDENTIALS_FILE" ]; then
            echo "❌ 錯誤: 缺少 credentials 文件: $CREDENTIALS_FILE"
            echo "💡 建議重新執行腳本並選擇 '刪除舊設定'"
            exit 1
        fi
    fi
else
    echo "建立 tunnel: $TUNNEL_NAME"
    if cloudflared tunnel create "$TUNNEL_NAME"; then
        echo "✅ Tunnel 建立成功"
    else
        echo "❌ Tunnel 建立失敗"
        exit 1
    fi
fi

# 取得 tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "🆔 Tunnel ID: $TUNNEL_ID"

# 步驟 3: 設定自訂域名路由
echo "🌐 步驟 3: 設定自訂域名路由"
echo "為 tunnel 設定自訂域名: $CUSTOM_DOMAIN"

# 先嘗試刪除現有記錄 (如果存在)
echo "🔍 檢查是否有現有 DNS 記錄..."
if nslookup $CUSTOM_DOMAIN > /dev/null 2>&1; then
    echo "⚠️ 發現現有 DNS 記錄，嘗試刪除..."
    cloudflared tunnel route dns delete $CUSTOM_DOMAIN 2>/dev/null || echo "💡 請手動刪除現有 DNS 記錄"
fi

# 建立新的路由 (強制覆蓋現有記錄)
if cloudflared tunnel route dns --overwrite-dns "$TUNNEL_NAME" "$CUSTOM_DOMAIN"; then
    echo "✅ 自訂域名路由設定成功"
    TUNNEL_URL="https://$CUSTOM_DOMAIN"
else
    echo "❌ 自訂域名路由設定失敗"
    echo ""
    echo "🔧 可能的解決方案："
    echo "1. 手動清理 DNS 記錄: ./cleanup_dns.sh"
    echo "2. 到 Cloudflare Dashboard 手動刪除 $CUSTOM_DOMAIN 記錄"
    echo "3. 確認域名正確託管在 Cloudflare"
    echo ""
    read -p "是否要繼續使用現有 DNS 記錄? (y/N): " continue_existing
    if [[ $continue_existing =~ ^[Yy]$ ]]; then
        echo "⚠️ 使用現有 DNS 記錄繼續..."
        TUNNEL_URL="https://$CUSTOM_DOMAIN"
    else
        echo "❌ 設定中止"
        exit 1
    fi
fi

# 步驟 4: 建立設定檔
echo "📝 步驟 4: 建立設定檔"
CONFIG_DIR="$HOME/.cloudflared"
CONFIG_FILE="$CONFIG_DIR/config.yml"

mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_FILE" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $CUSTOM_DOMAIN
    service: http://127.0.0.1:$LOCAL_PORT
  - service: http_status:404
EOF

echo "✅ 設定檔已建立: $CONFIG_FILE"

# 步驟 5: 配置完成
echo "⚙️ 步驟 5: 配置完成"
echo "✅ 已使用 cfargotunnel.com 固定域名，無需更新 config.py"

# 完成
echo ""
echo "🎉 Cloudflare Tunnel 固定 URL 設定完成！"
echo ""
echo "📋 設定摘要:"
echo "• Tunnel 名稱: $TUNNEL_NAME"
echo "• Tunnel ID: $TUNNEL_ID"
echo "• Tunnel URL: $TUNNEL_URL"
echo "• 設定檔: $CONFIG_FILE"
echo ""
echo "📍 LINE Webhook URL:"
echo "$TUNNEL_URL/webhook"
echo ""
echo "🚀 使用方式:"
echo "1. 設定 LINE webhook URL: $TUNNEL_URL/webhook (先不要驗證)"
echo "2. 啟動所有服務: ./start_all_services.sh"
echo "3. 在 LINE Console 驗證 webhook 連線 (點擊 Verify)"
echo "4. 連接到 tmux: tmux attach -t ai_line_session"
echo ""
echo "✨ 優點:"
echo "• 使用專業的自訂域名"
echo "• URL 永不改變，重啟後自動重連"
echo "• 使用 tmux 統一管理多個 Agent"