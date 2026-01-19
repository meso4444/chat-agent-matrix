#!/bin/bash
# setup_config.sh
# Chat Agent Matrix Interactive Setup Wizard

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Load existing configuration (if exists)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

echo "========================================================"
echo "☀️🌙 Chat Agent Matrix Setup Wizard"
echo "========================================================"
echo ""

# 1. Configure ngrok Authtoken
echo "--------------------------------------------------------"
echo "🔑 Configuration 1/3: ngrok Authtoken"
echo "--------------------------------------------------------"
echo "Please get your token from https://dashboard.ngrok.com/get-started/your-authtoken"
echo "If already configured, press Enter to skip."
echo ""
read -p "Enter ngrok Authtoken: " INPUT_NGROK_TOKEN

if [ -n "$INPUT_NGROK_TOKEN" ]; then
    if command -v ngrok &> /dev/null; then
        ngrok config add-authtoken "$INPUT_NGROK_TOKEN"
        echo "✅ ngrok Token configuration complete"
    else
        echo "⚠️  ngrok not installed, will skip configuration (please run install_dependencies.sh first)"
    fi
else
    echo "⏭️  Keeping existing ngrok configuration"
fi
echo ""

# 2. Configure Telegram Bot Token
echo "--------------------------------------------------------"
echo "🤖 Configuration 2/3: Telegram Bot Token"
echo "--------------------------------------------------------"
echo "Please search for @BotFather in Telegram to create a bot and get the Token."
echo "Current configuration: ${TELEGRAM_BOT_TOKEN:-Not configured}"
echo ""
read -p "Enter Bot Token (press Enter to keep existing value): " INPUT_BOT_TOKEN

if [ -n "$INPUT_BOT_TOKEN" ]; then
    BOT_TOKEN="$INPUT_BOT_TOKEN"
else
    BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
fi
echo ""

# 3. Configure Chat ID
echo "--------------------------------------------------------"
echo "👤 Configuration 3/3: Telegram Chat ID"
echo "--------------------------------------------------------"
echo "This is your personal ID used for identity verification."

# Define auto-retrieve function
get_chat_id_from_api() {
    export PY_BOT_TOKEN="$1"
    python3 -c "
import requests, sys, time, os

try:
    token = os.environ['PY_BOT_TOKEN']

    # 1. Delete Webhook
    requests.post(f'https://api.telegram.org/bot{token}/deleteWebhook')

    # 2. Polling - wait for message
    print('   ⏳ Waiting for message to arrive (max 30 seconds)...', file=sys.stderr)
    for i in range(10):
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        res = requests.get(url, timeout=5).json()

        if not res.get('ok'):
            print(f\"API Error: {res.get('description')}\", file=sys.stderr)
            sys.exit(2)

        if res['result']:
            # Successfully found!
            print(res['result'][-1]['message']['chat']['id'])
            sys.exit(0)

        # Not found, wait 3 seconds and retry
        time.sleep(3)

    sys.exit(1) # Timeout - no message
except Exception as e:
    print(f\"Error: {e}\", file=sys.stderr)
    sys.exit(2)
"
}

# Attempt automatic retrieval
DETECTED_CHAT_ID=""
if [ -n "$BOT_TOKEN" ]; then
    echo "🔄 Attempting to auto-retrieve your Chat ID..."
    # Here we remove 2>/dev/null to show Python error output, but we only capture stdout to variable
    # For aesthetics, we temporarily store stderr
    ERR_LOG=$(mktemp)
    DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")

    if [ -z "$DETECTED_CHAT_ID" ]; then
        echo "⚠️  Currently unable to auto-retrieve"

        # Force delete Webhook first, enter manual polling mode
        python3 -c "import requests; requests.post(f'https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook')" > /dev/null 2>&1

        echo "👉 System has switched to detection mode. Please send a message (like /start) to your Bot NOW."
        read -p "   After sending, press Enter to retry..." dummy

        echo "🔄 Reading..."
        # The function will also do another deleteWebhook internally as a backup, but the above one is critical
        DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")
    fi

    rm -f "$ERR_LOG"

    if [ -n "$DETECTED_CHAT_ID" ]; then
        echo "✅ Successfully retrieved Chat ID: $DETECTED_CHAT_ID"
    else
        echo "❌ Still unable to auto-retrieve. You can manually enter it later."
    fi
fi

CURRENT_ID="${TELEGRAM_CHAT_ID:-$DETECTED_CHAT_ID}"
echo "Current configuration: ${CURRENT_ID:-Not configured}"
echo ""
read -p "Enter Chat ID (press Enter to use [${DETECTED_CHAT_ID:-keep existing}]): " INPUT_CHAT_ID

if [ -n "$INPUT_CHAT_ID" ]; then
    CHAT_ID="$INPUT_CHAT_ID"
elif [ -n "$DETECTED_CHAT_ID" ]; then
    CHAT_ID="$DETECTED_CHAT_ID"
else
    CHAT_ID="$TELEGRAM_CHAT_ID"
fi

# Write to .env file
echo "--------------------------------------------------------"
echo "💾 Saving configuration..."

# If .env doesn't exist, copy from example
if [ ! -f "$ENV_FILE" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
fi

# Use sed to update .env (if file exists)
# If file doesn't exist, create it directly
if [ ! -f "$ENV_FILE" ]; then
    echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" > "$ENV_FILE"
    echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> "$ENV_FILE"
else
    # Update BOT_TOKEN
    if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
        # Use | as separator to avoid content conflicts
        sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$BOT_TOKEN|" "$ENV_FILE"
    else
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"
    fi

    # Update CHAT_ID
    if grep -q "TELEGRAM_CHAT_ID=" "$ENV_FILE"; then
        sed -i "s|TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=$CHAT_ID|" "$ENV_FILE"
    else
        echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> "$ENV_FILE"
    fi
fi

echo "✅ Configuration saved to .env"
echo ""
echo "🎉 Configuration complete! You can now run ./start_all_services.sh to start the service."
echo ""
