@echo off
REM Chat Agent Matrix - WSL Installer
REM This batch file launches the PowerShell installation script

cd /d "%~dp0"

REM Launch PowerShell with the installation script
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\install_wsl.ps1'"

REM Keep window open if there was an error
if errorlevel 1 pause
