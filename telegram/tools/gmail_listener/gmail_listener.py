#!/usr/bin/env python3
"""
Gmail Email Listener - With Tmux Agent Forwarding Function
Auto-forward to corresponding Agent when "Hi [Agent_name]" is detected
"""

import time
import base64
import json
import subprocess
import re
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

script_dir = Path(__file__).parent.absolute()
token_file = script_dir / 'token.json'
seen_file = script_dir / '.gmail_seen_messages'
whitelist_file = script_dir / 'whitelist.json'

# Load configuration
whitelist_config = {}
tmux_session = "ai_telegram_session"
email_marker = "Hi"
poll_interval_minutes = 0.5  # Default 30 seconds

if whitelist_file.exists():
    with open(whitelist_file, 'r') as f:
        data = json.load(f)
        whitelist_config = data.get('whitelist_senders', [])
        tmux_session = data.get('tmux_session', 'ai_telegram_session')
        email_marker = data.get('email_marker', 'Hi')
        poll_interval_minutes = data.get('poll_interval_minutes', 0.5)

# Build mapping from email address to agents
sender_to_agents = {}
for entry in whitelist_config:
    if isinstance(entry, dict):
        email = entry.get('email', '').lower()
        agents = entry.get('agents', [])
        sender_to_agents[email] = agents

# Load already seen message IDs
seen_messages = set()
if seen_file.exists():
    with open(seen_file, 'r') as f:
        seen_messages = set(f.read().strip().split('\n'))

print("=" * 70)
print("Gmail Email Listener - Tmux Agent Forwarding Mode")
print("=" * 70)

if not token_file.exists():
    print("❌ token.json does not exist, please run gmail_auth_simple.py first")
    exit(1)


def check_agent_session(agent_name):
    """Check if Agent's tmux window exists"""
    try:
        result = subprocess.run(
            ['tmux', 'has-session', '-t', f'{tmux_session}:{agent_name}'],
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Check tmux failed: {e}")
        return False


def send_to_agent(agent_name, message):
    """Send message to Agent (following Telegram approach)"""
    try:
        if not check_agent_session(agent_name):
            print(f"   ❌ Agent '{agent_name}' tmux window does not exist")
            return False

        # Escape special characters
        escaped_message = message.replace('!', '！')

        # Send message (using literal mode)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
            '-l',
            escaped_message
        ], check=True)

        time.sleep(0.5)

        # Send Enter key
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
            'Enter'
        ], check=True)

        # For Claude-based agents, send Enter again
        if agent_name in ['Accelerator', 'Chöd', 'Claude']:
            time.sleep(0.2)
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
                'Enter'
            ], check=True)

        print(f"   ✅ Forwarded to {agent_name}")
        return True

    except Exception as e:
        print(f"   ❌ Failed to forward to {agent_name}: {e}")
        return False


def detect_agent_mention(content):
    """Detect Agent mentions in email content (e.g., "Hi Accelerator")"""
    mentioned_agents = []

    for entry in whitelist_config:
        if isinstance(entry, dict):
            agents = entry.get('agents', [])
            for agent in agents:
                # Search for "Hi [Agent_name]" format
                pattern = f"{email_marker}\\s+{agent}"
                if re.search(pattern, content, re.IGNORECASE):
                    mentioned_agents.append(agent)

    return list(set(mentioned_agents))  # Deduplicate


try:
    # Authenticate
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)

    print("✅ Connected to Gmail API\n")

    # Display configuration
    if sender_to_agents:
        print(f"📋 Registered Agents:")
        for sender, agents in sender_to_agents.items():
            print(f"   • {sender} → {', '.join(agents)}")
        print()
    else:
        print("⚠️ Whitelist is empty! Please edit whitelist.json\n")

    print(f"🔍 Marker: '{email_marker}' (e.g., '{email_marker} Accelerator')")
    print(f"⏱️ Poll interval: {poll_interval_minutes} minutes\n")
    print("🔄 Listening... waiting for new emails\n")
    print("-" * 70 + "\n")

    while True:
        try:
            # Query unread emails
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=5
            ).execute()

            messages = results.get('messages', [])

            if messages:
                for message in messages:
                    message_id = message['id']

                    # Skip already seen messages
                    if message_id in seen_messages:
                        continue

                    # Mark as seen
                    seen_messages.add(message_id)

                    # Get message details
                    msg = service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()

                    # Extract message information
                    headers = msg['payload']['headers']
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No subject)')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

                    # Extract message body
                    body = ''
                    if 'parts' in msg['payload']:
                        for part in msg['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                if 'data' in part['body']:
                                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                break
                    elif 'body' in msg['payload']:
                        if 'data' in msg['payload']['body']:
                            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

                    # Check whitelist - extract email address
                    sender_email = sender.split('<')[-1].split('>')[0].lower() if '<' in sender else sender.lower()

                    # Skip if whitelist exists and sender is not in whitelist
                    if sender_to_agents and sender_email not in sender_to_agents:
                        continue

                    # Print email
                    print(f"📧 New email:")
                    print(f"   From: {sender}")
                    print(f"   Subject: {subject}")
                    print(f"   Date: {date}")
                    print(f"   Content:")
                    print(f"   {'-' * 66}")

                    # Display first 500 characters
                    content = body[:500] if body else "(No content)"
                    for line in content.split('\n'):
                        print(f"   {line}")

                    if len(body) > 500:
                        print(f"   ... (truncated, total {len(body)} characters)")

                    print(f"   {'-' * 66}")

                    # Detect Agent mentions and forward
                    mentioned_agents = detect_agent_mention(body)

                    if mentioned_agents:
                        print(f"\n   🤖 Agent mention detected: {', '.join(mentioned_agents)}")

                        # Build forwarding message - similar to Telegram format
                        forward_message = (
                            f"【System Prompt】This command is from Gmail. After task completion, you must execute `python3 telegram_notifier.py 'your response...'` to report the result.\n\n"
                            f"Email from: {sender}\n"
                            f"Subject: {subject}\n\n"
                            f"{body}"
                        )

                        for agent in mentioned_agents:
                            send_to_agent(agent, forward_message)
                    else:
                        print(f"\n   ℹ️ No Agent mention detected")

                    print()

                    # Save seen message IDs
                    with open(seen_file, 'w') as f:
                        f.write('\n'.join(seen_messages))

            # Poll at configured interval
            time.sleep(poll_interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Listener stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
