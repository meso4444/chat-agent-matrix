#!/bin/bash
# disable_systemd_line.sh
# Remove LINE version Systemd auto-startup configuration

SERVICE_NAME="chat-agent-matrix-line"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script with sudo"
  echo "   Example: sudo ./auto-startup/disable_systemd_line.sh"
  exit 1
fi

echo "🛑 Removing Systemd service: $SERVICE_NAME"

# 1. Stop and disable service
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "   Stopping service..."
    systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo "   Disabling auto-startup..."
    systemctl disable $SERVICE_NAME
fi

# 2. Delete configuration file
if [ -f "$SERVICE_FILE" ]; then
    echo "   Deleting configuration file: $SERVICE_FILE"
    rm "$SERVICE_FILE"
    systemctl daemon-reload
    echo "✅ Service completely removed"
else
    echo "⚠️  Configuration file does not exist, may have already been removed"
fi

echo ""
echo "💡 To re-enable, please run install_systemd_line.sh"
