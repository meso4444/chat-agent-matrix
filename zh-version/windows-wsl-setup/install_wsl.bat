@echo off
echo ========================================================
echo Chat Agent Nexus - Windows WSL Installer
echo ========================================================
echo.

echo [1/3] Checking WSL status...
wsl --status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ WSL is already installed.
) else (
    echo 📦 Installing WSL (Ubuntu)...
    echo This may take a few minutes. You might need to restart your PC.
    wsl --install -d Ubuntu
)

echo.
echo [2/3] Setting up environment...
echo Please open the "Ubuntu" app from your Start Menu to finish setup.
echo Once inside Ubuntu, run the following commands:
echo.
echo   git clone https://github.com/meso4444/chat-agent-matrix.git
echo   cd chat-agent-matrix/telegram
echo   ./install_dependencies.sh
echo.

echo [3/3] Done!
pause
