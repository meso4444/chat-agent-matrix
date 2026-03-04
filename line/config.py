# config.py - LINE 版本配置載入器

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
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"❌ 錯誤: config.yaml 格式有誤: {e}")
    sys.exit(1)

# ==========================================
# 變數導出
# ==========================================

# 伺服器設定
FLASK_HOST = _config['server']['host']
FLASK_PORT = _config['server']['port']

# LINE Bot 設定
# 優先讀取環境變數 (安全性考量)
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# Cloudflare 設定
# 優先從環境變數讀取，若無則使用預設值
CLOUDFLARE_TUNNEL_NAME = os.environ.get("CLOUDFLARE_TUNNEL_NAME", "line-bot-tunnel")
CLOUDFLARE_CUSTOM_DOMAIN = os.environ.get("CLOUDFLARE_CUSTOM_DOMAIN")
CLOUDFLARE_CONFIG_FILE = "" # 預設留空

# 檢查必要設定
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    sys.stderr.write("⚠️  警告: 未偵測到 LINE Token 環境變數\n")
    sys.stderr.write("   請執行 ./setup_config.sh 進行設定，或檢查 .env 檔案\n")

# AI Agent 設定
AGENTS = _config['agents']
DEFAULT_ACTIVE_AGENT = _config['default_active_agent']

# tmux 設定
TMUX_SESSION_NAME = _config['tmux']['session_name']
TMUX_WORKING_DIR = _config['tmux']['working_dir']

# 圖片處理設定
DEFAULT_CLEANUP_POLICY = _config.get('default_cleanup_policy', {'images_retention_days': 7})
# 使用安全獲取方式，因為 LINE 版 config.yaml 可能不包含 image_processing
TEMP_IMAGE_DIR_NAME = _config.get('image_processing', {}).get('temp_dir_name', 'images_temp')

# 自定義選單
CUSTOM_MENU = _config['menu']

# 排程任務
SCHEDULER_CONF = _config.get('scheduler', [])

# 協作群組
COLLABORATION_GROUPS = _config.get('collaboration_groups', [])