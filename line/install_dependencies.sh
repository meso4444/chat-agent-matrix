#!/bin/bash
# Install system dependencies required for tmux Claude session remote control functionality

echo "🔧 Installing tmux Claude session remote control dependencies..."

# Check and install tmux
if ! command -v tmux &> /dev/null; then
    echo "📦 Installing tmux..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tmux
    elif command -v yum &> /dev/null; then
        sudo yum install -y tmux
    elif command -v brew &> /dev/null; then
        brew install tmux
    else
        echo "❌ Unable to auto-install tmux, please install manually"
        exit 1
    fi
    echo "✅ tmux installation complete"
else
    echo "✅ tmux already installed"
fi

# Check and install Python dependencies
echo "📦 Installing Python dependencies..."

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not installed, attempting to install..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "❌ Unable to auto-install Python3, please install manually"
        echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "macOS: brew install python3"
        exit 1
    fi
    echo "✅ Python3 installation complete"
else
    echo "✅ Python3 already installed"
fi

# Check pip3
if ! command -v pip3 &> /dev/null; then
    echo "🔧 Attempting to install pip3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    else
        echo "❌ pip3 not installed, attempting to use ensurepip..."
        if python3 -m ensurepip --default-pip 2>/dev/null; then
            echo "✅ pip3 installation complete via ensurepip"
        else
            echo "❌ Unable to install pip3, please install manually"
            echo "Ubuntu/Debian: sudo apt-get install python3-pip"
            echo "CentOS/RHEL: sudo yum install python3-pip"
            echo "Or use: python3 -m ensurepip --default-pip"
            exit 1
        fi
    fi
fi

echo "✅ pip3 check complete"

# Install Flask and related dependencies
echo "📦 Installing Python packages..."
if pip3 install flask PyYAML requests; then
    echo "✅ Python packages installation successful"
else
    echo "❌ Python packages installation failed, attempting with --user parameter..."
    if pip3 install --user flask PyYAML requests; then
        echo "✅ Python packages installation successful (using --user)"
    else
        echo "❌ Python packages installation failed, please check network connection or install manually"
        echo "Manual installation command: pip3 install flask PyYAML requests"
        exit 1
    fi
fi

echo "✅ Python dependencies installation complete"

# Check installation results
echo ""
echo "📋 System information confirmation:"
echo "• tmux version: $(tmux -V 2>/dev/null || echo "not installed")"
echo "• Python version: $(python3 --version 2>/dev/null || echo "not installed")"
echo "• pip3 version: $(pip3 --version 2>/dev/null | cut -d' ' -f1-2 || echo "not installed")"
echo "• Flask version: $(python3 -c 'import flask; print(f"Flask {flask.__version__}")' 2>/dev/null || echo "not installed")"
echo "• requests version: $(python3 -c 'import requests; print(f"requests {requests.__version__}")' 2>/dev/null || echo "not installed")"
echo "• PyYAML version: $(python3 -c 'import yaml; print("PyYAML installed")' 2>/dev/null || echo "not installed")"

# Ask whether to install Cloudflare Tunnel
echo ""
read -p "Install Cloudflare Tunnel (cloudflared)? (y/N): " install_cloudflared
case $install_cloudflared in
    [Yy]*)
        echo "📦 Installing Cloudflare Tunnel..."
        if command -v curl &> /dev/null; then
            echo "Downloading cloudflared..."
            curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            echo "✅ cloudflared installation complete"
        else
            echo "⚠️ Please manually install cloudflared: https://github.com/cloudflare/cloudflared/releases"
        fi
        ;;
    *)
        echo "⏭️ Skipping Cloudflare Tunnel installation"
        ;;
esac

echo ""
echo "🎉 All dependencies installation complete!"
echo ""
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
echo "🔧 Service management commands:"
echo "• Start all services: ./start_all_services.sh"
echo "• Check service status: ./status_all_services.sh"
echo "• Stop all services: ./stop_all_services.sh"
echo ""
echo "💡 Advantages:"
echo "• Unified service management using tmux"
echo "• Single command to start/stop entire system"
echo "• Services continue running in background"
echo "• See README.md for detailed configuration"