#!/usr/bin/env python3
"""
Claude Code LINE 通知器
從模板文件讀取訊息格式，Claude Code 只需要填入變數
"""

import requests
import json
import yaml
import os
from datetime import datetime
from config import CHANNEL_ACCESS_TOKEN

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

def send_message(message: str, quick_reply_items: list = None) -> bool:
    """
    發送 LINE 訊息 (支援 Quick Reply)
    
    Args:
        message (str): 要發送的訊息內容
        quick_reply_items (list): Quick Reply 按鈕列表 (dict format)
        
    Returns:
        bool: 發送是否成功
    """
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ 錯誤: 請在 config.py 中設定 CHANNEL_ACCESS_TOKEN")
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
    
    # 加入 Quick Reply
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
            print(f'✅ LINE 通知發送成功: {datetime.now().strftime("%H:%M:%S")}')
            return True
        else:
            print(f'❌ LINE 通知發送失敗: {response.status_code} - {response.text}')
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

# 保留模板功能供參考，但 Claude Code 主要使用 send_message
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
    
    print("=== LINE 通知器測試 ===")
    
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ 請先在 config.py 中設定 CHANNEL_ACCESS_TOKEN")
        sys.exit(1)
    else:
        print("✅ 配置正確，發送測試訊息...")
    
    # 檢查是否有傳入訊息參數
    if len(sys.argv) > 1:
        # 使用 Claude Code 傳入的訊息，並正確處理換行符
        message = ' '.join(sys.argv[1:]).replace('\\n', '\n')
        print(f"📤 發送 Claude Code 訊息: {message[:50]}...")
        success = send_message(message)
        if success:
            print("✅ Claude Code 訊息發送成功")
        else:
            print("❌ Claude Code 訊息發送失敗")
    else:
        # 僅在沒有參數時才發送測試訊息
        print("📋 沒有傳入訊息，發送測試訊息...")
        send_message("🧪 LINE 通知系統測試\n\n系統運作正常，Claude Code 可以開始使用通知服務！")