# setup_autostart.ps1
# Automatically configure Windows Autostart for Chat Agent Matrix (WSL)

# Check for Administrator privileges
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[X] Error: Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "    (Right-click -> Run with PowerShell)"
    Write-Host "Press Enter to exit..."
    Read-Host
    exit
}

$TaskName = "ChatAgentMatrix_AutoStart"
# Uncomment and set your distro name if it is not default
# $WSLDistro = "Ubuntu" 
$Command = "wsl.exe"

# If WSLDistro is set, use it; otherwise run default distro
if ($WSLDistro) {
    $ArgsList = "-d $WSLDistro"
} else {
    $ArgsList = ""
}

Write-Host "[-] Configuring Windows Autostart Task..." -ForegroundColor Cyan

# 1. Check if task exists
$TaskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($TaskExists) {
    Write-Host "[!] Task already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 2. Define Trigger (AtStartup for true server-like behavior)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# 3. Define Action (Conditionally handle arguments)
if ($ArgsList) {
    $Action = New-ScheduledTaskAction -Execute $Command -Argument $ArgsList
} else {
    $Action = New-ScheduledTaskAction -Execute $Command
}

# 4. Define Principal (Run whether user is logged in or not)
# S4U allows running without storing password, perfect for background services
$Principal = New-ScheduledTaskPrincipal -UserId (Whoami) -LogonType S4U

# 5. Register Task
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Principal $Principal -Description "Chat Agent Matrix WSL Wake-up (Headless)"
    Write-Host ""
    Write-Host "[V] Success! Task '$TaskName' created." -ForegroundColor Green
    Write-Host "    Agent will now start automatically at Windows BOOT (no login required)."
    Write-Host "    Note: This runs in Session 0. You won't see the console window."
}
catch {
    Write-Host "[X] Failed to create task: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to finish..."
Read-Host