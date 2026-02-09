#!/bin/bash
# install_docker_zh.sh - 智能 Docker & Docker Compose 安装腳本
# 自動偵測環境（WSL/macOS/Linux）並應用最適當的安裝方法

set -e

echo "🐳 Docker 安裝精靈"
echo "========================================"
echo ""

# ============================================================================
# 第 1 步：偵測環境
# ============================================================================

detect_environment() {
    local os_type=$(uname -s)
    local uname_release=$(uname -r)

    # 檢查 WSL
    if grep -qi "microsoft" /proc/version 2>/dev/null; then
        # 偵測 WSL 版本
        if grep -qi "WSL2" /proc/version 2>/dev/null; then
            echo "WSL2"
        else
            echo "WSL1"
        fi
    # 檢查 macOS
    elif [[ "$os_type" == "Darwin" ]]; then
        echo "macOS"
    # 檢查 Linux
    elif [[ "$os_type" == "Linux" ]]; then
        # 偵測 Linux 發行版
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

echo "✅ 偵測到的環境：$ENVIRONMENT"
echo ""

# ============================================================================
# 第 2 步：環境特定安裝
# ============================================================================

install_docker_wsl2() {
    echo "🔧 為 WSL2 安裝 Docker (in WSL)..."
    echo ""

    # ===== WSL2 Systemd 自動啟用 =====
    if grep -qi "Microsoft" /proc/version; then
        echo "🔍 檢測到 WSL 環境，正在檢查 systemd 設定..."
        WSL_CONF="/etc/wsl.conf"

        # 檢查檔案是否存在，若無則建立
        if [ ! -f "$WSL_CONF" ]; then
            echo "   建立新的 $WSL_CONF..."
            touch "$WSL_CONF"
        fi

        # 檢查是否已設定 systemd=true
        if ! grep -q "systemd=true" "$WSL_CONF"; then
            echo "🔧 正在啟用 WSL Systemd 支援..."

            # 確保 [boot] 區塊存在
            if ! grep -q "\[boot\]" "$WSL_CONF"; then
                echo -e "\n[boot]" | tee -a "$WSL_CONF" > /dev/null
            fi

            # 加入 systemd=true
            echo "systemd=true" | tee -a "$WSL_CONF" > /dev/null

            echo "✅ 已更新 $WSL_CONF"
            echo ""
            echo "⚠️  重要提示：您必須完全重啟 WSL 才能使 Systemd 生效！"
            echo "   請在 Windows PowerShell 執行: wsl --shutdown"
            echo "   然後重新進入 Ubuntu 並執行此腳本。"
            echo ""
            exit 1
        else
            echo "✅ WSL Systemd 設定已存在 ($WSL_CONF)"
        fi
    fi

    echo ""
    install_docker_in_wsl
}

install_docker_in_wsl() {
    echo ""
    echo "📦 WSL 中的 Docker (直接安裝)"
    echo "========================================"
    echo ""

    # 檢查 Docker 是否已安裝
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安裝：$(docker --version)"
        return
    fi

    echo "正在透過 apt 安裝 Docker..."

    # 新增 Docker GPG 鑰匙
    echo "🔑 正在新增 Docker GPG 鑰匙..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null || {
        echo "⚠️  使用替代方式..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    }

    # 新增 Docker 儲存庫
    echo "📋 正在新增 Docker 儲存庫..."
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null || {
        echo "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    }

    # 安裝 Docker
    echo "📦 正在安裝 Docker Engine..."
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 驗證安裝
    if command -v docker &> /dev/null; then
        echo "✅ Docker 安裝成功：$(docker --version)"
    else
        echo "❌ Docker 安裝失敗"
        exit 1
    fi

    # 設定使用者權限
    echo "🔐 正在設定使用者權限..."
    sudo usermod -aG docker $USER
    echo "⚠️  請登出並重新登入，或執行：newgrp docker"
}

install_docker_wsl1() {
    echo ""
    echo "⚠️  偵測到 WSL1"
    echo "========================================"
    echo ""
    echo "❌ Docker 無法在 WSL1 中原生執行。"
    echo ""
    echo "解決方案："
    echo "1. 升級到 WSL2 (推薦)："
    echo "   • 執行：wsl --set-version <distro-name> 2"
    echo ""
    echo "2. 繼續不安裝 Docker (僅本機開發)"
    echo ""
    read -p "選擇選項 (1 或 2)：" wsl1_choice

    case "$wsl1_choice" in
        1)
            echo "❌ WSL 升級必須從 Windows PowerShell 執行。正在中止。"
            exit 1
            ;;
        2)
            echo "⏭️  跳過 Docker 安裝"
            return
            ;;
        *)
            echo "無效選擇"
            exit 1
            ;;
    esac
}

install_docker_macos() {
    echo ""
    echo "🍎 為 macOS 安裝 Docker"
    echo "========================================"
    echo ""

    # 檢查 Docker 是否已安裝
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安裝：$(docker --version)"
        return
    fi

    # 檢查 Homebrew 是否已安裝
    if ! command -v brew &> /dev/null; then
        echo "❌ 需要 Homebrew。從以下位置安裝：https://brew.sh"
        exit 1
    fi

    echo "📦 正在透過 Homebrew + colima 安裝 Docker..."
    echo ""

    echo "正在安裝 Docker CLI with colima..."
    brew install docker colima

    # 啟動 colima
    echo "🚀 正在啟動 colima..."
    colima start || {
        echo "⚠️  請手動啟動 colima：colima start"
    }

    echo "✅ 已透過 Homebrew + colima 安裝 Docker"
    echo "💡 提示：使用 Docker 前請先啟動 colima：colima start"
}

install_docker_linux() {
    local distro=$1

    echo ""
    echo "🐧 為 Linux ($distro) 安裝 Docker"
    echo "========================================"
    echo ""

    # 檢查 Docker 是否已安裝
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安裝：$(docker --version)"
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
            echo "⚠️  不支援的發行版：$distro"
            echo "請參考：https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
}

install_docker_ubuntu_debian() {
    echo "📦 為 Ubuntu/Debian 安裝 Docker..."

    # 新增 Docker GPG 鑰匙
    echo "🔑 正在新增 Docker GPG 鑰匙..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null || {
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    }

    # 新增 Docker 儲存庫
    echo "📋 正在新增 Docker 儲存庫..."
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null 2>&1 || {
        echo "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    }

    # 安裝
    echo "📦 正在安裝 Docker 套件..."
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 驗證
    if command -v docker &> /dev/null; then
        echo "✅ Docker 安裝成功：$(docker --version)"
    else
        echo "❌ Docker 安裝失敗"
        exit 1
    fi

    # 使用者權限
    echo "🔐 正在設定使用者權限..."
    sudo usermod -aG docker $USER
    echo "⚠️  請登出並重新登入，或執行：newgrp docker"
}

install_docker_fedora() {
    echo "📦 為 Fedora/RHEL/CentOS 安裝 Docker..."

    sudo dnf install -y dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    if command -v docker &> /dev/null; then
        echo "✅ Docker 安裝成功：$(docker --version)"
    else
        echo "❌ Docker 安裝失敗"
        exit 1
    fi

    # 啟動服務
    sudo systemctl start docker
    sudo systemctl enable docker

    # 使用者權限
    sudo usermod -aG docker $USER
    echo "⚠️  請登出並重新登入，或執行：newgrp docker"
}

install_docker_arch() {
    echo "📦 為 Arch Linux 安裝 Docker..."

    sudo pacman -S docker docker-compose

    if command -v docker &> /dev/null; then
        echo "✅ Docker 安裝成功：$(docker --version)"
    else
        echo "❌ Docker 安裝失敗"
        exit 1
    fi

    # 啟動服務
    sudo systemctl start docker
    sudo systemctl enable docker

    # 使用者權限
    sudo usermod -aG docker $USER
    echo "⚠️  請登出並重新登入，或執行：newgrp docker"
}

# ============================================================================
# 第 3 步：安裝 Docker Compose (如需要)
# ============================================================================

install_docker_compose() {
    echo ""
    echo "📦 Docker Compose 狀態"
    echo "========================================"

    # 檢查 Docker Compose v2 是否可用
    if docker compose version &> /dev/null; then
        echo "✅ 找到 Docker Compose v2：$(docker compose version --short)"
        return
    fi

    # 檢查舊版 docker-compose
    if command -v docker-compose &> /dev/null; then
        echo "✅ 找到 Docker Compose (舊版)：$(docker-compose --version)"
        return
    fi

    echo "⚠️  找不到 Docker Compose。正在安裝..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        brew install docker-compose
    else
        # 對於 Linux 系統，Docker Compose v2 隨 docker-compose-plugin 提供
        echo "💡 Docker Compose v2 外掛已隨 docker-ce-cli 安裝"
        echo "   使用：docker compose (而不是 docker-compose)"
    fi
}

# ============================================================================
# 第 4 步：驗證
# ============================================================================

verify_installation() {
    echo ""
    echo "✅ 驗證"
    echo "========================================"
    echo ""

    # 檢查 Docker
    if command -v docker &> /dev/null; then
        echo "✅ Docker：$(docker --version)"
    else
        echo "❌ Docker：未找到"
        return 1
    fi

    # 檢查 Docker Compose
    if docker compose version &> /dev/null; then
        echo "✅ Docker Compose：$(docker compose version --short)"
    elif command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose (舊版)：$(docker-compose --version)"
    else
        echo "⚠️  Docker Compose：未找到 (可能需要手動安裝)"
    fi

    # 嘗試測試執行
    echo ""
    echo "🧪 執行測試：docker ps"
    if docker ps > /dev/null 2>&1; then
        echo "✅ Docker 正常運作！"
    else
        echo "⚠️  Docker 測試失敗，進行診斷..."
        echo ""

        # WSL2 特定診斷
        if grep -qi "microsoft" /proc/version 2>/dev/null && grep -qi "WSL2" /proc/version 2>/dev/null; then
            echo "📋 WSL2 診斷資訊："
            echo ""

            # 檢查 systemd
            if systemctl is-active systemd &> /dev/null || [ -d /run/systemd/system ]; then
                echo "  ✅ systemd：已啟用"
            else
                echo "  ❌ systemd：未啟用 (需要啟用)"
                echo "     參考：編輯 %USERPROFILE%\\.wslconfig，設置 systemd=true"
            fi

            # 檢查 Docker daemon
            if sudo systemctl is-active docker &> /dev/null; then
                echo "  ✅ Docker daemon：運行中"
            else
                echo "  ⚠️  Docker daemon：未運行"
                echo "     嘗試手動啟動：sudo systemctl start docker"
            fi

            # 檢查使用者組
            if groups | grep -q docker; then
                echo "  ✅ docker 使用者組：已設置"
            else
                echo "  ❌ docker 使用者組：未設置"
                echo "     嘗試：newgrp docker 或 sudo usermod -aG docker \$USER"
            fi

            echo ""
            echo "💡 常見 WSL2 Docker 問題解決方案："
            echo "   1. 如果 systemd 未啟用，請編輯 .wslconfig 並重啟 WSL"
            echo "   2. 重啟 Docker daemon：sudo systemctl restart docker"
            echo "   3. 檢查 Docker 日誌：sudo journalctl -u docker -n 50"
            echo "   4. 重新登入 Shell 或執行：newgrp docker"
        else
            echo "⚠️  Docker 可能需要額外設定 (使用者權限、守護程序)"
            echo "   嘗試：newgrp docker 或 sudo systemctl restart docker"
        fi
    fi

    echo ""
    return 0
}

# ============================================================================
# 主要執行
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
        echo "❌ 未知環境：$ENVIRONMENT"
        exit 1
        ;;
esac

# 安裝 Docker Compose
install_docker_compose

# 驗證
verify_installation

echo ""
echo "🎉 Docker 安裝精靈已完成！"
echo ""
echo "下一步："
echo "1. 如果您以 root 身份登入或做了權限變更，請重啟終端機"
echo "2. 透過以下指令測試：docker run hello-world"
echo "3. 進行容器化部署，執行：docker-compose up -d"
echo ""
