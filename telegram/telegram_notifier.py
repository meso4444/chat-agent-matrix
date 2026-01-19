#!/usr/bin/env python3
"""
AI Engine Telegram Notifier
Read message format from template file, AI engine only needs to fill in variables
"""

import requests
import json
import yaml
import os
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_API_BASE_URL

def load_message_template(template_name: str, software: str = None) -> dict:
    """
    Load message template from template file

    Args:
        template_name (str): Template name (start, progress, success, error, custom)
        software (str): Software name for finding specific software templates

    Returns:
        dict: Template dictionary containing icon, title, content
    """
    template_file = os.path.join(os.path.dirname(__file__), 'message_templates.yaml')

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)

        # Prioritize using software-specific templates
        if software and software in templates.get('software_templates', {}):
            software_template = templates['software_templates'][software].get(template_name)
            if software_template:
                return software_template

        # Use general template
        return templates['templates'].get(template_name, {})

    except Exception as e:
        print(f"⚠️ Unable to load template: {e}")
        # Fallback to simple template
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
        print("❌ Error: Please set TELEGRAM_BOT_TOKEN in config.py")
        return False

    if not TELEGRAM_CHAT_ID:
        print("❌ Error: Please set TELEGRAM_CHAT_ID in config.py")
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
            print(f'❌ Telegram notification failed: {response.status_code} - {response.text}')
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
            print(f'❌ Telegram message with keyboard failed: {response.status_code} - {response.text}')
            return False

    except Exception as e:
        print(f'❌ Error during sending: {e}')
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
    Get chat updates from bot, used to get chat_id

    Returns:
        str: Found chat_id or error message
    """
    if not TELEGRAM_BOT_TOKEN:
        return "❌ Please set TELEGRAM_BOT_TOKEN first"

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

# Keep template feature for reference, but AI engine mainly uses send_message
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

    # Support direct message sending via command line (safer special character handling)
    if len(sys.argv) > 1:
        message_content = " ".join(sys.argv[1:])
        # Handle newline characters from command line, convert literal \n to actual newlines
        message_content = message_content.replace('\\n', '\n')
        if send_message(message_content):
            sys.exit(0)
        else:
            sys.exit(1)

    # Test functionality
    print("=== Telegram Notifier Test ===")
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Please set TELEGRAM_BOT_TOKEN in config.py first")
        print("📝 Steps to get Bot Token:")
        print("1. Search for @BotFather in Telegram")
        print("2. Send /newbot to create a new bot")
        print("3. Copy the Token you received to config.py")
    elif not TELEGRAM_CHAT_ID:
        print("❌ Please set TELEGRAM_CHAT_ID in config.py first")
        print("📝 Get Chat ID:")
        print(get_chat_id())
    else:
        print("✅ Configuration correct, sending test message...")

        # Test direct message sending
        send_message("🧪 <b>Telegram Notification System Test</b>\n\nSystem is working normally, AI engine can start using notification service!")

        # Test message with keyboard
        keyboard = [
            ["/status", "/help"],
            ["Check system status", "Restart service"]
        ]
        send_message_with_keyboard("🎯 <b>System Control Menu</b>\n\nSelect operation to execute:", keyboard)