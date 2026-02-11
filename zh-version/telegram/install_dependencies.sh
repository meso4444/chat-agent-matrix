#!/bin/bash
# Install dependencies for Telegram → AI Remote Control System (ngrok version)
# Automatically detects environment (WSL/Linux/macOS) and applies appropriate installation method

set -e

echo "🔧 Checking system environment..."

# ============================================================================
# Step 1: Detect Environment
# ============================================================================

detect_environment() {
    local os_type=$(uname -s)
    local uname_release=$(uname -r)

    # Check for WSL
    if grep -qi "microsoft" /proc/version 2>/dev/null; then
        # Detect WSL version
        if grep -qi "WSL2" /proc/version 2>/dev/null; then
            echo "WSL2"
        else
            echo "WSL1"
        fi
    # Check for macOS
    elif [[ "$os_type" == "Darwin" ]]; then
        echo "macOS"
    # Check for Linux
    elif [[ "$os_type" == "Linux" ]]; then
        echo "Linux"
    else
        echo "Unknown"
    fi
}

ENVIRONMENT=$(detect_environment)
echo "✅ Detected Environment: $ENVIRONMENT"
echo ""

# ============================================================================
# Step 2: Environment-Specific Dependency Installation
# ============================================================================

# ===== Homebrew Check (macOS only) =====
install_homebrew_if_needed() {
    if [[ "$ENVIRONMENT" != "macOS" ]]; then
        return
    fi

    if ! command -v brew &> /dev/null; then
        echo "📦 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Additional configuration for Apple Silicon Mac
        if [[ $(uname -m) == 'arm64' ]]; then
            echo "🍎 Detected Apple Silicon (M1/M2/M3), configuring Homebrew..."
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        echo "✅ Homebrew is already installed"
    fi
}

# ===== Basic Tools Installation =====
install_basic_tools() {
    echo "📦 Checking and installing basic tools (curl, wget, jq, tmux)..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: Use brew
        TOOLS="curl wget jq tmux"
        for tool in $TOOLS; do
            if ! command -v $tool &> /dev/null; then
                echo "   Installing $tool..."
                brew install $tool
            else
                echo "   ✅ $tool is already installed"
            fi
        done
    else
        # Linux/WSL: Use apt-get or yum
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y curl wget jq tmux
        elif command -v yum &> /dev/null; then
            sudo yum install -y curl wget jq tmux
        else
            echo "⚠️  Unable to automatically install basic tools. Please manually confirm: curl, wget, jq, tmux"
        fi
    fi
}

# ===== ngrok Installation =====
install_ngrok() {
    echo ""
    if command -v ngrok &> /dev/null; then
        echo "✅ ngrok is already installed: $(ngrok --version)"
        return
    fi

    echo "📦 Installing ngrok..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: Use brew
        brew install ngrok
    elif [[ "$ENVIRONMENT" == "WSL2" || "$ENVIRONMENT" == "Linux" ]]; then
        # Linux/WSL: Prefer apt-get, otherwise download directly
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
    fi

    if command -v ngrok &> /dev/null; then
        echo "✅ ngrok installed successfully"
    else
        echo "❌ ngrok installation failed. Please refer to official site for manual installation: https://ngrok.com/download"
        exit 1
    fi
}

# ===== Python 3 Installation (may be needed on macOS) =====
install_python3_if_needed() {
    if command -v python3 &> /dev/null; then
        echo "✅ Python 3 is already installed: $(python3 --version)"
        return
    fi

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        echo "📦 Installing Python 3..."
        brew install python3
    elif [[ "$ENVIRONMENT" == "Linux" || "$ENVIRONMENT" == "WSL2" ]]; then
        echo "📦 Installing Python 3..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y python3 python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        fi
    fi
}

# ===== Python Packages Installation =====
install_python_packages() {
    echo ""
    echo "🐍 Installing Python dependencies..."

    # Check pip3
    if ! command -v pip3 &> /dev/null; then
        echo "📦 Installing pip3..."
        if [[ "$ENVIRONMENT" == "macOS" ]]; then
            python3 -m ensurepip --upgrade
        else
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y python3-pip
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3-pip
            fi
        fi
    fi

    # Install packages
    PACKAGES="flask requests pyyaml apscheduler"
    echo "📦 Installing Python packages: $PACKAGES"
    if pip3 install $PACKAGES; then
        echo "✅ Python packages installed successfully"
    else
        echo "⚠️  Attempting installation with --user..."
        pip3 install --user $PACKAGES
    fi
}

# ===== Node.js Installation =====
install_nodejs() {
    echo ""
    echo "🤖 Checking and installing Node.js..."

    if command -v npm &> /dev/null; then
        echo "✅ Node.js is already installed: $(node --version)"
        return
    fi

    echo "📦 Installing Node.js..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: Use brew
        brew install node
    else
        # Linux/WSL: Use deb.nodesource.com
        if command -v apt-get &> /dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
        else
            echo "⚠️  Unable to automatically install Node.js. Please install manually and retry."
        fi
    fi
}

# ===== AI Agent CLI Installation =====
install_ai_cli_tools() {
    echo ""
    echo "🤖 Checking and installing AI Agent CLI..."

    # Whether sudo is needed (needed on Linux/WSL, usually not on macOS)
    local npm_prefix=""
    if [[ "$ENVIRONMENT" != "macOS" ]]; then
        npm_prefix="sudo"
    fi

    # Install Claude Code
    if ! command -v claude &> /dev/null; then
        if command -v npm &> /dev/null; then
            echo "📦 Installing Claude Code via npm..."
            $npm_prefix npm install -g @anthropic-ai/claude-code || echo "⚠️  Claude Code installation failed (permission issue?)"
        else
            echo "❌ Node.js not installed, skipping Claude Code installation"
        fi
    else
        echo "✅ Claude Code is already installed: $(claude --version 2>/dev/null || echo 'Detected')"
    fi

    # Install Gemini CLI
    if ! command -v gemini &> /dev/null; then
        if command -v npm &> /dev/null; then
            echo "📦 Installing Gemini CLI via npm..."
            $npm_prefix npm install -g @google/gemini-cli || echo "⚠️  Gemini CLI installation failed (permission issue?)"
        else
            echo "❌ Node.js not installed, skipping Gemini CLI installation"
        fi
    else
        echo "✅ Gemini CLI is already installed: $(gemini --version 2>/dev/null || echo 'Detected')"
    fi
}

# ===== Start Setup Wizard =====
start_setup_wizard() {
    echo ""
    echo "🚀 Dependency installation completed! Starting configuration wizard..."
    sleep 1

    # Check if setup script exists
    if [ -f "./setup_config.sh" ]; then
        chmod +x ./setup_config.sh
        ./setup_config.sh
    else
        echo "⚠️  setup_config.sh not found. Please manually edit the .env file"
    fi
}

# ===== Summary =====
print_summary() {
    echo ""
    echo "📋 System Dependencies Check ($ENVIRONMENT):"
    echo "   • Environment: $ENVIRONMENT"
    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        echo "   • Homebrew:  $(brew --version 2>/dev/null | head -1 || echo 'Not installed')"
    fi
    echo "   • tmux:      $(tmux -V 2>/dev/null || echo 'Not installed')"
    echo "   • jq:        $(jq --version 2>/dev/null || echo 'Not installed')"
    echo "   • ngrok:     $(ngrok --version 2>/dev/null || echo 'Not installed')"
    echo "   • Python:    $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo "   • Node.js:   $(node --version 2>/dev/null || echo 'Not installed')"
    echo ""
    echo "✅ Environment setup completed!"
    echo ""
}

# ============================================================================
# Main Execution Flow
# ============================================================================

# Check for unknown environment
if [[ "$ENVIRONMENT" == "Unknown" ]]; then
    echo "❌ Unrecognized operating system"
    exit 1
fi

# WSL1 Warning
if [[ "$ENVIRONMENT" == "WSL1" ]]; then
    echo "⚠️  WSL1 detected. Some features may be limited."
    echo "   Recommended to upgrade to WSL2: wsl --set-version <distro-name> 2"
    read -p "Continue anyway? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Execute installation steps
install_homebrew_if_needed
install_basic_tools
install_ngrok
install_python3_if_needed
install_python_packages
install_nodejs
install_ai_cli_tools
print_summary
start_setup_wizard
