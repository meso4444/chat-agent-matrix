#!/bin/bash
# disable_systemd_telegram.sh
# 移除 Telegram 版的 Systemd 開機自啟設定

SERVICE_NAME="chat-agent-matrix-telegram"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# 檢查 root 權限
if [ "$EUID" -ne 0 ]; then
  echo "❌ 請使用 sudo 執行此腳本"
  echo "   範例: sudo ./auto-startup/disable_systemd_telegram.sh"
  exit 1
fi

echo "🛑 正在移除 Systemd 服務: $SERVICE_NAME"

# 1. 停止並停用服務
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "   停止服務..."
    systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo "   停用開機自啟..."
    systemctl disable $SERVICE_NAME
fi

# 2. 刪除設定檔
if [ -f "$SERVICE_FILE" ]; then
    echo "   刪除設定檔: $SERVICE_FILE"
    rm "$SERVICE_FILE"
    systemctl daemon-reload
    echo "✅ 服務已完全移除"
else
    echo "⚠️  設定檔不存在，可能已經移除"
fi

echo ""
echo "💡 若要重新啟用，請執行 install_systemd_telegram.sh"
