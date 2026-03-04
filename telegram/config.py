# config.py - Configuration Loader (ISC - Instance-Specific Config)
# 支援三層疊加：Base YAML -> Instance YAML -> Environment
import os
import sys
import yaml
import json
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 第一層: 載入 .env (通用)
# ==========================================
def _load_env_file(env_path):
    """載入 .env 檔案到環境變數 (不覆蓋已存在的)"""
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'')
    except Exception as e:
        sys.stderr.write(f"⚠️  無法讀取 {env_path}: {e}\n")

# 載入通用 .env
_load_env_file(os.path.join(BASE_DIR, '.env'))

# ==========================================
# 第二層: 載入 Instance 專屬 .env (如果有)
# ==========================================
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', '')
if INSTANCE_NAME:
    _instance_env_path = os.path.join(BASE_DIR, f'.env.{INSTANCE_NAME}')
    _load_env_file(_instance_env_path)
    # 也檢查 docker-deploy 目錄
    _docker_env_path = os.path.join(BASE_DIR, 'docker-deploy', '.env')
    _load_env_file(_docker_env_path)

# 3. 載入 YAML 配置 (ISC: Instance-Specific Config)
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
INSTANCE_CONFIG_PATH = os.path.join(BASE_DIR, f"config.{INSTANCE_NAME}.yaml")
SCHEDULER_YAML_PATH = os.path.join(BASE_DIR, "scheduler.yaml")

def load_yaml(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def _deep_merge(base, override):
    """遞迴合併字典，支援巢狀配置"""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result

_config = load_yaml(CONFIG_PATH)
_instance_config = load_yaml(INSTANCE_CONFIG_PATH)

# 合併配置 (實例配置優先，支援遞迴深層合併)
if _instance_config:
    _config = _deep_merge(_config, _instance_config)

# 4. 變數映射與環境變數覆蓋
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

_registry_str = os.environ.get("BOT_REGISTRY", "{}")
try:
    BOT_REGISTRY = json.loads(_registry_str)
except Exception:
    BOT_REGISTRY = {}

FLASK_HOST = os.environ.get("FLASK_HOST", _config.get("server", {}).get("host", "127.0.0.1"))
# 【Port 配置統一化】Port 從 config.yaml 讀取，環境變量保留作緊急覆蓋用
FLASK_PORT = int(os.environ.get("FLASK_PORT", _config.get("server", {}).get("port", 5000)))
NGROK_API_PORT = int(os.environ.get("NGROK_API_PORT", _config.get("server", {}).get("ngrok_api_port", 4040)))

AGENTS = _config.get("agents", [])
DEFAULT_ACTIVE_AGENT = _config.get("default_active_agent", "")
TMUX_SESSION_NAME = os.environ.get("TMUX_SESSION_NAME", _config.get("tmux", {}).get("session_name", "chat_agent"))
TMUX_WORKING_DIR = _config.get("tmux", {}).get("working_dir", "")
TELEGRAM_API_BASE_URL = _config.get("telegram", {}).get("api_base_url", "https://api.telegram.org/bot")
TELEGRAM_WEBHOOK_PATH = os.environ.get("TELEGRAM_WEBHOOK_PATH", _config.get("telegram", {}).get("webhook_path", "/webhook"))
DEFAULT_CLEANUP_POLICY = _config.get("default_cleanup_policy", {"images_retention_days": 7})
TEMP_IMAGE_DIR_NAME = _config.get("image_processing", {}).get("temp_dir_name", "images_temp")
CUSTOM_MENU = _config.get("menu", [])

# 從分離的 scheduler.yaml 讀取排程配置
_scheduler_config = load_yaml(SCHEDULER_YAML_PATH)
SCHEDULER_CONF = _scheduler_config.get("scheduler", [])

COLLABORATION_GROUPS = _config.get("collaboration_groups", [])