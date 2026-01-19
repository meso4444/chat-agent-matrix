#!/usr/bin/env python3
"""
LINE Webhook Flask API (Chat Agent Matrix version)
Receive LINE user messages and dispatch to different AI Agent tmux windows
"""

from flask import Flask, request, jsonify, abort
import json
import subprocess
import time
import os
import requests
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from config import (
    CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, FLASK_HOST, FLASK_PORT, 
    TMUX_SESSION_NAME, AGENTS, DEFAULT_ACTIVE_AGENT,
    DEFAULT_CLEANUP_POLICY, CUSTOM_MENU, SCHEDULER_CONF, TEMP_IMAGE_DIR_NAME,
    COLLABORATION_GROUPS
)
from line_notifier import send_message
from line_scripts.scheduler_manager import SchedulerManager

app = Flask(__name__)

# User state tracking
USER_STATES = {}

# Current active Agent
CURRENT_AGENT = DEFAULT_ACTIVE_AGENT

class ImageManager:
    """Image Manager: responsible for downloading, storing, and auto-cleanup (supports multi-Agent isolation)"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
    
    def download_image(self, message_id, agent_name):
        """Download image from LINE and return local absolute path"""
        try:
            # 1. Ensure Agent directory structure is correct
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', agent_name, TEMP_IMAGE_DIR_NAME)
            if not os.path.exists(agent_img_dir):
                os.makedirs(agent_img_dir)

            # 2. Download image (LINE Content API)
            url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            headers = {'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'}

            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                print(f"❌ Unable to download LINE image: {response.status_code} {response.text}")
                return None

            # 3. Build local filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{message_id}.jpg"
            local_path = os.path.join(agent_img_dir, filename)

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            print(f"📸 Image downloaded to [{agent_name}]: {local_path}")
            return local_path

        except Exception as e:
            print(f"❌ Image download failed: {e}")
            return None

    def cleanup_old_files(self):
        """Traverse all Agent directories and execute differentiated cleanup (called by Scheduler)"""
        print("🧹 [ImageManager] Starting multi-Agent image cleanup task...")

        for agent in AGENTS:
            name = agent['name']
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', name, TEMP_IMAGE_DIR_NAME)

            if not os.path.exists(agent_img_dir):
                continue

            policy = agent.get('cleanup_policy', {})
            retention_days = policy.get('images_retention_days', DEFAULT_CLEANUP_POLICY['images_retention_days'])

            cutoff = time.time() - (retention_days * 86400)

            count = 0
            for filename in os.listdir(agent_img_dir):
                file_path = os.path.join(agent_img_dir, filename)
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                    try:
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        print(f"⚠️ Unable to delete [{name}] file {filename}: {e}")

            if count > 0:
                print(f"🧹 Cleaned {count} expired files for Agent[{name}]")

# Initialize Image Manager
image_manager = ImageManager()

def get_agent_info(name):
    for agent in AGENTS:
        if agent['name'].lower() == name.lower():
            return agent
    return None

def check_agent_session(name):
    try:
        result = subprocess.run(
            ['tmux', 'has-session', '-t', f'{TMUX_SESSION_NAME}:{name}'],
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to check tmux session: {e}")
        return False

def send_to_ai_session(message, agent_name=None):
    global CURRENT_AGENT
    target = agent_name or CURRENT_AGENT

    try:
        if not check_agent_session(target):
            send_message(f"❌ Agent '{target}' window does not exist\nPlease check configuration or run: ./start_all_services.sh")
            return False

        # Text -> Delay -> Enter
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}', message], check=True)
        time.sleep(0.1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}', 'Enter'], check=True)

        print(f"📤 Sent to Agent[{target}]: {message}")
        return True

    except Exception as e:
        print(f"❌ Failed to send to Agent: {e}")
        send_message(f"❌ System error: {str(e)}")
        return False

def check_system_status():
    try:
        # 0. Build role mapping table
        agent_role_map = {}
        for grp in COLLABORATION_GROUPS:
            roles = grp.get('roles', {})
            for member, role in roles.items():
                short_role = role[:15] + "..." if len(role) > 15 else role
                agent_role_map[member] = f"[{grp.get('name')}] {short_role}"

        # 1. Agent status
        agent_status_list = []
        for agent in AGENTS:
            name = agent['name']
            desc = agent.get('description', 'No description')
            engine = agent['engine']
            role_info = f"\n      └ {agent_role_map[name]}" if name in agent_role_map else ""
            is_active = " (⭐ Active)" if name == CURRENT_AGENT else ""
            status_icon = "🟢" if check_agent_session(name) else "🔴"
            agent_status_list.append(f"{status_icon} [{name}] {desc} ({engine}){is_active}{role_info}")

        agents_info = "\n".join(agent_status_list)

        # 2. Scheduler status
        scheduler_list = []
        if SCHEDULER_CONF:
            for job in SCHEDULER_CONF:
                if job.get('active'):
                    trigger_info = ""
                    if job['trigger'] == 'interval':
                        h = job.get('hours', job.get('hour', 0))
                        m = job.get('minutes', job.get('minute', 0))
                        s = job.get('seconds', job.get('second', 0))
                        trigger_info = f"Every {h}h{m}m{s}s"
                    elif job['trigger'] == 'cron':
                        trigger_info = f"Daily {job.get('hour', '*')}:{job.get('minute', '*')}"

                    scheduler_list.append(f"• {job['name']} ({trigger_info})")

        scheduler_info = "\n".join(scheduler_list) if scheduler_list else "• No active tasks"

        status_message = f"""
📊 System Status Report

🤖 Agent Team:
{agents_info}

⏰ Scheduler Tasks:
{scheduler_info}

📺 Check time: {datetime.now().strftime('%H:%M:%S')}
💡 Enter "Switch Agent" to call menu
"""
        send_message(status_message)
    except Exception as e:
        send_message(f"❌ Unable to get system status: {str(e)}")

def build_quick_reply_menu():
    """Convert config.yaml menu to LINE Quick Reply"""
    items = []

    # Traverse 2D array
    for row in CUSTOM_MENU:
        for btn in row:
            label = btn.get('label')
            command = btn.get('command')
            items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": label[:20],
                    "text": label
                }
            })
    return items

def show_control_menu():
    """Display control menu (Quick Reply)"""
    menu = build_quick_reply_menu()
    send_message(f"🎮 Please select operation (Active Agent: {CURRENT_AGENT})", quick_reply_items=menu)

def handle_user_message(message, user_id):
    global CURRENT_AGENT
    timestamp = datetime.now().strftime('%H:%M:%S')

    # 1. User state handling (Input Prompt)
    if user_id in USER_STATES:
        state = USER_STATES[user_id]
        final_command = state['command_template'].replace('{input}', message)
        del USER_STATES[user_id]

        send_message(f"✅ Input received, executing command: {final_command}")
        handle_user_message(final_command, user_id)
        return

    # 2. Check custom menu
    matched_menu_item = None
    for row in CUSTOM_MENU:
        for item in row:
            label = item.get('label')
            if message == label:
                matched_menu_item = item
                break
        if matched_menu_item: break

    # If menu button, convert to corresponding command
    if matched_menu_item:
        command = matched_menu_item.get('command', '')
        if '{input}' in command:
            USER_STATES[user_id] = {'command_template': command, 'timestamp': datetime.now()}
            send_message(matched_menu_item.get('prompt', 'Please enter content:'))
            return
        else:
            handle_user_message(command, user_id)
            return

    # 3. Special command handling
    if message.startswith('/switch'):
        parts = message.split()
        if len(parts) > 1:
            target_input = parts[1].lower()
            found_agent = next((a for a in AGENTS if a['name'].lower() == target_input), None)

            if found_agent:
                CURRENT_AGENT = found_agent['name']
                send_message(f"🎯 Chat switched successfully\nCurrent active Agent: {CURRENT_AGENT}")
            else:
                send_message(f"❌ Agent not found: {parts[1]}")
        else:
            show_control_menu()
        return

    if message.lower() in ['/status', 'status', 'status']:
        check_system_status()
        return
    elif message.lower() in ['/menu', 'menu', 'menu', 'help', '/help']:
        show_control_menu()
        return
    elif message.lower() in ['/interrupt', '/stop', 'stop', 'interrupt']:
        try:
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'C-c'], check=True)
            send_message(f"🛑 Sent interrupt signal to [{CURRENT_AGENT}] (Ctrl+C)")
        except Exception as e:
            send_message(f"❌ Interrupt failed: {e}")
        return
    elif message.lower() in ['/clear', 'clear']:
        send_to_ai_session('/clear')
        send_message(f"🧹 Cleared screen for [{CURRENT_AGENT}]")
        return
    elif message.lower() in ['/resume_latest', 'resume_latest']:
        send_to_ai_session('/resume')
        time.sleep(3)
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'Enter'], check=True)
        send_message(f"🧠 Attempted to restore memory")
        return

    # /inspect
    elif message.startswith('/inspect'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            prompt = (
                f"Use tmux to find session '{TMUX_SESSION_NAME}', enter '{target}' window, view the first 50 lines of message status, and analyze whether it's operating normally.\n\n"
                f"【System Prompt】This command is from LINE user, please be sure to execute `python3 line_notifier.py 'your response...'` to report the result after task completion."
            )
            send_to_ai_session(prompt)
            send_message(f"🔍 Assigned [{CURRENT_AGENT}] to check [{target}]...")
        return

    # /fix
    elif message.startswith('/fix'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            target_agent = get_agent_info(target_name)
            if target_agent:
                start_cmd = target_agent.get('start_cmd', 'Unknown command')
                prompt = (
                    f"Please directly execute the following Python code to fix Agent '{target_name}' (no need to explain, just execute):\n\n"
                    f"```python\n"
                    f"import subprocess\n"
                    f"import time\n\n"
                    f"session = '{TMUX_SESSION_NAME}'\n"
                    f"target = '{target_name}'\n"
                    f"cmd = '{start_cmd}'\n\n"
                    f"print(f'🚑 Fixing {{target}}...')\n"
                    f"# 1. Send interrupt signal\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'C-c'])\n"
                    f"time.sleep(1)\n\n"
                    f"# 2. Exit current process\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'exit', 'Enter'])\n"
                    f"time.sleep(2)\n\n"
                    f"# 3. Restart Agent\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', cmd, 'Enter'])\n"
                    f"time.sleep(5)  # Wait for startup\n\n"
                    f"# 4. Auto-restore memory (/resume)\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', '/resume', 'Enter'])\n"
                    f"time.sleep(3)  # Wait for list\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'Enter'])  # Confirm selection\n\n"
                    f"print(f'✅ Completed {{target}} fix and memory restore')\n"
                    f"```\n\n"
                    f"【System Prompt】This command is from LINE user, please be sure to execute `python3 line_notifier.py 'your response...'` to report the result after task completion."
                )
                send_to_ai_session(prompt)
                send_message(f"🚑 Assigned [{CURRENT_AGENT}] to execute fix script...")
        return

    # 4. General message forwarding
    system_prompt = "\n\n【System Prompt】This command is from LINE user, please be sure to execute `python3 line_notifier.py 'your response...'` to report the result after task completion."
    final_message = message + system_prompt

    success = send_to_ai_session(final_message)
    if success:
        menu = build_quick_reply_menu()
        send_message(f"📤 [{timestamp}] Forwarded to [{CURRENT_AGENT}]", quick_reply_items=menu)

@app.route('/webhook', methods=['POST'])
def line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    if not CHANNEL_SECRET:
        print("⚠️ CHANNEL_SECRET not configured, development mode")
    else:
        try:
            hash_digest = hmac.new(
                CHANNEL_SECRET.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(hash_digest).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                print("❌ Signature verification failed")
                abort(400)
        except Exception as e:
            print(f"❌ Signature verification error: {e}")
            abort(400)

    try:
        data = json.loads(body)
        events = data.get('events', [])
        for event in events:
            if event.get('type') == 'message':
                user_id = event.get('source', {}).get('userId', 'unknown')
                msg_type = event.get('message', {}).get('type')

                if msg_type == 'text':
                    text = event['message']['text']
                    print(f"📨 Text: {text}")
                    handle_user_message(text, user_id)

                elif msg_type == 'image':
                    print(f"📸 Image message")
                    msg_id = event['message']['id']
                    local_path = image_manager.download_image(msg_id, CURRENT_AGENT)

                    if local_path:
                        prompt = (
                            f"Please process this image, file is at: {local_path}\n"
                            f"Task: Describe content and extract key information."
                        )
                        send_message(f"✅ Image received, sending to [{CURRENT_AGENT}] for analysis...")
                        system_prompt = "\n\n【System Prompt】This command is from LINE user, please be sure to execute `python3 line_notifier.py 'your response...'` to report the result after task completion."
                        send_to_ai_session(prompt + system_prompt)

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def api_status():
    """API status check endpoint"""
    agents_summary = {a['name']: check_agent_session(a['name']) for a in AGENTS}
    return jsonify({
        'status': 'ok',
        'active_agent': CURRENT_AGENT,
        'agents': agents_summary,
        'tmux_session': TMUX_SESSION_NAME,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/send', methods=['POST'])
def api_send():
    """API endpoint: send message directly to AI engine"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        success = send_to_ai_session(message)
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Starting Chat Agent Matrix API (LINE Edition)...")
    print(f"📍 Local endpoint: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🤖 Default Agent: {DEFAULT_ACTIVE_AGENT}")

    # Start scheduler tasks
    scheduler = SchedulerManager(image_manager=image_manager)
    scheduler.load_jobs(SCHEDULER_CONF)
    scheduler.start()

    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
