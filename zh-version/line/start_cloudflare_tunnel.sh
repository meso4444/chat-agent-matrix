#!/bin/bash
# 使用 Cloudflare Tunnel 建立安全的 HTTPS 連線 (僅支援固定 URL)

# 從 Python config 讀取設定
SCRIPT_DIR="$(dirname "$0")"
LOCAL_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")
TUNNEL_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_TUNNEL_NAME; print(CLOUDFLARE_TUNNEL_NAME)")
CONFIG_FILE=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_CONFIG_FILE; print(CLOUDFLARE_CONFIG_FILE)")

echo "☁️ 啟動 Cloudflare Tunnel..."

# 檢查 cloudflared 是否安裝
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared 未安裝"
    echo ""
    echo "📦 安裝方式："
    echo ""
    echo "🐧 Linux (Debian/Ubuntu):"
    echo "curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
    echo "sudo dpkg -i cloudflared.deb"
    echo ""
    echo "🍎 macOS:"
    echo "brew install cloudflared"
    echo ""
    echo "🪟 Windows:"
    echo "前往 https://github.com/cloudflare/cloudflared/releases 下載"
    echo ""
    echo "📋 或使用快速安裝腳本："
    echo "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared"
    echo "chmod +x cloudflared"
    echo "sudo mv cloudflared /usr/local/bin/"
    exit 1
fi

# 檢查本地 Flask 是否運行
echo "🔍 檢查本地 Flask 服務 (port: $LOCAL_PORT)..."
if ! curl -s http://127.0.0.1:$LOCAL_PORT/status > /dev/null; then
    echo "❌ 本地 Flask 服務未運行"
    echo "請先執行: python3 webhook_server.py"
    exit 1
fi

echo "✅ 本地 Flask 服務運行正常"

# 檢查是否已登入 Cloudflare
echo "🧬 啟動固定 URL 模式"

if ! cloudflared tunnel list > /dev/null 2>&1; then
    echo "🔐 需要登入 Cloudflare 並建立固定 tunnel..."
    echo ""
    echo "📋 請先執行設定腳本:"
    echo "./setup_cloudflare_fixed_url.sh"
    echo ""
    echo "💡 該腳本會自動完成登入、建立 tunnel 和配置"
    exit 1
fi

# 檢查 tunnel 是否存在
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "✅ 找到固定 tunnel: $TUNNEL_NAME"
    
    # 檢查是否有設定檔
    CONFIG_PATH="$HOME/.cloudflared/config.yml"
    if [ -n "$CONFIG_FILE" ]; then
        CONFIG_PATH="$CONFIG_FILE"
    fi
    
    if [ -f "$CONFIG_PATH" ]; then
        echo "✅ 找到設定檔: $CONFIG_PATH"
        echo "🚀 啟動固定 Cloudflare Tunnel..."
        echo "📍 本地服務: http://127.0.0.1:$LOCAL_PORT"
        
        # 取得 tunnel URL
        TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        TUNNEL_URL="https://$TUNNEL_ID.cfargotunnel.com"
        echo "🌐 固定 URL: $TUNNEL_URL"
        echo "📍 Webhook URL: $TUNNEL_URL/webhook"
        echo "⏹️ 按 Ctrl+C 停止 tunnel"
        echo ""
        
        # 使用設定檔啟動
        cloudflared tunnel --config "$CONFIG_PATH" run
    else
        echo "⚠️ 找不到設定檔: $CONFIG_PATH"
        echo "🚀 嘗試直接啟動 tunnel..."
        
        # 直接啟動 tunnel
        cloudflared tunnel run $TUNNEL_NAME
    fi
else
    echo "❌ 未找到 tunnel: $TUNNEL_NAME"
    echo "📋 請先執行設定腳本:"
    echo "./setup_cloudflare_fixed_url.sh"
    exit 1
fi