# ⚡ Autostart Guide

This module provides integration scripts for Systemd and Windows Task Scheduler, implementing **"Phoenix Mode"**: even if the server restarts, agents will automatically resurrect in the background.

---

## 🐧 Linux / WSL Setup (Systemd)

First, we need to tell the Linux system to treat the Agent as a background service.

### 1. Run Registration Script
In the Ubuntu window, execute the corresponding command based on your platform version:

**Telegram Edition:**
```bash
# Go back to project root directory
cd ~/chat-agent-matrix
sudo ./auto-startup/install_systemd_telegram.sh
```

**LINE Edition:**
```bash
sudo ./auto-startup/install_systemd_line.sh
```

---

## 🪟 Windows Host Setup (Task Scheduler)

If you are running on Windows WSL, to prevent service failure after Windows updates restart, please follow these steps.

### 1. Configure Automatic Scheduling (Recommended Method)
You don't need to leave the Linux terminal. Simply execute the following command to call Windows for setup:

```bash
# In the project directory (chat-agent-matrix)
./auto-startup/setup_windows_scheduler.sh
```

This will automatically open a blue PowerShell window (if asked for permissions, press "Yes"), then press Enter as prompted to complete.

> **⚠️ Important Note: About Session 0 Isolation**
> To achieve "run without login" server-level capability, this task will run in Windows **Session 0**.
> *   **No visible window**: After your computer restarts, you **will not** see any Ubuntu window on the desktop, which is normal.
> *   **Background execution**: Although invisible, WSL is starting in the background and the Agent is online.
> *   **How to manage**: Use `ssh` to connect, or send commands via Telegram/LINE. To manually bring up the window, execute `start_agent.bat`.

### 2. Alternative Method (Manual Execution)
If the above method fails, you can manually execute in Windows PowerShell (Administrator):

1.  Open PowerShell in Windows (run as administrator).
2.  Enter the following command (replace the path with your actual path):
    ```powershell
    powershell -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu\home\YOUR_USERNAME\...\setup_autostart.ps1"
    ```

---

## 🛠️ FAQ

**Q: How do I know if the service is running?**
A: Open Telegram/LINE and send `/status` to your Bot.

**Q: I want to manually stop the service?**
A: Open Ubuntu and enter `sudo systemctl stop chat-agent-matrix-telegram` (or `chat-agent-matrix-line`).

**Q: I want to remove autostart on boot?**
A: Please execute the removal script:
   *   Telegram: `sudo ./auto-startup/disable_systemd_telegram.sh`
   *   LINE: `sudo ./auto-startup/disable_systemd_line.sh`

**Q: The script shows "WSL distro not found"?**
A: Our script defaults to using `Ubuntu`. If you have installed a different version, please edit the `$WSLDistro` variable in `setup_autostart.ps1`.
