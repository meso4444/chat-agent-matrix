#!/bin/bash
# Chat Agent Matrix (LINE) - System Status Check

# Read configuration from Python config
SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="$SCRIPT_DIR/.env"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "📊 Chat Agent Matrix (LINE) System Status"
echo "⏰ Check time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==========================================="

# 1. Check tmux
echo "1️⃣  tmux Session:"
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "   ✅ Running ($TMUX_SESSION_NAME)"
    echo "   📋 Window status:"
    tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name} (#{?window_active,⭐ Active,Background})"
else
    echo "   ❌ Not running"
    echo "   💡 Please run: ./start_all_services.sh"
    exit 1
fi
echo ""

# 2. Check Flask and Agent active status
echo "2️⃣  API server status:"
API_DATA=$(curl -s --max-time 2 "http://127.0.0.1:$FLASK_PORT/status" || echo "failed")

if [ "$API_DATA" != "failed" ]; then
    echo "   ✅ Flask normal (Port $FLASK_PORT)"

    # Parse JSON to show active Agent
    ACTIVE=$(echo "$API_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('active_agent', 'Unknown'))" 2>/dev/null)
    echo "   ⭐ Current active Agent: $ACTIVE"

    # List Agent status (traffic light)
    echo "$API_DATA" | python3 -c "
import sys, json
try:
    agents = json.load(sys.stdin).get('agents', {})
    status_line = '   🤖 Agent status: '
    for name, status in agents.items():
        icon = '🟢' if status else '🔴'
        status_line += f'{icon} {name}  '
    print(status_line)
except: pass
"
else
    echo "   ❌ Unable to connect to API (Connection Refused)"
    echo "   💡 Suggest checking logs: tmux capture-pane -t $TMUX_SESSION_NAME:line_api -p | tail -n 20"
fi
echo ""

# 3. Check Cloudflare Tunnel
echo "3️⃣  Tunnel status (Cloudflare):"
# Check if cloudflared is running in tmux
if tmux list-windows -t "$TMUX_SESSION_NAME" | grep -q "cloudflared"; then
    # Check for error logs
    TUNNEL_LOG=$(tmux capture-pane -t "$TMUX_SESSION_NAME:cloudflared" -p 2>/dev/null | tail -n 5)
    if [[ "$TUNNEL_LOG" == *"ERR"* || "$TUNNEL_LOG" == *"error"* ]]; then
        echo "   ⚠️  Running but may have errors:"
        echo "$TUNNEL_LOG"
    else
        echo "   ✅ Running"
        echo "   🌍 Fixed URL: (see config.yaml or setup_cloudflare_fixed_url.sh output)"
    fi
else
    echo "   ❌ Not started"
fi
echo ""

echo "🔧 Management commands:"
echo "   • Enter terminal: tmux attach -t $TMUX_SESSION_NAME"
echo "   • Restart service: ./stop_all_services.sh && ./start_all_services.sh"