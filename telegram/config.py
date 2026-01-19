# config.py - Configuration loader
# Responsible for reading config.yaml and environment variables, providing to application

import os
import sys
import yaml

# Get current script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

# Manually load .env (ensure it can be read in systemd/tmux environment)
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only write if environment variable doesn't exist (avoid overwriting existing)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'') # Remove possible quotes
    except Exception as e:
        sys.stderr.write(f"⚠️  Cannot read .env: {e}\n")

# Load YAML configuration
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"❌ Error: Configuration file not found {CONFIG_PATH}")
    print("💡 Please ensure config.yaml exists in the correct location")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"❌ Error: config.yaml format is incorrect: {e}")
    sys.exit(1)

# ==========================================
# Variable export (maintain backward compatible interface)
# ==========================================

# Sensitive information (read from environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Server configuration
FLASK_HOST = _config['server']['host']
FLASK_PORT = _config['server']['port']

# AI Agent configuration
AGENTS = _config['agents']
DEFAULT_ACTIVE_AGENT = _config['default_active_agent']

# tmux configuration
TMUX_SESSION_NAME = _config['tmux']['session_name']
TMUX_WORKING_DIR = _config['tmux']['working_dir']

# Telegram API configuration
TELEGRAM_API_BASE_URL = _config['telegram']['api_base_url']
TELEGRAM_WEBHOOK_PATH = _config['telegram']['webhook_path']

# Image processing configuration
DEFAULT_CLEANUP_POLICY = _config.get('default_cleanup_policy', {'images_retention_days': 7})
TEMP_IMAGE_DIR_NAME = _config['image_processing'].get('temp_dir_name', 'images_temp')

# Custom menu
CUSTOM_MENU = _config['menu']

# Scheduler tasks
SCHEDULER_CONF = _config.get('scheduler', [])

# Collaboration groups
COLLABORATION_GROUPS = _config.get('collaboration_groups', [])

# Debug message
# print(f"✅ Configuration loaded (Agents: {len(AGENTS)}, Menu Rows: {len(CUSTOM_MENU)})")
