#!/bin/bash
# setup_docker.sh - Chat Agent Matrix Docker Deployment Configuration Wizard
# Purpose: Setup Docker instance with credentials and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_GENERATOR="$SCRIPT_DIR/generate_config.py"

echo "=========================================="
echo "🐳 Chat Agent Matrix - Docker Instance Setup Wizard"
echo "=========================================="
echo ""

# Step 1: Instance naming
echo "Step 1/3: Instance Naming"
echo "----------------------------------------"
echo "Instance name is used to distinguish different deployment environments or test scenarios"
echo ""
echo "💡 Naming suggestions:"
echo "   • Environment: dev, staging, production, test, sandbox"
echo "   • Use case: travel_planner, investment_advisor, meditation_coach"
echo "   • Project code: gupta, chod, omega, alpha, nexus"
echo "   • Personal use: work, hobby, research, learning, experiment"
echo "   • Custom: anything_goes (as long as it follows the rules)"
echo ""
echo "⚠️  Restrictions: Only alphanumeric characters and underscores (no spaces or special characters)"
echo ""

# Instance name validation function
validate_instance_name() {
  local name="$1"
  if [[ ! "$name" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ Invalid instance name: '$name'"
    echo "   Allowed characters: letters, numbers, underscores"
    return 1
  fi
  return 0
}

# Loop until valid input
while true; do
  read -p "Enter instance name: " INSTANCE_NAME
  if validate_instance_name "$INSTANCE_NAME"; then
    break
  fi
done

echo "✓ Instance locked: $INSTANCE_NAME"
echo ""

ENV_FILE="$SCRIPT_DIR/.env.${INSTANCE_NAME}"

# Step 2: ngrok credentials
echo "Step 2/3: ngrok Authentication Token"
echo "----------------------------------------"
read -p "Enter Authtoken: " INPUT_NGROK_TOKEN
NGROK_AUTHTOKEN="${INPUT_NGROK_TOKEN:-}"
echo "✓ ngrok recorded"
echo ""

# Step 3: Telegram setup
echo "Step 3/3: Telegram Setup"
echo "----------------------------------------"
read -p "Enter Bot Token: " BOT_TOKEN
echo "✓ Telegram Bot recorded"
echo ""

# --- Auto-detect Chat ID function ---
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

# Telegram Chat ID (auto-detect)
echo "Telegram Chat ID (Auto-detect)"
echo "----------------------------------------"
DETECTED_CHAT_ID=""
if [ -n "$BOT_TOKEN" ]; then
    echo "🔄 Attempting to auto-detect your Chat ID..."
    echo "👉 Please send a message (e.g., /start) to your Bot."
    DETECTED_CHAT_ID=$(get_chat_id_from_api "$BOT_TOKEN") || echo ""

    if [ -n "$DETECTED_CHAT_ID" ]; then
        echo "✅ Chat ID detected: $DETECTED_CHAT_ID"
    else
        echo "⚠️  Auto-detection failed, please enter manually."
    fi
fi

read -p "Enter Chat ID [default: ${DETECTED_CHAT_ID}]: " INPUT_CHAT_ID
CHAT_ID="${INPUT_CHAT_ID:-$DETECTED_CHAT_ID}"
echo "✓ Chat ID recorded: $CHAT_ID"
echo ""

# Generate .env file
# [Note]
#   - Port information should NOT be written to .env, but to config.yaml (handled by generate_config.py)
#   - INSTANCE_NAME is explicitly set in docker-compose environment section, so no need to write here
cat > "$ENV_FILE" << EOF
NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

# Agent configuration (optional)
echo "=========================================="
echo "🤖 Agent Configuration (Optional)"
echo "=========================================="
echo ""
read -p "Define custom agents for this instance? [y/N]: " DEFINE_AGENTS

AGENTS_DATA=""
if [[ "$DEFINE_AGENTS" =~ ^[Yy]$ ]]; then
    agent_count=0
    add_agent="Y"
    while [[ "$add_agent" =~ ^[Yy]$ ]]; do
        agent_count=$((agent_count + 1))
        echo ""
        echo "Agent #$agent_count Configuration"
        read -p "  Name (e.g., Index): " AGENT_NAME
        if [ -z "$AGENT_NAME" ]; then break; fi
        read -p "  Engine (gemini/claude) [gemini]: " ENGINE
        ENGINE="${ENGINE:-gemini}"
        read -p "  Use case (usecase): " USECASE
        read -p "  Description (description): " DESCRIPTION
        AGENTS_DATA="${AGENTS_DATA}|||${AGENT_NAME}:${ENGINE}:${USECASE}:${DESCRIPTION}"
        read -p "Continue adding next agent? [y/N]: " add_agent
        add_agent="${add_agent:-N}"
    done
    if [ -n "$AGENTS_DATA" ]; then AGENTS_DATA="${AGENTS_DATA:3}"; fi
fi

echo ""
echo "⚙️  Invoking generator to materialize configuration..."

# Call external generator to produce config.yaml
python3 "$CONFIG_GENERATOR" "config" "$INSTANCE_NAME" "$AGENTS_DATA" "$SCRIPT_DIR"

# Call external generator to produce docker-compose override
python3 "$CONFIG_GENERATOR" "compose" "$INSTANCE_NAME" "" "$SCRIPT_DIR"

# Create container credential persistence directory
echo "📁 Creating container credential storage directory..."
mkdir -p "$SCRIPT_DIR/container_home/$INSTANCE_NAME"
chmod 750 "$SCRIPT_DIR/container_home/$INSTANCE_NAME"
echo "✅ Credential directory created: $SCRIPT_DIR/container_home/$INSTANCE_NAME"

echo ""
echo "=========================================="
echo "✅ Instance setup completed!"
echo ""
echo "Generated files:"
echo "  • .env.${INSTANCE_NAME}"
echo "  • config.${INSTANCE_NAME}.yaml"
echo "  • docker-compose.${INSTANCE_NAME}.yml"
echo "  • container_home/${INSTANCE_NAME}/ (credential storage)"
echo ""
echo "Standard workflow (manual execution):"
echo "  1️⃣  Setup AI Agent credentials:"
echo "     bash ../agent_credential_wizard.sh"
echo ""
echo "  2️⃣  Build image:"
echo "     docker compose -f docker-compose.${INSTANCE_NAME}.yml build bot"
echo ""
echo "  3️⃣  Start container:"
echo "     docker compose -f docker-compose.${INSTANCE_NAME}.yml up -d bot"
echo ""
echo "  4️⃣  Check status:"
echo "     docker ps -a | grep chat-agent-${INSTANCE_NAME}"
echo ""
echo "=========================================="
echo ""
