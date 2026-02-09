# 🪟 Windows WSL 安裝指南

本模組協助 Windows 10/11 用戶一鍵安裝 **WSL2 (Windows Subsystem for Linux)** 與 Ubuntu 環境，為 Chat Agent Matrix 打造運作基石。

---

## 🚀 安裝步驟

### 1. 執行安裝腳本
在 `windows-wsl-setup` 資料夾中，雙擊執行 **`install_wsl.bat`**。
*   這會自動啟用 Windows 的虛擬化功能並安裝 Ubuntu。
*   **注意**：安裝完成後，電腦可能會要求重新開機。

### 2. 初始化 Linux 環境
重新開機後，打開開始選單中的 **"Ubuntu"** 應用程式。
等待它初始化完成（第一次開啟會花幾分鐘），然後設定您的帳號密碼。

接著，在 Ubuntu 的黑色視窗中複製貼上以下指令（按右鍵可貼上）：

```bash
# 下載專案
git clone https://github.com/meso4444/chat-agent-matrix.git
cd chat-agent-matrix/telegram
# (或是 line 目錄，視您需求而定)

# 安裝依賴與設定 (會跳出設定精靈)
./install_dependencies.sh
```

---

### ⏭️ 下一步
環境建置完成後，若您希望設定 **開機自動啟動 (Autostart)**，請參考 `../auto-startup/README.md`。
