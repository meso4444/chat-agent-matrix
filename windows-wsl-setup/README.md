# 🪟 Windows WSL Installation Guide

This module helps Windows 10/11 users install **WSL2 (Windows Subsystem for Linux)** and Ubuntu environment with one click, building the foundation for Chat Agent Matrix.

---

## 🚀 Installation Steps

### 1. Run Installation Script
In the `windows-wsl-setup` folder, double-click to execute **`install_wsl.bat`**.
*   This will automatically enable Windows virtualization features and install Ubuntu.
*   **Note**: After installation completes, your computer may require a restart.

### 2. Initialize Linux Environment
After restart, open the **"Ubuntu"** application from the Start menu.
Wait for it to initialize (first launch may take a few minutes), then set your account password.

Next, copy and paste the following commands in the Ubuntu black window (right-click to paste):

```bash
# Download project
git clone https://github.com/meso4444/chat-agent-matrix.git
cd chat-agent-matrix/telegram
# (or line directory, depending on your needs)

# Install dependencies and configure (will open configuration wizard)
./install_dependencies.sh
```

---

### ⏭️ Next Steps
After environment setup is complete, if you wish to configure **autostart on boot**, please refer to `../auto-startup/README.md`.
