# Chat Agent Matrix - WSL 安裝說明

## 概述

此安裝程式會自動為您：
- ✅ 安裝 WSL (如果未安裝)
- ✅ 自動啟用虛擬機器平台 (Hyper-V)
- ✅ 配置所有必要設定
- ✅ 提示您重新啟動電腦

**用戶只需雙擊執行，然後重新啟動即可！**

## 使用步驟

### 第一步：雙擊執行

1. 找到 **install_wsl.bat** 檔案
2. **雙擊此檔案**
3. 如果看到「是否允許此應用進行變更？」，點擊「是」

### 第二步：等待安裝完成

安裝程式會自動執行以下操作：

1. **檢查 WSL 狀態** - 檢查 WSL 是否已安裝
2. **檢查虛擬機平台** - 檢查 Hyper-V 是否已啟用
3. **自動啟用功能** - 如需要，自動啟用虛擬機平台
4. **提示重新啟動** - 詢問是否立即重新啟動電腦

### 第三步：選擇重新啟動方式

安裝程式完成後，會詢問您：

**現在重新啟動電腦嗎？(Y/N)**

- 輸入 **Y** → 立即重新啟動（推薦）
- 輸入 **N** → 稍後手動重新啟動

#### ⚠️ 重要提醒

**虛擬機平台的設定只有在重新啟動後才會生效！**

不重新啟動的話，WSL2 將無法正常使用。

### 第四步：重新啟動後的設定

重新啟動完成後：

1. 打開「開始」菜單
2. 搜尋並打開 **Ubuntu** 應用
3. 首次執行時會要求建立用戶名和密碼，請按照指示設定

#### 第五步：安裝 Git 工具

設定完成後，在 Ubuntu 視窗中先安裝 Git：

```bash
sudo apt update
sudo apt install git -y
```

系統會提示輸入您剛才設定的密碼，請輸入密碼並按 Enter（輸入時不會顯示密碼）。

#### 第六步：克隆並安裝 Chat Agent Matrix

Git 安裝完成後，執行以下命令：

```bash
git clone https://github.com/meso4444/chat-agent-matrix.git
cd chat-agent-matrix/telegram
./install_dependencies.sh
```

7. 按照安裝精靈的指示完成設定

## 故障排除

### 問題 1：雙擊後沒有反應

**解決方案：**
1. 確保您已將 `install_wsl.bat` 和 `install_wsl.ps1` 放在同一個文件夾中
2. 嘗試右鍵點擊 `install_wsl.bat`
3. 選擇「以管理員身份執行」

### 問題 2：看到「使用者帳戶控制」提示

**解決方案：**
這是正常的。點擊「是」以允許安裝程式進行必要的系統變更。

### 問題 3：虛擬機平台啟用後，Ubuntu 仍無法啟動

**可能原因：** BIOS 中未啟用虛擬化

**解決方案：**

#### 第一步：進入 BIOS（按電腦品牌選擇按鍵）

**Lenovo 電腦（ThinkPad/IdeaCentre/Yoga/Legion）：**
- 重新啟動電腦
- **在重新啟動時**，當看到 Lenovo 標誌時：
  1. 按 **Enter** 鍵
  2. 菜單跳出來後按 **F1**
- 進入 BIOS 設定

**其他品牌：**
- **Dell**：按 **F2** 或 **Del**
- **HP/Pavilion**：按 **F2** 或 **Esc**
- **ASUS**：按 **Del** 或 **F2**
- **MSI**：按 **Del**
- **其他**：嘗試 **Del**、**F2**、**F10** 或 **F12**

#### 第二步：尋找虛擬化選項

在 BIOS 設定中尋找以下任何一個選項（名稱因品牌而異）：
- 「虛擬化技術」(Virtualization Technology)
- 「Intel VT-x」或「VT-x」
- 「AMD-V」或「SVM Mode」
- 「Enable Virtualization」

選項通常位於以下標籤：
- **Security** (安全)
- **Processor** (處理器)
- **Chipset** (晶片組)
- **Advanced** (進階)

#### 第三步：啟用虛擬化

**Lenovo ThinkPad 實際操作步驟：**

1. **選中虛擬化選項**
   - 用方向鍵移動到「Intel® Virtualization Technology」

2. **按 Enter 進入選項**
   - 按 Enter 鍵

3. **菜單跳出來後按 F1**
   - 選單會顯示啟用/停用的選項

4. **選擇「On」(啟用)**
   - 用方向鍵選擇 **On**
   - 按 Enter 確認

5. **按 F10 保存並退出**
   - 按 F10 保存設定
   - 系統會自動重新啟動返回 Windows

**按鍵參考：**
- **方向鍵**：在菜單中移動
- **Enter**：進入選項或菜單
- **F1**：顯示選項幫助和內容
- **F10**：保存並退出 BIOS

#### 第四步：重新嘗試
1. 返回 Windows 後
2. 從開始菜單開啟 **Ubuntu** 應用
3. 或在 PowerShell 中輸入：`wsl`
4. 完成初始設定

### 問題 3.5：找不到虛擬化技術選項

**如果在 BIOS 中找不到「虛擬化技術」選項：**

#### 可能的原因

**原因 1：選項名稱不同**
- 搜尋以下任一名稱：
  - Virtualization Technology
  - Intel VT-x
  - VT-x Support
  - Virtualization Mode
  - AMD-V（AMD 處理器）
  - SVM Mode（AMD 處理器）

**原因 2：在不同菜單中**
- 檢查以下菜單：
  - Security（安全）
  - Processor（處理器）
  - CPU（CPU 設定）
  - Chipset（晶片組）
  - Advanced（進階）
  - Features（功能）

**原因 3：已預設啟用**
- 虛擬化技術可能已經啟用
- 返回 Windows 試試 WSL 是否能正常運作

**原因 4：CPU 不支援虛擬化**
- 並非所有 CPU 都支援虛擬化技術
- 檢查您的 CPU 型號規格
- 如不支援，WSL 2 無法使用，但 WSL 1 可以

#### 解決方案
1. 截圖 BIOS 中 CPU 菜單的所有選項
2. 將選項名稱告訴技術人員
3. 逐個檢查上述所有菜單
4. 如 CPU 不支援虛擬化，改為安裝 WSL 1（執行 `wsl --set-default-version 1`）

### 問題 4：看到錯誤訊息 "HCS_E_HYPERV_NOT_INSTALLED"

**表示：** 虛擬機平台未啟用

**解決方案：**
1. 確認已完成「第二步」和「第三步」
2. **必須重新啟動電腦**
3. 如果仍未解決，檢查 BIOS 虛擬化設定（參考「問題 3」）

### 問題 5：Windows 版本不符

**要求：**
- Windows 10 版本 2004 或更新
- 或 Windows 11

**檢查方法：**
1. 按 **Win+R**
2. 輸入 **winver**
3. 查看「OS 組建」編號
4. 應該是 19041 或更高

如果您的 Windows 版本太舊，請先更新 Windows。

## WSL 1 vs WSL 2 - 選擇指南

### 什麼時候應該使用 WSL 1？

**WSL 1 適合的情況：**
- ✅ 簡單的命令行操作
- ✅ 文字處理和編輯
- ✅ 基礎開發（不需要 Docker）
- ✅ 系統管理任務
- ✅ 學習 Linux 命令

**WSL 1 不適合的情況：**
- ❌ Docker / 容器化開發
- ❌ Kubernetes 或複雜編排
- ❌ 某些資料庫（PostgreSQL 等）
- ❌ GPU 加速應用
- ❌ 生產環境工作

### WSL 1 的限制

| 項目 | WSL 1 | WSL 2 |
|------|-------|-------|
| **啟動時間** | 快（1-2秒）| 較慢（3-5秒）|
| **執行速度** | 慢 | 快 |
| **檔案 I/O** | 慢（跨系統）| 快（原生） |
| **Docker 支援** | ❌ 不支援 | ✅ 支援 |
| **Linux 相容性** | 70% | 100% |
| **資源使用** | 輕量級 | 中等（VM）|
| **系統呼叫** | 不完整 | 完整 |
| **GPU 加速** | ❌ 不支援 | ✅ 支援 |

### 如何使用 WSL 1

**安裝 WSL 1：**
```powershell
wsl --install -d Ubuntu --web-download
wsl --set-default-version 1
```

**檢查目前版本：**
```powershell
wsl --list --verbose
```

### 我應該選擇哪一個？

**選擇 WSL 1：**
- 您的 CPU 不支援虛擬化
- 您只需要基礎 Linux 工具
- 您需要最輕量級的環境

**選擇 WSL 2：**
- 您的電腦支援虛擬化
- 您從事軟體開發
- 您需要 Docker / 容器技術
- 您需要完整的 Linux 相容性

## 常見問題

### Q: 這個安裝程式會修改我的電腦嗎？

**A:** 是的，它會進行以下變更：
- 安裝 WSL (Windows Subsystem for Linux)
- 啟用虛擬機器平台 (Hyper-V)

這些是使用 WSL2 所必需的。

### Q: 需要網路連線嗎？

**A:** 是的。
- 首次安裝 WSL 時需要下載 Ubuntu 發行版
- 後續的 `install_dependencies.sh` 命令也會下載依賴套件

### Q: 安裝需要多久？

**A:** 通常需要 5-15 分鐘，取決於您的網路速度和系統效能。

### Q: 我可以稍後重新啟動電腦嗎？

**A:** 可以。
- 在安裝程式詢問時輸入 **N**
- 稍後手動重新啟動電腦
- 但不重新啟動的話，WSL 將無法使用

### Q: 如何卸載 WSL？

**A:** 如果需要卸載：
1. 按 **Win+R**
2. 輸入 **optionalfeatures**
3. 在視窗中取消勾選：
   - 虛擬機器平台
   - Windows Subsystem for Linux
4. 點擊「確定」並重新啟動電腦

## 需要幫助？

更多資訊請訪問：
- [微軟 WSL 官方文檔](https://docs.microsoft.com/zh-tw/windows/wsl/install)
- [虛擬化支援檢查](https://aka.ms/enablevirtualization)

---

**版本：** v2.0（雙擊執行版）
**最後更新：** 2026-02-09
**支援系統：** Windows 10 版本 2004 或更新、Windows 11
