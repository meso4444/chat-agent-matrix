#!/usr/bin/env python3
"""
Telegram Webhook Flask API (Multi-Agent Edition)
Receive Telegram user messages and distribute them to different AI Agent tmux windows
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
from scheduler_manager import SchedulerManager

app = Flask(__name__)

# 🔧 Support long messages: increase JSON request size limit (default 16MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB (support very long messages)
app.config['JSON_MAX_SIZE'] = 50 * 1024 * 1024       # JSON max size

# Read dynamic Webhook Secret
try:
    SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webhook_secret.token')
    with open(SECRET_FILE, 'r') as f:
        WEBHOOK_SECRET_TOKEN = f.read().strip()
except Exception as e:
    print(f"⚠️ Unable to read Webhook Secret: {e}")
    WEBHOOK_SECRET_TOKEN = None

# User state tracking: {user_id: {'command_template': '...', 'timestamp': ...}}
USER_STATES = {}

# Current active Agent (default to configured default value)
CURRENT_AGENT = DEFAULT_ACTIVE_AGENT

# Global scheduler manager (initialized in main program)
scheduler = None

class ImageManager:
    """Image Manager: responsible for downloading, storing and auto-cleanup (supports multi-Agent isolation)"""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Note: cleanup work has been handed over to SchedulerManager for unified management

    def download_image(self, file_id, agent_name):
        """Download image and return local absolute path"""
        try:
            # 1. Ensure Agent's directory structure is correct
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', agent_name, TEMP_IMAGE_DIR_NAME)
            if not os.path.exists(agent_img_dir):
                os.makedirs(agent_img_dir)

            # 2. Get file information (getFile)
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            response = requests.get(url)
            data = response.json()

            if not data.get('ok'):
                print(f"❌ Unable to get file information: {data}")
                return None

            file_path = data['result']['file_path']
            file_ext = os.path.splitext(file_path)[1] or ".jpg"

            # 3. Build local filename
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
        """Traverse all Agent directories for differential cleanup (called by Scheduler)"""
        print("🧹 [ImageManager] Starting multi-Agent image cleanup task...")
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
                        print(f"⚠️ Unable to delete [{name}] file {filename}: {e}")

            if count > 0:
                print(f"🧹 Cleaned up {count} expired files for Agent[{name}]")

# Initialize image manager
image_manager = ImageManager()

def get_agent_info(name):
    """Get detailed information of specified Agent (case-insensitive)"""
    for agent in AGENTS:
        if agent['name'].lower() == name.lower():
            return agent
    return None

def check_agent_session(name):
    """Check if tmux window of specific Agent exists"""
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
    """Send message to specified Agent tmux window (with special character escape support)"""
    global CURRENT_AGENT
    target = agent_name or CURRENT_AGENT

    try:
        if not check_agent_session(target):
            send_message(f"❌ Agent '{target}' window not found\nPlease check configuration or run: ./start_all_services.sh")
            return False

        # 🔧 Prevent Gemini CLI misinterpreting exclamation marks entering shell mode
        # Escape invalid: ! → ！(full-width exclamation mark)
        escaped_message = message.replace('!', '！')

        # 🔧 Use -l (literal mode) to send message, preventing tmux interpreting special characters
        # This resolves:
        # - tmux command interpretation (like #{pane_id} etc)
        # - bash history expansion
        # - "\n" accidentally triggering paste mode
        # (! → ！ replacement already handled above to prevent Gemini entering special mode)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            '-l',       # ← Key: literal mode, no tmux interpretation
            escaped_message
        ], check=True)

        # Delay to let message completely enter input buffer
        time.sleep(0.5)

        # Send first Enter key
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            'Enter'
        ], check=True)

        # 🔒 Double insurance: for Agents like Claude that need paste mode confirmation, press Enter again
        # This ensures long text is sent correctly
        if target in ['Claude', 'Accelerator', 'Chöd']:  # Claude-based agents
            time.sleep(0.2)
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
                'Enter'
            ], check=True)

        msg_preview = message[:80] + ('...' if len(message) > 80 else '')
        print(f"📤 Sent to Agent[{target}] (mode: literal): {msg_preview}")
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
        # 1. Security check: verify Secret Token (prevent malicious requests from non-Telegram)
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if WEBHOOK_SECRET_TOKEN and secret_header != WEBHOOK_SECRET_TOKEN:
            print(f"🛑 Reject unauthorized request (Invalid Secret): {secret_header}")
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

            # 1. Handle text messages
            if 'text' in message_data:
                user_message = message_data['text']
                # Improvement: log handling for long messages (show first 100 characters to avoid log explosion)
                msg_preview = user_message[:100] + ('...' if len(user_message) > 100 else '')
                msg_length = len(user_message)
                print(f"📨 Received text message (length: {msg_length} chars): {msg_preview} (from: @{username})")

            # 2. Handle photo messages
            elif 'photo' in message_data:
                print(f"📸 Received photo message (from: @{username})")
                photo_array = message_data['photo']
                best_photo = photo_array[-1]
                file_id = best_photo['file_id']

                local_path = image_manager.download_image(file_id, CURRENT_AGENT)
                if local_path:
                    user_message = (
                        f"Please process this image, file located at: {local_path}\n"
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
    """Handle user message (with Agent switching logic)"""
    global CURRENT_AGENT
    timestamp = datetime.now().strftime('%H:%M:%S')

    # 1. User state handling (custom menu input)
    if user_id in USER_STATES:
        state = USER_STATES[user_id]
        final_command = state['command_template'].replace('{input}', message)
        del USER_STATES[user_id]

        send_message(f"✅ Input received, execute command: {final_command}")

        # Key fix: recursively call itself, giving the system a chance to intercept special commands (like /switch, /inspect)
        # instead of directly send_to_ai_session
        handle_user_message(final_command, user_id, username)
        return

    # 2. Special command handling (highest priority)
    # A. Agent switching command
    if message.startswith('/switch'):
        parts = message.split()
        if len(parts) > 1:
            target_input = parts[1].lower()
            # Find Agent matching name (case-insensitive)
            found_agent = next((a for a in AGENTS if a['name'].lower() == target_input), None)

            if found_agent:
                CURRENT_AGENT = found_agent['name'] # Use original defined name (like "Güpa")
                send_message(f"⚡ <b>Dialog switched successfully</b>\nCurrent active Agent: <code>{CURRENT_AGENT}</code>")
            else:
                send_message(f"❌ Agent not found: <code>{parts[1]}</code>\nPlease enter <code>/status</code> to view available list.")
        else:
            # If only /switch is entered, show menu-style guidance
            show_agent_selector()
        return

    # B. System commands
    if message.lower() in ['/status', '状态', 'status']:
        check_system_status()
        return
    elif message.lower() in ['/help', '帮助', 'help', '/start']:
        show_help()
        return
    elif message.lower() in ['/menu', '菜单', 'menu']:
        show_control_menu()
        return
    elif message.lower() in ['/interrupt', '/stop', '停止', '中断']:
        try:
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'C-c'], check=True)
            send_message(f"🛑 Sent interrupt signal (Ctrl+C) to <b>[{CURRENT_AGENT}]</b>")
        except Exception as e:
            send_message(f"❌ Interrupt failed: {e}")
        return
    elif message.lower() in ['/clear', '清除']:
        send_to_ai_session('/clear')
        send_message(f"🧹 Cleared screen and memory of <b>[{CURRENT_AGENT}]</b>")
        return
    elif message.lower() in ['/resume_latest', '恢复记忆']:
        # Auto-restore recent memory
        # Process: send /resume -> wait for menu -> send Enter (select default/latest)
        try:
            print(f"⏳ [DEBUG] Starting memory restoration for {CURRENT_AGENT}...")
            send_to_ai_session('/resume')

            print(f"⏳ [DEBUG] Waiting 3 seconds for list to load...")
            time.sleep(3) # Wait for CLI to load Session list

            # Send Enter to confirm selection (use CURRENT_AGENT to replace non-existent function)
            print(f"⏳ [DEBUG] Sending Enter key to {CURRENT_AGENT}")
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'Enter'], check=True)

            send_message(f"🧠 Attempted to restore <b>[{CURRENT_AGENT}]</b> most recent conversation memory, if no response please run 'Reset'")
        except Exception as e:
            print(f"❌ [DEBUG] Memory restoration failed: {e}")
            send_message(f"❌ Memory restoration failed: {e}")
        return

    # C. Agent interaction monitoring commands
    # Format: /inspect [target_agent]
    elif message.startswith('/inspect'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            # Build Prompt (natural language style)
            prompt = (
                f"Find tmux session '{TMUX_SESSION_NAME}' via tmux, enter '{target}' window, view first 50 lines of message status, and analyze if it's working normally.\n\n"
                f"【System Prompt】This command is from Telegram user, after task completion you must execute `python3 telegram_notifier.py 'your response...'` to report result."
            )
            send_to_ai_session(prompt)
            send_message(f"🔍 Assigned <b>[{CURRENT_AGENT}]</b> to check status of <b>[{target}]</b>...")
        else:
            send_message("❌ Please specify the Agent name to check, for example: `/inspect claude`")
        return

    # Format: /awake [target_agent] - Automatic one-click agent recovery
    elif message.startswith('/awake'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            target_agent = get_agent_info(target_name)
            if target_agent:
                send_message(f"⚡ Starting automatic recovery for <b>[{target_name}]</b>...")
                # Launch in background thread to avoid blocking
                import threading
                thread = threading.Thread(target=awake_agent, args=(target_name, target_agent))
                thread.daemon = True
                thread.start()
            else:
                send_message(f"❌ Agent not found in configuration: {target_name}")
        else:
            send_message("❌ Please specify the Agent name to awake, for example: `/awake Güpa`")
        return

    # Format: /fix [target_agent]
    elif message.startswith('/fix'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            # Find target Agent's startup command
            target_agent = get_agent_info(target_name)

            if target_agent:
                start_cmd = target_agent.get('start_cmd', 'unknown command')
                # Build Prompt (natural language style, including Enter key technical details)
                prompt = (
                    f"Find tmux session '{TMUX_SESSION_NAME}' via tmux, enter '{target_name}' window, "
                    f"type /quit or /exit and execute Enter, wait 3 seconds then execute pwd command to confirm returning to Linux Shell, then execute startup command: `{start_cmd}`.\n"
                    f"Wait 5 seconds for startup to complete, then please type `/resume`, execute Enter, wait 3 seconds then execute enter once more to restore most recent conversation record.\n\n"
                    f"【⚠️ Technical Limit: Tmux Send-Keys and Enter Key Handling (Strictly Enforce)】\n"
                    f"Since tmux send-keys sends extremely fast, if text and Enter are sent in the same command, will cause target Shell buffer overflow and 'lose' Enter signal. Must obey following::\n"
                    f"1. Forbidden method (❌)\n"
                    f"tmux send-keys -t target text Enter (strictly prohibit sending on same line)\n"
                    f"tmux send-keys -t target text C-m (prohibit C-m)\n"
                    f"2. Forced method (✅)\n"
                    f"Must use 'text -> delay -> Enter' three-step method:\n"
                    f"tmux send-keys -t target your message content && sleep 1 && tmux send-keys -t target Enter\n\n"
                    f"【System Prompt】This command is from Telegram user, after task completion you must execute `python3 telegram_notifier.py 'your response...'` to report result."
                )
                send_to_ai_session(prompt)
                send_message(f"🚑 Assigned <b>[{CURRENT_AGENT}]</b> to fix <b>[{target_name}]</b>...")
            else:
                send_message(f"❌ Agent not found in configuration: {target_name}")
        else:
            send_message("❌ Please specify the Agent name to fix, for example: `/fix claude`")
        return

    # Format: /capture [target_agent]
    elif message.startswith('/capture'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            if check_agent_session(target):
                try:
                    # Capture tmux pane content
                    result = subprocess.run(
                        ['tmux', 'capture-pane', '-t', f'{TMUX_SESSION_NAME}:{target}', '-p'],
                        capture_output=True, text=True, timeout=5
                    )

                    if result.returncode == 0:
                        output_lines = result.stdout.split('\n')
                        # Take last 100 lines
                        captured_lines = output_lines[-100:] if len(output_lines) > 100 else output_lines
                        captured_content = '\n'.join(captured_lines).strip()

                        # Split into multiple messages to send (avoid Telegram limit)
                        msg_chunks = []
                        current_chunk = ""
                        for line in captured_lines:
                            if len(current_chunk) + len(line) + 1 > 4000:  # Telegram message limit
                                if current_chunk:
                                    msg_chunks.append(current_chunk)
                                current_chunk = line
                            else:
                                current_chunk += line + '\n'
                        if current_chunk:
                            msg_chunks.append(current_chunk)

                        # Send screenshot
                        send_message(f"📸 <b>[{target}]</b> Screen capture (last 100 lines)\n<code>{msg_chunks[0]}</code>" if msg_chunks else f"❌ [{target}] screen is empty")

                        # If more chunks, continue sending
                        for chunk in msg_chunks[1:]:
                            time.sleep(0.3)
                            send_message(f"<code>{chunk}</code>")
                    else:
                        send_message(f"❌ Unable to capture [{target}]: {result.stderr}")
                except subprocess.TimeoutExpired:
                    send_message(f"⏱️ Capture timeout [{target}]")
                except Exception as e:
                    send_message(f"❌ Capture failed [{target}]: {str(e)}")
            else:
                send_message(f"❌ Agent '{target}' window not found")
        else:
            send_message("❌ Please specify the Agent name to capture, for example: `/capture Güpa20`")
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
            # Recursively process menu command (handle possible /status etc)
            handle_user_message(command, user_id, username)
        return

    # 4. General message forwarding
    # Append forced reporting hint to ensure AI knows this is an external command needing response
    system_prompt = "\n\n【System Prompt】This command is from Telegram user, after task completion you must execute `python3 telegram_notifier.py 'your response...'` to report result."
    final_message = message + system_prompt

    success = send_to_ai_session(final_message)
    if success:
        send_message(f"🐙 <b>[{timestamp}]</b> > Matrix Connected :: <b>[{CURRENT_AGENT}]</b>")

def handle_callback_query(callback_data, user_id):
    """Handle button callback"""
    global CURRENT_AGENT
    if callback_data.startswith('sw_'):
        target = callback_data.replace('sw_', '')
        CURRENT_AGENT = target
        send_message(f"⚡ <b>Dialog switched successfully</b>\nCurrent active Agent: <code>{target}</code>")
    elif callback_data == 'system_status':
        check_system_status()
    elif callback_data == 'help':
        show_help()

def show_agent_selector():
    """Display Agent switching menu"""
    keyboard = []
    for agent in AGENTS:
        # Here inline keyboard is better, but to maintain consistent use Reply Keyboard or simple text response
        # temporarily use text response to guide switching
        pass

    agent_list = "\n".join([f"• <code>{a['name']}</code> - {a['description']}" for a in AGENTS])
    msg = f"🤖 <b>Please select Agent to switch to</b>\nFormat: <code>/switch [name]</code>\n\nAvailable list:\n{agent_list}"
    send_message(msg)

def wait_for_agent_prompt(target_name, engine, max_wait=30):
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
                ['tmux', 'capture-pane', '-t', f'{TMUX_SESSION_NAME}:{target_name}', '-p'],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout
            if not output:
                time.sleep(0.5)
                continue

            # Check if entire pane content contains any expected prompt marker
            for marker in prompt_markers:
                if marker in output:
                    return True
        except Exception as e:
            pass

        time.sleep(0.5)

    return False

def awake_agent(target_name, target_agent):
    """Automatically recover a faulty Agent with precise timing control"""
    try:
        # Determine startup command based on agent engine type
        engine = target_agent.get('engine', 'claude')
        engine_cmd_map = {
            'gemini': 'gemini --yolo',
            'claude': 'claude --permission-mode bypassPermissions'
        }
        start_cmd = target_agent.get('start_cmd', engine_cmd_map.get(engine, 'python3 main.py'))

        send_message(f"📍 [Step 1/6] Entering {target_name} tmux window...")

        # Step 1: Send /quit command
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            '/quit'
        ], check=True)
        time.sleep(1)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)
        time.sleep(3)

        send_message(f"📍 [Step 2/6] Verifying shell return with pwd...")

        # Step 2: Verify with pwd
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'pwd'
        ], check=True)
        time.sleep(1)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)
        time.sleep(2)

        send_message(f"📍 [Step 3/6] Executing startup command: {start_cmd}...")

        # Step 3: Restart Agent
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            start_cmd
        ], check=True)
        time.sleep(1)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)

        send_message(f"📍 [Step 4/6] Waiting for {engine} CLI prompt to appear...")
        if wait_for_agent_prompt(target_name, engine, max_wait=60):
            send_message(f"✅ Detected {engine} prompt - startup successful")
        else:
            send_message(f"⚠️ Timeout waiting for {engine} prompt, continuing with recovery...")

        send_message(f"📍 [Step 5/6] Restoring conversation with /resume...")

        # Step 5: Resume conversation
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            '/resume'
        ], check=True)
        time.sleep(1)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)
        time.sleep(3)

        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)
        time.sleep(2)

        send_message(f"✅ [Step 6/6] Agent <b>{target_name}</b> awakened successfully! Ready to use.")

    except subprocess.CalledProcessError as e:
        send_message(f"❌ Awake failed at step: {str(e)}")
    except Exception as e:
        send_message(f"❌ Error during awake process: {str(e)}")

def check_system_status():
    """Check system status (Multi-Agent Edition)"""
    try:
        # 0. Create role reference table
        agent_role_map = {}
        for grp in COLLABORATION_GROUPS:
            roles = grp.get('roles', {})
            for member, role in roles.items():
                # Display complete role description (no length limit)
                agent_role_map[member] = f"[{grp.get('name')}] {role}"

        # 1. Agent status
        agent_status_list = []
        for agent in AGENTS:
            name = agent['name']
            desc = agent.get('description', 'No description')
            engine = agent['engine']
            role_info = f"\n      └ {agent_role_map[name]}" if name in agent_role_map else ""

            is_active = " (⭐ active)" if name == CURRENT_AGENT else ""
            status_icon = "🟢" if check_agent_session(name) else "🔴"

            agent_status_list.append(f"{status_icon} <b>[{name}]</b> {desc} ({engine}){is_active}{role_info}")

        agents_info = "\n".join(agent_status_list)

        # 2. Schedule status (Real-time query)
        scheduler_list = []
        if scheduler:
            scheduler_data = scheduler.list_jobs()
            for job in scheduler_data.get('jobs', []):
                job_id = job.get('id', '?')
                trigger_str = job.get('trigger', '?')
                next_run = job.get('next_run_time', '?')

                # Format next run time
                if next_run and next_run != 'None':
                    # next_run_time format: "2026-03-04 12:34:56.123456"
                    next_run_display = next_run.split('.')[0]  # Remove milliseconds
                else:
                    next_run_display = "Not scheduled"

                # Combine display (Real-time information)
                scheduler_list.append(f"• {job_id}\n  └ Trigger: {trigger_str}\n  └ Next run: {next_run_display}")

        scheduler_info = "\n".join(scheduler_list) if scheduler_list else "• No enabled tasks"

        # 3. tmux status
        result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
        session_info = "Running" if TMUX_SESSION_NAME in result.stdout else "Session not started"

        status_message = f"""
📊 <b>Chat Agent Matrix Status Report</b>

🤖 <b>Agent Squad:</b>
{agents_info}

⏰ <b>Schedule Tasks:</b>
{scheduler_info}

📺 <b>System Status:</b>
• tmux Session: {session_info}
• Telegram API: 🟢 Normal
• Check time: {datetime.now().strftime('%H:%M:%S')}

💡 Enter <code>/switch [name]</code> to switch Agent
"""
        send_message(status_message)
    except Exception as e:
        send_message(f"❌ Unable to get system status: {str(e)}")

def show_help():
    """Display help message"""
    help_message = f"""
📖 <b>Chat Agent Matrix - Complete Feature Guide</b>

<b>🎯 Current Focused Agent:</b> <code>{CURRENT_AGENT}</code>

───────────────────────────────

<b>🔧 Basic Conversation Operations</b>
• Send message directly - to active Agent (⭐)
• Send image - to active Agent for multimodal analysis
• <code>/switch [name]</code> - Switch active Agent
• <code>/menu</code> - Show shortcut function menu

───────────────────────────────

<b>🔍 System Check and Control</b>
• <code>/status</code> - View all Agent status, schedule tasks, system info
• <code>/inspect [agent]</code> - Deep check specified Agent's tmux session
• <code>/capture [agent]</code> - Capture specified Agent's window content (last 100 lines)
• <code>/interrupt</code> or <code>/stop</code> - Interrupt current Agent execution (Ctrl+C)
• <code>/clear</code> - Clear current Agent window and memory

───────────────────────────────

<b>🧠 Memory and Recovery</b>
• <code>/resume_latest</code> - Restore most recent conversation content

───────────────────────────────

<b>🛠️ Advanced Operations</b>
• <code>/fix [agent]</code> - Try to fix faulty Agent (clear stuck commands)

───────────────────────────────

<b>💡 Quick Tips</b>
1️⃣ Agent marked with ⭐ is current active, direct messages go to it
2️⃣ /status quickly understand overall system status
3️⃣ Schedule tasks configured in scheduler.yaml
4️⃣ Use /menu to select common operations, no need to remember commands

"""
    send_message(help_message)

def show_control_menu():
    """Display control menu (based on config.py customization)"""
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

# ==========================================
# Schedule Management API
# ==========================================

@app.route('/scheduler/refresh', methods=['POST'])
def scheduler_refresh():
    """Re-read scheduler.yaml and refresh schedules"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': 'Scheduler manager not initialized'}), 500

    result = scheduler.refresh_jobs()
    return jsonify(result), 200 if result['status'] == 'ok' else 400

@app.route('/scheduler/jobs', methods=['GET'])
def scheduler_list_jobs():
    """List all schedule tasks"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': 'Scheduler manager not initialized'}), 500

    result = scheduler.list_jobs()
    return jsonify(result), 200

@app.route('/scheduler/jobs/register', methods=['POST'])
def scheduler_register_job():
    """Register new schedule task"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': 'Scheduler manager not initialized'}), 500

    job_config = request.get_json()
    if not job_config:
        return jsonify({'status': 'error', 'message': 'Please provide valid JSON configuration'}), 400

    result = scheduler.register_job(job_config)
    return jsonify(result), 200 if result['status'] == 'ok' else 400

@app.route('/scheduler/jobs/<job_id>', methods=['DELETE'])
def scheduler_delete_job(job_id):
    """Delete schedule task"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': 'Scheduler manager not initialized'}), 500

    result = scheduler.delete_job(job_id)
    return jsonify(result), 200 if result['status'] == 'ok' else 400

if __name__ == '__main__':
    print(f"🚀 Starting Chat Agent Matrix API (Multi-Agent Mode)...")
    print(f"📍 Local endpoint: http://{FLASK_HOST}:{FLASK_PORT}")
    # === AACS: physically write current Port for startup script to read ===
    port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".flask_port")
    with open(port_file, "w") as f:
        f.write(str(FLASK_PORT))

    print(f"🤖 Default Agent: {DEFAULT_ACTIVE_AGENT}")
    print(f"👥 Configured Agents: {', '.join([a['name'] for a in AGENTS])}")
    print("")

    # Start schedule tasks
    scheduler = SchedulerManager(image_manager=image_manager)
    scheduler.load_jobs(SCHEDULER_CONF)
    scheduler.start()

    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
