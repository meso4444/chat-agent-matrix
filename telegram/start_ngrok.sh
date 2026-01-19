#!/bin/bash
# start_ngrok.sh (Secure Version)
# Start ngrok and automatically configure Telegram Webhook (using dynamic key)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
RUNTIME_STATE_FILE="$SCRIPT_DIR/.runtime_state"
NGROK_LOG="$SCRIPT_DIR/ngrok.log"

cd "$SCRIPT_DIR"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Error: Environment variable TELEGRAM_BOT_TOKEN not set"
    exit 1
fi

BOT_TOKEN="$TELEGRAM_BOT_TOKEN"

# Read dynamic Secret
if [ ! -f "$SECRET_FILE" ]; then
    echo "❌ Error: Webhook Secret not found, please run start_all_services.sh first"
    exit 1
fi
WEBHOOK_SECRET=$(cat "$SECRET_FILE")

# Read Port
FLASK_PORT=$(python3 -c "import sys; sys.path.append('.'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "🚀 Starting ngrok (Port $FLASK_PORT)..."

# Clean up old processes
pkill -f "ngrok http $FLASK_PORT"
rm -f "$NGROK_LOG"

# Start ngrok
nohup ngrok http $FLASK_PORT > "$NGROK_LOG" 2>&1 &
NGROK_PID=$!

echo "⏳ Waiting for ngrok to establish connection and retrieve URL..."

# Polling - retrieve public URL
PUBLIC_URL=""
for i in {1..10}; do
    echo "   ▸ Attempting to retrieve URL ($i/10)..."

    if command -v jq &> /dev/null; then
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    else
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4 | head -1)
    fi

    # Check if successfully retrieved valid URL
    if [[ -n "$PUBLIC_URL" && "$PUBLIC_URL" != "null" && "$PUBLIC_URL" == http* ]]; then
        echo "✅ Successfully retrieved new URL: $PUBLIC_URL"
        break
    fi

    sleep 3
done

if [[ -z "$PUBLIC_URL" || "$PUBLIC_URL" == "null" ]]; then
    echo "❌ Failed to retrieve ngrok URL (timeout 30 seconds)"
    echo "📋 Recent ngrok logs:"
    tail -n 5 "$NGROK_LOG"
    exit 1
fi

# Write runtime state file (for other programs to read)
echo "{\"ngrok_url\": \"$PUBLIC_URL\"}" > "$RUNTIME_STATE_FILE"
echo "📝 Updated runtime state: $RUNTIME_STATE_FILE"

# Notify Telegram to update Webhook (with Secret Token)
WEBHOOK_URL="$PUBLIC_URL/telegram_webhook"
echo "🔄 Updating Telegram Webhook to: $WEBHOOK_URL"

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
     -d "url=$WEBHOOK_URL" \
     -d "secret_token=$WEBHOOK_SECRET")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook configuration successful (Secret Token verification enabled)"
else
    echo "❌ Webhook configuration failed"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "🎉 ngrok startup and configuration complete!"