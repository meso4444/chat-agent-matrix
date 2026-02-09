#!/bin/bash
# 安裝 Telegram → AI 遠端控制系統 (ngrok 版) 所需的依賴 - macOS 版

echo "🔧 正在安裝 macOS 系統依賴..."

# 檢查是否為 macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "⚠️  此腳本主要針對 macOS 設計"
    echo "   Linux 用戶請使用 install_dependencies.sh"
    read -p "是否繼續? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 檢查 Homebrew 是否已安裝
if ! command -v brew &> /dev/null; then
    echo "📦 正在安裝 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # 針對 Apple Silicon Mac 的額外設定
    if [[ $(uname -m) == 'arm64' ]]; then
        echo "🍎 檢測到 Apple Silicon (M1/M2/M3)，配置 Homebrew..."
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
fi

# 1. 安裝基礎工具
echo "📦 正在檢查並安裝基礎工具 (curl, wget, jq, tmux)..."
TOOLS="curl wget jq tmux"
for tool in $TOOLS; do
    if ! command -v $tool &> /dev/null; then
        echo "   安裝 $tool..."
        brew install $tool
    else
        echo "   ✅ $tool 已安裝"
    fi
done

# 2. 安裝 ngrok
echo ""
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok 已安裝: $(ngrok --version)"
else
    echo "📦 正在安裝 ngrok..."
    brew install ngrok

    if command -v ngrok &> /dev/null; then
        echo "✅ ngrok 安裝成功"
    else
        echo "❌ ngrok 安裝失敗，請參考官網手動安裝: https://ngrok.com/download"
        exit 1
    fi
fi

# 3. 安裝 Python 3 (如果未安裝)
echo ""
if ! command -v python3 &> /dev/null; then
    echo "📦 正在安裝 Python 3..."
    brew install python3
else
    echo "✅ Python 3 已安裝: $(python3 --version)"
fi

# 4. 安裝 Python 依賴
echo ""
echo "🐍 正在安裝 Python 依賴..."

# 檢查 pip3
if ! command -v pip3 &> /dev/null; then
    echo "📦 安裝 pip3..."
    python3 -m ensurepip --upgrade
fi

# 安裝套件
PACKAGES="flask requests pyyaml apscheduler"
echo "📦 安裝 Python 套件: $PACKAGES"
if pip3 install $PACKAGES; then
    echo "✅ Python 套件安裝成功"
else
    echo "⚠️  嘗試使用 --user 安裝..."
    pip3 install --user $PACKAGES
fi

# 5. 安裝 AI Agent CLI 工具
echo ""
echo "🤖 正在檢查與安裝 AI Agent CLI..."

# 5-1. 安裝 Node.js (如果需要)
if ! command -v npm &> /dev/null; then
    echo "📦 正在安裝 Node.js (Claude Code 需要)..."
    brew install node
else
    echo "✅ Node.js 已安裝: $(node --version)"
fi

# 5-2. 安裝 Claude Code
if ! command -v claude &> /dev/null; then
    if command -v npm &> /dev/null; then
        echo "📦 正在透過 npm 安裝 Claude Code..."
        npm install -g @anthropic-ai/claude-code || echo "⚠️  Claude Code 安裝失敗 (權限不足?)"
    else
        echo "❌ Node.js 未安裝，跳過 Claude Code 安裝"
    fi
else
    echo "✅ Claude Code 已安裝: $(claude --version 2>/dev/null || echo 'Detected')"
fi

# 5-3. 安裝 Gemini CLI
if ! command -v gemini &> /dev/null; then
    if command -v npm &> /dev/null; then
        echo "📦 正在透過 npm 安裝 Gemini CLI..."
        npm install -g @google/gemini-cli || echo "⚠️  Gemini CLI 安裝失敗 (權限不足?)"
    else
        echo "❌ Node.js 未安裝，跳過 Gemini CLI 安裝"
    fi
else
    echo "✅ Gemini CLI 已安裝: $(gemini --version 2>/dev/null || echo 'Detected')"
fi

# 6. 進入設定精靈
echo ""
echo "🚀 依賴安裝完成！正在啟動設定精靈..."
sleep 1

# 檢查設定腳本是否存在
if [ -f "./setup_config.sh" ]; then
    chmod +x ./setup_config.sh
    ./setup_config.sh
else
    echo "⚠️  找不到 setup_config.sh，請手動編輯 .env 檔案"
fi

# 7. 總結
echo ""
echo "📋 系統依賴檢查 (macOS):"
echo "   • Homebrew: $(brew --version 2>/dev/null | head -1)"
echo "   • tmux:     $(tmux -V 2>/dev/null || echo '未安裝')"
echo "   • jq:       $(jq --version 2>/dev/null || echo '未安裝')"
echo "   • ngrok:    $(ngrok --version 2>/dev/null || echo '未安裝')"
echo "   • Python:   $(python3 --version 2>/dev/null || echo '未安裝')"
echo "   • Node.js:  $(node --version 2>/dev/null || echo '未安裝')"
echo ""
echo "✅ macOS 環境準備完成！"
