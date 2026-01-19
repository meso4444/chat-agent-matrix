#!/bin/bash
# setup_systemd.sh
# Automatically register Chat Agent Matrix as Systemd service to enable auto-startup on boot

# 1. Prepare paths and variables
# Point to telegram project directory
SCRIPT_DIR="$(cd "$(dirname "$0")/../telegram" && pwd)"
START_SCRIPT="$SCRIPT_DIR/start_all_services.sh"
STOP_SCRIPT="$SCRIPT_DIR/stop_telegram_services.sh"
SERVICE_NAME="chat-agent-matrix-telegram"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Detect real user (avoid becoming root when sudo is executed)
REAL_USER=${SUDO_USER:-$(whoami)}
USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

# Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script with sudo (because it needs to write to /etc/systemd/system)"
  echo "   Example: sudo ./auto-startup/install_systemd_telegram.sh"
  exit 1
fi

echo "🔧 Configuring Systemd service..."
echo "   - Service name: $SERVICE_NAME"
echo "   - Run as user: $REAL_USER"
  echo "   - Start script: $START_SCRIPT"

# 2. Create Service file
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Chat Agent Matrix - AI Remote Commander
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$START_SCRIPT
ExecStop=$STOP_SCRIPT
Restart=always
RestartSec=10
RemainAfterExit=yes
Environment="HOME=$USER_HOME"
Environment="PATH=$PATH"
Environment="TERM=xterm-256color"

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: $SERVICE_FILE"

# 3. Enable service
echo "🔄 Enabling service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# 4. Check WSL Systemd support
if grep -qi "Microsoft" /proc/version; then
    echo "🔍 WSL environment detected, checking systemd configuration..."
    WSL_CONF="/etc/wsl.conf"

    # Check if file exists, create if not
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
        echo "⚠️  Important notice: You must fully restart WSL for Systemd to take effect!"
        echo "   Please run in Windows PowerShell: wsl --shutdown"
        echo "   Then re-enter Ubuntu."
    else
        echo "✅ WSL Systemd configuration already exists ($WSL_CONF)"
    fi
fi

echo "✅ Auto-startup has been enabled!"
echo ""
echo "👉 You can now use the following commands to manage the service:"
echo "   sudo systemctl start chat-agent-matrix-telegram"
echo "   sudo systemctl stop chat-agent-matrix-telegram"
echo "   sudo systemctl status chat-agent-matrix-telegram"
echo ""
echo "📝 Next steps (Windows users):"
echo "   Please run ./auto-startup/setup_windows_scheduler.sh to configure host machine wake-up scheduling."
