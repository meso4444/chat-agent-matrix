#!/bin/bash
# Gmail 郵件監聽系統 - 依賴安裝腳本

echo "=========================================="
echo "Gmail 郵件監聽系統 - 依賴安裝"
echo "=========================================="
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：找不到 Python 3"
    echo "請先安裝 Python 3"
    exit 1
fi

echo "✅ 檢測到 Python 3："
python3 --version
echo ""

# 安裝依賴
echo "📦 安裝依賴包..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 安裝完成！"
    echo "=========================================="
    echo ""
    echo "下一步："
    echo "1. 將 credentials.json 複製到此目錄"
    echo "2. 編輯 whitelist.json 配置"
    echo "3. 運行認證：python3 gmail_auth_simple.py"
    echo "4. 啟動監聽：python3 gmail_listener.py"
    echo ""
else
    echo ""
    echo "❌ 安裝失敗"
    echo "請檢查網絡連接或重試"
    exit 1
fi
