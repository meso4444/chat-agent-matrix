#!/bin/bash
# 在 Linux (WSL) 端呼叫 Windows PowerShell 來設定工作排程器
# 使用中間人 .bat 策略以確保穩定性並解決 UNC 路徑參數傳遞問題

echo "🔧 正在呼叫 Windows PowerShell 設定開機自啟..."

# 獲取腳本所在目錄 (解決從根目錄執行時的路徑錯誤)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. 取得 setup_autostart.ps1 的 Windows 路徑
PS1_PATH=$(wslpath -w "$SCRIPT_DIR/setup_autostart.ps1")

# 2. 產生一個臨時的 .bat 啟動器
# 這是為了讓 Start-Process 的參數傳遞更簡單，且能確保視窗暫停
LAUNCHER="run_setup_tmp.bat"
# 確保 .bat 產生在腳本目錄下
LAUNCHER_PATH="$SCRIPT_DIR/$LAUNCHER"

cat > "$LAUNCHER_PATH" <<EOF
@echo off
title Chat Agent Matrix - Setup
echo Starting PowerShell Setup Script...
echo Script: "$PS1_PATH"
echo.

:: 呼叫 PowerShell 執行 .ps1
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
del "%~f0" &:: 自毀
EOF

# ⚠️ 關鍵修正：將 .bat 轉換為 Windows CRLF 格式
# 否則 CMD 會解析錯誤導致亂碼
sed -i 's/$/\r/' "$LAUNCHER_PATH"

# 3. 取得 .bat 的 Windows 路徑
BAT_PATH=$(wslpath -w "$LAUNCHER_PATH")

echo "📍 啟動器路徑: $BAT_PATH"

# 4. 觸發 Windows UAC 並執行 .bat
# 使用 cmd /c 來執行 .bat，這樣最穩
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
    "Start-Process cmd -Verb RunAs -ArgumentList '/c \"$BAT_PATH\"'"

echo ""
echo "✅ 請求已送出！"
echo "👉 請查看跳出的黑色 CMD 視窗，它會自動呼叫 PowerShell。"