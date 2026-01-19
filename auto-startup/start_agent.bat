@echo off
title Chat Agent Matrix Launcher
echo ========================================================
echo   Chat Agent Matrix - WSL Launcher
echo ========================================================
echo.

echo [1/2] Checking Matrix location in WSL...

:: Check if TG and LINE exist
wsl -d Ubuntu bash -c "if [ -d ~/chat-agent-matrix/telegram ]; then echo 'YES'; else echo 'NO'; fi" > %temp%\check_tg.txt
wsl -d Ubuntu bash -c "if [ -d ~/chat-agent-matrix/line ]; then echo 'YES'; else echo 'NO'; fi" > %temp%\check_line.txt

set /p HAS_TG=<%temp%\check_tg.txt
set /p HAS_LINE=<%temp%\check_line.txt

:: Logic check
if "%HAS_TG%"=="YES" (
    if "%HAS_LINE%"=="YES" (
        goto :MENU
    ) else (
        echo ✅ Found Telegram Edition. Starting...
        goto :START_TG
    )
) else (
    if "%HAS_LINE%"=="YES" (
        echo ✅ Found LINE Edition. Starting...
        goto :START_LINE
    ) else (
        echo ❌ Error: Neither Telegram nor LINE edition found.
        echo Path: ~/chat-agent-matrix/
        pause
        exit
    )
)

:MENU
echo.
echo ⚠️  Found BOTH Telegram and LINE editions.
echo Please choose which one to start:
echo.
echo   [1] Telegram Edition
echo   [2] LINE Edition
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto :START_TG
if "%choice%"=="2" goto :START_LINE
echo Invalid choice.
goto :MENU

:START_TG
wsl -d Ubuntu bash -c "cd ~/chat-agent-matrix/telegram && ./start_all_services.sh"
goto :END

:START_LINE
wsl -d Ubuntu bash -c "cd ~/chat-agent-matrix/line && ./start_all_services.sh"
goto :END

:END
echo.
echo [2/2] Done.
pause
