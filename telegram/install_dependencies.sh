#!/bin/bash
# Install dependencies for Telegram → AI Remote Control System (ngrok edition)

echo "🔧 Installing system dependencies..."

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "⚠️  This script is primarily designed for Linux environment (Ubuntu/Debian)"
    echo "   macOS users please use: brew install ngrok jq tmux"
    read -p "Continue? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Update system and install basic tools
echo "📦 Checking and installing basic tools (curl, wget, jq, tmux)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y curl wget jq tmux
elif command -v yum &> /dev/null; then
    sudo yum install -y curl wget jq tmux
else
    echo "⚠️  Unable to auto-install basic tools, please manually confirm installation: curl, wget, jq, tmux"
fi

# 2. Install ngrok
echo ""
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok already installed: $(ngrok --version)"
else
    echo "📦 Installing ngrok..."
    # Official installation method (Linux)
    if command -v apt-get &> /dev/null; then
        echo "   (Using apt installation)"
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt-get update
        sudo apt-get install -y ngrok
    else
        echo "   (Using direct download method)"
        wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin
        rm ngrok-v3-stable-linux-amd64.tgz
    fi

    if command -v ngrok &> /dev/null; then
        echo "✅ ngrok installation successful"
    else
        echo "❌ ngrok installation failed, please manually install from: https://ngrok.com/download"
        exit 1
    fi
fi

# 4. Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."

# Check pip3
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing python3-pip..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    fi
fi

# Install packages
PACKAGES="flask requests pyyaml apscheduler"
echo "📦 Installing Python packages: $PACKAGES"
if pip3 install $PACKAGES; then
    echo "✅ Python packages installation successful"
else
    echo "⚠️  Trying to install with --user flag..."
    pip3 install --user $PACKAGES
fi

# 5. Install AI Agent CLI tools
echo ""
echo "🤖 Checking and installing AI Agent CLI..."

# 5-1. Install Node.js (if needed)
if ! command -v npm &> /dev/null; then
    echo "📦 Installing Node.js (required for Claude Code)..."
    if command -v apt-get &> /dev/null; then
        # Install Node.js 20.x LTS
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "⚠️  Unable to auto-install Node.js, please manually install and retry."
    fi
fi

# 5-2. Install Claude Code
if ! command -v claude &> /dev/null; then
    if command -v npm &> /dev/null; then
        echo "📦 Installing Claude Code via npm..."
        # Attempt global installation
        sudo npm install -g @anthropic-ai/claude-code || echo "⚠️  Claude Code installation failed (Permission denied?)"
    else
        echo "❌ Node.js not installed, skipping Claude Code installation"
    fi
else
    echo "✅ Claude Code already installed: $(claude --version 2>/dev/null || echo 'Detected')"
fi

# 5-3. Install Gemini CLI
if ! command -v gemini &> /dev/null; then
    if command -v npm &> /dev/null; then
        echo "📦 Installing Gemini CLI via npm..."
        # Attempt global installation
        sudo npm install -g @google/gemini-cli || echo "⚠️  Gemini CLI installation failed (Permission denied?)"
    else
        echo "❌ Node.js not installed, skipping Gemini CLI installation"
    fi
else
    echo "✅ Gemini CLI already installed: $(gemini --version 2>/dev/null || echo 'Detected')"
fi

# 6. Enter setup wizard
echo ""
echo "🚀 Dependency installation complete! Starting setup wizard..."
sleep 1

# Check if setup script exists
if [ -f "./setup_config.sh" ]; then
    chmod +x ./setup_config.sh
    ./setup_config.sh
else
    echo "⚠️  setup_config.sh not found, please manually edit .env file"
fi

# 6. Summary (this section is replaced by setup_config.sh, can be simplified)
echo "📋 System dependency check:"
echo "   • tmux:   $(tmux -V 2>/dev/null || echo 'not installed')"
echo "   • jq:     $(jq --version 2>/dev/null || echo 'not installed')"
echo "   • ngrok:  $(ngrok --version 2>/dev/null || echo 'not installed')"
echo "   • Python: $(python3 --version 2>/dev/null || echo 'not installed')"
echo ""
