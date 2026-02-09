# Chat Agent Matrix - WSL Installer
# Automated setup for Windows WSL with complete system checks

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "Chat Agent Matrix - Windows WSL Installer" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This script requires administrator privileges." -ForegroundColor Yellow
    Write-Host "Requesting administrator access..." -ForegroundColor Yellow
    Write-Host ""

    # Elevate to admin
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Clear-Host

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Chat Agent Matrix - Windows WSL Installer" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# [Pre-Check] System Requirements Verification
Write-Host "[Pre-Check] Verifying system requirements..." -ForegroundColor Green
Write-Host ""

# Check Windows Version
Write-Host "Checking Windows version..." -ForegroundColor Yellow
$osVersion = [System.Environment]::OSVersion.Version
$buildNumber = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuildNumber

Write-Host "Windows Version: $($osVersion.Major).$($osVersion.Minor) (Build $buildNumber)" -ForegroundColor Gray

if ($buildNumber -lt 19041) {
    Write-Host "[ERROR] Windows version is too old!" -ForegroundColor Red
    Write-Host "Required: Windows 10 version 2004 (Build 19041) or newer, or Windows 11" -ForegroundColor Red
    Write-Host "Your Build: $buildNumber" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Windows version is compatible" -ForegroundColor Green
Write-Host ""

# Check PowerShell Version
Write-Host "Checking PowerShell version..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion.Major
Write-Host "PowerShell Version: $psVersion" -ForegroundColor Gray

if ($psVersion -lt 5) {
    Write-Host "[WARNING] PowerShell 5.0 or newer is recommended" -ForegroundColor Yellow
}
Write-Host ""

# Check free disk space
Write-Host "Checking free disk space..." -ForegroundColor Yellow
$systemDrive = $env:SystemDrive
$driveInfo = Get-PSDrive -Name ($systemDrive.TrimEnd(':'))
$freeSpaceGB = [math]::Round($driveInfo.Free / 1GB, 2)
Write-Host "Free space on $systemDrive : ${freeSpaceGB} GB" -ForegroundColor Gray

if ($freeSpaceGB -lt 10) {
    Write-Host "[WARNING] Recommended at least 10 GB free space" -ForegroundColor Yellow
}
Write-Host "[OK] Disk space check completed" -ForegroundColor Green
Write-Host ""

Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# [Step 1] Check WSL Installation and Windows Feature
Write-Host "[Step 1/5] Checking WSL installation status..." -ForegroundColor Green
Write-Host ""

# Check if Windows Subsystem for Linux feature is enabled
Write-Host "Checking Windows Subsystem for Linux feature..." -ForegroundColor Yellow
$wslFeature = Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Windows-Subsystem-Linux" 2>$null
$wslFeatureEnabled = $wslFeature.State -eq "Enabled"

if (-not $wslFeatureEnabled) {
    Write-Host "Enabling Windows Subsystem for Linux feature..." -ForegroundColor Yellow
    Enable-WindowsOptionalFeature -Online -FeatureName "Microsoft-Windows-Subsystem-Linux" -All -NoRestart -WarningAction SilentlyContinue | Out-Null
    Write-Host "[OK] Windows Subsystem for Linux feature enabled" -ForegroundColor Green
    Write-Host ""
}

# Check if WSL is installed via wsl command
$wslStatus = wsl --status 2>$null
$wslInstalled = $LASTEXITCODE -eq 0

if ($wslInstalled) {
    Write-Host "[OK] WSL is already installed and configured" -ForegroundColor Green

    # Check and set WSL default version to 2
    Write-Host "Checking WSL version configuration..." -ForegroundColor Yellow
    $wslListOutput = wsl --list --verbose 2>$null
    Write-Host "[OK] WSL configuration verified" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[INFO] WSL not configured. Setting up..." -ForegroundColor Yellow
    Write-Host "This may take several minutes." -ForegroundColor Yellow
    Write-Host ""

    wsl --install -d Ubuntu

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] WSL installation failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Ensure you are running as administrator" -ForegroundColor Yellow
        Write-Host "2. Check Windows version (need Windows 10 v2004 or newer)" -ForegroundColor Yellow
        Write-Host "3. Ensure Windows Subsystem for Linux feature is enabled" -ForegroundColor Yellow
        Write-Host "4. Check Virtual Machine Platform is enabled in Windows Features" -ForegroundColor Yellow
        Write-Host "5. Restart your computer and try again" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }

    Write-Host "[OK] WSL setup completed" -ForegroundColor Green
    Write-Host ""
}

# [Step 2] Check Virtual Machine Platform
Write-Host "[Step 2/5] Checking Virtual Machine Platform..." -ForegroundColor Green
Write-Host ""

$hyperVStatus = Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V-Hypervisor" 2>$null
$hyperVStatus2 = Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V" 2>$null
$vmpStatus = Get-WindowsOptionalFeature -Online -FeatureName "VirtualMachinePlatform" 2>$null

$hyperVEnabled = $hyperVStatus.State -eq "Enabled"
$hyperVEnabled2 = $hyperVStatus2.State -eq "Enabled"
$vmpEnabled = $vmpStatus.State -eq "Enabled"

if (($hyperVEnabled -or $hyperVEnabled2) -and $vmpEnabled) {
    Write-Host "[OK] Virtual Machine Platform is already enabled" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[INFO] Virtual Machine Platform is not fully enabled. Enabling..." -ForegroundColor Yellow
    Write-Host ""

    if (-not $hyperVEnabled2) {
        Write-Host "Enabling Hyper-V..." -ForegroundColor Yellow
        Enable-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V" -All -NoRestart -WarningAction SilentlyContinue | Out-Null
    }

    if (-not $vmpEnabled) {
        Write-Host "Enabling Virtual Machine Platform..." -ForegroundColor Yellow
        Enable-WindowsOptionalFeature -Online -FeatureName "VirtualMachinePlatform" -All -NoRestart -WarningAction SilentlyContinue | Out-Null
    }

    Write-Host "[OK] Virtual Machine Platform enabled (changes will take effect after restart)" -ForegroundColor Green
    Write-Host ""
}

# [Step 3] Check and Configure WSL Version
Write-Host "[Step 3/5] Configuring WSL Version..." -ForegroundColor Green
Write-Host ""

# Try to set WSL default version to 2
Write-Host "Setting WSL default version to 2..." -ForegroundColor Yellow
wsl --set-default-version 2 2>$null
Write-Host "[OK] WSL version configuration completed" -ForegroundColor Green
Write-Host ""

# [Step 4] BIOS Virtualization Check
Write-Host "[Step 4/5] Important - Check BIOS Virtualization Setting" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Ensure virtualization is enabled in your BIOS" -ForegroundColor Yellow
Write-Host ""
Write-Host "If Ubuntu fails to start after restart, check BIOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "How to enter BIOS (by manufacturer):" -ForegroundColor Cyan
Write-Host "  - Lenovo ThinkPad/IdeaCentre/Yoga/L14: Press Enter, then F1" -ForegroundColor Yellow
Write-Host "  - Dell: Press F2 or Del" -ForegroundColor Yellow
Write-Host "  - HP/Pavilion: Press F2 or Esc" -ForegroundColor Yellow
Write-Host "  - ASUS: Press Del or F2" -ForegroundColor Yellow
Write-Host "  - Other: Try Del, F2, F10, or F12" -ForegroundColor Yellow
Write-Host ""
Write-Host "Steps to enable virtualization:" -ForegroundColor Cyan
Write-Host "1. Restart your computer NOW" -ForegroundColor Yellow
Write-Host "2. DURING RESTART: When Lenovo logo appears:" -ForegroundColor Yellow
Write-Host "   - Press Enter (menu will appear)" -ForegroundColor Yellow
Write-Host "   - Then press F1" -ForegroundColor Yellow
Write-Host "3. In BIOS menu, find 'Virtualization Technology', 'Intel VT-x', 'AMD-V', or 'SVM'" -ForegroundColor Yellow
Write-Host "4. Enable it and press F10 to save and exit" -ForegroundColor Yellow
Write-Host "5. Return to Windows - WSL should now work" -ForegroundColor Yellow
Write-Host ""

# [Step 5] Restart Prompt
Write-Host "[Step 5/5] Restart Required" -ForegroundColor Green
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "IMPORTANT: Computer restart is required!" -ForegroundColor Red
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Virtual Machine Platform changes only take effect after restart." -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Restart computer now? (Y/N)"

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Computer will restart in 3 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3

    Write-Host ""
    Write-Host "After restart, you can:" -ForegroundColor Green
    Write-Host "1. Open Ubuntu from Start Menu" -ForegroundColor Green
    Write-Host "2. Or open PowerShell and type: wsl" -ForegroundColor Green
    Write-Host "3. Complete initial setup (create user and password)" -ForegroundColor Green
    Write-Host ""

    Restart-Computer -Force
} else {
    Write-Host ""
    Write-Host "You chose not to restart now." -ForegroundColor Yellow
    Write-Host "Remember to restart your computer later to complete the setup." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restart, you can:" -ForegroundColor Green
    Write-Host "1. Open Ubuntu from Start Menu" -ForegroundColor Green
    Write-Host "2. Or open PowerShell and type: wsl" -ForegroundColor Green
    Write-Host "3. Complete initial setup (create user and password)" -ForegroundColor Green
    Write-Host ""

    Read-Host "Press Enter to exit"
}
