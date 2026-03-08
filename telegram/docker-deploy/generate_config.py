#!/usr/bin/env python3
"""
Configuration Generator for Chat Agent Matrix
生成實例特定的配置檔案（docker-compose、config.yaml 等）
"""

import sys
import yaml
import os

def generate_docker_compose(instance, user, script_dir):
    """根據模板生成完整的 docker-compose 檔案"""
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
    """生成實例配置 yaml（完整結構）"""
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

    # 取得預設 Agent 名稱（第一個 Agent）
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
                {"label": "🔄 切換 Agent", "command": "/switch {input}", "prompt": "請輸入要切換的 Agent 名稱:"}
            ],
            [
                {"label": "🔍 健檢", "command": "/inspect {input}", "prompt": "請輸入要檢查的 Agent 名稱:"},
                {"label": "🚑 修復", "command": "/fix {input}", "prompt": "請輸入要修復的 Agent 名稱:"},
                {"label": "🧠 恢復記憶", "command": "/resume_latest"}
            ],
            [
                {"label": "🛑 中斷", "command": "/interrupt"},
                {"label": "🧹 重置", "command": "/clear"},
                {"label": "📖 幫助", "command": "/help"},
                {"label": "📊 系統狀態", "command": "/status"}
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

    # 解析可選參數
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

    # 生成配置
    if mode == "compose":
        compose = generate_docker_compose(instance, user, script_dir)
        output_file = os.path.join(script_dir, f"docker-compose.{instance}.yml")
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(compose, f, allow_unicode=True, default_flow_style=False)
        print(f"✅ Generated: {output_file}")

    elif mode == "config":
        config = generate_config(instance, data, flask_port, ngrok_api_port)
        output_file = os.path.join(script_dir, f"config.{instance}.yaml")

        # 生成包含註解的 YAML（用字符串模板）
        agents_yaml = yaml.dump({"agents": config["agents"]}, allow_unicode=True, default_flow_style=False)
        menu_yaml = yaml.dump({"menu": config["menu"]}, allow_unicode=True, default_flow_style=False)

        config_content = f"""# ==========================================
# Chat Agent Matrix 配置檔案 (Telegram Edition)
# ==========================================

# 🌐 伺服器與網路設定
server:
  host: {config['server']['host']}
  port: {config['server']['port']}
  ngrok_api_port: {config['server']['ngrok_api_port']}

# 🤖 AI Agent 軍團配置
{agents_yaml}

# 預設啟動時活躍的 Agent 名稱
default_active_agent: "{config['default_active_agent']}"

# 🤝 協作群組 (Collaboration Groups)
# 組內成員會自動建立雙向互連 (Full Mesh) 的軟連結
#collaboration_groups:
#  - name: "core_team"
#    description: "協作規劃高CP值的旅遊行程"
#    members: ["Güpa", "Chöd"]
#    roles:
#      Güpa: "負責依照使用者要求規劃旅遊行程，並將旅遊行程交付Chöd來估算預算"
#      Chöd: "負責行程所有花費的預算估算，若單人花費超出台幣五萬時，就提交預算報告給Güpa，讓他調整行程"

# ⏰ 排程任務 (Scheduler)
#scheduler:
#  - name: "每日系統清理"
#    type: "system"
#    action: "cleanup_images"
#    trigger: "interval"
#    hour: 24
#    minute: 0
#    second: 0
#    active: true
#
#  - name: "國際新聞日報"
#    type: "agent_command"
#    agent: "Güpa"
#    command: "查詢一下這兩天重要的國際新聞"
#    trigger: "cron"
#    hour: 12
#    minute: 0
#    second: 0
#    active: true
#
#  - name: "Chöd 定期股價回報"
#    type: "agent_command"
#    agent: "Chöd"
#    command: "查詢英偉達當前股價"
#    trigger: "interval"
#    hour: 12
#    minute: 0
#    second: 0
#    active: true

# 🧹 全域預設清理規則
default_cleanup_policy:
  images_retention_days: {config['default_cleanup_policy']['images_retention_days']}

# 📱 Telegram API 設定
telegram:
  api_base_url: "{config['telegram']['api_base_url']}"
  webhook_path: "{config['telegram']['webhook_path']}"

# 🖼️ 多模態圖片處理
image_processing:
  temp_dir_name: "{config['image_processing']['temp_dir_name']}"

# tmux 設定
tmux:
  session_name: "{config['tmux']['session_name']}"
  working_dir: "{config['tmux']['working_dir']}"

# 🎮 自定義選單 (Custom Menu)
menu:
#  - - label: "🌤 台北今日天氣"
#      command: "查詢台北今天的天氣，分成早中晚"
#    - label: "國際新聞"
#      command: "查詢近日的重大國際新聞"
  - - label: "🔄 切換 Agent"
      command: "/switch {{input}}"
      prompt: "請輸入要切換的 Agent 名稱:"
#    - label: "🧘 喚醒 Güpa"
#      command: "/switch Güpa"
#    - label: "🔪 喚醒 Chöd"
#      command: "/switch Chöd"
  - - label: "🔍 健檢"
      command: "/inspect {{input}}"
      prompt: "請輸入要檢查的 Agent 名稱:"
    - label: "🚑 修復"
      command: "/fix {{input}}"
      prompt: "請輸入要修復的 Agent 名稱:"
    - label: "🧠 恢復記憶"
      command: "/resume_latest"
  - - label: "🛑 中斷"
      command: "/interrupt"
    - label: "🧹 重置"
      command: "/clear"
    - label: "📖 幫助"
      command: "/help"
    - label: "📊 系統狀態"
      command: "/status"
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"✅ Generated: {output_file}")

    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)
