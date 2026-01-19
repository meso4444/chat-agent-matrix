# config.py - 配置載入器
# 負責讀取 config.yaml 與環境變數，並提供給應用程式使用

import os
import sys
import yaml

# 獲取當前腳本所在目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

# 手動載入 .env (確保在 systemd/tmux 環境下能讀取)
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 只有在環境變數不存在時才寫入 (避免覆蓋已存在的)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'') # 去除可能引號
    except Exception as e:
        sys.stderr.write(f"⚠️  無法讀取 .env: {e}\n")

# 載入 YAML 配置
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"❌ 錯誤: 找不到設定檔 {CONFIG_PATH}")
    print("💡 請確保 config.yaml 存在於正確位置")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"❌ 錯誤: config.yaml 格式有誤: {e}")
    sys.exit(1)

# ==========================================
# 變數導出 (保持與舊版相容的介面)
# ==========================================

# 敏感資訊 (從環境變數讀取)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 伺服器設定
FLASK_HOST = _config['server']['host']
FLASK_PORT = _config['server']['port']

# AI Agent 設定
AGENTS = _config['agents']
DEFAULT_ACTIVE_AGENT = _config['default_active_agent']

# tmux 設定
TMUX_SESSION_NAME = _config['tmux']['session_name']
TMUX_WORKING_DIR = _config['tmux']['working_dir']

# Telegram API 設定
TELEGRAM_API_BASE_URL = _config['telegram']['api_base_url']
TELEGRAM_WEBHOOK_PATH = _config['telegram']['webhook_path']

# 圖片處理設定
DEFAULT_CLEANUP_POLICY = _config.get('default_cleanup_policy', {'images_retention_days': 7})
TEMP_IMAGE_DIR_NAME = _config['image_processing'].get('temp_dir_name', 'images_temp')

# 自定義選單
CUSTOM_MENU = _config['menu']

# 排程任務
SCHEDULER_CONF = _config.get('scheduler', [])

# 協作群組
COLLABORATION_GROUPS = _config.get('collaboration_groups', [])

# 除錯訊息
# print(f"✅ 已載入配置 (Agents: {len(AGENTS)}, Menu Rows: {len(CUSTOM_MENU)})")