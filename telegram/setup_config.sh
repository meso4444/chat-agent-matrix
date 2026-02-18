#!/bin/bash
# setup_config.sh
# Chat Agent Matrix Interactive Configuration Wizard

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Load existing configuration (if any)
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

echo "========================================================"
echo "☀️🌙 Chat Agent Matrix Configuration Wizard"
echo "========================================================"
echo ""

# 0. Configure Port (avoid conflicts with other services)
echo "--------------------------------------------------------"
echo "🔌 Step 1/4: Port Configuration"
echo "--------------------------------------------------------"
echo "Configure service ports to avoid conflicts with other applications."
echo ""
echo "Default values:"
echo "  • Flask Webhook Port: 5000"
echo "  • Ngrok API Port: 4040"
echo ""

read -p "Flask Webhook Port [default: 5000]: " INPUT_FLASK_PORT
FLASK_PORT="${INPUT_FLASK_PORT:-5000}"

read -p "Ngrok API Port [default: 4040]: " INPUT_NGROK_API_PORT
NGROK_API_PORT="${INPUT_NGROK_API_PORT:-4040}"

echo "✅ Port configured: Flask=$FLASK_PORT, Ngrok API=$NGROK_API_PORT"
echo ""

# 1. Configure ngrok Authtoken
echo "--------------------------------------------------------"
echo "🔑 Step 2/4: ngrok Authentication Token"
echo "--------------------------------------------------------"
echo "Get it from https://dashboard.ngrok.com/get-started/your-authtoken"
echo "Current: ${NGROK_AUTHTOKEN:-not set}"
echo ""
read -p "Enter ngrok Authtoken (press Enter to keep current): " INPUT_NGROK_TOKEN

if [ -n "$INPUT_NGROK_TOKEN" ]; then
    NGROK_AUTHTOKEN="$INPUT_NGROK_TOKEN"
    echo "✅ ngrok Authtoken recorded"
else
    NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN"
    echo "⏭️  Keeping existing ngrok configuration"
fi
echo ""

# 2. Configure Telegram Bot Token
echo "--------------------------------------------------------"
echo "🤖 Step 3/4: Telegram Bot Token"
echo "--------------------------------------------------------"
echo "Search for @BotFather on Telegram to create a bot and get the token."
echo "Current: ${TELEGRAM_BOT_TOKEN:-not set}"
echo ""
read -p "Enter Bot Token (press Enter to keep current): " INPUT_BOT_TOKEN

if [ -n "$INPUT_BOT_TOKEN" ]; then
    BOT_TOKEN="$INPUT_BOT_TOKEN"
else
    BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
fi
echo ""

# 3. Configure Chat ID
echo "--------------------------------------------------------"
echo "👤 Step 4/4: Telegram Chat ID"
echo "--------------------------------------------------------"
echo "This is your personal ID used for authentication."
echo "💡 The system will auto-detect it, you need to send a message to the Bot (e.g., /start)."
echo ""

# Define auto-detection function
get_chat_id_from_api() {
    export PY_BOT_TOKEN="$1"
    python3 -c "
import requests, sys, time, os

try:
    token = os.environ['PY_BOT_TOKEN']

    # 1. Delete Webhook
    requests.post(f'https://api.telegram.org/bot{token}/deleteWebhook')

    # 2. Polling - wait for message
    print('   ⏳ Waiting for message (up to 30 seconds)...', file=sys.stderr)
    for i in range(10):
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        res = requests.get(url, timeout=5).json()

        if not res.get('ok'):
            print(f\"API Error: {res.get('description')}\", file=sys.stderr)
            sys.exit(2)

        if res['result']:
            # Successfully captured!
            print(res['result'][-1]['message']['chat']['id'])
            sys.exit(0)

        # Didn't capture, wait 3 seconds and retry
        time.sleep(3)

    sys.exit(1) # Timeout - no message
except Exception as e:
    print(f\"Error: {e}\", file=sys.stderr)
    sys.exit(2)
"
}

# Attempt auto-detection
DETECTED_CHAT_ID=""
if [ -n "$BOT_TOKEN" ]; then
    echo "🔄 Attempting to auto-detect your Chat ID..."
    # Here we remove 2>/dev/null to display Python error output, but only capture stdout to variable
    # For aesthetics, we temporarily store stderr
    ERR_LOG=$(mktemp)
    DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")

    if [ -z "$DETECTED_CHAT_ID" ]; then
        echo "⚠️  Currently unable to auto-detect"

        # Forcefully delete Webhook first, enter manual polling mode
        python3 -c "import requests; requests.post(f'https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook')" > /dev/null 2>&1

        echo "👉 System switched to detection mode. Please send a message (e.g., /start) to your Bot NOW."
        read -p "   After sending, press Enter to retry..." dummy

        echo "🔄 Reading..."
        # The function will also delete Webhook internally once more for safety, but the key is the one above
        DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN" 2> "$ERR_LOG")
    fi
    
    rm -f "$ERR_LOG"
    
    if [ -n "$DETECTED_CHAT_ID" ]; then
        echo "✅ Successfully retrieved Chat ID: $DETECTED_CHAT_ID"
    else
        echo "❌ Still unable to auto-detect. You can fill it in manually later."
    fi
fi

CURRENT_ID="${TELEGRAM_CHAT_ID:-$DETECTED_CHAT_ID}"
echo "Current setting: ${CURRENT_ID:-not set}"
echo ""
read -p "Enter Chat ID (press Enter to use [${DETECTED_CHAT_ID:-keep current}]): " INPUT_CHAT_ID

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

# Generate .env file physically (simplified mode, no Multi-Bot registration)
cat > "$ENV_FILE" << EOF
NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

echo "✅ Configuration saved to .env"
echo ""

# Update Port configuration in config.yaml
echo "💾 Updating Port configuration in config.yaml..."
CONFIG_YAML="$SCRIPT_DIR/config.yaml"

if [ -f "$CONFIG_YAML" ]; then
    # Use Python to update Port in YAML (preserve original indentation and formatting)
    python3 << PYTHON_EOF
import re

with open('$CONFIG_YAML', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if server section already exists
if 'server:' in content:
    # Update existing port
    content = re.sub(r'(\s+)port:\s*\d+', r'\1port: $FLASK_PORT', content)
    # If ngrok_api_port doesn't exist, add it
    if 'ngrok_api_port:' not in content:
        content = re.sub(r'(server:.*?\n\s+port:.*?\n)', r'\1  ngrok_api_port: $NGROK_API_PORT\n', content, flags=re.DOTALL)
    else:
        content = re.sub(r'(\s+)ngrok_api_port:\s*\d+', r'\1ngrok_api_port: $NGROK_API_PORT', content)
else:
    # If no server section, add to end of file
    if not content.endswith('\n'):
        content += '\n'
    content += f'server:\n  port: $FLASK_PORT\n  ngrok_api_port: $NGROK_API_PORT\n'

with open('$CONFIG_YAML', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Port updated in config.yaml:")
print("   • Flask Port: $FLASK_PORT")
print("   • Ngrok API Port: $NGROK_API_PORT")
PYTHON_EOF
else
    echo "⚠️  config.yaml doesn't exist, will be generated on first startup"
fi

echo ""
echo "🎉 Configuration complete! You can now run ./start_all_services.sh to start the services."
echo ""
