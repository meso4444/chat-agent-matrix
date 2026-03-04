#!/usr/bin/env python3
"""
Telegram Webhook Flask API (Multi-Agent 版)
接收 Telegram 用戶訊息並分發到不同的 AI Agent tmux window
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

# 🔧 支援長訊息: 增加 JSON 請求大小限制 (預設 16MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB (支援超長訊息)
app.config['JSON_MAX_SIZE'] = 50 * 1024 * 1024       # JSON 最大大小

# 讀取動態 Webhook Secret
try:
    SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webhook_secret.token')
    with open(SECRET_FILE, 'r') as f:
        WEBHOOK_SECRET_TOKEN = f.read().strip()
except Exception as e:
    print(f"⚠️ 無法讀取 Webhook Secret: {e}")
    WEBHOOK_SECRET_TOKEN = None

# 用戶狀態追蹤: {user_id: {'command_template': '...', 'timestamp': ...}}
USER_STATES = {}

# 當前活躍 Agent (預設為配置中的預設值)
CURRENT_AGENT = DEFAULT_ACTIVE_AGENT

# 全局排程管理器（在主程式中初始化）
scheduler = None

class ImageManager:
    """圖片管理員：負責下載、儲存與自動清理 (支援多 Agent 隔離)"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # 注意：清理工作已移交給 SchedulerManager 統一管理
    
    def download_image(self, file_id, agent_name):
        """下載圖片並回傳本地絕對路徑"""
        try:
            # 1. 確保 Agent 的目錄結構正確
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', agent_name, TEMP_IMAGE_DIR_NAME)
            if not os.path.exists(agent_img_dir):
                os.makedirs(agent_img_dir)

            # 2. 獲取檔案資訊 (getFile)
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            response = requests.get(url)
            data = response.json()
            
            if not data.get('ok'):
                print(f"❌ 無法獲取檔案資訊: {data}")
                return None
                
            file_path = data['result']['file_path']
            file_ext = os.path.splitext(file_path)[1] or ".jpg"
                
            # 3. 建構本地檔名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{file_id[:8]}{file_ext}"
            local_path = os.path.join(agent_img_dir, filename)
            
            # 4. 下載檔案內容
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            img_data = requests.get(download_url).content
            
            with open(local_path, 'wb') as f:
                f.write(img_data)
                
            print(f"📸 圖片已下載至 [{agent_name}]: {local_path}")
            return local_path
            
        except Exception as e:
            print(f"❌ 圖片下載失敗: {e}")
            return None

    def cleanup_old_files(self):
        """遍歷所有 Agent 目錄執行差異化清理 (由 Scheduler 呼叫)"""
        print("🧹 [ImageManager] 開始執行多 Agent 圖片清理任務...")
        from config import AGENTS, DEFAULT_CLEANUP_POLICY
        
        for agent in AGENTS:
            name = agent['name']
            agent_img_dir = os.path.join(self.base_dir, 'agent_home', name, TEMP_IMAGE_DIR_NAME)
            
            if not os.path.exists(agent_img_dir):
                continue
                
            # 讀取清理策略
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
    """獲取指定 Agent 的詳細資訊 (不分大小寫)"""
    for agent in AGENTS:
        if agent['name'].lower() == name.lower():
            return agent
    return None

def check_agent_session(name):
    """檢查特定 Agent 的 tmux window 是否存在"""
    try:
        # tmux has-session -t session:window
        result = subprocess.run(
            ['tmux', 'has-session', '-t', f'{TMUX_SESSION_NAME}:{name}'],
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 檢查 tmux session 失敗: {e}")
        return False

def send_to_ai_session(message, agent_name=None):
    """發送訊息到指定的 Agent tmux window (含特殊字符轉義支持)"""
    global CURRENT_AGENT
    target = agent_name or CURRENT_AGENT

    try:
        if not check_agent_session(target):
            send_message(f"❌ Agent '{target}' 視窗不存在\n請檢查配置或執行: ./start_all_services.sh")
            return False

        # 🔧 防止 Gemini CLI 誤解感叹號進入 shell 模式
        # 轉義無效，直接替換: ! → ！(全形感叹號)
        escaped_message = message.replace('!', '！')

        # 🔧 使用 -l (literal mode) 發送訊息，防止 tmux 解釋特殊字符
        # 這解決了:
        # - tmux 命令解釋 (如 #{pane_id} 等)
        # - bash 歷史展開
        # - "\n" 誤觸粘貼模式
        # （! → ！ 替換已在上方處理，防止 Gemini 進入特殊模式）
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            '-l',       # ← 關鍵: 字面量模式，不執行 tmux 解釋
            escaped_message
        ], check=True)

        # 延遲讓訊息完全進入輸入緩衝區
        time.sleep(0.5)

        # 發送第一次 Enter 鍵
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
            'Enter'
        ], check=True)

        # 🔒 雙重保險: 對 Claude 等需要粘貼模式確認的 Agent 再按一次 Enter
        # 這確保長文本被正確發送
        if target in ['Claude', 'Accelerator', 'Chöd']:  # Claude-based agents
            time.sleep(0.2)
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target}',
                'Enter'
            ], check=True)

        msg_preview = message[:80] + ('...' if len(message) > 80 else '')
        print(f"📤 已發送到 Agent[{target}] (模式: literal): {msg_preview}")
        return True

    except Exception as e:
        print(f"❌ 發送到 Agent 失敗: {e}")
        send_message(f"❌ 系統錯誤: {str(e)}")
        return False

def capture_ai_response(agent_name=None, delay=3):
    """擷取特定 Agent 的回應"""
    target = agent_name or CURRENT_AGENT
    try:
        time.sleep(delay)
        result = subprocess.run([
            'tmux', 'capture-pane', '-t', f'{TMUX_SESSION_NAME}:{target}', '-p'
        ], capture_output=True, text=True)

        if result.stdout:
            lines = result.stdout.strip().split('\n')
            recent_output = '\n'.join(lines[-15:])
            send_message(f"💬 <b>[{target}] 最新回應:</b>\n<pre>{recent_output}</pre>")
            return True
    except Exception as e:
        print(f"⚠️ 擷取 {target} 輸出失敗: {e}")
        return False

@app.route(TELEGRAM_WEBHOOK_PATH, methods=['POST'])
def telegram_webhook():
    """接收 Telegram webhook"""
    try:
        # 1. 安全檢查: 驗證 Secret Token (防止非來自 Telegram 的惡意請求)
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if WEBHOOK_SECRET_TOKEN and secret_header != WEBHOOK_SECRET_TOKEN:
            print(f"🛑 拒絕未授權請求 (Invalid Secret): {secret_header}")
            return jsonify({'status': 'unauthorized'}), 403

        webhook_data = request.get_json()
        if 'message' in webhook_data:
            message_data = webhook_data['message']
            
            # 驗證 chat_id
            chat_id = str(message_data.get('chat', {}).get('id', ''))
            if TELEGRAM_CHAT_ID and chat_id != str(TELEGRAM_CHAT_ID):
                print(f"⚠️ 未授權的 chat_id: {chat_id}")
                return jsonify({'status': 'unauthorized'}), 403
            
            # 取得用戶資訊
            user_id = message_data.get('from', {}).get('id', 'unknown')
            username = message_data.get('from', {}).get('username', 'unknown')
            
            user_message = None
            
            # 1. 處理文字訊息
            if 'text' in message_data:
                user_message = message_data['text']
                # 改進: 長訊息的日誌處理 (前 100 字符顯示，避免日誌爆炸)
                msg_preview = user_message[:100] + ('...' if len(user_message) > 100 else '')
                msg_length = len(user_message)
                print(f"📨 收到文字訊息 (長度: {msg_length} chars): {msg_preview} (from: @{username})")
                
            # 2. 處理圖片訊息
            elif 'photo' in message_data:
                print(f"📸 收到圖片訊息 (from: @{username})")
                photo_array = message_data['photo']
                best_photo = photo_array[-1]
                file_id = best_photo['file_id']
                
                local_path = image_manager.download_image(file_id, CURRENT_AGENT)
                if local_path:
                    user_message = (
                        f"請處理這張圖片，檔案位於: {local_path}\n"
                        f"任務：\n"
                        f"1. 描述圖片的主要內容與場景。\n"
                        f"2. 若圖片包含文字，請提取關鍵訊息。\n"
                        f"3. 總結這張圖片的重點。"
                    )
                    send_message(f"✅ 圖片已接收，正在傳送給 <b>[{CURRENT_AGENT}]</b> 分析...")
                else:
                    send_message("❌ 圖片下載失敗")
            
            if user_message:
                handle_user_message(user_message, user_id, username)
        
        elif 'callback_query' in webhook_data:
            callback = webhook_data['callback_query']
            callback_data = callback.get('data', '')
            user_id = callback.get('from', {}).get('id', 'unknown')
            print(f"🔘 收到按鈕點擊: {callback_data}")
            handle_callback_query(callback_data, user_id)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"❌ Webhook 處理錯誤: {e}")
        return jsonify({'error': str(e)}), 500

def handle_user_message(message, user_id, username):
    """處理用戶訊息 (含 Agent 切換邏輯)"""
    global CURRENT_AGENT
    timestamp = datetime.now().strftime('%H:%M:%S')

    # 1. 用戶狀態處理 (自定義選單輸入)
    if user_id in USER_STATES:
        state = USER_STATES[user_id]
        final_command = state['command_template'].replace('{input}', message)
        del USER_STATES[user_id]
        
        send_message(f"✅ 已接收輸入，執行指令: {final_command}")
        
        # 關鍵修正：遞迴呼叫自己，讓系統有機會攔截特殊指令 (如 /switch, /inspect)
        # 而不是直接 send_to_ai_session
        handle_user_message(final_command, user_id, username)
        return

    # 2. 特殊指令處理 (優先級最高)
    # A. Agent 切換指令
    if message.startswith('/switch'):
        parts = message.split()
        if len(parts) > 1:
            target_input = parts[1].lower()
            # 找到名稱一致（不分大小寫）的 Agent
            found_agent = next((a for a in AGENTS if a['name'].lower() == target_input), None)
            
            if found_agent:
                CURRENT_AGENT = found_agent['name'] # 使用原始定義名稱 (如 "Güpa")
                send_message(f"⚡ <b>對話切換成功</b>\n當前活躍 Agent: <code>{CURRENT_AGENT}</code>")
            else:
                send_message(f"❌ 找不到 Agent: <code>{parts[1]}</code>\n請輸入 <code>/status</code> 查看可用列表。")
        else:
            # 如果只輸入 /switch，顯示選單式引導
            show_agent_selector()
        return

    # B. 系統指令
    if message.lower() in ['/status', '狀態', 'status']:
        check_system_status()
        return
    elif message.lower() in ['/help', '幫助', 'help', '/start']:
        show_help()
        return
    elif message.lower() in ['/menu', '選單', 'menu']:
        show_control_menu()
        return
    elif message.lower() in ['/interrupt', '/stop', '停止', '中斷']:
        try:
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'C-c'], check=True)
            send_message(f"🛑 已對 <b>[{CURRENT_AGENT}]</b> 發送中斷訊號 (Ctrl+C)")
        except Exception as e:
            send_message(f"❌ 中斷失敗: {e}")
        return
    elif message.lower() in ['/clear', '清除']:
        send_to_ai_session('/clear')
        send_message(f"🧹 已清除 <b>[{CURRENT_AGENT}]</b> 的畫面與記憶")
        return
    elif message.lower() in ['/resume_latest', '恢復記憶']:
        # 自動恢復最近一次記憶
        # 流程: 發送 /resume -> 等待選單 -> 發送 Enter (選擇預設/最近)
        try:
            print(f"⏳ [DEBUG] 開始恢復 {CURRENT_AGENT} 的記憶...")
            send_to_ai_session('/resume')
            
            print(f"⏳ [DEBUG] 等待 3 秒讓列表載入...")
            time.sleep(3) # 等待 CLI 載入 Session 列表
            
            # 發送 Enter 來確認選擇 (使用 CURRENT_AGENT 取代已不存在的函數)
            print(f"⏳ [DEBUG] 發送 Enter 鍵至 {CURRENT_AGENT}")
            subprocess.run(['tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{CURRENT_AGENT}', 'Enter'], check=True)
            
            send_message(f"🧠 已嘗試恢復 <b>[{CURRENT_AGENT}]</b> 最近一次的對話記憶, 若無回應請執行「重置」")
        except Exception as e:
            print(f"❌ [DEBUG] 恢復記憶失敗: {e}")
            send_message(f"❌ 恢復記憶失敗: {e}")
        return

    # C. Agent 交互監控指令
    # 格式: /inspect [target_agent]
    elif message.startswith('/inspect'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            # 構建 Prompt (自然語言風格)
            prompt = (
                f"透過 tmux 查找 session '{TMUX_SESSION_NAME}'，進入 '{target}' 的視窗，查看其前 50 行的訊息狀態，並分析它是否正常運作。\n\n"
                f"【系統提示】此指令來自 Telegram 用戶，任務完成後請務必執行 `python3 telegram_notifier.py '你的回應...'` 來回報結果。"
            )
            send_to_ai_session(prompt)
            send_message(f"🔍 已指派 <b>[{CURRENT_AGENT}]</b> 去檢查 <b>[{target}]</b> 的狀態...")
        else:
            send_message("❌ 請指定要檢查的 Agent 名稱，例如: `/inspect claude`")
        return

    # 格式: /awake [target_agent] - 自動一鍵喚醒 Agent
    elif message.startswith('/awake'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            target_agent = get_agent_info(target_name)
            if target_agent:
                send_message(f"⚡ 開始自動修復 <b>[{target_name}]</b>...")
                # 在後台執行以避免阻塞
                import threading
                thread = threading.Thread(target=awake_agent, args=(target_name, target_agent))
                thread.daemon = True
                thread.start()
            else:
                send_message(f"❌ 找不到配置檔中的 Agent: {target_name}")
        else:
            send_message("❌ 請指定要喚醒的 Agent 名稱，例如: `/awake Chöd`")
        return

    # 格式: /fix [target_agent]
    elif message.startswith('/fix'):
        parts = message.split()
        if len(parts) > 1:
            target_name = parts[1]
            # 查找目標 Agent 的啟動指令
            target_agent = get_agent_info(target_name)
            
            if target_agent:
                start_cmd = target_agent.get('start_cmd', '未知指令')
                # 構建 Prompt (自然語言風格，包含 Enter 鍵技術細節)
                prompt = (
                    f"透過 tmux 查找 session '{TMUX_SESSION_NAME}'，進入 '{target_name}' 的視窗，"
                    f"輸入 /quit 或 /exit 並執行 Enter，等待3秒後執行 pwd 指令確認回到 Linux Shell 後，再執行啟動指令：`{start_cmd}`。\n"
                    f"等待5秒啟動完成後，請輸入 `/resume` ,執行 Enter, 等待3秒後再執行1次enter, 以恢復最近一次的對話紀錄。\n\n"
                    f"【⚠️ 技術限制：Tmux Send-Keys 與 Enter 鍵處理 (嚴格執行)】\n"
                    f"由於 tmux send-keys 發送速度極快，若文字與 Enter 在同一指令中發送，會導致目標 Shell 緩衝區溢位而「吃掉」Enter 訊號。請務必遵守以下規範：\n"
                    f"1. 禁止寫法 (❌)\n"
                    f"tmux send-keys -t target text Enter (嚴禁同行發送)\n"
                    f"tmux send-keys -t target text C-m (禁用 C-m)\n"
                    f"2. 強制寫法 (✅)\n"
                    f"必須採用 「文字 -> 延遲 -> Enter」 的三部曲寫法：\n"
                    f"tmux send-keys -t target 您的訊息內容 && sleep 1 && tmux send-keys -t target Enter\n\n"
                    f"【系統提示】此指令來自 Telegram 用戶，任務完成後請務必執行 `python3 telegram_notifier.py '你的回應...'` 來回報結果。"
                )
                send_to_ai_session(prompt)
                send_message(f"🚑 已指派 <b>[{CURRENT_AGENT}]</b> 去修復 <b>[{target_name}]</b>...")
            else:
                send_message(f"❌ 找不到配置檔中的 Agent: {target_name}")
        else:
            send_message("❌ 請指定要修復的 Agent 名稱，例如: `/fix claude`")
        return

    # 格式: /capture [target_agent]
    elif message.startswith('/capture'):
        parts = message.split()
        if len(parts) > 1:
            target = parts[1]
            if check_agent_session(target):
                try:
                    # 擷取 tmux pane 的內容
                    result = subprocess.run(
                        ['tmux', 'capture-pane', '-t', f'{TMUX_SESSION_NAME}:{target}', '-p'],
                        capture_output=True, text=True, timeout=5
                    )

                    if result.returncode == 0:
                        output_lines = result.stdout.split('\n')
                        # 取最後 100 行
                        captured_lines = output_lines[-100:] if len(output_lines) > 100 else output_lines
                        captured_content = '\n'.join(captured_lines).strip()

                        # 分割成多條訊息發送（避免超過 Telegram 限制）
                        msg_chunks = []
                        current_chunk = ""
                        for line in captured_lines:
                            if len(current_chunk) + len(line) + 1 > 4000:  # Telegram 訊息限制
                                if current_chunk:
                                    msg_chunks.append(current_chunk)
                                current_chunk = line
                            else:
                                current_chunk += line + '\n'
                        if current_chunk:
                            msg_chunks.append(current_chunk)

                        # 發送擷圖
                        send_message(f"📸 <b>[{target}]</b> 畫面擷圖（最後 100 行）\n<code>{msg_chunks[0]}</code>" if msg_chunks else f"❌ [{target}] 畫面為空")

                        # 如果有多個 chunk，繼續發送
                        for chunk in msg_chunks[1:]:
                            time.sleep(0.3)
                            send_message(f"<code>{chunk}</code>")
                    else:
                        send_message(f"❌ 無法擷圖 [{target}]: {result.stderr}")
                except subprocess.TimeoutExpired:
                    send_message(f"⏱️ 擷圖超時 [{target}]")
                except Exception as e:
                    send_message(f"❌ 擷圖失敗 [{target}]: {str(e)}")
            else:
                send_message(f"❌ Agent '{target}' 視窗不存在")
        else:
            send_message("❌ 請指定要擷圖的 Agent 名稱，例如: `/capture Güpa20`")
        return

    # 3. 檢查是否為自定義選單標籤
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
            send_message(matched_menu_item.get('prompt', '請輸入內容:'))
        else:
            # 遞迴處理選單指令 (處理可能的 /status 等)
            handle_user_message(command, user_id, username)
        return

    # 4. 一般訊息轉發
    # 追加強制回報提示，確保 AI 知道這是一條需要回應的外部指令
    system_prompt = "\n\n【系統提示】此指令來自 Telegram 用戶，任務完成後請務必執行 `python3 telegram_notifier.py '你的回應...'` 來回報結果。"
    final_message = message + system_prompt
    
    success = send_to_ai_session(final_message)
    if success:
        send_message(f"🐙 <b>[{timestamp}]</b> > Matrix Connected :: <b>[{CURRENT_AGENT}]</b>")

def handle_callback_query(callback_data, user_id):
    """處理按鈕回調"""
    global CURRENT_AGENT
    if callback_data.startswith('sw_'):
        target = callback_data.replace('sw_', '')
        CURRENT_AGENT = target
        send_message(f"⚡ <b>對話切換成功</b>\n當前活躍 Agent: <code>{target}</code>")
    elif callback_data == 'system_status':
        check_system_status()
    elif callback_data == 'help':
        show_help()

def show_agent_selector():
    """顯示 Agent 切換選單"""
    keyboard = []
    for agent in AGENTS:
        # 這裡使用 inline 鍵盤比較好，但為維持統一使用 Reply Keyboard 或簡單文字回覆
        # 暫時用文字回覆引導切換
        pass
    
    agent_list = "\n".join([f"• <code>{a['name']}</code> - {a['description']}" for a in AGENTS])
    msg = f"🤖 <b>請選擇要切換的 Agent</b>\n格式: <code>/switch [名稱]</code>\n\n可用列表:\n{agent_list}"
    send_message(msg)

def awake_agent(target_name, target_agent):
    """自動修復故障 Agent，精確控制時間延迿"""
    try:
        # Determine startup command based on agent engine type
        engine = target_agent.get('engine', 'claude')
        engine_cmd_map = {
            'gemini': 'gemini --yolo',
            'claude': 'claude --permission-mode bypassPermissions'
        }
        start_cmd = target_agent.get('start_cmd', engine_cmd_map.get(engine, 'python3 main.py'))

        send_message(f"📍 [步驟 1/6] 進入 {target_name} tmux 視窗...")

        # 步驟 1: 發送 /quit 指令
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

        send_message(f"📍 [步驟 2/6] 用 pwd 驗證返回 Shell...")

        # 步驟 2: 用 pwd 驗證
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

        send_message(f"📍 [步驟 3/6] 執行啟動指令: {start_cmd}...")

        # 步驟 3: 重新啟動 Agent
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            start_cmd
        ], check=True)
        time.sleep(1)
        subprocess.run([
            'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{target_name}',
            'Enter'
        ], check=True)
        time.sleep(5)

        send_message(f"📍 [步驟 4/6] 等待啟動完成（5秒）...")
        time.sleep(1)  # 額外穩定等待

        send_message(f"📍 [步驟 5/6] 使用 /resume 恢復對話...")

        # 步驟 4: 恢復對話
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

        send_message(f"✅ [步驟 6/6] Agent <b>{target_name}</b> 成功喚醒！已準備好使用。")

    except subprocess.CalledProcessError as e:
        send_message(f"❌ 喚醒在某一步驟失敗: {str(e)}")
    except Exception as e:
        send_message(f"❌ 喚醒過程中出現錯誤: {str(e)}")

def check_system_status():
    """檢查系統狀態 (Multi-Agent 版)"""
    try:
        # 0. 建立角色對照表
        agent_role_map = {}
        for grp in COLLABORATION_GROUPS:
            roles = grp.get('roles', {})
            for member, role in roles.items():
                # 完整顯示角色說明（無長度限制）
                agent_role_map[member] = f"[{grp.get('name')}] {role}"

        # 1. Agent 狀態
        agent_status_list = []
        for agent in AGENTS:
            name = agent['name']
            desc = agent.get('description', '無描述')
            engine = agent['engine']
            role_info = f"\n      └ {agent_role_map[name]}" if name in agent_role_map else ""
            
            is_active = " (⭐ 活躍)" if name == CURRENT_AGENT else ""
            status_icon = "🟢" if check_agent_session(name) else "🔴"
            
            agent_status_list.append(f"{status_icon} <b>[{name}]</b> {desc} ({engine}){is_active}{role_info}")
        
        agents_info = "\n".join(agent_status_list)
        
        # 2. 排程狀態（實時查詢）
        scheduler_list = []
        if scheduler:
            scheduler_data = scheduler.list_jobs()
            for job in scheduler_data.get('jobs', []):
                job_id = job.get('id', '?')
                trigger_str = job.get('trigger', '?')
                next_run = job.get('next_run_time', '?')

                # 格式化下次運行時間
                if next_run and next_run != 'None':
                    # next_run_time 格式: "2026-03-04 12:34:56.123456"
                    next_run_display = next_run.split('.')[0]  # 移除毫秒
                else:
                    next_run_display = "暫無"

                # 組合呈現（實時信息）
                scheduler_list.append(f"• {job_id}\n  └ 觸發: {trigger_str}\n  └ 下次運行: {next_run_display}")

        scheduler_info = "\n".join(scheduler_list) if scheduler_list else "• 無啟用中的任務"
        
        # 3. tmux 狀態
        result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
        session_info = "運行中" if TMUX_SESSION_NAME in result.stdout else "Session 未啟動"

        status_message = f"""
📊 <b>Chat Agent Matrix 狀態報告</b>

🤖 <b>Agent 軍團:</b>
{agents_info}

⏰ <b>排程任務:</b>
{scheduler_info}

📺 <b>系統狀態:</b>
• tmux Session: {session_info}
• Telegram API: 🟢 正常
• 檢查時間: {datetime.now().strftime('%H:%M:%S')}

💡 輸入 <code>/switch [名稱]</code> 切換 Agent
"""
        send_message(status_message)
    except Exception as e:
        send_message(f"❌ 無法取得系統狀態: {str(e)}")

def show_help():
    """顯示幫助訊息"""
    help_message = f"""
📖 <b>Chat Agent Matrix - 完整功能說明</b>

<b>🎯 當前聚焦 Agent:</b> <code>{CURRENT_AGENT}</code>

───────────────────────────────

<b>🔧 基本對話操作</b>
• 直接發送訊息 - 交給活躍 Agent (⭐)
• 發送圖片 - 交給活躍 Agent 進行多模態分析
• <code>/switch [name]</code> - 切換活躍 Agent
• <code>/menu</code> - 顯示快捷功能選單

───────────────────────────────

<b>🔍 系統檢查與控制</b>
• <code>/status</code> - 查看所有 Agent 狀態、排程任務、系統資訊
• <code>/inspect [agent]</code> - 深度檢查指定 Agent 的 tmux 會話
• <code>/capture [agent]</code> - 截取指定 Agent 視窗內容（最後100行）
• <code>/interrupt</code> 或 <code>/stop</code> - 中斷當前 Agent 執行 (Ctrl+C)
• <code>/clear</code> - 清除當前 Agent 視窗與記憶

───────────────────────────────

<b>🧠 記憶與恢復</b>
• <code>/resume_latest</code> - 恢復最近一次對話內容

───────────────────────────────

<b>🛠️ 進階操作</b>
• <code>/fix [agent]</code> - 嘗試修復故障 Agent（清除卡住的指令）

───────────────────────────────

<b>💡 快速技巧</b>
1️⃣ 標註 ⭐ 的 Agent 為當前活躍，直接訊息會交給它
2️⃣ /status 可快速了解系統整體狀態
3️⃣ 排程任務在 scheduler.yaml 中配置
4️⃣ 使用 /menu 選擇常用操作，無需記指令

"""
    send_message(help_message)

def show_control_menu():
    """顯示控制選單 (基於 config.py 自定義)"""
    menu_message = f"🎮 <b>系統控制選單</b> (活躍: {CURRENT_AGENT})\n\n請選擇操作："
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
    """API 狀態檢查端點"""
    agents_summary = {a['name']: check_agent_session(a['name']) for a in AGENTS}
    return jsonify({
        'status': 'ok',
        'active_agent': CURRENT_AGENT,
        'agents': agents_summary,
        'tmux_session': TMUX_SESSION_NAME,
        'timestamp': datetime.now().isoformat()
    })

# ==========================================
# 排程管理 API (Scheduler Management)
# ==========================================

@app.route('/scheduler/refresh', methods=['POST'])
def scheduler_refresh():
    """重新讀取 scheduler.yaml 並刷新排程"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': '排程管理器未初始化'}), 500

    result = scheduler.refresh_jobs()
    return jsonify(result), 200 if result['status'] == 'ok' else 400

@app.route('/scheduler/jobs', methods=['GET'])
def scheduler_list_jobs():
    """列出所有排程任務"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': '排程管理器未初始化'}), 500

    result = scheduler.list_jobs()
    return jsonify(result), 200

@app.route('/scheduler/jobs/register', methods=['POST'])
def scheduler_register_job():
    """註冊新排程任務"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': '排程管理器未初始化'}), 500

    job_config = request.get_json()
    if not job_config:
        return jsonify({'status': 'error', 'message': '請提供有效的 JSON 配置'}), 400

    result = scheduler.register_job(job_config)
    return jsonify(result), 200 if result['status'] == 'ok' else 400

@app.route('/scheduler/jobs/<job_id>', methods=['DELETE'])
def scheduler_delete_job(job_id):
    """刪除排程任務"""
    if scheduler is None:
        return jsonify({'status': 'error', 'message': '排程管理器未初始化'}), 500

    result = scheduler.delete_job(job_id)
    return jsonify(result), 200 if result['status'] == 'ok' else 400

if __name__ == '__main__':
    print(f"🚀 啟動 Chat Agent Matrix API (Multi-Agent Mode)...")
    print(f"📍 本地端點: http://{FLASK_HOST}:{FLASK_PORT}")
    # === AACS: 物理寫入當前 Port 供啟動腳本讀取 ===
    port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".flask_port")
    with open(port_file, "w") as f:
        f.write(str(FLASK_PORT))

    print(f"🤖 預設 Agent: {DEFAULT_ACTIVE_AGENT}")
    print(f"👥 已配置 Agents: {', '.join([a['name'] for a in AGENTS])}")
    print("")

    # 啟動排程任務
    scheduler = SchedulerManager(image_manager=image_manager)
    scheduler.load_jobs(SCHEDULER_CONF)
    scheduler.start()
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ 啟動 Flask 伺服器失敗: {e}")
