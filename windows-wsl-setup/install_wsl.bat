@echo off
REM Chat Agent Matrix - Windows WSL Installer
REM This script detects and installs WSL2 with Ubuntu distribution

setlocal enabledelayedexpansion

echo ========================================================
echo Chat Agent Matrix - Windows WSL Installer
echo ========================================================
echo.

echo [1/3] Checking WSL status...
wsl --status >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] WSL is already installed.
    echo.
) else (
    echo [INFO] WSL not detected. Installing WSL with Ubuntu...
    echo.
    echo This may take several minutes. Your PC may need to restart.
    echo.

    REM Try to install WSL
    wsl --install -d Ubuntu

    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] WSL installation encountered an issue.
        echo.
        echo TROUBLESHOOTING:
        echo 1. Enable "Virtual Machine Platform" in Windows Features
        echo    - Press Win+R, type: optionalfeatures
        echo    - Check "Virtual Machine Platform" and "Windows Subsystem for Linux"
        echo    - Restart your PC
        echo.
        echo 2. Enable Hyper-V (if using Windows Pro/Enterprise)
        echo    - Run: wsl.exe --install --no-distribution
        echo.
        echo 3. Enable virtualization in BIOS settings
        echo.
        echo For more info: https://aka.ms/enablevirtualization
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [2/3] Next Steps - Setup Inside Ubuntu
echo ========================================================
echo.
echo After WSL installation completes:
echo.
echo 1. Open "Ubuntu" from your Start Menu (or type: wsl)
echo 2. Inside Ubuntu terminal, run:
echo.
echo    git clone https://github.com/meso4444/chat-agent-matrix.git
echo    cd chat-agent-matrix/telegram
echo    ./install_dependencies.sh
echo.
echo 3. Follow the setup wizard
echo.

echo [3/3] Installation Complete
echo.
pause
