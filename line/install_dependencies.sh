#!/bin/bash
# Install dependencies for LINE → AI Remote Control System (Cloudflare Tunnel version)
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

# ===== Basic Tools Installation (tmux only for LINE) =====
install_basic_tools() {
    echo "📦 Checking and installing basic tools (tmux)..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: Use brew
        if ! command -v tmux &> /dev/null; then
            echo "   Installing tmux..."
            brew install tmux
        else
            echo "   ✅ tmux is already installed"
        fi
    else
        # Linux/WSL: Use apt-get or yum
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y tmux
        elif command -v yum &> /dev/null; then
            sudo yum install -y tmux
        else
            echo "⚠️  Unable to automatically install tmux. Please manually confirm: tmux"
        fi
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
    elif [[ "$ENVIRONMENT" == "Linux" || "$ENVIRONMENT" == "WSL2" || "$ENVIRONMENT" == "WSL1" ]]; then
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

    # Install packages (LINE-specific: no apscheduler needed)
    PACKAGES="flask requests pyyaml"
    echo "📦 Installing Python packages: $PACKAGES"
    if pip3 install $PACKAGES; then
        echo "✅ Python packages installed successfully"
    else
        echo "⚠️  Attempting installation with --user..."
        pip3 install --user $PACKAGES
    fi
}

# ===== Cloudflare Tunnel Installation =====
install_cloudflared() {
    echo ""
    echo "📦 Installing Cloudflare Tunnel (cloudflared)..."

    if command -v cloudflared &> /dev/null; then
        echo "✅ cloudflared is already installed: $(cloudflared --version 2>&1 | head -1)"
        return
    fi

    local cloudflared_url=""
    local install_method=""

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: Use Homebrew (handles both Intel and Apple Silicon)
        if command -v brew &> /dev/null; then
            echo "   (Using brew installation)"
            brew install cloudflare/cloudflare/cloudflared
            install_method="brew"
        else
            echo "⚠️  Homebrew not found. Please install manually: https://github.com/cloudflare/cloudflared/releases"
            return
        fi
    elif [[ "$ENVIRONMENT" == "WSL2" || "$ENVIRONMENT" == "WSL1" || "$ENVIRONMENT" == "Linux" ]]; then
        # Linux/WSL: Download binary directly
        local arch=$(uname -m)
        case "$arch" in
            x86_64)
                cloudflared_url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
                ;;
            aarch64|arm64)
                cloudflared_url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
                ;;
            *)
                echo "⚠️  Unsupported architecture: $arch. Please install cloudflared manually."
                return
                ;;
        esac

        if [[ -z "$cloudflared_url" ]]; then
            echo "⚠️  Unable to determine download URL for architecture: $arch"
            return
        fi

        if command -v curl &> /dev/null; then
            echo "   (Using direct download method for $arch)"
            curl -L "$cloudflared_url" -o cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            install_method="download"
        elif command -v wget &> /dev/null; then
            echo "   (Using wget download method for $arch)"
            wget "$cloudflared_url" -O cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            install_method="wget"
        else
            echo "⚠️  Neither curl nor wget found. Please install cloudflared manually: $cloudflared_url"
            return
        fi
    fi

    if command -v cloudflared &> /dev/null; then
        echo "✅ cloudflared installed successfully via $install_method"
    else
        echo "⚠️  cloudflared installation may have failed. Please verify: cloudflared --version"
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
    echo "   • Python:    $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo "   • Flask:     $(python3 -c 'import flask; print(f"Flask {flask.__version__}")' 2>/dev/null || echo 'Not installed')"
    echo "   • cloudflared: $(cloudflared --version 2>&1 | head -1 || echo 'Not installed')"
    echo ""
    echo "✅ Core dependencies installation completed!"
    echo ""
}

# ===== Next Steps =====
print_next_steps() {
    echo "📋 Next steps to perform:"
    echo "1. Fill in CHANNEL_SECRET in config.py (if not already filled)"
    echo "2. Update CLOUDFLARE_CUSTOM_DOMAIN in config.py to your domain name"
    echo "3. Configure Cloudflare fixed URL: ./setup_cloudflare_fixed_url.sh"
    echo "4. Configure LINE Webhook URL (don't verify yet)"
    echo "5. Start all services: ./start_all_services.sh"
    echo "6. Verify Webhook connection in LINE Console"
    echo ""
    echo "💡 Important reminders:"
    echo "• Need to own a domain name and host it on Cloudflare"
    echo "• Webhook verification must be performed after service startup"
    echo "• See SETUP_GUIDE.md for detailed configuration"
    echo "• See TMUX_GUIDE.md for tmux operation instructions"
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
install_python3_if_needed
install_python_packages
install_cloudflared
print_summary
print_next_steps

echo "🚀 Setup preparation complete! Ready to configure LINE integration."
echo ""
