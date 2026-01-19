#!/bin/bash
# Configure Cloudflare Tunnel fixed URL

# Read configuration from Python config
SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="$SCRIPT_DIR/.env"

# Load environment variables (avoid config.py errors)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "🔐 .env environment variables loaded"
fi

TUNNEL_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_TUNNEL_NAME; print(CLOUDFLARE_TUNNEL_NAME)")
CUSTOM_DOMAIN=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import CLOUDFLARE_CUSTOM_DOMAIN; print(CLOUDFLARE_CUSTOM_DOMAIN)")
LOCAL_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

# Check if domain is None
if [ "$CUSTOM_DOMAIN" == "None" ] || [ -z "$CUSTOM_DOMAIN" ]; then
    echo "❌ Error: Custom domain not configured (CLOUDFLARE_CUSTOM_DOMAIN)"
    echo "💡 Please first run ./setup_config.sh to configure"
    exit 1
fi

echo "🧬 Configuring Cloudflare Tunnel fixed URL"
echo "📋 Tunnel name: $TUNNEL_NAME"
echo "🌐 Custom domain: $CUSTOM_DOMAIN"
echo "📍 Local port: $LOCAL_PORT"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not installed, please first run: ./install_dependencies.sh"
    exit 1
fi

# Step 1: Log in to Cloudflare
echo "🔐 Step 1: Log in to Cloudflare"

# Check if already logged in
echo "🔍 Checking Cloudflare login status..."
if cloudflared tunnel list > /dev/null 2>&1; then
    echo "✅ Already logged in to Cloudflare, skipping login step"
else
    echo "Browser will automatically open for Cloudflare login..."
    echo ""
    echo "📋 Login steps:"
    echo "1. Browser will automatically open Cloudflare authorization page"
    echo "2. Please log in to your Cloudflare account in the browser"
    echo "3. Click 'Authorize' button"
    echo "4. After seeing 'You have successfully logged in' return to this terminal"
    echo ""
    echo "⚠️ If browser doesn't open automatically, please manually copy the URL below:"
    echo ""

    # Run login command in background with timeout
    timeout 120 cloudflared tunnel login &
    LOGIN_PID=$!

    echo "⏳ Waiting for browser authorization..."
    echo "💡 If not completed within 2 minutes, will automatically cancel"

    # Wait for login to complete or timeout
    if wait $LOGIN_PID; then
        echo "✅ Cloudflare login successful"
    else
        echo "❌ Login timeout or failed"
        echo ""
        echo "🔧 Please try manual login:"
        echo "1. Open new terminal"
        echo "2. Run: cloudflared tunnel login"
        echo "3. After completing authorization press any key to continue..."
        read -p ""

        # Check login status again
        if cloudflared tunnel list > /dev/null 2>&1; then
            echo "✅ Confirmed login successful"
        else
            echo "❌ Still not logged in, please check network connection or Cloudflare account status"
            exit 1
        fi
    fi
fi

# Step 2: Create tunnel
echo "🚀 Step 2: Create tunnel"

# Check if already exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "⚠️  Tunnel '$TUNNEL_NAME' already exists"
    read -p "Delete old configuration and recreate? (y/N): " reset_choice

    if [[ "$reset_choice" =~ ^[Yy]$ ]]; then
        echo "🗑️ Cleaning up old configuration..."

        # Try to clean up DNS
        cloudflared tunnel route dns delete $CUSTOM_DOMAIN 2>/dev/null

        # Delete Tunnel
        if cloudflared tunnel delete "$TUNNEL_NAME"; then
            echo "✅ Old Tunnel deleted"
        else
            echo "❌ Unable to delete old Tunnel (may have insufficient permissions or not exist)"
        fi

        # Create new one
        echo "🆕 Creating new tunnel: $TUNNEL_NAME"
        if cloudflared tunnel create "$TUNNEL_NAME"; then
            echo "✅ Tunnel created successfully"
        else
            echo "❌ Tunnel creation failed"
            exit 1
        fi
    else
        echo "⏩ Keep existing Tunnel configuration"

        # Check if credentials file exists
        EXISTING_TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        CREDENTIALS_FILE="$HOME/.cloudflared/$EXISTING_TUNNEL_ID.json"

        if [ ! -f "$CREDENTIALS_FILE" ]; then
            echo "❌ Error: Missing credentials file: $CREDENTIALS_FILE"
            echo "💡 Recommend re-running script and selecting 'Delete old configuration'"
            exit 1
        fi
    fi
else
    echo "Creating tunnel: $TUNNEL_NAME"
    if cloudflared tunnel create "$TUNNEL_NAME"; then
        echo "✅ Tunnel created successfully"
    else
        echo "❌ Tunnel creation failed"
        exit 1
    fi
fi

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "🆔 Tunnel ID: $TUNNEL_ID"

# Step 3: Configure custom domain routing
echo "🌐 Step 3: Configure custom domain routing"
echo "Setting up custom domain for tunnel: $CUSTOM_DOMAIN"

# Try to delete existing records first (if exists)
echo "🔍 Checking for existing DNS records..."
if nslookup $CUSTOM_DOMAIN > /dev/null 2>&1; then
    echo "⚠️ Found existing DNS record, attempting to delete..."
    cloudflared tunnel route dns delete $CUSTOM_DOMAIN 2>/dev/null || echo "💡 Please manually delete existing DNS record"
fi

# Create new route (force overwrite existing records)
if cloudflared tunnel route dns --overwrite-dns "$TUNNEL_NAME" "$CUSTOM_DOMAIN"; then
    echo "✅ Custom domain routing configured successfully"
    TUNNEL_URL="https://$CUSTOM_DOMAIN"
else
    echo "❌ Custom domain routing configuration failed"
    echo ""
    echo "🔧 Possible solutions:"
    echo "1. Manually clean DNS records: ./cleanup_dns.sh"
    echo "2. Manually delete $CUSTOM_DOMAIN record in Cloudflare Dashboard"
    echo "3. Verify domain is correctly hosted on Cloudflare"
    echo ""
    read -p "Continue using existing DNS record? (y/N): " continue_existing
    if [[ $continue_existing =~ ^[Yy]$ ]]; then
        echo "⚠️ Using existing DNS record to continue..."
        TUNNEL_URL="https://$CUSTOM_DOMAIN"
    else
        echo "❌ Configuration aborted"
        exit 1
    fi
fi

# Step 4: Create configuration file
echo "📝 Step 4: Create configuration file"
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

echo "✅ Configuration file created: $CONFIG_FILE"

# Step 5: Configuration complete
echo "⚙️ Step 5: Configuration complete"
echo "✅ Using cfargotunnel.com fixed domain, no need to update config.py"

# Done
echo ""
echo "🎉 Cloudflare Tunnel fixed URL configuration complete!"
echo ""
echo "📋 Configuration summary:"
echo "• Tunnel name: $TUNNEL_NAME"
echo "• Tunnel ID: $TUNNEL_ID"
echo "• Tunnel URL: $TUNNEL_URL"
echo "• Configuration file: $CONFIG_FILE"
echo ""
echo "📍 LINE Webhook URL:"
echo "$TUNNEL_URL/webhook"
echo ""
echo "🚀 Usage:"
echo "1. Configure LINE webhook URL: $TUNNEL_URL/webhook (don't verify yet)"
echo "2. Start all services: ./start_all_services.sh"
echo "3. Verify webhook connection in LINE Console (click Verify)"
echo "4. Connect to tmux: tmux attach -t ai_line_session"
echo ""
echo "✨ Advantages:"
echo "• Uses professional custom domain"
echo "• URL never changes, auto-reconnects after restart"
echo "• Unified Agent management using tmux"
