FROM python:3.11-slim

# 動態指定容器用戶名（預設: appuser，可在 build 時覆蓋）
ARG BUILD_USER=appuser

# 安裝系統工具
RUN apt-get update && apt-get install -y \
    curl wget jq tmux procps git gnupg2 lsb-release sudo \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# 安裝 Ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
    tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
    tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok

# 安裝 AI Agent CLIs
RUN npm install -g @google/gemini-cli @anthropic-ai/claude-code && \
    echo "✅ AI CLI tools installed successfully" && \
    which gemini && which claude

# 建立非 root 用戶（使用動態指定的用戶名）
RUN useradd -m -s /bin/bash $BUILD_USER && \
    echo "$BUILD_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 【鏡像固化】只複製必要的生產代碼
# 建立必要的目錄結構
RUN mkdir -p /app/telegram/docker-deploy/scripts

# 核心啟動腳本
COPY config.py /app/telegram/
COPY start_all_services.sh /app/telegram/

# 服務腳本
COPY telegram_webhook_server.py /app/telegram/
COPY telegram_notifier.py /app/telegram/
COPY start_ngrok.sh /app/telegram/
COPY status_telegram_services.sh /app/telegram/
COPY stop_telegram_services.sh /app/telegram/

# 訊息模板
COPY message_templates.yaml /app/telegram/

# Agent 規則與協議
COPY CLAUDE.md /app/telegram/
COPY GEMINI.md /app/telegram/
COPY agent_home_rules.md /app/telegram/
COPY agent_home_rules_templates/ /app/telegram/agent_home_rules_templates/

# 初始化腳本
COPY telegram_scripts/ /app/telegram/telegram_scripts/

# 容器入口
COPY docker-deploy/scripts/entrypoint.sh /app/telegram/docker-deploy/scripts/

WORKDIR /app/telegram

# 安裝 Python 依賴
RUN pip install --no-cache-dir flask requests pyyaml apscheduler

# 修正權限
RUN chown -R $BUILD_USER:$BUILD_USER /app && \
    chmod +x /app/telegram/docker-deploy/scripts/entrypoint.sh

# 切換到非 root 用戶
USER $BUILD_USER

# 預設指令
CMD ["/app/telegram/docker-deploy/scripts/entrypoint.sh"]
