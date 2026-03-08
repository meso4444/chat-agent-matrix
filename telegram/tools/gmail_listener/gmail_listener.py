#!/usr/bin/env python3
"""
Gmail 郵件監聽 - 含 Tmux Agent 轉發功能
偵測到 "Hi [Agent_name]" 時自動轉發給對應 Agent
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

# 讀取配置
whitelist_config = {}
tmux_session = "ai_telegram_session"
email_marker = "Hi"
poll_interval_minutes = 0.5  # 預設 30 秒

if whitelist_file.exists():
    with open(whitelist_file, 'r') as f:
        data = json.load(f)
        whitelist_config = data.get('whitelist_senders', [])
        tmux_session = data.get('tmux_session', 'ai_telegram_session')
        email_marker = data.get('email_marker', 'Hi')
        poll_interval_minutes = data.get('poll_interval_minutes', 0.5)

# 構建郵件地址到 agents 的映射
sender_to_agents = {}
for entry in whitelist_config:
    if isinstance(entry, dict):
        email = entry.get('email', '').lower()
        agents = entry.get('agents', [])
        sender_to_agents[email] = agents

# 讀取已經看過的郵件 ID
seen_messages = set()
if seen_file.exists():
    with open(seen_file, 'r') as f:
        seen_messages = set(f.read().strip().split('\n'))

print("=" * 70)
print("Gmail 郵件監聽 - Tmux Agent 轉發模式")
print("=" * 70)

if not token_file.exists():
    print("❌ token.json 不存在，請先運行 gmail_auth_simple.py")
    exit(1)


def check_agent_session(agent_name):
    """檢查 Agent 的 tmux 窗口是否存在"""
    try:
        result = subprocess.run(
            ['tmux', 'has-session', '-t', f'{tmux_session}:{agent_name}'],
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 檢查 tmux 失敗: {e}")
        return False


def send_to_agent(agent_name, message):
    """發送訊息給 Agent（參考 Telegram 的做法）"""
    try:
        if not check_agent_session(agent_name):
            print(f"   ❌ Agent '{agent_name}' 的 tmux 窗口不存在")
            return False

        # 轉義特殊字符
        escaped_message = message.replace('!', '！')

        # 發送訊息（使用 literal 模式）
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
            '-l',
            escaped_message
        ], check=True)

        time.sleep(0.5)

        # 發送 Enter 鍵
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
            'Enter'
        ], check=True)

        # 對於 Claude-based agents，再發送一次 Enter
        if agent_name in ['Accelerator', 'Chöd', 'Claude']:
            time.sleep(0.2)
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{tmux_session}:{agent_name}',
                'Enter'
            ], check=True)

        print(f"   ✅ 已轉發給 {agent_name}")
        return True

    except Exception as e:
        print(f"   ❌ 轉發給 {agent_name} 失敗: {e}")
        return False


def detect_agent_mention(content):
    """偵測郵件內容中的 Agent 提及 (例如 "Hi Accelerator")"""
    mentioned_agents = []

    for entry in whitelist_config:
        if isinstance(entry, dict):
            agents = entry.get('agents', [])
            for agent in agents:
                # 搜尋 "Hi [Agent_name]" 格式
                pattern = f"{email_marker}\\s+{agent}"
                if re.search(pattern, content, re.IGNORECASE):
                    mentioned_agents.append(agent)

    return list(set(mentioned_agents))  # 去重


try:
    # 認證
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)

    print("✅ 已連接到 Gmail API\n")

    # 顯示配置
    if sender_to_agents:
        print(f"📋 已註冊 Agent:")
        for sender, agents in sender_to_agents.items():
            print(f"   • {sender} → {', '.join(agents)}")
        print()
    else:
        print("⚠️ 白名單為空！請編輯 whitelist.json\n")

    print(f"🔍 標記詞: '{email_marker}' (e.g., '{email_marker} Accelerator')")
    print(f"⏱️ 輪詢間隔: {poll_interval_minutes} 分鐘\n")
    print("🔄 監聽中... 等待新郵件\n")
    print("-" * 70 + "\n")

    while True:
        try:
            # 查詢未讀郵件
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=5
            ).execute()

            messages = results.get('messages', [])

            if messages:
                for message in messages:
                    message_id = message['id']

                    # 跳過已經看過的郵件
                    if message_id in seen_messages:
                        continue

                    # 標記為已看
                    seen_messages.add(message_id)

                    # 獲取郵件詳情
                    msg = service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()

                    # 提取信息
                    headers = msg['payload']['headers']
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), '未知')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(無主旨)')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '未知')

                    # 提取郵件正文
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

                    # 檢查白名單 - 提取郵件地址
                    sender_email = sender.split('<')[-1].split('>')[0].lower() if '<' in sender else sender.lower()

                    # 如果有白名單且寄件者不在白名單中，跳過
                    if sender_to_agents and sender_email not in sender_to_agents:
                        continue

                    # 打印郵件
                    print(f"📧 新郵件：")
                    print(f"   寄件者: {sender}")
                    print(f"   主旨:  {subject}")
                    print(f"   時間:  {date}")
                    print(f"   內容:")
                    print(f"   {'-' * 66}")

                    # 顯示前 500 字
                    content = body[:500] if body else "(無內容)"
                    for line in content.split('\n'):
                        print(f"   {line}")

                    if len(body) > 500:
                        print(f"   ... (已省略，共 {len(body)} 字)")

                    print(f"   {'-' * 66}")

                    # 偵測 Agent 提及並轉發
                    mentioned_agents = detect_agent_mention(body)

                    if mentioned_agents:
                        print(f"\n   🤖 偵測到 Agent 提及: {', '.join(mentioned_agents)}")

                        # 構建轉發訊息 - 類似 Telegram 的格式
                        forward_message = (
                            f"【系統提示】此指令來自 Gmail，任務完成後請務必執行 `python3 telegram_notifier.py '你的回應...'` 來回報結果。\n\n"
                            f"郵件寄件者: {sender}\n"
                            f"主旨: {subject}\n\n"
                            f"{body}"
                        )

                        for agent in mentioned_agents:
                            send_to_agent(agent, forward_message)
                    else:
                        print(f"\n   ℹ️ 未偵測到 Agent 提及")

                    print()

                    # 保存已看過的郵件 ID
                    with open(seen_file, 'w') as f:
                        f.write('\n'.join(seen_messages))

            # 按配置間隔檢查
            time.sleep(poll_interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n👋 停止監聽")
            break
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            time.sleep(5)

except Exception as e:
    print(f"❌ 連接失敗: {e}")
    exit(1)
