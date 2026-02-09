#!/usr/bin/env python3
"""
LINE Webhook Flask API (Chat Agent Matrix 版)
接收 LINE 用戶訊息並分發到不同的 AI Agent tmux window
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

# 用戶狀態追蹤
USER_STATES = {}

# 當前活躍 Agent
CURRENT_AGENT = DEFAULT_ACTIVE_AGENT

class ImageManager:
    """圖片管理員：負責下載、儲存與自動清理 (支援多 Agent 隔離)"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
    
    def download_image(self, message_id, agent_name):
        """從 LINE 下載圖片並回傳本地絕對路徑"""
        try:
            # 1. 確保 Agent 的目錄結構正確
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', agent_name, TEMP_IMAGE_DIR_NAME)
            if not os.path.exists(agent_img_dir):
                os.makedirs(agent_img_dir)

            # 2. 下載圖片 (LINE Content API)
            url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            headers = {'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'}
            
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                print(f"❌ 無法下載 LINE 圖片: {response.status_code} {response.text}")
                return None
                
            # 3. 建構本地檔名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{message_id}.jpg"
            local_path = os.path.join(agent_img_dir, filename)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
                
            print(f"📸 圖片已下載至 [{agent_name}]: {local_path}")
            return local_path
            
        except Exception as e:
            print(f"❌ 圖片下載失敗: {e}")
            return None

    def cleanup_old_files(self):
        """遍歷所有 Agent 目錄執行差異化清理 (由 Scheduler 呼叫)"""
        print("🧹 [ImageManager] 開始執行多 Agent 圖片清理任務...")
        
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
                        print(f"⚠️ 無法刪除 [{name}] 檔案 {filename}: {e}")
            
            if count > 0:
                print(f"🧹 已清理 Agent[{name}] 的 {count} 個過期檔案")

# 初始化圖片管理器
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
        print(f"❌ 檢查 tmux session 失敗: {e}")
        return False

def send_to_ai_session(message, agent_name=None):
    global CURRENT_AGENT
    target = agent_name or CURRENT_AGENT
    
    try:
        if not check_agent_session(target):
            send_message(f"❌ Agent '{target}' 視窗不存在\n請檢查配置或執行: ./start_all_services.sh")
            return False

        # 文字 -> 延遲 -> Enter
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}', message], check=True)
        time.sleep(0.1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}', 'Enter'], check=True)

        print(f"📤 已發送到 Agent[{target}]: {message}")
        return True
        
    except Exception as e:
        print(f"❌ 發送到 Agent 失敗: {e}")
        send_message(f"❌ 系統錯誤: {str(e)}")
        return False

def check_system_status():
    try:
        # 0. 建立角色對照表
        agent_role_map = {}
        for grp in COLLABORATION_GROUPS:
            roles = grp.get('roles', {})
            for member, role in roles.items():
                short_role = role[:15] + "..." if len(role) > 15 else role
                agent_role_map[member] = f"[{grp.get('name')}] {short_role}"

        # 1. Agent 狀態
        agent_status_list = []
        for agent in AGENTS:
            name = agent['name']
            desc = agent.get('description', '無描述')
            engine = agent['engine']
            role_info = f"\n      └ {agent_role_map[name]}" if name in agent_role_map else ""
            is_active = " (⭐ 活躍)" if name == CURRENT_AGENT else ""
            status_icon = "🟢" if check_agent_session(name) else "🔴"
            agent_status_list.append(f"{status_icon} [{name}] {desc} ({engine}){is_active}{role_info}")
        
        agents_info = "\n".join(agent_status_list)
        
        # 2. 排程狀態
        scheduler_list = []
        if SCHEDULER_CONF:
            for job in SCHEDULER_CONF:
                if job.get('active'):
                    trigger_info = ""
                    if job['trigger'] == 'interval':
                        h = job.get('hours', job.get('hour', 0))
                        m = job.get('minutes', job.get('minute', 0))
                        s = job.get('seconds', job.get('second', 0))
                        trigger_info = f"每 {h}時{m}分{s}秒"
                    elif job['trigger'] == 'cron':
                        trigger_info = f"每天 {job.get('hour', '*')}:{job.get('minute', '*')}"
                    
                    scheduler_list.append(f"• {job['name']} ({trigger_info})")
        
        scheduler_info = "\n".join(scheduler_list) if scheduler_list else "• 無啟用中的任務"
        
        status_message = f"""
📊 系統狀態報告

🤖 Agent 軍團:
{agents_info}

⏰ 排程任務:
{scheduler_info}

📺 檢查時間: {datetime.now().strftime('%H:%M:%S')}
💡 輸入 "切換 Agent" 呼叫選單
"""
        send_message(status_message)
    except Exception as e:
        send_message(f"❌ 無法取得系統狀態: {str(e)}")

def build_quick_reply_menu():
    """將 config.yaml 的 menu 轉換為 LINE Quick Reply"""
    items = []
    
    # 遍歷二維陣列
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
    """顯示控制選單 (Quick Reply)"""
    menu = build_quick_reply_menu()
    send_message(f"🎮 請選擇操作 (活躍 Agent: {CURRENT_AGENT})", quick_reply_items=menu)

def handle_user_message(message, user_id):
    global CURRENT_AGENT
    timestamp = datetime.now().strftime('%H:%M:%S')

    # 1. 用戶狀態處理 (Input Prompt)
    if user_id in USER_STATES:
        state = USER_STATES[user_id]
        final_command = state['command_template'].replace('{input}', message)
        del USER_STATES[user_id]
        
        send_message(f"✅ 已接收輸入，執行指令: {final_command}")
        handle_user_message(final_command, user_id)
        return

    # 2. 檢查自定義選單
    matched_menu_item = None
    for row in CUSTOM_MENU:
        for item in row:
            label = item.get('label')
            if message == label:
                matched_menu_item = item
                break
        if matched_menu_item: break

    # 如果是選單按鈕，轉換成對應指令
    if matched_menu_item:
        command = matched_menu_item.get('command', '')
        if '{input}' in command:
            USER_STATES[user_id] = {'command_template': command, 'timestamp': datetime.now()}
            send_message(matched_menu_item.get('prompt', '請輸入內容:'))
            return
        else:
            handle_user_message(command, user_id)
            return

    # 3. 特殊指令處理
    if message.startswith('/switch'):
        parts = message.split()
        if len(parts) > 1:
            target_input = parts[1].lower()
            found_agent = next((a for a in AGENTS if a['name'].lower() == target_input), None)
            
            if found_agent:
                CURRENT_AGENT = found_agent['name']
                send_message(f"🎯 對話切換成功\n當前活躍 Agent: {CURRENT_AGENT}")
            else:
                send_message(f"❌ 找不到 Agent: {parts[1]}")
        else:
            show_control_menu()
        return

    if message.lower() in ['/status', '狀態', 'status']:
        check_system_status()
        return
    elif message.lower() in ['/menu', '選單', 'menu', 'help', '/help']:
        show_control_menu()
        return
    elif message.lower() in ['/interrupt', '/stop', '停止', '中斷']:
        try:
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'C-c'], check=True)
            send_message(f"🛑 已對 [{CURRENT_AGENT}] 發送中斷訊號 (Ctrl+C)")
        except Exception as e:
            send_message(f"❌ 中斷失敗: {e}")
        return
    elif message.lower() in ['/clear', '清除']:
        send_to_ai_session('/clear')
        send_message(f"🧹 已清除 [{CURRENT_AGENT}] 的畫面")
        return
    elif message.lower() in ['/resume_latest', '恢復記憶']:
        send_to_ai_session('/resume')
        time.sleep(3)
        subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'Enter'], check=True)
        send_message(f"🧠 已嘗試恢復記憶")
        return

    # /inspect
    elif message.startswith('/inspect'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            prompt = (
                f"透過 tmux 查找 session '{TMUX_SESSION_NAME}'，進入 '{target}' 的視窗，查看其前 50 行的訊息狀態，並分析它是否正常運作。\n\n"
                f"【系統提示】此指令來自 LINE 用戶，任務完成後請務必執行 `python3 line_notifier.py '你的回應...'` 來回報結果。"
            )
            send_to_ai_session(prompt)
            send_message(f"🔍 已指派 [{CURRENT_AGENT}] 去檢查 [{target}]...")
        return

    # /fix
    elif message.startswith('/fix'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            target_agent = get_agent_info(target_name)
            if target_agent:
                start_cmd = target_agent.get('start_cmd', '未知指令')
                prompt = (
                    f"請直接執行以下 Python 代碼來修復 Agent '{target_name}'（不要解釋代碼，直接執行即可）：\n\n"
                    f"```python\n"
                    f"import subprocess\n"
                    f"import time\n\n"
                    f"session = '{TMUX_SESSION_NAME}'\n"
                    f"target = '{target_name}'\n"
                    f"cmd = '{start_cmd}'\n\n"
                    f"print(f'🚑 正在修復 {{target}}...')\n"
                    f"# 1. 發送中斷訊號\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'C-c'])\n"
                    f"time.sleep(1)\n\n"
                    f"# 2. 退出當前進程\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'exit', 'Enter'])\n"
                    f"time.sleep(2)\n\n"
                    f"# 3. 重新啟動 Agent\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', cmd, 'Enter'])\n"
                    f"time.sleep(5)  # 等待啟動\n\n"
                    f"# 4. 自動恢復記憶 (/resume)\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', '/resume', 'Enter'])\n"
                    f"time.sleep(3)  # 等待列表\n"
                    f"subprocess.run(['tmux', 'send-keys', '-t', f'{{session}}:{{target}}', 'Enter'])  # 確認選擇\n\n"
                    f"print(f'✅ 已完成 {{target}} 的修復與記憶恢復')\n"
                    f"```\n\n"
                    f"【系統提示】此指令來自 LINE 用戶，任務完成後請務必執行 `python3 line_notifier.py '你的回應...'` 來回報結果。"
                )
                send_to_ai_session(prompt)
                send_message(f"🚑 已指派 [{CURRENT_AGENT}] 執行修復腳本...")
        return

    # 4. 一般訊息轉發
    system_prompt = "\n\n【系統提示】此指令來自 LINE 用戶，任務完成後請務必執行 `python3 line_notifier.py '你的回應...'` 來回報結果。"
    final_message = message + system_prompt
    
    success = send_to_ai_session(final_message)
    if success:
        menu = build_quick_reply_menu()
        send_message(f"📤 [{timestamp}] 已轉發到 [{CURRENT_AGENT}]", quick_reply_items=menu)

@app.route('/webhook', methods=['POST'])
def line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    if not CHANNEL_SECRET:
        print("⚠️ CHANNEL_SECRET 未設定，開發模式")
    else:
        try:
            hash_digest = hmac.new(
                CHANNEL_SECRET.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(hash_digest).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                print("❌ 簽名驗證失敗")
                abort(400)
        except Exception as e:
            print(f"❌ 簽名驗證過程錯誤: {e}")
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
                    print(f"📨 文字: {text}")
                    handle_user_message(text, user_id)
                    
                elif msg_type == 'image':
                    print(f"📸 圖片訊息")
                    msg_id = event['message']['id']
                    local_path = image_manager.download_image(msg_id, CURRENT_AGENT)
                    
                    if local_path:
                        prompt = (
                            f"請處理這張圖片，檔案位於: {local_path}\n"
                            f"任務：描述內容並提取關鍵資訊。"
                        )
                        send_message(f"✅ 圖片已接收，傳送給 [{CURRENT_AGENT}] 分析...")
                        system_prompt = "\n\n【系統提示】此指令來自 LINE 用戶，任務完成後請務必執行 `python3 line_notifier.py '你的回應...'` 來回報結果。"
                        send_to_ai_session(prompt + system_prompt)

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"❌ 處理錯誤: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def api_status():
    """API 狀態檢查端點"""
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
    """API 端點：直接發送訊息到 AI 引擎"""
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
    print(f"🚀 啟動 Chat Agent Matrix API (LINE Edition)...")
    print(f"📍 本地端點: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🤖 預設 Agent: {DEFAULT_ACTIVE_AGENT}")
    
    # 啟動排程任務
    scheduler = SchedulerManager(image_manager=image_manager)
    scheduler.load_jobs(SCHEDULER_CONF)
    scheduler.start()
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ 啟動 Flask 伺服器失敗: {e}")
