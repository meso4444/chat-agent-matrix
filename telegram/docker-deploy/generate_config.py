#!/usr/bin/env python3
"""
Configuration Generator for Chat Agent Matrix
Generates instance-specific configuration files (docker-compose, config.yaml, etc.)
"""

import sys
import yaml
import os

def generate_docker_compose(instance, user, script_dir):
    """Generate complete docker-compose file from template"""
    return {
        "services": {
            "bot": {
                "build": {
                    "context": "../",
                    "dockerfile": "docker-deploy/Dockerfile",
                    "args": {
                        "BUILD_USER": user
                    }
                },
                "container_name": f"chat-agent-{instance}",
                "restart": "unless-stopped",
                "user": "1000:1000",
                "environment": [
                    f"INSTANCE_NAME={instance}"
                ],
                "volumes": [
                    "../agent_home:/app/telegram/agent_home",
                    f"./container_home/{instance}:/home/{user}",
                    f"./.env.{instance}:/app/telegram/.env",
                    f"./config.{instance}.yaml:/app/telegram/config.yaml",
                    f"./scheduler.{instance}.yaml:/app/telegram/scheduler.yaml"
                ],
                "dns": ["8.8.8.8", "8.8.4.4"],
                "networks": [f"telegram_net_{instance}"]
            }
        },
        "networks": {
            f"telegram_net_{instance}": {
                "driver": "bridge",
                "name": f"telegram_net_{instance}"
            }
        }
    }

def generate_config(instance, data, flask_port=5000, ngrok_api_port=4040):
    """Generate instance configuration yaml (complete structure)"""
    agents = []
    if data:
        for entry in data.split('|||'):
            p = entry.split(':')
            if len(p) >= 4:
                agents.append({
                    "name": p[0],
                    "engine": p[1],
                    "usecase": p[2],
                    "description": p[3]
                })
    if not agents:
        agents = [{"name": "Default", "engine": "gemini", "usecase": "Default", "description": "Default"}]

    # Get default agent name (first agent)
    default_agent = agents[0]["name"] if agents else "Default"

    return {
        "server": {
            "host": "127.0.0.1",
            "port": flask_port,
            "ngrok_api_port": ngrok_api_port
        },
        "agents": agents,
        "default_active_agent": default_agent,
        "default_cleanup_policy": {
            "images_retention_days": 7
        },
        "telegram": {
            "api_base_url": "https://api.telegram.org/bot",
            "webhook_path": "/telegram_webhook"
        },
        "image_processing": {
            "temp_dir_name": "images_temp"
        },
        "tmux": {
            "session_name": f"ai_{instance}",
            "working_dir": ""
        },
        "menu": [
            [
                {"label": "🔄 Switch Agent", "command": "/switch {input}", "prompt": "Enter agent name to switch to:"}
            ],
            [
                {"label": "🔍 Health Check", "command": "/inspect {input}", "prompt": "Enter agent name to inspect:"},
                {"label": "🚑 Repair", "command": "/fix {input}", "prompt": "Enter agent name to repair:"},
                {"label": "🧠 Restore Memory", "command": "/resume_latest"}
            ],
            [
                {"label": "🛑 Interrupt", "command": "/interrupt"},
                {"label": "🧹 Reset", "command": "/clear"},
                {"label": "📖 Help", "command": "/help"},
                {"label": "📊 System Status", "command": "/status"}
            ]
        ]
    }

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: generate_config.py <mode> <instance> <agents_data> <script_dir> [flask_port] [ngrok_api_port] [user]")
        sys.exit(1)

    mode = sys.argv[1]
    instance = sys.argv[2]
    data = sys.argv[3]
    script_dir = sys.argv[4]

    flask_port = 5000
    ngrok_api_port = 4040
    user = os.environ.get('USER', 'appuser')

    # Parse optional parameters
    if len(sys.argv) >= 6:
        try:
            flask_port = int(sys.argv[5])
        except (ValueError, IndexError):
            pass

    if len(sys.argv) >= 7:
        try:
            ngrok_api_port = int(sys.argv[6])
        except (ValueError, IndexError):
            pass

    if len(sys.argv) >= 8:
        user = sys.argv[7]

    # Generate configuration
    if mode == "compose":
        compose = generate_docker_compose(instance, user, script_dir)
        output_file = os.path.join(script_dir, f"docker-compose.{instance}.yml")
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(compose, f, allow_unicode=True, default_flow_style=False)
        print(f"✅ Generated: {output_file}")

    elif mode == "config":
        config = generate_config(instance, data, flask_port, ngrok_api_port)
        output_file = os.path.join(script_dir, f"config.{instance}.yaml")

        # Generate YAML with comments (using string template)
        agents_yaml = yaml.dump({"agents": config["agents"]}, allow_unicode=True, default_flow_style=False)
        menu_yaml = yaml.dump({"menu": config["menu"]}, allow_unicode=True, default_flow_style=False)

        config_content = f"""# ==========================================
# Chat Agent Matrix Configuration File (Telegram Edition)
# ==========================================

# 🌐 Server and Network Configuration
server:
  host: {config['server']['host']}
  port: {config['server']['port']}
  ngrok_api_port: {config['server']['ngrok_api_port']}

# 🤖 AI Agent Configuration
{agents_yaml}

# Default active agent name on startup
default_active_agent: "{config['default_active_agent']}"

# 🤝 Collaboration Groups
# Members will automatically establish bidirectional interconnection (Full Mesh) via soft links
#collaboration_groups:
#  - name: "core_team"
#    description: "Collaborate to plan cost-effective travel itineraries"
#    members: ["Güpa", "Chöd"]
#    roles:
#      Güpa: "Responsible for planning travel itineraries per user requests and delivering to Chöd for budget estimation"
#      Chöd: "Responsible for budgeting all expenses. If per-person cost exceeds 50,000 TWD, submit budget report to Güpa for adjustment"

# ⏰ Scheduled Tasks (Scheduler)
#scheduler:
#  - name: "Daily System Cleanup"
#    type: "system"
#    action: "cleanup_images"
#    trigger: "interval"
#    hour: 24
#    minute: 0
#    second: 0
#    active: true
#
#  - name: "International News Daily Report"
#    type: "agent_command"
#    agent: "Güpa"
#    command: "Find important international news from the past two days"
#    trigger: "cron"
#    hour: 12
#    minute: 0
#    second: 0
#    active: true
#
#  - name: "Chöd Regular Stock Price Report"
#    type: "agent_command"
#    agent: "Chöd"
#    command: "Check current NVIDIA stock price"
#    trigger: "interval"
#    hour: 12
#    minute: 0
#    second: 0
#    active: true

# 🧹 Global Default Cleanup Policy
default_cleanup_policy:
  images_retention_days: {config['default_cleanup_policy']['images_retention_days']}

# 📱 Telegram API Configuration
telegram:
  api_base_url: "{config['telegram']['api_base_url']}"
  webhook_path: "{config['telegram']['webhook_path']}"

# 🖼️ Multimodal Image Processing
image_processing:
  temp_dir_name: "{config['image_processing']['temp_dir_name']}"

# tmux Configuration
tmux:
  session_name: "{config['tmux']['session_name']}"
  working_dir: "{config['tmux']['working_dir']}"

# 🎮 Custom Menu
menu:
#  - - label: "🌤 Taipei Today Weather"
#      command: "Check Taipei weather today, divided into morning, afternoon, and evening"
#    - label: "International News"
#      command: "Find major international news from recent days"
  - - label: "🔄 Switch Agent"
      command: "/switch {{input}}"
      prompt: "Enter agent name to switch to:"
#    - label: "🧘 Wake Güpa"
#      command: "/switch Güpa"
#    - label: "🔪 Wake Chöd"
#      command: "/switch Chöd"
  - - label: "🔍 Health Check"
      command: "/inspect {{input}}"
      prompt: "Enter agent name to inspect:"
    - label: "🚑 Repair"
      command: "/fix {{input}}"
      prompt: "Enter agent name to repair:"
    - label: "🧠 Restore Memory"
      command: "/resume_latest"
  - - label: "🛑 Interrupt"
      command: "/interrupt"
    - label: "🧹 Reset"
      command: "/clear"
    - label: "📖 Help"
      command: "/help"
    - label: "📊 System Status"
      command: "/status"
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"✅ Generated: {output_file}")

    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)
