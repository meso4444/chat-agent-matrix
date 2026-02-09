@echo off
REM Chat Agent Matrix - Windows WSL Installer (English)
REM This script detects and installs WSL2 with Ubuntu distribution
REM Detects Hyper-V/Virtual Machine Platform status

setlocal enabledelayedexpansion

echo ========================================================
echo Chat Agent Matrix - Windows WSL Installer
echo ========================================================
echo.

echo [1/4] Checking WSL installation status...
wsl --status >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] WSL is already installed.
    echo.
    echo [2/4] Checking Virtual Machine Platform status...
    echo.

    REM Check if Hyper-V feature is enabled
    powershell -Command "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Hypervisor" >nul 2>&1

    if !errorlevel! equ 0 (
        echo [OK] Virtual Machine Platform is enabled.
        echo.
    ) else (
        echo [WARNING] Virtual Machine Platform is NOT enabled.
        echo.
        echo ======================================================
        echo [ERROR] System Configuration Required
        echo ======================================================
        echo.
        echo Your system has WSL installed but the Virtual Machine
        echo Platform (Hyper-V) is not enabled. WSL2 requires this.
        echo.
        echo SOLUTIONS (choose one):
        echo.
        echo [OPTION 1] Manual Setup (Recommended for all users)
        echo -------------------------------------------------------
        echo 1. Press Win+R, type: optionalfeatures
        echo 2. In the window, check BOTH:
        echo    - Virtual Machine Platform
        echo    - Windows Subsystem for Linux
        echo 3. Click OK and restart your PC
        echo 4. Run this script again after restart
        echo.
        echo [OPTION 2] PowerShell (Requires Admin Privilege)
        echo -------------------------------------------------------
        echo 1. Right-click PowerShell and select "Run as administrator"
        echo 2. Copy and paste this command:
        echo    dism /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
        echo 3. After completion, restart your PC
        echo 4. Run this script again after restart
        echo.
        echo [OPTION 3] Check BIOS Settings
        echo -------------------------------------------------------
        echo If both methods fail, virtualization may be disabled in BIOS:
        echo 1. Restart PC and enter BIOS (usually Del, F2, or F10)
        echo 2. Find "Virtualization Technology" or "AMD-V" setting
        echo 3. Enable it and save
        echo 4. Return to Windows and use Option 1 or 2 above
        echo.
        echo More info: https://docs.microsoft.com/en-us/windows/wsl/install
        echo.
        pause
        exit /b 1
    )
) else (
    echo [INFO] WSL not detected. Installing WSL with Ubuntu...
    echo.
    echo This may take several minutes. Your PC may need to restart.
    echo.

    REM Try to install WSL
    wsl --install -d Ubuntu

    if !errorlevel! neq 0 (
        echo.
        echo ======================================================
        echo [ERROR] WSL installation encountered an issue.
        echo ======================================================
        echo.
        echo SOLUTIONS (try in order):
        echo.
        echo [STEP 1] Enable Virtual Machine Platform
        echo -------------------------------------------------------
        echo 1. Press Win+R, type: optionalfeatures
        echo 2. Check BOTH:
        echo    - Virtual Machine Platform
        echo    - Windows Subsystem for Linux
        echo 3. Click OK and restart your PC
        echo 4. Run this script again after restart
        echo.
        echo [STEP 2] Use PowerShell (Requires Admin)
        echo -------------------------------------------------------
        echo 1. Right-click PowerShell, select "Run as administrator"
        echo 2. Copy and paste this command:
        echo    dism /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
        echo 3. Restart your PC
        echo 4. Run this script again
        echo.
        echo [STEP 3] Check BIOS Virtualization Settings
        echo -------------------------------------------------------
        echo If both steps above fail:
        echo 1. Restart and enter BIOS (usually Del, F2, or F10)
        echo 2. Find and enable "Virtualization Technology" or "AMD-V"
        echo 3. Save and restart Windows
        echo 4. Repeat Step 1 or Step 2
        echo.
        echo Reference: https://aka.ms/enablevirtualization
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [3/4] Setup Instructions - Run Inside Ubuntu
echo ========================================================
echo.
echo After WSL installation is complete:
echo.
echo 1. Open "Ubuntu" from your Start Menu (or type 'wsl' in cmd)
echo 2. Inside Ubuntu terminal, run these commands:
echo.
echo    git clone https://github.com/meso4444/chat-agent-matrix.git
echo    cd chat-agent-matrix/telegram
echo    ./install_dependencies.sh
echo.
echo 3. Follow the setup wizard
echo.

echo [4/4] Installation Complete
echo.
pause
