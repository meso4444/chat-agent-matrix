#!/bin/bash
# Establish secure HTTPS connection using Cloudflare Tunnel (fixed URL only)

# Read configuration from Python config
SCRIPT_DIR="$(dirname "$0")"
LOCAL_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")
TUNNEL_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_TUNNEL_NAME; print(CLOUDFLARE_TUNNEL_NAME)")
CONFIG_FILE=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_CONFIG_FILE; print(CLOUDFLARE_CONFIG_FILE)")

echo "☁️ Starting Cloudflare Tunnel..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not installed"
    echo ""
    echo "📦 Installation methods:"
    echo ""
    echo "🐧 Linux (Debian/Ubuntu):"
    echo "curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
    echo "sudo dpkg -i cloudflared.deb"
    echo ""
    echo "🍎 macOS:"
    echo "brew install cloudflared"
    echo ""
    echo "🪟 Windows:"
    echo "Visit https://github.com/cloudflare/cloudflared/releases to download"
    echo ""
    echo "📋 Or use quick install script:"
    echo "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared"
    echo "chmod +x cloudflared"
    echo "sudo mv cloudflared /usr/local/bin/"
    exit 1
fi

# Check if local Flask is running
echo "🔍 Checking local Flask service (port: $LOCAL_PORT)..."
if ! curl -s http://127.0.0.1:$LOCAL_PORT/status > /dev/null; then
    echo "❌ Local Flask service not running"
    echo "Please first run: python3 webhook_server.py"
    exit 1
fi

echo "✅ Local Flask service running normally"

# Check if logged in to Cloudflare
echo "🧬 Starting fixed URL mode"

if ! cloudflared tunnel list > /dev/null 2>&1; then
    echo "🔐 Need to log in to Cloudflare and create fixed tunnel..."
    echo ""
    echo "📋 Please first run the setup script:"
    echo "./setup_cloudflare_fixed_url.sh"
    echo ""
    echo "💡 This script will automatically complete login, create tunnel and configure"
    exit 1
fi

# Check if tunnel exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "✅ Found fixed tunnel: $TUNNEL_NAME"

    # Check if configuration file exists
    CONFIG_PATH="$HOME/.cloudflared/config.yml"
    if [ -n "$CONFIG_FILE" ]; then
        CONFIG_PATH="$CONFIG_FILE"
    fi

    if [ -f "$CONFIG_PATH" ]; then
        echo "✅ Found configuration file: $CONFIG_PATH"
        echo "🚀 Starting fixed Cloudflare Tunnel..."
        echo "📍 Local service: http://127.0.0.1:$LOCAL_PORT"

        # Get tunnel URL
        TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        TUNNEL_URL="https://$TUNNEL_ID.cfargotunnel.com"
        echo "🌐 Fixed URL: $TUNNEL_URL"
        echo "📍 Webhook URL: $TUNNEL_URL/webhook"
        echo "⏹️ Press Ctrl+C to stop tunnel"
        echo ""

        # Start using configuration file
        cloudflared tunnel --config "$CONFIG_PATH" run
    else
        echo "⚠️ Configuration file not found: $CONFIG_PATH"
        echo "🚀 Attempting to start tunnel directly..."

        # Start tunnel directly
        cloudflared tunnel run $TUNNEL_NAME
    fi
else
    echo "❌ Tunnel not found: $TUNNEL_NAME"
    echo "📋 Please first run the setup script:"
    echo "./setup_cloudflare_fixed_url.sh"
    exit 1
fi