#!/bin/bash
# Start Telegram → AI Agent Army Remote Control System

set -e

# Parse as absolute path
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "🔐 .env loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Read configuration
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "🚀 Starting Chat Agent Matrix (Telegram Edition)"
echo "==========================================="

# Generate dynamic Webhook Secret
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
openssl rand -hex 32 > "$SECRET_FILE"
export WEBHOOK_SECRET_TOKEN=$(cat "$SECRET_FILE")

# Terminate existing session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "🔄 Terminating existing session…"
    tmux kill-session -t "$TMUX_SESSION_NAME"
    sleep 1
fi

# Create main session
echo "🧬  Creating tmux session '$TMUX_SESSION_NAME'…"
tmux new-session -d -s "$TMUX_SESSION_NAME" -n "init" -c "$SCRIPT_DIR"

# 1. Initialize Agent ecosystem
echo "🧬  Initializing Agent ecosystem…"
python3 "$SCRIPT_DIR/telegram_scripts/setup_agent_env.py"

# 2. Dynamically start AI Agent Army
echo "🤖 Deploying AI Agent Army…"
export SCRIPT_DIR
export TMUX_SESSION_NAME

python3 << 'EOF'
import sys
import os
import subprocess
import time

script_dir = os.environ['SCRIPT_DIR']
session_name = os.environ['TMUX_SESSION_NAME']
sys.path.append(script_dir)

try:
    from config import AGENTS, COLLABORATION_GROUPS

    rules_path = os.path.join(script_dir, 'agent_home_rules.md')
    template_path = os.path.join(script_dir, 'agent_home_rules_templates', 'agent_rule_gen_template.txt')

    with open(template_path, 'r') as f:
        gen_template = f.read()

    for i, agent in enumerate(AGENTS):
        name = agent['name']
        engine = agent['engine']
        usecase = agent.get('usecase', 'No description')
        home_path = os.path.join(script_dir, 'agent_home', name)

        # Generate collaboration context
        collab_context_lines = []
        for grp in COLLABORATION_GROUPS:
            if name in grp.get('members', []):
                collab_context_lines.append(f"- Team: {grp.get('name')} ({grp.get('description', '')})")
                collab_context_lines.append("  Team member responsibilities:")
                roles = grp.get('roles', {})
                for member, role in roles.items():
                    marker = " (you)" if member == name else ""
                    collab_context_lines.append(f"  * {member}{marker}: {role}")
                collab_context_lines.append("")

        collab_context = "\n".join(collab_context_lines) if collab_context_lines else "No specific collaboration team configuration."

        print(f"   ▸ Starting Agent: {name} ({engine})")

        if i == 0:
            subprocess.run(['tmux', 'rename-window', '-t', f'{session_name}:0', name], check=True)
        else:
            subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', name, '-c', home_path], check=True)

        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', f'cd {home_path}', 'Enter'], check=True)

        if engine == 'gemini':
            cmd = 'gemini --yolo'
            protocol_file = 'GEMINI.md'
        else:
            cmd = 'claude --permission-mode bypassPermissions'
            protocol_file = 'CLAUDE.md'

        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', cmd, 'Enter'], check=True)

        # Check if protocol file exists
        target_rule_file = os.path.join(home_path, protocol_file)
        if not os.path.exists(target_rule_file):
            print(f"     ✨ Triggering {name} self-construction of protocol file (waiting 10 seconds to start)…")

            protocol_path = os.path.join(script_dir, protocol_file)

            prompt = (gen_template.replace('{agent_name}', name)
                                 .replace('{agent_usecase}', usecase)
                                 .replace('{engine_doc_name}', protocol_file)
                                 .replace('{rules_path}', rules_path)
                                 .replace('{protocol_path}', protocol_path)
                                 .replace('{collaboration_context}', collab_context)
                                 .replace('{home_path}', home_path))

            time.sleep(10)

            prompt_file = os.path.join(script_dir, f".prompt_temp_{name}")
            with open(prompt_file, 'w') as f:
                f.write(prompt)

            with open(prompt_file, 'r') as pf:
                prompt_content = pf.read()

            # Use send-keys -l (literal) to simulate typing, bypassing paste mode
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', prompt_content], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            os.remove(prompt_file)

except Exception as e:
    print(f"❌ Error during deployment: {e}")
    sys.exit(1)
EOF

echo "   ✅ All Agents ready"

# Window: Flask Telegram API
echo "📱 Starting Telegram Webhook API…"
tmux new-window -t "$TMUX_SESSION_NAME" -n "telegram" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:telegram" "python3 $SCRIPT_DIR/telegram_webhook_server.py" Enter

# Wait for Flask to start
sleep 3

# Window: ngrok Tunnel
echo "☁️  Creating secure tunnel (ngrok)…"
tmux new-window -t "$TMUX_SESSION_NAME" -n "ngrok" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:ngrok" "$SCRIPT_DIR/start_ngrok.sh" Enter

echo "⏳ Synchronizing network address and webhook…"
sleep 5

# Return to first Agent window
tmux select-window -t "$TMUX_SESSION_NAME:0"

echo "==========================================="
echo "🎉 Chat Agent Matrix v1.0.0 fully deployed!"
echo ""
echo "📋 Run summary:"
echo "   Session: $TMUX_SESSION_NAME"
echo "   Active Agent windows:"
tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
echo ""
echo "🚀 Connect to session: tmux attach -t $TMUX_SESSION_NAME"
