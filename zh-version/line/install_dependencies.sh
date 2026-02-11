#!/bin/bash
# 安裝 LINE → AI 遠端控制系統 (Cloudflare Tunnel 版) 所需的依賴
# 自動偵測環境 (WSL/Linux/macOS) 並應用適當的安裝方法

set -e

echo "🔧 正在檢查系統環境..."

# ============================================================================
# 步驟 1: 環境偵測
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
        echo "Linux"
    else
        echo "Unknown"
    fi
}

ENVIRONMENT=$(detect_environment)
echo "✅ 偵測到的環境: $ENVIRONMENT"
echo ""

# ============================================================================
# 步驟 2: 環境特定的依賴安裝
# ============================================================================

# ===== Homebrew 檢查 (僅 macOS) =====
install_homebrew_if_needed() {
    if [[ "$ENVIRONMENT" != "macOS" ]]; then
        return
    fi

    if ! command -v brew &> /dev/null; then
        echo "📦 正在安裝 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # 針對 Apple Silicon Mac 的額外配置
        if [[ $(uname -m) == 'arm64' ]]; then
            echo "🍎 偵測到 Apple Silicon (M1/M2/M3)，配置 Homebrew..."
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        echo "✅ Homebrew 已安裝"
    fi
}

# ===== 基礎工具安裝 (僅 tmux，LINE 版本) =====
install_basic_tools() {
    echo "📦 正在檢查並安裝基礎工具 (tmux)..."

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: 使用 brew
        if ! command -v tmux &> /dev/null; then
            echo "   正在安裝 tmux..."
            brew install tmux
        else
            echo "   ✅ tmux 已安裝"
        fi
    else
        # Linux/WSL: 使用 apt-get 或 yum
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y tmux
        elif command -v yum &> /dev/null; then
            sudo yum install -y tmux
        else
            echo "⚠️  無法自動安裝 tmux，請手動確認已安裝: tmux"
        fi
    fi
}

# ===== Python 3 安裝 (macOS 可能需要) =====
install_python3_if_needed() {
    if command -v python3 &> /dev/null; then
        echo "✅ Python 3 已安裝: $(python3 --version)"
        return
    fi

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        echo "📦 正在安裝 Python 3..."
        brew install python3
    elif [[ "$ENVIRONMENT" == "Linux" || "$ENVIRONMENT" == "WSL2" || "$ENVIRONMENT" == "WSL1" ]]; then
        echo "📦 正在安裝 Python 3..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y python3 python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        fi
    fi
}

# ===== Python 套件安裝 =====
install_python_packages() {
    echo ""
    echo "🐍 正在安裝 Python 依賴..."

    # 檢查 pip3
    if ! command -v pip3 &> /dev/null; then
        echo "📦 正在安裝 pip3..."
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

    # 安裝套件 (LINE 特定: 無需 apscheduler)
    PACKAGES="flask requests pyyaml"
    echo "📦 正在安裝 Python 套件: $PACKAGES"
    if pip3 install $PACKAGES; then
        echo "✅ Python 套件安裝成功"
    else
        echo "⚠️  嘗試使用 --user 安裝..."
        pip3 install --user $PACKAGES
    fi
}

# ===== Cloudflare Tunnel 安裝 =====
install_cloudflared() {
    echo ""
    echo "📦 正在安裝 Cloudflare Tunnel (cloudflared)..."

    if command -v cloudflared &> /dev/null; then
        echo "✅ cloudflared 已安裝: $(cloudflared --version 2>&1 | head -1)"
        return
    fi

    local cloudflared_url=""
    local install_method=""

    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        # macOS: 使用 Homebrew (自動處理 Intel 和 Apple Silicon)
        if command -v brew &> /dev/null; then
            echo "   (使用 brew 安裝)"
            brew install cloudflare/cloudflare/cloudflared
            install_method="brew"
        else
            echo "⚠️  找不到 Homebrew，請手動安裝: https://github.com/cloudflare/cloudflared/releases"
            return
        fi
    elif [[ "$ENVIRONMENT" == "WSL2" || "$ENVIRONMENT" == "WSL1" || "$ENVIRONMENT" == "Linux" ]]; then
        # Linux/WSL: 直接下載二進制
        local arch=$(uname -m)
        case "$arch" in
            x86_64)
                cloudflared_url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
                ;;
            aarch64|arm64)
                cloudflared_url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
                ;;
            *)
                echo "⚠️  不支援的架構: $arch，請手動安裝 cloudflared"
                return
                ;;
        esac

        if [[ -z "$cloudflared_url" ]]; then
            echo "⚠️  無法確定架構下載 URL: $arch"
            return
        fi

        if command -v curl &> /dev/null; then
            echo "   (使用直接下載方式，架構: $arch)"
            curl -L "$cloudflared_url" -o cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            install_method="download"
        elif command -v wget &> /dev/null; then
            echo "   (使用 wget 下載方式，架構: $arch)"
            wget "$cloudflared_url" -O cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            install_method="wget"
        else
            echo "⚠️  找不到 curl 或 wget，請手動下載: $cloudflared_url"
            return
        fi
    fi

    if command -v cloudflared &> /dev/null; then
        echo "✅ cloudflared 安裝成功 (方式: $install_method)"
    else
        echo "⚠️  cloudflared 安裝可能失敗，請驗證: cloudflared --version"
    fi
}

# ===== 摘要 =====
print_summary() {
    echo ""
    echo "📋 系統依賴檢查 ($ENVIRONMENT):"
    echo "   • 環境: $ENVIRONMENT"
    if [[ "$ENVIRONMENT" == "macOS" ]]; then
        echo "   • Homebrew:  $(brew --version 2>/dev/null | head -1 || echo '未安裝')"
    fi
    echo "   • tmux:      $(tmux -V 2>/dev/null || echo '未安裝')"
    echo "   • Python:    $(python3 --version 2>/dev/null || echo '未安裝')"
    echo "   • Flask:     $(python3 -c 'import flask; print(f"Flask {flask.__version__}")' 2>/dev/null || echo '未安裝')"
    echo "   • cloudflared: $(cloudflared --version 2>&1 | head -1 || echo '未安裝')"
    echo ""
    echo "✅ 核心依賴安裝完成！"
    echo ""
}

# ===== 下一步 =====
print_next_steps() {
    echo "📋 接下來執行的步驟："
    echo "1. 在 config.py 中填入 CHANNEL_SECRET (如尚未填入)"
    echo "2. 在 config.py 中更新 CLOUDFLARE_CUSTOM_DOMAIN 為您的網域名稱"
    echo "3. 設定 Cloudflare 固定 URL: ./setup_cloudflare_fixed_url.sh"
    echo "4. 在 LINE Console 中設定 Webhook URL (先勿驗證)"
    echo "5. 啟動所有服務: ./start_all_services.sh"
    echo "6. 在 LINE Console 中驗證 Webhook 連接"
    echo ""
    echo "💡 重要提醒："
    echo "• 需要擁有網域名稱並在 Cloudflare 上託管"
    echo "• Webhook 驗證必須在服務啟動後進行"
    echo "• 詳細設定請參考 SETUP_GUIDE.md"
    echo "• tmux 操作說明請參考 TMUX_GUIDE.md"
    echo ""
}

# ============================================================================
# 主執行流程
# ============================================================================

# 檢查未知環境
if [[ "$ENVIRONMENT" == "Unknown" ]]; then
    echo "❌ 無法辨識的作業系統"
    exit 1
fi

# WSL1 警告
if [[ "$ENVIRONMENT" == "WSL1" ]]; then
    echo "⚠️  偵測到 WSL1，某些功能可能受限。"
    echo "   建議升級至 WSL2: wsl --set-version <distro-name> 2"
    read -p "是否繼續? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 執行安裝步驟
install_homebrew_if_needed
install_basic_tools
install_python3_if_needed
install_python_packages
install_cloudflared
print_summary
print_next_steps

echo "🚀 設定準備完成！已準備好設定 LINE 整合。"
echo ""
