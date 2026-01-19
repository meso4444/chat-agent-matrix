#!/usr/bin/env python3
"""
Telegram Webhook Flask API (Multi-Agent Version)
Receive Telegram user messages and dispatch to different AI Agent tmux windows
"""

from flask import Flask, request, jsonify
import json
import subprocess
import time
import os
import threading
import requests
from datetime import datetime, timedelta
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FLASK_HOST, FLASK_PORT, 
    TMUX_SESSION_NAME, TELEGRAM_WEBHOOK_PATH, AGENTS, DEFAULT_ACTIVE_AGENT,
    DEFAULT_CLEANUP_POLICY, CUSTOM_MENU, SCHEDULER_CONF, TEMP_IMAGE_DIR_NAME,
    COLLABORATION_GROUPS
)
from telegram_notifier import send_message, send_message_with_keyboard
from telegram_scripts.scheduler_manager import SchedulerManager

app = Flask(__name__)

# Load dynamic Webhook Secret
try:
    SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webhook_secret.token')
    with open(SECRET_FILE, 'r') as f:
        WEBHOOK_SECRET_TOKEN = f.read().strip()
except Exception as e:
    print(f"⚠️ Failed to read Webhook Secret: {e}")
    WEBHOOK_SECRET_TOKEN = None

# User state tracking: {user_id: {'command_template': '...', 'timestamp': ...}}
USER_STATES = {}

# Current active Agent (default from configuration)
CURRENT_AGENT = DEFAULT_ACTIVE_AGENT

class ImageManager:
    """Image Manager: responsible for downloading, storing, and auto-cleanup (supports multi-agent isolation)"""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Note: cleanup tasks have been delegated to SchedulerManager for unified management
    
    def download_image(self, file_id, agent_name):
        """Download image and return local absolute path"""
        try:
            # 1. Ensure Agent directory structure is correct
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', agent_name, TEMP_IMAGE_DIR_NAME)
            if not os.path.exists(agent_img_dir):
                os.makedirs(agent_img_dir)

            # 2. Get file info (getFile)
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            response = requests.get(url)
            data = response.json()

            if not data.get('ok'):
                print(f"❌ Failed to get file info: {data}")
                return None

            file_path = data['result']['file_path']
            file_ext = os.path.splitext(file_path)[1] or ".jpg"

            # 3. Construct local filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{file_id[:8]}{file_ext}"
            local_path = os.path.join(agent_img_dir, filename)

            # 4. Download file content
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            img_data = requests.get(download_url).content

            with open(local_path, 'wb') as f:
                f.write(img_data)

            print(f"📸 Image downloaded to [{agent_name}]: {local_path}")
            return local_path

        except Exception as e:
            print(f"❌ Image download failed: {e}")
            return None

    def cleanup_old_files(self):
        """Traverse all Agent directories and execute differentiated cleanup (called by Scheduler)"""
        print("🧹 [ImageManager] Starting multi-agent image cleanup task...")
        from config import AGENTS, DEFAULT_CLEANUP_POLICY

        for agent in AGENTS:
            name = agent['name']
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', name, TEMP_IMAGE_DIR_NAME)

            if not os.path.exists(agent_img_dir):
                continue

            # Read cleanup policy
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
                        print(f"⚠️ Failed to delete [{name}] file {filename}: {e}")

            if count > 0:
                print(f"🧹 Cleaned {count} expired files for Agent[{name}]")

# Initialize Image Manager
image_manager = ImageManager()

def get_agent_info(name):
    """Get detailed information of specified Agent (case-insensitive)"""
    for agent in AGENTS:
        if agent['name'].lower() == name.lower():
            return agent
    return None

def check_agent_session(name):
    """Check if tmux window for specific Agent exists"""
    try:
        # tmux has-session -t session:window
        result = subprocess.run(
            ['tmux', 'has-session', '-t', f'{TMUX_SESSION_NAME}:{name}'],
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to check tmux session: {e}")
        return False

def send_to_ai_session(message, agent_name=None):
    """Send message to specified Agent tmux window"""
    global CURRENT_AGENT
    target = agent_name or CURRENT_AGENT
    
    try:
        if not check_agent_session(target):
            send_message(f"❌ Agent '{target}' window does not exist\nPlease check configuration or run: ./start_all_services.sh")
            return False

        # Send message to tmux session's specified window
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            message
        ], check=True)

        time.sleep(0.1)

        # Send Enter key
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            'Enter'
        ], check=True)

        print(f"📤 Sent to Agent[{target}]: {message}")
        return True

    except Exception as e:
        print(f"❌ Failed to send to Agent: {e}")
        send_message(f"❌ System error: {str(e)}")
        return False

def capture_ai_response(agent_name=None, delay=3):
    """Capture response from specific Agent"""
    target = agent_name or CURRENT_AGENT
    try:
        time.sleep(delay)
        result = subprocess.run([
            'tmux', 'capture-pane', '-t', f'{TMUX_SESSION_NAME}:{target}', '-p'
        ], capture_output=True, text=True)

        if result.stdout:
            lines = result.stdout.strip().split('\n')
            recent_output = '\n'.join(lines[-15:])
            send_message(f"💬 <b>[{target}] Latest Response:</b>\n<pre>{recent_output}</pre>")
            return True
    except Exception as e:
        print(f"⚠️ Failed to capture {target} output: {e}")
        return False

@app.route(TELEGRAM_WEBHOOK_PATH, methods=['POST'])
def telegram_webhook():
    """Receive Telegram webhook"""
    try:
        # 1. Security check: verify Secret Token (prevent malicious requests not from Telegram)
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if WEBHOOK_SECRET_TOKEN and secret_header != WEBHOOK_SECRET_TOKEN:
            print(f"🛑 Rejected unauthorized request (Invalid Secret): {secret_header}")
            return jsonify({'status': 'unauthorized'}), 403

        webhook_data = request.get_json()
        if 'message' in webhook_data:
            message_data = webhook_data['message']

            # Verify chat_id
            chat_id = str(message_data.get('chat', {}).get('id', ''))
            if TELEGRAM_CHAT_ID and chat_id != str(TELEGRAM_CHAT_ID):
                print(f"⚠️ Unauthorized chat_id: {chat_id}")
                return jsonify({'status': 'unauthorized'}), 403

            # Get user information
            user_id = message_data.get('from', {}).get('id', 'unknown')
            username = message_data.get('from', {}).get('username', 'unknown')

            user_message = None

            # 1. Handle text message
            if 'text' in message_data:
                user_message = message_data['text']
                print(f"📨 Received text message: {user_message} (from: @{username})")
                
            # 2. Handle image message
            elif 'photo' in message_data:
                print(f"📸 Received image message (from: @{username})")
                photo_array = message_data['photo']
                best_photo = photo_array[-1]
                file_id = best_photo['file_id']

                local_path = image_manager.download_image(file_id, CURRENT_AGENT)
                if local_path:
                    user_message = (
                        f"Please process this image, file is at: {local_path}\n"
                        f"Tasks:\n"
                        f"1. Describe the main content and scene of the image.\n"
                        f"2. If the image contains text, please extract key information.\n"
                        f"3. Summarize the key points of this image."
                    )
                    send_message(f"✅ Image received, sending to <b>[{CURRENT_AGENT}]</b> for analysis...")
                else:
                    send_message("❌ Image download failed")
            
            if user_message:
                handle_user_message(user_message, user_id, username)
        
        elif 'callback_query' in webhook_data:
            callback = webhook_data['callback_query']
            callback_data = callback.get('data', '')
            user_id = callback.get('from', {}).get('id', 'unknown')
            print(f"🔘 Received button click: {callback_data}")
            handle_callback_query(callback_data, user_id)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return jsonify({'error': str(e)}), 500

def handle_user_message(message, user_id, username):
    """Handle user message (including Agent switching logic)"""
    global CURRENT_AGENT
    timestamp = datetime.now().strftime('%H:%M:%S')

    # 1. User state handling (custom menu input)
    if user_id in USER_STATES:
        state = USER_STATES[user_id]
        final_command = state['command_template'].replace('{input}', message)
        del USER_STATES[user_id]
        
        send_message(f"✅ Input received, executing command: {final_command}")

        # Critical fix: Recursively call itself to give the system a chance to intercept special commands (e.g., /switch, /inspect)
        # rather than directly sending to send_to_ai_session
        handle_user_message(final_command, user_id, username)
        return

    # 2. Special command handling (highest priority)
    # A. Agent switching command
    if message.startswith('/switch'):
        parts = message.split()
        if len(parts) > 1:
            target_input = parts[1].lower()
            # Find Agent with matching name (case-insensitive)
            found_agent = next((a for a in AGENTS if a['name'].lower() == target_input), None)

            if found_agent:
                CURRENT_AGENT = found_agent['name'] # Use original defined name (e.g., "Güpa")
                send_message(f"🎯 <b>Chat switched successfully</b>\nCurrent active Agent: <code>{CURRENT_AGENT}</code>")
            else:
                send_message(f"❌ Agent not found: <code>{parts[1]}</code>\nPlease enter <code>/status</code> to view available list.")
        else:
            # If only /switch is entered, display menu-style guidance
            show_agent_selector()
        return

    # B. System commands
    if message.lower() in ['/status', 'status']:
        check_system_status()
        return
    elif message.lower() in ['/help', 'help', '/start']:
        show_help()
        return
    elif message.lower() in ['/menu', 'menu']:
        show_control_menu()
        return
    elif message.lower() in ['/interrupt', '/stop']:
        try:
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'C-c'], check=True)
            send_message(f"🛑 Sent interrupt signal to <b>[{CURRENT_AGENT}]</b> (Ctrl+C)")
        except Exception as e:
            send_message(f"❌ Interrupt failed: {e}")
        return
    elif message.lower() in ['/clear']:
        send_to_ai_session('/clear')
        send_message(f"🧹 Cleared screen and memory for <b>[{CURRENT_AGENT}]</b>")
        return
    elif message.lower() in ['/resume_latest']:
        # Auto-restore latest memory
        # Process: Send /resume -> Wait for menu -> Send Enter (select default/latest)
        try:
            print(f"⏳ [DEBUG] Starting to restore memory for {CURRENT_AGENT}...")
            send_to_ai_session('/resume')

            print(f"⏳ [DEBUG] Waiting 3 seconds for list to load...")
            time.sleep(3) # Wait for CLI to load Session list

            # Send Enter to confirm selection (using CURRENT_AGENT to replace non-existent function)
            print(f"⏳ [DEBUG] Sending Enter key to {CURRENT_AGENT}")
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'Enter'], check=True)

            send_message(f"🧠 Attempted to restore latest conversation memory for <b>[{CURRENT_AGENT}]</b>, please execute 'Reset' if no response")
        except Exception as e:
            print(f"❌ [DEBUG] Failed to restore memory: {e}")
            send_message(f"❌ Failed to restore memory: {e}")
        return

    # C. Agent interaction monitoring commands
    # Format: /inspect [target_agent]
    elif message.startswith('/inspect'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            # Build Prompt (natural language style)
            prompt = (
                f"Use tmux to find session '{TMUX_SESSION_NAME}', enter '{target}' window, view the first 50 lines of message status, and analyze whether it's operating normally.\n\n"
                f"【System Prompt】This command is from Telegram user, please be sure to execute `python3 telegram_notifier.py 'your response...'` to report the result after task completion."
            )
            send_to_ai_session(prompt)
            send_message(f"🔍 Assigned <b>[{CURRENT_AGENT}]</b> to check status of <b>[{target}]</b>...")
        else:
            send_message("❌ Please specify the Agent name to check, for example: `/inspect claude`")
        return

    # Format: /fix [target_agent]
    elif message.startswith('/fix'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            # Find target Agent's startup command
            target_agent = get_agent_info(target_name)

            if target_agent:
                start_cmd = target_agent.get('start_cmd', 'Unknown command')
                # Build Prompt (natural language style, including Enter key technical details)
                prompt = (
                    f"Use tmux to find session '{TMUX_SESSION_NAME}', enter '{target_name}' window, "
                    f"type /quit or /exit and press Enter, wait 3 seconds then execute pwd command to confirm back to Linux Shell, then execute startup command: `{start_cmd}`.\n"
                    f"Wait 5 seconds for startup to complete, then type `/resume`, press Enter, wait 3 seconds then press Enter again to restore the latest conversation record.\n\n"
                    f"【⚠️ Technical Limitation: Tmux Send-Keys and Enter Key Handling (Strict Compliance)】\n"
                    f"Because tmux send-keys sends at extremely high speed, if text and Enter are sent in the same command, it will cause the target shell buffer to overflow and 'drop' the Enter signal. Please strictly follow these standards:\n"
                    f"1. Forbidden Methods (❌)\n"
                    f"tmux send-keys -t target text Enter (Strictly prohibit same-line sending)\n"
                    f"tmux send-keys -t target text C-m (Disable C-m)\n"
                    f"2. Mandatory Methods (✅)\n"
                    f"Must adopt 'Text -> Delay -> Enter' three-step method:\n"
                    f"tmux send-keys -t target Your message content && sleep 1 && tmux send-keys -t target Enter\n\n"
                    f"【System Prompt】This command is from Telegram user, please be sure to execute `python3 telegram_notifier.py 'your response...'` to report the result after task completion."
                )
                send_to_ai_session(prompt)
                send_message(f"🚑 Assigned <b>[{CURRENT_AGENT}]</b> to fix <b>[{target_name}]</b>...")
            else:
                send_message(f"❌ Agent not found in config: {target_name}")
        else:
            send_message("❌ Please specify the Agent name to fix, for example: `/fix claude`")
        return

    # 3. Check if it's a custom menu label
    matched_menu_item = None
    for row in CUSTOM_MENU:
        for item in row:
            label = item.get('label') if isinstance(item, dict) else item
            if message == label:
                matched_menu_item = item
                break
        if matched_menu_item: break

    if matched_menu_item:
        command = matched_menu_item.get('command', '')
        if '{input}' in command:
            USER_STATES[user_id] = {'command_template': command, 'timestamp': datetime.now()}
            send_message(matched_menu_item.get('prompt', 'Please enter content:'))
        else:
            # Recursively handle menu commands (handle possible /status, etc.)
            handle_user_message(command, user_id, username)
        return

    # 4. General message forwarding
    # Add mandatory report prompt to ensure AI knows this is an external command that requires response
    system_prompt = "\n\n【System Prompt】This command is from Telegram user, please be sure to execute `python3 telegram_notifier.py 'your response...'` to report the result after task completion."
    final_message = message + system_prompt
    
    success = send_to_ai_session(final_message)
    if success:
        send_message(f"📤 <b>[{timestamp}]</b> Forwarded to <b>[{CURRENT_AGENT}]</b>:\n<i>{message}</i>")

def handle_callback_query(callback_data, user_id):
    """Handle button callback"""
    global CURRENT_AGENT
    if callback_data.startswith('sw_'):
        target = callback_data.replace('sw_', '')
        CURRENT_AGENT = target
        send_message(f"🎯 <b>Chat switched successfully</b>\nCurrent active Agent: <code>{target}</code>")
    elif callback_data == 'system_status':
        check_system_status()
    elif callback_data == 'help':
        show_help()

def show_agent_selector():
    """Display Agent switching menu"""
    keyboard = []
    for agent in AGENTS:
        # It's better to use inline keyboard here, but to maintain consistent use of Reply Keyboard or simple text response
        # Temporarily use text response to guide switching
        pass

    agent_list = "\n".join([f"• <code>{a['name']}</code> - {a['description']}" for a in AGENTS])
    msg = f"🤖 <b>Please select Agent to switch to</b>\nFormat: <code>/switch [Name]</code>\n\nAvailable list:\n{agent_list}"
    send_message(msg)

def check_system_status():
    """Check system status (Multi-Agent version)"""
    try:
        # 0. Build role mapping table
        agent_role_map = {}
        for grp in COLLABORATION_GROUPS:
            roles = grp.get('roles', {})
            for member, role in roles.items():
                # Simplified display: only take first 15 characters
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

            agent_status_list.append(f"{status_icon} <b>[{name}]</b> {desc} ({engine}){is_active}{role_info}")

        agents_info = "\n".join(agent_status_list)

        # 2. Scheduler status
        scheduler_list = []
        if SCHEDULER_CONF:
            for job in SCHEDULER_CONF:
                if job.get('active'):
                    trigger_info = ""
                    if job['trigger'] == 'interval':
                        # Simplified interval display
                        h = job.get('hours', job.get('hour', 0))
                        m = job.get('minutes', job.get('minute', 0))
                        s = job.get('seconds', job.get('second', 0))
                        trigger_info = f"Every {h}h{m}m{s}s"
                    elif job['trigger'] == 'cron':
                        trigger_info = f"Daily {job.get('hour', '*')}:{job.get('minute', '*')}"

                    scheduler_list.append(f"• {job['name']} ({trigger_info})")

        scheduler_info = "\n".join(scheduler_list) if scheduler_list else "• No active tasks"

        # 3. tmux status
        result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
        session_info = "Running" if TMUX_SESSION_NAME in result.stdout else "Session not started"

        status_message = f"""
📊 <b>Chat Agent Matrix Status Report</b>

🤖 <b>Agent Team:</b>
{agents_info}

⏰ <b>Scheduler Tasks:</b>
{scheduler_info}

📺 <b>System Status:</b>
• tmux Session: {session_info}
• Telegram API: 🟢 Normal
• Check time: {datetime.now().strftime('%H:%M:%S')}

💡 Enter <code>/switch [Name]</code> to switch Agent
"""
        send_message(status_message)
    except Exception as e:
        send_message(f"❌ Unable to get system status: {str(e)}")

def show_help():
    """Display help message"""
    help_message = f"""
📖 <b>Chat Agent Matrix Command Guide</b>

🎯 <b>Current focused Agent:</b> <code>{CURRENT_AGENT}</code>

🔧 <b>Core Commands:</b>
• <code>/switch [name]</code> - Switch dialog Agent
• <code>/status</code> - Check all Agent status
• <code>/menu</code> - Display function menu
• <code>/interrupt</code> - Interrupt current execution (Ctrl+C)
• <code>/clear</code> - Clear current window and memory

💡 <b>Usage Tips:</b>
Send messages or images directly, the system will automatically forward them to the active Agent marked with ⭐."""
    send_message(help_message)

def show_control_menu():
    """Display control menu (customizable from config.py)"""
    menu_message = f"🎮 <b>System Control Menu</b> (Active: {CURRENT_AGENT})\n\nPlease select operation:"
    keyboard = []
    for row in CUSTOM_MENU:
        keyboard_row = []
        for item in row:
            label = item.get('label') if isinstance(item, dict) else item
            keyboard_row.append(str(label))
        keyboard.append(keyboard_row)
    send_message_with_keyboard(menu_message, keyboard)

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

if __name__ == '__main__':
    print(f"🚀 Starting Chat Agent Matrix API (Multi-Agent Mode)...")
    print(f"📍 Local endpoint: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🤖 Default Agent: {DEFAULT_ACTIVE_AGENT}")
    print(f"👥 Configured Agents: {', '.join([a['name'] for a in AGENTS])}")
    print("")

    # Start scheduler tasks
    scheduler = SchedulerManager(image_manager=image_manager)
    scheduler.load_jobs(SCHEDULER_CONF)
    scheduler.start()

    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
