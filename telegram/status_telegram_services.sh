#!/bin/bash
# status_telegram_services.sh (Multi-Agent edition)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"

# Read configuration
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "📊 Chat Agent Matrix System Status (Multi-Agent)"
echo "⏰ Check time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==========================================="

# 1. Check tmux
echo "1️⃣  tmux Session:"
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "   ✅ Running ($TMUX_SESSION_NAME)"
    echo "   📋 Window status:"
    tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
else
    echo "   ❌ Not running"
fi
echo ""

# 2. Check Flask and Agent active status
echo "2️⃣  API server status:"
API_DATA=$(curl -s "http://localhost:$FLASK_PORT/status" || echo "failed")
if [ "$API_DATA" != "failed" ]; then
    echo "   ✅ Flask normal (Port $FLASK_PORT)"
    ACTIVE=$(echo "$API_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['active_agent'])")
    echo "   ⭐ Current active Agent: $ACTIVE"
else
    echo "   ❌ Unable to connect to API service"
fi
echo ""

# 3. Check ngrok
echo "3️⃣  Tunnel status (ngrok):"
if pgrep -f "ngrok http $FLASK_PORT" > /dev/null; then
    echo "   ✅ Running"
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data['tunnels'] else 'N/A')" 2>/dev/null)
    echo "   🌍 Public address: $PUBLIC_URL"
else
    echo "   ❌ Not started"
fi
echo ""