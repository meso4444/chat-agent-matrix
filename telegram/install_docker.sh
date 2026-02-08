#!/bin/bash
# install_docker.sh - Intelligent Docker & Docker Compose Installation Script
# Detects environment (WSL/macOS/Linux) and applies appropriate installation method

set -e

echo "🐳 Docker Installation Wizard"
echo "========================================"
echo ""

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
        # Detect Linux distribution
        if command -v lsb_release &> /dev/null; then
            local distro=$(lsb_release -si)
            echo "Linux-$distro"
        elif [[ -f /etc/os-release ]]; then
            local distro=$(grep "^ID=" /etc/os-release | cut -d'=' -f2 | tr -d '"')
            echo "Linux-$distro"
        else
            echo "Linux-Unknown"
        fi
    else
        echo "Unknown"
    fi
}

ENVIRONMENT=$(detect_environment)

echo "✅ Detected Environment: $ENVIRONMENT"
echo ""

# ============================================================================
# Step 2: Environment-Specific Installation
# ============================================================================

install_docker_wsl2() {
    echo "🔧 Installing Docker for WSL2 (in WSL)..."
    echo ""

    # ===== WSL2 Systemd Auto-Enable =====
    if grep -qi "Microsoft" /proc/version; then
        echo "🔍 WSL environment detected, checking systemd configuration..."
        WSL_CONF="/etc/wsl.conf"

        # Create file if it doesn't exist
        if [ ! -f "$WSL_CONF" ]; then
            echo "   Creating new $WSL_CONF..."
            touch "$WSL_CONF"
        fi

        # Check if systemd=true is already configured
        if ! grep -q "systemd=true" "$WSL_CONF"; then
            echo "🔧 Enabling WSL Systemd support..."

            # Ensure [boot] section exists
            if ! grep -q "\[boot\]" "$WSL_CONF"; then
                echo -e "\n[boot]" | tee -a "$WSL_CONF" > /dev/null
            fi

            # Add systemd=true
            echo "systemd=true" | tee -a "$WSL_CONF" > /dev/null

            echo "✅ Updated $WSL_CONF"
            echo ""
            echo "⚠️  Important: You must completely restart WSL for Systemd to take effect!"
            echo "   Execute in Windows PowerShell: wsl --shutdown"
            echo "   Then re-enter Ubuntu and run this script again."
            echo ""
            exit 1
        else
            echo "✅ WSL Systemd configuration already exists ($WSL_CONF)"
        fi
    fi

    echo ""
    install_docker_in_wsl
}

install_docker_in_wsl() {
    echo ""
    echo "📦 Docker in WSL (Direct Installation)"
    echo "========================================"
    echo ""

    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
        return
    fi

    echo "Installing Docker via apt..."

    # Add Docker GPG key
    echo "🔑 Adding Docker GPG key..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null || {
        echo "⚠️  Using alternative method..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    }

    # Add Docker repository
    echo "📋 Adding Docker repository..."
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null || {
        echo "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    }

    # Install Docker
    echo "📦 Installing Docker Engine..."
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Verify installation
    if command -v docker &> /dev/null; then
        echo "✅ Docker installed successfully: $(docker --version)"
    else
        echo "❌ Docker installation failed"
        exit 1
    fi

    # Set user permissions
    echo "🔐 Setting up user permissions..."
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in, or run: newgrp docker"
}

install_docker_wsl1() {
    echo ""
    echo "⚠️  WSL1 Detected"
    echo "========================================"
    echo ""
    echo "❌ Docker cannot run natively in WSL1."
    echo ""
    echo "Solutions:"
    echo "1. Upgrade to WSL2 (Recommended):"
    echo "   • Run: wsl --set-version <distro-name> 2"
    echo ""
    echo "2. Continue without installing Docker (local development only)"
    echo ""
    read -p "Choose option (1 or 2): " wsl1_choice

    case "$wsl1_choice" in
        1)
            echo "❌ WSL upgrade must be done from Windows PowerShell. Aborting."
            exit 1
            ;;
        2)
            echo "⏭️  Skipping Docker installation"
            return
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
}

install_docker_macos() {
    echo ""
    echo "🍎 Installing Docker for macOS"
    echo "========================================"
    echo ""

    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
        return
    fi

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is required. Install from: https://brew.sh"
        exit 1
    fi

    echo "📦 Installing Docker via Homebrew + colima..."
    echo ""

    echo "Installing Docker CLI with colima..."
    brew install docker colima

    # Start colima
    echo "🚀 Starting colima..."
    colima start || {
        echo "⚠️  Please start colima manually: colima start"
    }

    echo "✅ Docker installed via Homebrew + colima"
    echo "💡 Tip: Start colima before using Docker: colima start"
}

install_docker_linux() {
    local distro=$1

    echo ""
    echo "🐧 Installing Docker for Linux ($distro)"
    echo "========================================"
    echo ""

    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
        return
    fi

    case "$distro" in
        Ubuntu|Debian)
            install_docker_ubuntu_debian
            ;;
        Fedora|RHEL|CentOS)
            install_docker_fedora
            ;;
        Arch)
            install_docker_arch
            ;;
        *)
            echo "⚠️  Unsupported distribution: $distro"
            echo "Please refer to: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
}

install_docker_ubuntu_debian() {
    echo "📦 Installing Docker for Ubuntu/Debian..."

    # Add Docker GPG key
    echo "🔑 Adding Docker GPG key..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null || {
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    }

    # Add Docker repository
    echo "📋 Adding Docker repository..."
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null 2>&1 || {
        echo "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    }

    # Install
    echo "📦 Installing Docker packages..."
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Verify
    if command -v docker &> /dev/null; then
        echo "✅ Docker installed successfully: $(docker --version)"
    else
        echo "❌ Docker installation failed"
        exit 1
    fi

    # User permissions
    echo "🔐 Setting up user permissions..."
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in, or run: newgrp docker"
}

install_docker_fedora() {
    echo "📦 Installing Docker for Fedora/RHEL/CentOS..."

    sudo dnf install -y dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    if command -v docker &> /dev/null; then
        echo "✅ Docker installed successfully: $(docker --version)"
    else
        echo "❌ Docker installation failed"
        exit 1
    fi

    # Start service
    sudo systemctl start docker
    sudo systemctl enable docker

    # User permissions
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in, or run: newgrp docker"
}

install_docker_arch() {
    echo "📦 Installing Docker for Arch Linux..."

    sudo pacman -S docker docker-compose

    if command -v docker &> /dev/null; then
        echo "✅ Docker installed successfully: $(docker --version)"
    else
        echo "❌ Docker installation failed"
        exit 1
    fi

    # Start service
    sudo systemctl start docker
    sudo systemctl enable docker

    # User permissions
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in, or run: newgrp docker"
}

# ============================================================================
# Step 3: Install Docker Compose (if needed)
# ============================================================================

install_docker_compose() {
    echo ""
    echo "📦 Docker Compose Status"
    echo "========================================"

    # Check if Docker Compose v2 is available
    if docker compose version &> /dev/null; then
        echo "✅ Docker Compose v2 found: $(docker compose version --short)"
        return
    fi

    # Check for legacy docker-compose
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose (legacy) found: $(docker-compose --version)"
        return
    fi

    echo "⚠️  Docker Compose not found. Installing..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        brew install docker-compose
    else
        # For Linux systems, Docker Compose v2 comes with docker-compose-plugin
        echo "💡 Docker Compose v2 plugin already installed with docker-ce-cli"
        echo "   Use: docker compose (instead of docker-compose)"
    fi
}

# ============================================================================
# Step 4: Verification
# ============================================================================

verify_installation() {
    echo ""
    echo "✅ Verification"
    echo "========================================"
    echo ""

    # Check Docker
    if command -v docker &> /dev/null; then
        echo "✅ Docker: $(docker --version)"
    else
        echo "❌ Docker: Not found"
        return 1
    fi

    # Check Docker Compose
    if docker compose version &> /dev/null; then
        echo "✅ Docker Compose: $(docker compose version --short)"
    elif command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose (legacy): $(docker-compose --version)"
    else
        echo "⚠️  Docker Compose: Not found (may need manual installation)"
    fi

    # Try a test run
    echo ""
    echo "🧪 Running test: docker ps"
    if docker ps > /dev/null 2>&1; then
        echo "✅ Docker is working correctly!"
    else
        echo "⚠️  Docker test failed, running diagnostics..."
        echo ""

        # WSL2-specific diagnostics
        if grep -qi "microsoft" /proc/version 2>/dev/null && grep -qi "WSL2" /proc/version 2>/dev/null; then
            echo "📋 WSL2 Diagnostic Information:"
            echo ""

            # Check systemd
            if systemctl is-active systemd &> /dev/null || [ -d /run/systemd/system ]; then
                echo "  ✅ systemd: Enabled"
            else
                echo "  ❌ systemd: Not enabled (needs to be enabled)"
                echo "     Reference: Edit %USERPROFILE%\\.wslconfig, set systemd=true"
            fi

            # Check Docker daemon
            if sudo systemctl is-active docker &> /dev/null; then
                echo "  ✅ Docker daemon: Running"
            else
                echo "  ⚠️  Docker daemon: Not running"
                echo "     Try manually starting: sudo systemctl start docker"
            fi

            # Check user group
            if groups | grep -q docker; then
                echo "  ✅ docker user group: Configured"
            else
                echo "  ❌ docker user group: Not configured"
                echo "     Try: newgrp docker or sudo usermod -aG docker \$USER"
            fi

            echo ""
            echo "💡 Common WSL2 Docker Problem Solutions:"
            echo "   1. If systemd is not enabled, edit .wslconfig and restart WSL"
            echo "   2. Restart Docker daemon: sudo systemctl restart docker"
            echo "   3. Check Docker logs: sudo journalctl -u docker -n 50"
            echo "   4. Re-login to shell or run: newgrp docker"
        else
            echo "⚠️  Docker may need additional configuration (user permissions, daemon)"
            echo "   Try: newgrp docker or sudo systemctl restart docker"
        fi
    fi

    echo ""
    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

case "$ENVIRONMENT" in
    WSL2)
        install_docker_wsl2
        ;;
    WSL1)
        install_docker_wsl1
        ;;
    macOS)
        install_docker_macos
        ;;
    Linux-*)
        distro=$(echo $ENVIRONMENT | cut -d'-' -f2)
        install_docker_linux "$distro"
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Install Docker Compose
install_docker_compose

# Verify
verify_installation

echo ""
echo "🎉 Docker installation wizard completed!"
echo ""
echo "Next steps:"
echo "1. If you logged in as root or made permission changes, restart your terminal"
echo "2. Test with: docker run hello-world"
echo "3. For containerized deployment, run: docker-compose up -d"
echo ""
