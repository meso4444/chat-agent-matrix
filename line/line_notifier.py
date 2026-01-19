#!/usr/bin/env python3
"""
Claude Code LINE Notifier
Read message format from template file, Claude Code only needs to fill in variables
"""

import requests
import json
import yaml
import os
from datetime import datetime
from config import CHANNEL_ACCESS_TOKEN

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

def send_message(message: str, quick_reply_items: list = None) -> bool:
    """
    Send LINE message (supports Quick Reply)

    Args:
        message (str): Message content to send
        quick_reply_items (list): Quick Reply button list (dict format)

    Returns:
        bool: Whether sending was successful
    """
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ Error: Please set CHANNEL_ACCESS_TOKEN in config.py")
        return False

    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    msg_payload = {
        'type': 'text',
        'text': message
    }

    # Add Quick Reply
    if quick_reply_items:
        msg_payload['quickReply'] = {
            'items': quick_reply_items
        }

    data = {
        'messages': [msg_payload]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            print(f'✅ LINE notification sent successfully: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ LINE notification failed: {response.status_code} - {response.text}')
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

# Keep template feature for reference, but Claude Code mainly uses send_message
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

    print("=== LINE Notifier Test ===")

    if not CHANNEL_ACCESS_TOKEN:
        print("❌ Please set CHANNEL_ACCESS_TOKEN in config.py first")
        sys.exit(1)
    else:
        print("✅ Configuration correct, sending test message...")

    # Check if message parameter is passed
    if len(sys.argv) > 1:
        # Use message passed from Claude Code, handle newlines correctly
        message = ' '.join(sys.argv[1:]).replace('\\n', '\n')
        print(f"📤 Sending Claude Code message: {message[:50]}...")
        success = send_message(message)
        if success:
            print("✅ Claude Code message sent successfully")
        else:
            print("❌ Claude Code message failed to send")
    else:
        # Only send test message when no parameters
        print("📋 No message passed, sending test message...")
        send_message("🧪 LINE Notification System Test\n\nSystem is working normally, Claude Code can start using notification service!")