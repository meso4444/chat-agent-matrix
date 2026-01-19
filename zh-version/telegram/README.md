# Chat Agent Matrix - Telegram Edition

> **基於 Telegram 協作介面的全方位遠端 AI 代理系統**
> 
> 本專案提供一套完整的自動化框架，將 Telegram 轉化為高效能的遠端 AI 指揮中心。透過整合自動化安全隧道、Webhook 動態綁定及終端模擬技術，實現跨地域的系統協作與資訊代理。

## 🌟 核心技術優勢

*   **自動化網路連線管理**：內建自動化腳本解決 ngrok 動態 URL 變動問題，確保 Webhook 服務的持續性。
*   **多引擎協作架構**：支援 Claude Code (深度邏輯與程式碼處理) 與 Google Gemini (高速資訊檢索) 雙引擎切換。
*   **多模態圖片支援**：具備自動化圖片落地與分析機制，支援發送圖片進行即時摘要與文字提取。
*   **互動式組件支援**：完整支援 Telegram 鍵盤選單 (Reply Keyboard) 與自定義指令模板，優化操作效率。
*   **非同步通知機制**：透過監聽終端輸出，實現執行結果的即時回報。

---

## 🚀 部署指南 (Deployment Guide)

### 1. 環境初始化與配置
執行整合安裝腳本，系統將自動配置運作環境，並啟動 **互動式設定精靈** 引導您輸入必要的憑證（ngrok Token、Telegram Token 等）：

```bash
./install_dependencies.sh
```

> **提示**：若日後需要修改設定，可直接執行 `./setup_config.sh` 啟動設定精靈，無需手動編輯檔案。

### 2. 獲取憑證說明
#### A. ngrok Authtoken (必要)
1. 註冊並登入 [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)。
2. 在頁面上方找到 **Your Authtoken**。
3. 複製該 Token（以 `2...` 開頭的長字串），稍後在安裝精靈中填入。

#### B. TELEGRAM_BOT_TOKEN
1. 在 Telegram 中搜尋官方帳號 **@BotFather** 並開啟對話。
2. 發送 `/newbot` 指令，依提示輸入機器人名稱。
3. 創建成功後，BotFather 會提供一組 **HTTP API Token**。
4. **重要**：請點擊機器人連結並發送至少一則訊息（如 `/start`）以啟動通訊。

#### B. 個人 TELEGRAM_CHAT_ID
1. 確保已在設定精靈中填入 Token。
2. 在 Telegram 中發送任何訊息（如 `/start`）給您的機器人。
3. **設定精靈會自動偵測**並抓取您的個人 ID，您只需按 Enter 確認即可。
4. 若自動偵測失敗，亦可手動輸入。

### 3. 進階配置 (可選)
若需調整 AI Agent 列表或自定義選單，請編輯 **`config.yaml`**：
```bash
nano config.yaml
```
> **注意**：敏感資訊 (Token/ID) 已移至 `.env` 檔案管理。若需修改憑證，請執行 `./setup_config.sh`。

### 4. 啟動服務
執行主啟動腳本，系統將自動完成隧道建立、Webhook 註冊及各項服務初始化：

```bash
./start_all_services.sh
```

---

## 🖥️ tmux 操作指引 (tmux Guide)

本系統利用 tmux 在背景維持 AI 引擎與 Webhook 伺服器的運行。以下為常用操作：

### 1. 進入/連接 Session
若要查看 AI 運行狀況或偵錯，請執行：
```bash
tmux attach -t ai_telegram_session
```

### 2. 視窗切換與常用快捷鍵
進入 tmux 後，可使用以下組合鍵（預設前綴鍵為 `Ctrl+B`）：

*   **`Ctrl+B` 隨後按 `0`**：切換至 AI 引擎視窗 (Claude/Gemini)。
*   **`Ctrl+B` 隨後按 `1`**：切換至 Telegram API 伺服器視窗。
*   **`Ctrl+B` 隨後按 `2`**：切換至 ngrok 隧道監控視窗。
*   **`Ctrl+B` 隨後按 `D`**：**分離 (Detach)** Session。此操作會讓您回到普通終端機，但服務仍會在背景持續運行。

---

## ⚙️ 進階配置 (Advanced Configuration)

### 自定義選單 (menu)
本系統支援透過 `config.yaml` 中的 `menu` 陣列來自定義 Telegram 的互動式選單。

#### YAML 數據結構範例
```yaml
menu:
  # 第一行：有兩個按鈕
  - - label: "🌤 天氣查詢"
      command: "查詢今日天氣狀態"
    - label: "📊 系統監控"
      command: "/status"
      
  # 第二行：只有一個按鈕
  - - label: "🔄 切換對象"
      command: "/switch"
      prompt: "請輸入 Agent 名稱:"
```

**💡 YAML 排版規則 (鍵盤佈局)：**
*   `menu` 對應到 Telegram 的鍵盤，是一個二維陣列。
*   **`- -` (雙破折號)**：代表 **新的一行 (Row)** 的開始。
*   **`  -` (縮排 + 單破折號)**：代表 **同一行** 中的下一個按鈕。
*   透過調整縮排與破折號，您可以自由設計 2x2、3x1 等各種按鈕排列。

*   **label**: 按鈕顯示之標籤文字。
*   **command**: 觸發後發送至 AI 引擎的指令字串。

### 多模態圖片處理與隔離
系統具備自動化圖片落地與隔離機制：
*   **隔離儲存**: 圖片會根據當前活躍 Agent 存入其專屬目錄：`agent_home/{name}/images_temp/`。
*   **保留機制**: 支援差異化清理，可在各 Agent 配置中設定 `images_retention_days`（預設 7 天），系統每日自動掃描並清理。

### AI Agent 軍團與協作配置
您可以在 `config.yaml` 中定義多個 Agent，並透過「協作群組」讓它們共享產出：

```yaml
agents:
  - name: "Güpa"
    engine: "gemini"
    usecase: "負責研究與摘要..."
    cleanup_policy:
      images_retention_days: 3  # 差異化清理

# 協作群組：成員間會自動建立雙向共享空間 (軟連結)
collaboration_groups:
  - name: "core_team"
    members: ["Güpa", "Chöd"]
```

### 排程任務系統 (Scheduler)
支援 Cron 與 Interval 兩種模式，讓 Agent 主動執行任務：

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

#### 切換與協作指令
| 指令 | 用途 |
|------|------|
| `/switch [name]` | 切換當前對話的 Agent (支援模糊搜尋，如 `/switch chod`) |
| `/inspect [name]` | **監控模式**：派遣當前 Agent 去檢查目標 Agent 的終端機畫面 |
| `/fix [name]` | **急救模式**：由系統直接介入重啟目標 Agent 並嘗試恢復記憶 |
| `/resume_latest` | **恢復記憶**：自動恢復當前 Agent 最近一次的對話紀錄 |

---

## 🛠️ 技術架構與組件說明 (Technical Overview)

### 📂 目錄結構 (Directory Structure)
```text
telegram/
├── .env.example                # 環境變數範本
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
├── message_templates.yaml      # 通知訊息模板
├── setup_config.sh             # 互動式設定精靈
├── start_all_services.sh       # 主啟動腳本 (tmux + Flask + Agent)
├── start_ngrok.sh              # ngrok 隧道啟動器
├── status_telegram_services.sh # 系統狀態檢查工具
├── stop_telegram_services.sh   # 系統停止工具
├── telegram_notifier.py        # Telegram 訊息發送模組
├── telegram_webhook_server.py  # Flask Webhook 伺服器
└── telegram_scripts/           # 內部輔助腳本 (Scheduler, Env Setup)
```

### 核心組件職責
| 組件名稱 | 檔案 | 功能描述 |
|------|------|----------|
| **Webhook 服務器** | `telegram_webhook_server.py` | 負責接收 Webhook、分發指令至 tmux、並整合 Scheduler 與 ImageManager。 |
| **排程管理器** | `scheduler_manager.py` | 基於 APScheduler，負責執行定時任務 (Cron/Interval) 與系統清理。 |
| **環境初始化器** | `setup_agent_env.py` | 自動建立 Agent 目錄結構、處理協作群組的軟連結 (Shared Space)。 |
| **通知引擎** | `telegram_notifier.py` | 負責調用 Telegram Bot API 進行消息推送。 |
| **配置載入器** | `config.py` | 讀取 `.env` 與 `config.yaml`，提供統一的變數介面。 |
| **憲法與規範** | `agent_home_rules.md` | 定義 Agent 的自我認知、目錄結構權限與協作原則。 |
| **通訊協議** | `CLAUDE.md` / `GEMINI.md` | 定義 AI 引擎與通知系統之間的交互規範、指令格式與自動化回報準則。 |

### 維運腳本清單
| 檔案 | 功能描述 |
|------|----------|
| `start_all_services.sh` | **主啟動腳本**。建立 tmux session，初始化環境，並引導 Agent 自動生成操作手冊。 |
| `start_ngrok.sh` | **連線自動化**。啟動隧道並自動更新 Webhook URL (Telegram 專用)。 |
| `status_telegram_services.sh` | **健康檢查**。顯示所有 Agent 存活狀態、Flask API 健康度與 Tunnel 資訊。 |
| `stop_telegram_services.sh` | **一鍵停止**。優雅關閉所有相關進程與 tmux session。 |
| `setup_config.sh` | **設定精靈**。互動式引導建立 `.env` 安全設定檔。 |
| `../auto-startup/install_systemd_telegram.sh` | **服務化安裝**。將系統註冊為 systemd 服務，實現開機自啟。 |

---

## 🔒 安全性說明 (Security)

1.  **身分驗證**：系統強制檢查 `TELEGRAM_CHAT_ID`。除非發送者 ID 符合白名單，否則 Webhook 伺服器將拒絕任何指令處理。
2.  **隔離環境**：AI 引擎運行於獨立的 tmux 會話中，與 API 服務器解耦，確保系統穩定性。
3.  **加密傳輸**：所有對外通訊皆透過 ngrok 提供的 TLS 1.2+ 加密隧道傳輸。

## 📄 授權 (License)
MIT License