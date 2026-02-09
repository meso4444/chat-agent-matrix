# ☀️🌙 Chat Agent Matrix - LINE Edition

> **Take the Red Pill. Control your AI Matrix through LINE.**
> 將 LINE 轉化為強大的多代理 AI 指揮中心，搭配 Cloudflare Tunnel 實現穩定的遠端協作。

---

## 🎯 系統概述 (Overview)

**Chat Agent Matrix (LINE 版)** 採用 **Cloudflare Tunnel** 作為連線方案，提供基於固定網域的 Webhook 服務。此版本適配了 LINE Messaging API 的特性，使用 Quick Reply 作為主要的互動介面。

### 🌟 LINE 版核心特性
*   **多代理矩陣**: 同時控制 **Güpa (Gemini)** 與 **Chöd (Claude)**。
*   **固定網域**: 透過 Cloudflare Tunnel 建立固定 Webhook URL，無需每次重啟後更新 LINE Console 設定。
*   **快速選單 (Quick Reply)**: 適配 LINE 介面，提供對話框上方的快捷指令按鈕。
*   **排程系統**: 支援自動巡檢與差異化圖片清理。

---

## 🔑 前置準備 (Prerequisites)

### 1. 準備網域 (Cloudflare)
本系統依賴 Cloudflare Tunnel 讓 LINE Webhook 連線到您的本地電腦。
1.  前往 [Cloudflare](https://www.cloudflare.com/) 註冊免費帳號。
2.  **必要條件**：您需要擁有一個網域 (Domain) 並將其 DNS 託管在 Cloudflare (例如 `example.com`)。
3.  **決定 Webhook 網址**：請想好一個子網域，例如 `webhook.example.com`。這將是您稍後在設定中填寫的 `CLOUDFLARE_CUSTOM_DOMAIN`。
    *   **注意**：此網址必須是您所擁有網域的子網域，不能隨意填寫不屬於您的網址。

### 2. 建立 LINE Bot (取得憑證)
1.  前往 [LINE Developers Console](https://developers.line.biz/) 並登入。
2.  點擊 **Create a new provider**，輸入名稱後建立。
3.  點擊 **Create a LINE Official Account** (這會開啟新視窗跳轉至 Official Account Manager)。
4.  依照指引完成官方帳號建立。
5.  **啟用 Messaging API (在 OA Manager)**：
    *   在 LINE Official Account Manager 右上角點擊 **設定**。
    *   左側選單找到 **Messaging API** 並點擊啟用。
    *   選擇剛才建立的 Provider，完成綁定。
6.  **取得憑證 (回到 Developers Console)**：
    *   回到 LINE Developers Console，點進您的 Provider 與 Channel。
    *   **Basic settings** 頁籤：捲動至底部複製 **Channel secret**。
    *   **Messaging API** 頁籤：捲動至底部 **Channel access token** 區域，點擊 **Issue** 按鈕生成並複製 Token。
7.  **設定回應模式 (在 OA Manager)**：
    *   在 LINE Official Account Manager 右上角點擊 **設定**。
    *   在左側選單點擊 **回應設定**。
    *   在 **Messaging API** 頁籤中，關閉 "Auto-reply messages" 與 "Greeting messages"，並啟用 "Use webhooks"。

---

## 🚀 部署指南 (Deployment Guide)

### 1. 環境初始化
執行安裝腳本，系統將自動安裝 Node.js、Claude Code、Gemini CLI 及所有 Python 依賴：

```bash
./install_dependencies.sh
```

### 2. 配置憑證 (Security Setup)
強烈建議使用設定精靈來加密管理您的 Token，這會自動生成 `.env` 檔案並防止憑證洩漏：

```bash
./setup_config.sh
```
*   依序輸入 LINE Token 與 Secret。
*   **Cloudflare Tunnel Name**: 為您的隧道取個名字 (如 `line-bot-tunnel`)。
*   **Cloudflare Domain**: 填入您想使用的完整子網域 (如 `webhook.example.com`)。

### 3. Cloudflare Tunnel 設定 (一次性)
如果您尚未建立 Tunnel 並綁定自訂域名，請執行引導腳本：
```bash
./setup_cloudflare_fixed_url.sh
```
*   **授權流程**：腳本執行時會自動開啟瀏覽器，請登入 Cloudflare 並選擇您擁有該子網域的主網域 (Zone) 進行授權。

### 4. 設定 Webhook (最後步驟)
*   完成 Tunnel 設定後，回到 LINE Developers Console 的 **Messaging API** 頁籤。
*   將 Tunnel URL (需加上 `/webhook`) 貼入 **Webhook URL** 欄位並更新。
*   啟動本地服務後，點擊 **Verify** 確認連線成功。

### 5. 啟動服務
執行主啟動腳本，系統將自動載入環境變數並初始化生態系：

```bash
./start_all_services.sh
```

---

## ⚙️ 進階配置 (Advanced Configuration)

編輯 `config.yaml` 來自定義系統行為。

### 自定義選單 (Quick Reply)
本系統支援透過 `menu` 陣列來自定義 LINE 的快速回覆按鈕。

```yaml
menu:
  # 第一行
  - - label: "🌤 天氣查詢"
      command: "查詢今日天氣狀態"
    - label: "📊 系統監控"
      command: "/status"
      
  # 第二行
  - - label: "🔄 切換對象"
      command: "/switch {input}"
      prompt: "請輸入 Agent 名稱:"
```

### AI Agent 軍團與協作
定義多個 Agent 並建立協作關係：

```yaml
agents:
  - name: "Güpa"
    engine: "gemini"
    usecase: "負責研究與摘要..."
    cleanup_policy:
      images_retention_days: 3

# 協作群組：成員間會自動建立雙向共享空間 (軟連結)
collaboration_groups:
  - name: "core_team"
    members: ["Güpa", "Chöd"]
```

### 排程任務 (Scheduler)
```yaml
scheduler:
  - name: "每日清理"
    type: "system"
    action: "cleanup_images"
    trigger: "interval"
    hour: 24
  - name: "定期回報"
    type: "agent_command"
    agent: "Güpa"
    command: "請提供最新的市場摘要"
    trigger: "cron"
    hour: 9
    minute: 0
```

---

## 🖥️ tmux 操作指引 (tmux Guide)

本系統利用 tmux 在背景維持 AI 引擎與 Webhook 伺服器的運行。

### 1. 進入/連接 Session
若要查看 AI 運行狀況或偵錯，請執行：
```bash
tmux attach -t ai_line_session
```

### 2. 視窗切換與常用快捷鍵
進入 tmux 後，可使用以下組合鍵（預設前綴鍵為 `Ctrl+B`）：

*   **`Ctrl+B` 隨後按 `0`**：切換至 Agent 1 (Güpa)。
*   **`Ctrl+B` 隨後按 `1`**：切換至 Agent 2 (Chöd)。
*   **`Ctrl+B` 隨後按 `2`**：切換至 LINE Webhook API。
*   **`Ctrl+B` 隨後按 `3`**：切換至 Cloudflare Tunnel 監控。
*   **`Ctrl+B` 隨後按 `D`**：**分離 (Detach)** Session，讓服務在背景繼續運行。

---

## 📊 系統管理與指令

| 指令 | 說明 |
|------|------|
| `/status` | 檢查所有 Agent 存活狀態、當前角色與排程任務。 |
| `/switch [name]` | 切換當前對話的 Agent (支援模糊搜尋)。 |
| `/inspect [name]` | **監控模式**：派遣當前 Agent 去檢查目標 Agent 的終端機畫面。 |
| `/fix [name]` | **急救模式**：由系統直接介入重啟目標 Agent 並嘗試恢復記憶。 |
| `/resume_latest` | **恢復記憶**：自動恢復當前 Agent 最近一次的對話紀錄。 |

---

## 🛠️ 技術架構與組件說明 (Technical Overview)

### 📂 目錄結構 (Directory Structure)
```text
line/
├── agent_home/                 # [核心] Agent 專屬工作空間 (自動生成)
│   ├── Güpa/                   # Agent 範例: Güpa (Gemini)
│   │   ├── GEMINI.md           # 自我認知與操作規範
│   │   ├── knowledge/          # 專屬知識庫
│   │   ├── my_shared_space/    # 工作產出存放區
│   │   └── Chöd_shared_space@  # 協作連結 (指向夥伴的共享區)
│   └── Chöd/                   # Agent 範例: Chöd (Claude)
├── config.yaml                 # [核心] 系統行為與 Agent 定義檔
├── config.py                   # 配置讀取與驗證模組
├── install_dependencies.sh     # 環境初始化安裝腳本
├── line_notifier.py            # LINE 訊息與 Quick Reply 發送模組
├── line_scripts/               # 內部輔助腳本 (Scheduler, Env Setup)
├── setup_cloudflare_fixed_url.sh # Cloudflare Tunnel 設定腳本
├── setup_config.sh             # 互動式設定精靈
├── start_all_services.sh       # 主啟動腳本
├── status_all_services.sh      # 系統狀態檢查工具
├── stop_all_services.sh        # 系統停止工具
└── webhook_server.py           # Flask Webhook 伺服器
```

### 核心組件職責
| 組件名稱 | 檔案 | 功能描述 |
|------|------|----------|
| **Webhook 服務器** | `webhook_server.py` | 負責接收 LINE Webhook、處理 Quick Reply、分發指令至 tmux、並整合 Scheduler。 |
| **排程管理器** | `scheduler_manager.py` | 基於 APScheduler，負責執行定時任務 (Cron/Interval) 與系統清理。 |
| **環境初始化器** | `setup_agent_env.py` | 自動建立 Agent 目錄結構、處理協作群組的軟連結 (Shared Space)。 |
| **通知引擎** | `line_notifier.py` | 負責調用 LINE Messaging API 進行消息與 Quick Reply 推送。 |
| **配置載入器** | `config.py` | 讀取 `.env` 與 `config.yaml`，提供統一的變數介面。 |
| **憲法與規範** | `agent_home_rules.md` | 定義 Agent 的自我認知、目錄結構權限與協作原則。 |
| **通訊協議** | `CLAUDE.md` / `GEMINI.md` | 定義 AI 引擎與通知系統之間的交互規範、指令格式與自動化回報準則。 |

### 維運腳本清單
| 檔案 | 功能描述 |
|------|----------|
| `start_all_services.sh` | **主啟動腳本**。建立 tmux session，初始化環境，並引導 Agent 自動生成操作手冊。 |
| `setup_cloudflare_fixed_url.sh` | **連線自動化**。引導 Cloudflare 登入並建立固定 Webhook URL (LINE 專用)。 |
| `status_all_services.sh` | **健康檢查**。顯示所有 Agent 存活狀態、Flask API 健康度與 Tunnel 資訊。 |
| `stop_all_services.sh` | **一鍵停止**。優雅關閉所有相關進程與 tmux session。 |
| `setup_config.sh` | **設定精靈**。互動式引導建立 `.env` 安全設定檔。 |
| `../auto-startup/install_systemd_line.sh` | **服務化安裝**。將系統註冊為 systemd 服務，實現開機自啟。 |

---

## 📄 授權 (License)
MIT License

