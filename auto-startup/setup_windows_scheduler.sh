#!/bin/bash
# Call Windows PowerShell from Linux (WSL) to configure Task Scheduler
# Use intermediary .bat strategy to ensure stability and resolve UNC path parameter passing issues

echo "🔧 Calling Windows PowerShell to configure auto-startup..."

# Get script directory (resolves path errors when executing from root directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Get Windows path for setup_autostart.ps1
PS1_PATH=$(wslpath -w "$SCRIPT_DIR/setup_autostart.ps1")

# 2. Generate a temporary .bat launcher
# This is to make parameter passing in Start-Process simpler and ensure window pause
LAUNCHER="run_setup_tmp.bat"
# Ensure .bat is generated in script directory
LAUNCHER_PATH="$SCRIPT_DIR/$LAUNCHER"

cat > "$LAUNCHER_PATH" <<EOF
@echo off
title Chat Agent Matrix - Setup
echo Starting PowerShell Setup Script...
echo Script: "$PS1_PATH"
echo.

:: Call PowerShell to execute .ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_PATH"

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Script execution failed.
    echo Please check the error message above.
) else (
    echo [SUCCESS] Script finished.
)
echo.
pause
del "%~f0" &:: Self-destruct
EOF

# ⚠️ Critical fix: Convert .bat to Windows CRLF format
# Otherwise CMD will parse incorrectly causing garbled text
sed -i 's/$/\r/' "$LAUNCHER_PATH"

# 3. Get Windows path for .bat
BAT_PATH=$(wslpath -w "$LAUNCHER_PATH")

echo "📍 Launcher path: $BAT_PATH"

# 4. Trigger Windows UAC and execute .bat
# Use cmd /c to execute .bat, this is most stable
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
    "Start-Process cmd -Verb RunAs -ArgumentList '/c \"$BAT_PATH\"'"

echo ""
echo "✅ Request has been sent!"
echo "👉 Please check the black CMD window that pops up, it will automatically call PowerShell."
