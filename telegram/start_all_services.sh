#!/bin/bash
# Start Telegram → AI Agent Squad Remote Control System

set -e

# Resolve to absolute path
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
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

echo "🚀 Starting Chat Agent Matrix (Telegram Edition)"
echo "==========================================="

# Generate dynamic Webhook Secret
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
openssl rand -hex 32 > "$SECRET_FILE"
export WEBHOOK_SECRET_TOKEN=$(cat "$SECRET_FILE")

# Kill existing session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "🔄 Killing existing session…"
    tmux kill-session -t "$TMUX_SESSION_NAME"
    sleep 1
fi

# Create main session
echo "🧬 Creating tmux session '$TMUX_SESSION_NAME'…"
tmux new-session -d -s "$TMUX_SESSION_NAME" -n "init" -c "$SCRIPT_DIR"

# 1. Initialize Agent environment
echo "🧬 Initializing Agent ecosystem…"
python3 "$SCRIPT_DIR/telegram_scripts/setup_agent_env.py"

# 2. Dynamically start AI Agent Squad
echo "🤖 Deploying AI Agent Squad…"
export SCRIPT_DIR
export TMUX_SESSION_NAME

python3 << 'EOF'
import sys
import os
import subprocess
import time
import re

script_dir = os.environ['SCRIPT_DIR']
session_name = os.environ['TMUX_SESSION_NAME']
sys.path.append(script_dir)

def wait_for_prompt(session_name, window_name, engine, max_wait=30):
    """Wait for tmux pane to show corresponding CLI prompt

    Args:
        engine: 'claude' or 'gemini'
        - claude → ❯
        - gemini → * or >
    """
    start_time = time.time()
    # Select corresponding prompt marker based on engine
    if engine == 'claude':
        prompt_markers = ['❯']
    else:  # gemini - could be * or >
        prompt_markers = ['*', '>']

    while time.time() - start_time < max_wait:
        try:
            result = subprocess.run(
                ['tmux', 'capture-pane', '-t', f'{session_name}:{window_name}', '-p'],
                capture_output=True, text=True
            )
            output = result.stdout
            if not output:
                time.sleep(0.5)
                continue

            # Check if entire pane content contains any expected prompt marker
            for marker in prompt_markers:
                if marker in output:
                    print(f"       ✅ Detected {engine} prompt '{marker}'")
                    return True
        except Exception as e:
            pass

        time.sleep(0.5)

    return False

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

        collab_context = "\n".join(collab_context_lines) if collab_context_lines else "No specific team collaboration configured."

        print(f"   ▸ Starting Agent: {name} ({engine})")

        if i == 0:
            subprocess.run(['tmux', 'rename-window', '-t', f'{session_name}:0', name], check=True)
        else:
            subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', name], check=True)

        # Set up pipe-pane to monitor authorization prompts and stuck commands
        responder_script = os.path.join(script_dir, 'auto_permission_responder.py')
        subprocess.run(['tmux', 'pipe-pane', '-t', f'{session_name}:{name}',
                       f'python3 {responder_script} {session_name}:{name}'], check=True)

        # 📋 Copy necessary tool scripts to Agent home
        # Copy telegram_notifier.py to agent_home (not in toolbox)
        telegram_notifier_src = os.path.join(script_dir, 'telegram_notifier.py')
        telegram_notifier_dst = os.path.join(home_path, 'telegram_notifier.py')
        if os.path.exists(telegram_notifier_src):
            subprocess.run(['cp', telegram_notifier_src, telegram_notifier_dst], check=True)

        # Create shared space, knowledge base, and memory directories
        shared_space_path = os.path.join(home_path, 'my_shared_space')
        os.makedirs(shared_space_path, exist_ok=True)

        knowledge_path = os.path.join(home_path, 'knowledge')
        os.makedirs(knowledge_path, exist_ok=True)

        memory_path = os.path.join(home_path, 'memory')
        os.makedirs(memory_path, exist_ok=True)

        # Initialize today's memory file
        from datetime import datetime
        today_memory_file = os.path.join(memory_path, 'memory.md')
        if not os.path.exists(today_memory_file):
            with open(today_memory_file, 'w', encoding='utf-8') as f:
                f.write(f"# {name} Daily Memory\n\n")
                f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write("## Today's Task Record\n\n")

        # 📚 Unified knowledge document copy logic
        # Copy rules and protocol files (directly to agent_home)
        rule_files_to_copy = ['agent_home_rules.md', 'AGENT_PROTOCOL.md']
        for rule_file in rule_files_to_copy:
            src_file = os.path.join(script_dir, rule_file)
            dst_file = os.path.join(home_path, rule_file)
            if os.path.exists(src_file):
                subprocess.run(['cp', src_file, dst_file], check=True)

        # Copy knowledge base files (to knowledge directory)
        knowledge_files_to_copy = ['SCHEDULER_FUNCTIONALITY.md']
        for knowledge_file in knowledge_files_to_copy:
            src_file = os.path.join(script_dir, knowledge_file)
            dst_file = os.path.join(knowledge_path, knowledge_file)
            if os.path.exists(src_file):
                subprocess.run(['cp', src_file, dst_file], check=True)

        # Copy template files (copy directly to agent_home, no subdirectory)
        template_src = os.path.join(script_dir, 'agent_home_rules_templates', 'agent_rule_gen_template.txt')
        template_dst = os.path.join(home_path, 'agent_rule_gen_template.txt')
        if os.path.exists(template_src):
            subprocess.run(['cp', template_src, template_dst], check=True)

        # 🎯 Enter Agent working directory
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', f'cd {home_path}'], check=True)
        time.sleep(1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

        if engine == 'gemini':
            cmd = 'gemini --yolo'
            engine_doc_name = 'GEMINI.md'
        else:
            cmd = 'claude --permission-mode bypassPermissions'
            engine_doc_name = 'CLAUDE.md'

        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', cmd], check=True)
        time.sleep(1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

        # Wait for CLI prompt to appear (check corresponding prompt based on engine type, max wait 60 seconds)
        print(f"     ⏳ Waiting for {name} CLI to start…")
        if not wait_for_prompt(session_name, name, engine, max_wait=60):
            print(f"     ⚠️ {name} startup timeout (did not detect {engine} prompt), still attempting to inject prompt…")

        # ✅ Check if specification file already exists (avoid duplicate injection and overwrite)
        doc_path = os.path.join(home_path, engine_doc_name)
        if os.path.exists(doc_path):
            print(f"     ✅ {engine_doc_name} exists, skip initialization injection (protect existing specifications)")

            # 📋 Inject prompt: check if specifications are complete
            print(f"     📋 Injecting specification check prompt…")
            engine_upper = engine.upper()
            check_prompt = f"Check AGENT_PROTOCOL.md content, confirm if {engine_upper}.md specifications are complete, and update"

            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', check_prompt], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            # 🔒 Double insurance: ensure prompt is correctly received
            time.sleep(0.2)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)
        else:
            # Trigger Agent specification file construction
            print(f"     ✨ Triggering {name} self-construction of specification files…")

            # Point to local copy in agent_home
            rules_path = os.path.join(home_path, 'agent_home_rules.md')
            protocol_path = os.path.join(home_path, 'AGENT_PROTOCOL.md')  # Reference notification rules

            # Generate initialization prompt
            prompt = (gen_template.replace('{agent_name}', name)
                                 .replace('{agent_usecase}', usecase)
                                 .replace('{engine_doc_name}', engine_doc_name)
                                 .replace('{rules_path}', rules_path)
                                 .replace('{protocol_path}', protocol_path)
                                 .replace('{collaboration_context}', collab_context)
                                 .replace('{home_path}', home_path))

            prompt_file = os.path.join(script_dir, f".prompt_temp_{name}")
            with open(prompt_file, 'w') as f:
                f.write(prompt)

            with open(prompt_file, 'r') as pf:
                prompt_content = pf.read()

            # Use send-keys -l (literal) to simulate typing, bypassing paste mode
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', prompt_content], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            # 🔒 Double insurance: all Agents need paste mode confirmation
            # This ensures long prompts are sent correctly
            time.sleep(0.2)
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
tmux send-keys -t "$TMUX_SESSION_NAME:telegram" "python3 $SCRIPT_DIR/telegram_webhook_server.py"
sleep 1
tmux send-keys -t "$TMUX_SESSION_NAME:telegram" Enter

# Wait for Flask to start
sleep 3

# Window: ngrok Tunnel
echo "☁️  Establishing secure tunnel (ngrok)…"
tmux new-window -t "$TMUX_SESSION_NAME" -n "ngrok" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:ngrok" "$SCRIPT_DIR/start_ngrok.sh"
sleep 1
tmux send-keys -t "$TMUX_SESSION_NAME:ngrok" Enter

echo "⏳ Synchronizing network address and webhook…"
sleep 5

# Return to first Agent window
tmux select-window -t "$TMUX_SESSION_NAME:0"

echo "==========================================="
echo "🎉 Chat Agent Matrix v1.0.0 fully deployed!"
echo ""
echo "📋 Execution summary:"
echo "   Session: $TMUX_SESSION_NAME"
echo "   Started Agent windows:"
tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
echo ""
echo "🚀 Attach to session: tmux attach -t $TMUX_SESSION_NAME"
