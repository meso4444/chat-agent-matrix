#!/bin/bash
# Chat Agent Matrix (LINE) - 互動式設定精靈
# 協助生成 .env 環境變數檔案，保護敏感資訊

ENV_FILE=".env"

# 載入現有設定作為預設值
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

echo "🤖 Chat Agent Matrix (LINE Edition) 設定精靈"
echo "============================================="
echo "此腳本將協助您設定 LINE Bot 與 Cloudflare 的敏感憑證。"
echo "按 Enter 可保留 [中括號] 內的現有設定。"
echo ""

# 函數：讀取輸入並支援預設值
get_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_secret="$4"
    
    local display_default="$default"
    if [ "$is_secret" == "true" ] && [ -n "$default" ]; then
        display_default="${default:0:5}******"
    fi
    
    if [ -n "$display_default" ]; then
        echo -e "📝 $prompt [預設: $display_default]"
    else
        echo -e "📝 $prompt"
    fi
    
    read -p "> " input
    
    if [ -z "$input" ]; then
        input="$default"
    fi
    
    # 匯出變數供後續寫入
    eval "$var_name=\"$input\""
}

# 1. LINE Channel Access Token
get_input "請輸入 LINE Channel Access Token" "$LINE_CHANNEL_ACCESS_TOKEN" "NEW_LINE_TOKEN" "true"
echo ""

# 2. LINE Channel Secret
get_input "請輸入 LINE Channel Secret" "$LINE_CHANNEL_SECRET" "NEW_LINE_SECRET" "true"
echo ""

# 3. Cloudflare Tunnel Name
# 這是給 Tunnel 取個名字，例如 'line-bot-tunnel'
get_input "請為您的 Cloudflare Tunnel 取個名字 (例如 line-bot)" "${CLOUDFLARE_TUNNEL_NAME:-line-bot-tunnel}" "NEW_CF_NAME" "false"
echo ""

# 4. Cloudflare Custom Domain
# 這是完整的子域名，例如 webhook.meso4444.dpdns.org
echo "📝 請輸入您希望使用的 Webhook 完整網址 (子域名)"
echo "   例如: webhook.example.com"
echo "   (注意: 您必須擁有 example.com 的 Cloudflare 管理權限)"
get_input "網址" "$CLOUDFLARE_CUSTOM_DOMAIN" "NEW_CF_DOMAIN" "false"

# 寫入 .env
echo ""
echo "💾 正在寫入設定至 $ENV_FILE..."

cat > "$ENV_FILE" <<EOF
# LINE Bot Credentials
LINE_CHANNEL_ACCESS_TOKEN=$NEW_LINE_TOKEN
LINE_CHANNEL_SECRET=$NEW_LINE_SECRET

# Cloudflare Tunnel Configuration
CLOUDFLARE_TUNNEL_NAME=$NEW_CF_NAME
CLOUDFLARE_CUSTOM_DOMAIN=$NEW_CF_DOMAIN
EOF

echo "✅ 設定完成！"
echo "👉 接下來請執行 ./setup_cloudflare_fixed_url.sh 建立連線"