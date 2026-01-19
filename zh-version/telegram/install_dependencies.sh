#!/bin/bash
# 安裝 Telegram → AI 遠端控制系統 (ngrok 版) 所需的依賴

echo "🔧 正在安裝系統依賴..."

# 檢查是否為 Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "⚠️  此腳本主要針對 Linux 環境設計 (Ubuntu/Debian)"
    echo "   macOS 用戶請使用 brew install ngrok jq tmux"
    read -p "是否繼續? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 更新系統並安裝基礎工具
echo "📦 正在檢查並安裝基礎工具 (curl, wget, jq, tmux)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y curl wget jq tmux
elif command -v yum &> /dev/null; then
    sudo yum install -y curl wget jq tmux
else
    echo "⚠️  無法自動安裝基礎工具，請手動確認已安裝: curl, wget, jq, tmux"
fi

# 2. 安裝 ngrok
echo ""
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok 已安裝: $(ngrok --version)"
else
    echo "📦 正在安裝 ngrok..."
    # 官方安裝方式 (Linux)
    if command -v apt-get &> /dev/null; then
        echo "   (使用 apt 安裝)"
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt-get update
        sudo apt-get install -y ngrok
    else
        echo "   (使用直接下載方式)"
        wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin
        rm ngrok-v3-stable-linux-amd64.tgz
    fi
    
    if command -v ngrok &> /dev/null; then
        echo "✅ ngrok 安裝成功"
    else
        echo "❌ ngrok 安裝失敗，請參考官網手動安裝: https://ngrok.com/download"
        exit 1
    fi
fi

# 4. 安裝 Python 依賴
echo ""
echo "🐍 正在安裝 Python 依賴..."

# 檢查 pip3
if ! command -v pip3 &> /dev/null; then
    echo "📦 安裝 python3-pip..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    fi
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
    if command -v apt-get &> /dev/null; then
        # 安裝 Node.js 20.x LTS
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "⚠️  無法自動安裝 Node.js，請手動安裝後重試。"
    fi
fi

# 5-2. 安裝 Claude Code
if ! command -v claude &> /dev/null; then
    if command -v npm &> /dev/null; then
        echo "📦 正在透過 npm 安裝 Claude Code..."
        # 嘗試全域安裝
        sudo npm install -g @anthropic-ai/claude-code || echo "⚠️  Claude Code 安裝失敗 (權限不足?)"
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
        # 嘗試全域安裝
        sudo npm install -g @google/gemini-cli || echo "⚠️  Gemini CLI 安裝失敗 (權限不足?)"
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

# 6. 總結 (此部分已被 setup_config.sh 取代，可簡化)
echo "📋 系統依賴檢查:"
echo "   • tmux:   $(tmux -V 2>/dev/null || echo '未安裝')"
echo "   • jq:     $(jq --version 2>/dev/null || echo '未安裝')"
echo "   • ngrok:  $(ngrok --version 2>/dev/null || echo '未安裝')"
echo "   • Python: $(python3 --version 2>/dev/null || echo '未安裝')"
echo ""
