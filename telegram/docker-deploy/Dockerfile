FROM python:3.11-slim

# Dynamically specify container username (default: appuser, can be overridden during build)
ARG BUILD_USER=appuser

# Install system tools
RUN apt-get update && apt-get install -y \
    curl wget jq tmux procps git gnupg2 lsb-release sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install Ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
    tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
    tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok

# Install AI Agent CLIs
RUN npm install -g @google/gemini-cli @anthropic-ai/claude-code && \
    echo "✅ AI CLI tools installed successfully" && \
    which gemini && which claude

# Create non-root user (using dynamically specified username)
RUN useradd -m -s /bin/bash $BUILD_USER && \
    echo "$BUILD_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# [Image Hardening] Only copy necessary production code
# Create required directory structure
RUN mkdir -p /app/telegram/docker-deploy/scripts

# Core startup scripts
COPY config.py /app/telegram/
COPY start_all_services.sh /app/telegram/

# Service scripts
COPY telegram_webhook_server.py /app/telegram/
COPY telegram_notifier.py /app/telegram/
COPY start_ngrok.sh /app/telegram/
COPY status_telegram_services.sh /app/telegram/
COPY stop_telegram_services.sh /app/telegram/

# Message templates
COPY message_templates.yaml /app/telegram/

# Agent rules and protocols
COPY CLAUDE.md /app/telegram/
COPY GEMINI.md /app/telegram/
COPY agent_home_rules.md /app/telegram/
COPY agent_home_rules_templates/ /app/telegram/agent_home_rules_templates/

# Initialization scripts
COPY telegram_scripts/ /app/telegram/telegram_scripts/

# Container entrypoint
COPY docker-deploy/scripts/entrypoint.sh /app/telegram/docker-deploy/scripts/

WORKDIR /app/telegram

# Install Python dependencies
RUN pip install --no-cache-dir flask requests pyyaml apscheduler

# Fix permissions
RUN chown -R $BUILD_USER:$BUILD_USER /app && \
    chmod +x /app/telegram/docker-deploy/scripts/entrypoint.sh

# Switch to non-root user
USER $BUILD_USER

# Default command
CMD ["/app/telegram/docker-deploy/scripts/entrypoint.sh"]
