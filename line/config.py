# config.py - LINE version configuration loader

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
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"❌ Error: config.yaml format is incorrect: {e}")
    sys.exit(1)

# ==========================================
# Variable export
# ==========================================

# Server configuration
FLASK_HOST = _config['server']['host']
FLASK_PORT = _config['server']['port']

# LINE Bot configuration
# Prioritize reading from environment variables (for security)
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# Cloudflare configuration
# Read from environment variables first, use default if not available
CLOUDFLARE_TUNNEL_NAME = os.environ.get("CLOUDFLARE_TUNNEL_NAME", "line-bot-tunnel")
CLOUDFLARE_CUSTOM_DOMAIN = os.environ.get("CLOUDFLARE_CUSTOM_DOMAIN")
CLOUDFLARE_CONFIG_FILE = "" # Leave empty by default

# Check required configuration
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    sys.stderr.write("⚠️  Warning: No LINE Token environment variables detected\n")
    sys.stderr.write("   Please run ./setup_config.sh to configure, or check .env file\n")

# AI Agent configuration
AGENTS = _config['agents']
DEFAULT_ACTIVE_AGENT = _config['default_active_agent']

# tmux configuration
TMUX_SESSION_NAME = _config['tmux']['session_name']
TMUX_WORKING_DIR = _config['tmux']['working_dir']

# Image processing configuration
DEFAULT_CLEANUP_POLICY = _config.get('default_cleanup_policy', {'images_retention_days': 7})
# Use safe retrieval method, as LINE version config.yaml may not contain image_processing
TEMP_IMAGE_DIR_NAME = _config.get('image_processing', {}).get('temp_dir_name', 'images_temp')

# Custom menu
CUSTOM_MENU = _config['menu']

# Scheduler tasks
SCHEDULER_CONF = _config.get('scheduler', [])

# Collaboration groups
COLLABORATION_GROUPS = _config.get('collaboration_groups', [])
