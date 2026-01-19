#!/usr/bin/env python3
"""
AI 引擎 Telegram 通知器
從模板文件讀取訊息格式，AI 引擎只需要填入變數
"""

import requests
import json
import yaml
import os
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_API_BASE_URL

def load_message_template(template_name: str, software: str = None) -> dict:
    """
    從模板文件載入訊息模板
    
    Args:
        template_name (str): 模板名稱 (start, progress, success, error, custom)
        software (str): 軟體名稱，用於查找特定軟體模板
        
    Returns:
        dict: 包含 icon, title, content 的模板字典
    """
    template_file = os.path.join(os.path.dirname(__file__), 'message_templates.yaml')
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        # 優先使用軟體特定模板
        if software and software in templates.get('software_templates', {}):
            software_template = templates['software_templates'][software].get(template_name)
            if software_template:
                return software_template
        
        # 使用通用模板
        return templates['templates'].get(template_name, {})
        
    except Exception as e:
        print(f"⚠️ 無法載入模板: {e}")
        # 回退到簡單模板
        return {
            'icon': '📋',
            'title': f'{template_name.upper()}',
            'content': '{content}'
        }

def send_message(message: str) -> bool:
    """
    發送 Telegram 訊息
    
    Args:
        message (str): 要發送的訊息內容
        
    Returns:
        bool: 發送是否成功
    """
    if not TELEGRAM_BOT_TOKEN:
        print("❌ 錯誤: 請在 config.py 中設定 TELEGRAM_BOT_TOKEN")
        return False
    
    if not TELEGRAM_CHAT_ID:
        print("❌ 錯誤: 請在 config.py 中設定 TELEGRAM_CHAT_ID")
        return False
    
    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'  # 支援 HTML 格式
    }
    
    try:
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print(f'✅ Telegram 通知發送成功: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ Telegram 通知發送失敗: {response.status_code} - {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ 發送過程發生錯誤: {e}')
        return False

def send_message_with_keyboard(message: str, keyboard_buttons: list = None) -> bool:
    """
    發送帶有自定義鍵盤的 Telegram 訊息
    
    Args:
        message (str): 要發送的訊息內容
        keyboard_buttons (list): 鍵盤按鈕配置
        
    Returns:
        bool: 發送是否成功
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 錯誤: 請檢查 Telegram 配置")
        return False
    
    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    # 添加自定義鍵盤
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
            print(f'✅ Telegram 帶鍵盤訊息發送成功: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ Telegram 帶鍵盤訊息發送失敗: {response.status_code} - {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ 發送過程發生錯誤: {e}')
        return False

def format_message_from_template(template_name: str, software: str = "", **kwargs) -> str:
    """
    從模板格式化訊息
    
    Args:
        template_name (str): 模板名稱
        software (str): 軟體名稱
        **kwargs: 模板變數
        
    Returns:
        str: 格式化後的訊息
    """
    template = load_message_template(template_name, software)
    
    # 準備模板變數
    variables = {
        'software': software,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **kwargs
    }
    
    # 格式化模板
    try:
        icon = template.get('icon', '')
        title = template.get('title', '').format(**variables)
        content = template.get('content', '').format(**variables)
        
        # 組合最終訊息
        message = f"{icon} {title}\n\n{content}" if icon else f"{title}\n\n{content}"
        return message.strip()
        
    except KeyError as e:
        print(f"⚠️ 模板變數缺失: {e}")
        return f"訊息模板錯誤: 缺少變數 {e}"

def get_chat_id() -> str:
    """
    取得機器人的 chat updates，用於獲取 chat_id
    
    Returns:
        str: 找到的 chat_id 或錯誤訊息
    """
    if not TELEGRAM_BOT_TOKEN:
        return "❌ 請先設定 TELEGRAM_BOT_TOKEN"
    
    url = f"{TELEGRAM_API_BASE_URL}{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['result']:
                chat_id = data['result'][-1]['message']['chat']['id']
                return f"✅ 找到 Chat ID: {chat_id}"
            else:
                return "⚠️ 沒有找到任何對話，請先發送訊息給機器人"
        else:
            return f"❌ 請求失敗: {response.status_code}"
    except Exception as e:
        return f"❌ 錯誤: {e}"

# 保留模板功能供參考，但 AI 引擎主要使用 send_message
def send_template_message(template_name: str, **variables) -> bool:
    """
    使用模板發送訊息 (可選功能)
    
    Args:
        template_name (str): 模板名稱
        **variables: 模板變數
        
    Returns:
        bool: 發送是否成功
    """
    software = variables.get('software', '')
    message = format_message_from_template(template_name, software, **variables)
    return send_message(message)

if __name__ == '__main__':
    import sys
    
    # 支援命令行直接發送訊息 (更安全的特殊字符處理方式)
    if len(sys.argv) > 1:
        message_content = " ".join(sys.argv[1:])
        # 處理命令行傳入的換行符號，將字面量的 \n 轉換為實際換行
        message_content = message_content.replace('\\n', '\n')
        if send_message(message_content):
            sys.exit(0)
        else:
            sys.exit(1)

    # 測試功能
    print("=== Telegram 通知器測試 ===")
    if not TELEGRAM_BOT_TOKEN:
        print("❌ 請先在 config.py 中設定 TELEGRAM_BOT_TOKEN")
        print("📝 取得 Bot Token 步驟:")
        print("1. 在 Telegram 搜尋 @BotFather")
        print("2. 發送 /newbot 創建新機器人")
        print("3. 複製取得的 Token 到 config.py")
    elif not TELEGRAM_CHAT_ID:
        print("❌ 請先在 config.py 中設定 TELEGRAM_CHAT_ID")
        print("📝 取得 Chat ID:")
        print(get_chat_id())
    else:
        print("✅ 配置正確，發送測試訊息...")
        
        # 測試直接發送訊息
        send_message("🧪 <b>Telegram 通知系統測試</b>\n\n系統運作正常，AI 引擎可以開始使用通知服務！")
        
        # 測試帶鍵盤的訊息
        keyboard = [
            ["/status", "/help"],
            ["檢查系統狀態", "重啟服務"]
        ]
        send_message_with_keyboard("🎯 <b>系統控制選單</b>\n\n選擇要執行的操作：", keyboard)