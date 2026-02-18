#!/usr/bin/env python3
"""
AI Engine Telegram Notifier
Read message format from template files, AI engine only needs to fill in variables
"""

import requests
import json
import yaml
import os
import sys
from datetime import datetime

# Support execution from agent_home directory: find config.py in parent directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# If config not found in current directory, search upwards level by level
if not os.path.exists(os.path.join(script_dir, 'config.py')):
    # From agent_home/AgentName/ go up two levels to telegram/
    telegram_dir = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(telegram_dir, 'config.py')):
        sys.path.insert(0, telegram_dir)
    else:
        # If still not found, try one more level up
        telegram_dir = os.path.dirname(telegram_dir)
        if os.path.exists(os.path.join(telegram_dir, 'config.py')):
            sys.path.insert(0, telegram_dir)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_API_BASE_URL

def load_message_template(template_name: str, software: str = None) -> dict:
    """
    Load message template from template file

    Args:
        template_name (str): Template name (start, progress, success, error, custom)
        software (str): Software name, used to find software-specific templates

    Returns:
        dict: Template dictionary containing icon, title, content
    """
    # Support execution from agent_home directory: prioritize finding message_templates.yaml in parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(script_dir, 'message_templates.yaml')

    if not os.path.exists(template_file):
        # Go up two levels to telegram/ directory
        telegram_dir = os.path.dirname(os.path.dirname(script_dir))
        template_file = os.path.join(telegram_dir, 'message_templates.yaml')

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)

        # Prioritize using software-specific templates
        if software and software in templates.get('software_templates', {}):
            software_template = templates['software_templates'][software].get(template_name)
            if software_template:
                return software_template

        # Use generic template
        return templates['templates'].get(template_name, {})

    except Exception as e:
        print(f"⚠️ Unable to load template: {e}")
        # Fall back to simple template
        return {
            'icon': '📋',
            'title': f'{template_name.upper()}',
            'content': '{content}'
        }

def send_message(message: str) -> bool:
    """
    Send Telegram message

    Args:
        message (str): Message content to send

    Returns:
        bool: Whether sending was successful
    """
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: Please configure TELEGRAM_BOT_TOKEN in config.py")
        return False

    if not TELEGRAM_CHAT_ID:
        print("❌ Error: Please configure TELEGRAM_CHAT_ID in config.py")
        return False

    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'  # Support HTML format
    }

    try:
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print(f'✅ Telegram notification sent successfully: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ Telegram notification failed to send: {response.status_code} - {response.text}')
            return False

    except Exception as e:
        print(f'❌ Error during sending: {e}')
        return False

def send_message_with_keyboard(message: str, keyboard_buttons: list = None) -> bool:
    """
    Send Telegram message with custom keyboard

    Args:
        message (str): Message content to send
        keyboard_buttons (list): Keyboard button configuration

    Returns:
        bool: Whether sending was successful
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Please check Telegram configuration")
        return False

    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    # Add custom keyboard
    if keyboard_buttons:
        keyboard = {
            'keyboard': keyboard_buttons,
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        data['reply_markup'] = json.dumps(keyboard)

    try:
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print(f'✅ Telegram message with keyboard sent successfully: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ Telegram message with keyboard failed to send: {response.status_code} - {response.text}')
            return False

    except Exception as e:
        print(f'❌ Error during sending: {e}')
        return False

def send_file(file_path: str, file_type: str = 'document', caption: str = '') -> bool:
    """
    Send file to Telegram

    Args:
        file_path (str): Full path to file
        file_type (str): File type ('document', 'photo', 'video', 'audio')
        caption (str): File description (optional)

    Returns:
        bool: Whether sending was successful
    """
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: Please configure TELEGRAM_BOT_TOKEN in config.py")
        return False

    if not TELEGRAM_CHAT_ID:
        print("❌ Error: Please configure TELEGRAM_CHAT_ID in config.py")
        return False

    if not os.path.exists(file_path):
        print(f"❌ Error: File does not exist - {file_path}")
        return False

    # Determine API endpoint
    api_method_map = {
        'document': 'sendDocument',
        'photo': 'sendPhoto',
        'video': 'sendVideo',
        'audio': 'sendAudio'
    }

    api_method = api_method_map.get(file_type, 'sendDocument')
    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/{api_method}"

    # File parameter mapping
    file_param_map = {
        'document': 'document',
        'photo': 'photo',
        'video': 'video',
        'audio': 'audio'
    }

    file_param = file_param_map.get(file_type, 'document')

    try:
        with open(file_path, 'rb') as f:
            files = {file_param: f}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'parse_mode': 'HTML'
            }

            if caption:
                data['caption'] = caption

            response = requests.post(url, files=files, data=data, timeout=30)

        if response.status_code == 200:
            file_name = os.path.basename(file_path)
            print(f'✅ File sent successfully ({file_type}): {file_name} - {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ File failed to send ({file_type}): {response.status_code} - {response.text}')
            return False

    except Exception as e:
        print(f'❌ Error during file sending: {e}')
        return False

def format_message_from_template(template_name: str, software: str = "", **kwargs) -> str:
    """
    Format message from template

    Args:
        template_name (str): Template name
        software (str): Software name
        **kwargs: Template variables

    Returns:
        str: Formatted message
    """
    template = load_message_template(template_name, software)

    # Prepare template variables
    variables = {
        'software': software,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **kwargs
    }

    # Format template
    try:
        icon = template.get('icon', '')
        title = template.get('title', '').format(**variables)
        content = template.get('content', '').format(**variables)

        # Combine final message
        message = f"{icon} {title}\n\n{content}" if icon else f"{title}\n\n{content}"
        return message.strip()

    except KeyError as e:
        print(f"⚠️ Template variable missing: {e}")
        return f"Message template error: missing variable {e}"

def get_chat_id() -> str:
    """
    Get bot's chat updates to retrieve chat_id

    Returns:
        str: Found chat_id or error message
    """
    if not TELEGRAM_BOT_TOKEN:
        return "❌ Please configure TELEGRAM_BOT_TOKEN first"

    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['result']:
                chat_id = data['result'][-1]['message']['chat']['id']
                return f"✅ Found Chat ID: {chat_id}"
            else:
                return "⚠️ No conversations found, please send a message to the bot first"
        else:
            return f"❌ Request failed: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {e}"

# Keep template functionality for reference, but AI engine mainly uses send_message
def send_template_message(template_name: str, **variables) -> bool:
    """
    Send message using template (optional feature)

    Args:
        template_name (str): Template name
        **variables: Template variables

    Returns:
        bool: Whether sending was successful
    """
    software = variables.get('software', '')
    message = format_message_from_template(template_name, software, **variables)
    return send_message(message)

if __name__ == '__main__':
    import sys

    # Support file sending: python3 telegram_notifier.py --file <file_type> <file_path> [caption]
    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        if len(sys.argv) < 4:
            print("❌ Usage: python3 telegram_notifier.py --file <type> <path> [caption]")
            print("   Types: document, photo, video, audio")
            sys.exit(1)

        file_type = sys.argv[2]
        file_path = sys.argv[3]
        caption = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ''
        caption = caption.replace('\\n', '\n')

        if send_file(file_path, file_type, caption):
            sys.exit(0)
        else:
            sys.exit(1)

    # Support direct message sending from command line (safer special character handling)
    if len(sys.argv) > 1:
        message_content = " ".join(sys.argv[1:])
        # Handle newline characters passed from command line, convert literal \n to actual newline
        message_content = message_content.replace('\\n', '\n')
        if send_message(message_content):
            sys.exit(0)
        else:
            sys.exit(1)

    # Test functionality
    print("=== Telegram Notifier Test ===")
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Please configure TELEGRAM_BOT_TOKEN in config.py first")
        print("📝 Steps to get Bot Token:")
        print("1. Search for @BotFather on Telegram")
        print("2. Send /newbot to create new bot")
        print("3. Copy the received Token to config.py")
    elif not TELEGRAM_CHAT_ID:
        print("❌ Please configure TELEGRAM_CHAT_ID in config.py first")
        print("📝 Get Chat ID:")
        print(get_chat_id())
    else:
        print("✅ Configuration correct, sending test message...")

        # Test direct message sending
        send_message("🧪 <b>Telegram Notification System Test</b>\n\nSystem working normally, AI engine can start using notification service!")

        # Test message with keyboard
        keyboard = [
            ["/status", "/help"],
            ["Check system status", "Restart service"]
        ]
        send_message_with_keyboard("🎯 <b>System Control Menu</b>\n\nSelect operation to execute:", keyboard)
