#!/bin/bash
# 安裝 tmux Claude session 遠端控制功能所需的系統依賴

echo "🔧 安裝 tmux Claude session 遠端控制依賴..."

# 檢查並安裝 tmux
if ! command -v tmux &> /dev/null; then
    echo "📦 安裝 tmux..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tmux
    elif command -v yum &> /dev/null; then
        sudo yum install -y tmux
    elif command -v brew &> /dev/null; then
        brew install tmux
    else
        echo "❌ 無法自動安裝 tmux，請手動安裝"
        exit 1
    fi
    echo "✅ tmux 安裝完成"
else
    echo "✅ tmux 已安裝"
fi

# 檢查並安裝 Python 依賴
echo "📦 安裝 Python 依賴..."

# 檢查 Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，正在嘗試安裝..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "❌ 無法自動安裝 Python3，請手動安裝"
        echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "macOS: brew install python3"
        exit 1
    fi
    echo "✅ Python3 安裝完成"
else
    echo "✅ Python3 已安裝"
fi

# 檢查 pip3
if ! command -v pip3 &> /dev/null; then
    echo "🔧 嘗試安裝 pip3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    else
        echo "❌ pip3 未安裝，正在嘗試使用 ensurepip..."
        if python3 -m ensurepip --default-pip 2>/dev/null; then
            echo "✅ pip3 透過 ensurepip 安裝完成"
        else
            echo "❌ 無法安裝 pip3，請手動安裝"
            echo "Ubuntu/Debian: sudo apt-get install python3-pip"
            echo "CentOS/RHEL: sudo yum install python3-pip"
            echo "或使用: python3 -m ensurepip --default-pip"
            exit 1
        fi
    fi
fi

echo "✅ pip3 檢查完成"

# 安裝 Flask 和相關依賴
echo "📦 正在安裝 Python 套件..."
if pip3 install flask PyYAML requests; then
    echo "✅ Python 套件安裝成功"
else
    echo "❌ Python 套件安裝失敗，嘗試使用 --user 參數..."
    if pip3 install --user flask PyYAML requests; then
        echo "✅ Python 套件安裝成功 (使用 --user)"
    else
        echo "❌ Python 套件安裝失敗，請檢查網路連線或手動安裝"
        echo "手動安裝指令: pip3 install flask PyYAML requests"
        exit 1
    fi
fi

echo "✅ Python 依賴安裝完成"

# 檢查安裝結果
echo ""
echo "📋 系統資訊確認:"
echo "• tmux 版本: $(tmux -V 2>/dev/null || echo "未安裝")"
echo "• Python 版本: $(python3 --version 2>/dev/null || echo "未安裝")"
echo "• pip3 版本: $(pip3 --version 2>/dev/null | cut -d' ' -f1-2 || echo "未安裝")"
echo "• Flask 版本: $(python3 -c 'import flask; print(f"Flask {flask.__version__}")' 2>/dev/null || echo "未安裝")"
echo "• requests 版本: $(python3 -c 'import requests; print(f"requests {requests.__version__}")' 2>/dev/null || echo "未安裝")"
echo "• PyYAML 版本: $(python3 -c 'import yaml; print("PyYAML 已安裝")' 2>/dev/null || echo "未安裝")"

# 詢問是否安裝 Cloudflare Tunnel
echo ""
read -p "是否安裝 Cloudflare Tunnel (cloudflared)? (y/N): " install_cloudflared
case $install_cloudflared in
    [Yy]*)
        echo "📦 安裝 Cloudflare Tunnel..."
        if command -v curl &> /dev/null; then
            echo "下載 cloudflared..."
            curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
            echo "✅ cloudflared 安裝完成"
        else
            echo "⚠️ 請手動安裝 cloudflared: https://github.com/cloudflare/cloudflared/releases"
        fi
        ;;
    *)
        echo "⏭️ 跳過 Cloudflare Tunnel 安裝"
        ;;
esac

echo ""
echo "🎉 所有依賴安裝完成！"
echo ""
echo "📋 接下來請依序執行:"
echo "1. 填入 config.py 中的 CHANNEL_SECRET (如果尚未填入)"
echo "2. 更新 config.py 中的 CLOUDFLARE_CUSTOM_DOMAIN 為你的域名"
echo "3. 設定 Cloudflare 固定 URL: ./setup_cloudflare_fixed_url.sh"
echo "4. 設定 LINE Webhook URL (先不要驗證)"
echo "5. 啟動所有服務: ./start_all_services.sh"
echo "6. 在 LINE Console 驗證 Webhook 連線"
echo ""
echo "💡 重要提醒:"
echo "• 需要擁有域名並託管在 Cloudflare"
echo "• Webhook 驗證必須在服務啟動後進行"
echo "• 詳細設定請參考 SETUP_GUIDE.md"
echo "• tmux 操作說明請參考 TMUX_GUIDE.md"
echo ""
echo "🔧 服務管理命令:"
echo "• 啟動所有服務: ./start_all_services.sh"
echo "• 檢查服務狀態: ./status_all_services.sh"
echo "• 停止所有服務: ./stop_all_services.sh"
echo ""
echo "💡 優勢:"
echo "• 使用 tmux 統一管理所有服務"
echo "• 單一命令啟動/停止整個系統"
echo "• 服務在背景持續運行"
echo "• 詳細設定請參考 README.md"