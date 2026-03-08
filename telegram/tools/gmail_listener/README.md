# 📧 Gmail 郵件監聽 & Agent 轉發系統

**功能**: Gmail 郵件監聽 → 智能 Agent 轉發 → Telegram 回報

---

## ⚙️ 前置準備：Google Cloud 設置

### 1. 建立 Google Cloud 專案

1. 打開 [Google Cloud Console](https://console.cloud.google.com)
2. 點擊「選擇專案」→「新建專案」
3. 輸入專案名稱（例如：`chat-agent-matrix`）
4. 點擊「建立」

### 2. 啟用 Gmail API

1. 在 Google Cloud Console 中，左側菜單點擊「APIs 和服務」
2. 點擊「啟用 APIs 和服務」
3. 搜尋「Gmail API」
4. 點擊「Gmail API」
5. 點擊「啟用」按鈕

### 3. 建立 OAuth 2.0 認證

1. 左側菜單點擊「APIs 和服務」→「凭證」
2. 點擊「建立凭證」→「OAuth 客户端 ID」
3. 如果提示配置 OAuth 同意屏幕，點擊「配置」
   - 應用程式名稱：輸入 `chat-agent-matrix`
   - 使用者支援電郵：輸入你的 Gmail
   - 點擊「保存並繼續」
4. 在「凭证」頁面，點擊「建立 OAuth 2.0 客户端 ID」
5. 應用程式類型選擇「已安裝的應用程式」
6. 名稱：輸入 `gmail-listener`
7. 點擊「建立」

### 4. 下載 credentials.json

1. 在「OAuth 2.0 客户端 ID」部分找到剛建立的應用
2. 點擊右側的下載按鈕（向下箭頭圖標）
3. 選擇「下載為 JSON」
4. 將下載的 `client_secret_*.json` 檔案重命名為 `credentials.json`
5. 複製到 `skills/` 目錄

### 5. 設置授權的重定向 URI（可選但建議）

1. 找到剛建立的 OAuth 2.0 客户端 ID，點擊編輯
2. 在「授權的重定向 URI」中添加：
   ```
   http://localhost:8080/
   ```
3. 點擊「保存」

---

## 🚀 快速開始（5 分鐘）

### 1️⃣ 安裝依賴
```bash
pip3 install -r requirements.txt
```

### 2️⃣ OAuth 認證（一次性）
```bash
python3 gmail_auth_simple.py
```
- 在瀏覽器中授權 Gmail 訪問
- 自動生成 `token.json`

### 3️⃣ 配置白名單
編輯 `whitelist.json`:

```json
{
  "whitelist_senders": [
    {
      "email": "karanoyui214@gmail.com",
      "agents": ["Güpa", "Chöd"]
    }
  ],
  "tmux_session": "ai_telegram_session",
  "email_marker": "Hi"
}
```

### 4️⃣ 啟動監聽
```bash
python3 gmail_listener.py
```

---

## 📋 使用範例

### 發送郵件給 Agent

**郵件內容**:
```
收件人: karanoyui214@gmail.com
主旨: 市場分析
內容:

Hi Güpa

請為我分析過去一週的市場趨勢
```

### 系統自動

✅ 檢測郵件
✅ 檢查寄件者在白名單中
✅ 偵測 "Hi Güpa"
✅ 轉發給 Güpa 的 tmux
✅ Güpa 執行指令
✅ 通過 Telegram 回報結果

---

## ⚙️ 配置說明

### whitelist.json

| 欄位 | 說明 | 範例 |
|------|------|------|
| `email` | 寄件者郵件 | `karanoyui214@gmail.com` |
| `agents` | 可觸發的 Agent | `["Accelerator", "Chöd"]` |
| `tmux_session` | tmux session 名稱 | `ai_telegram_session` |
| `email_marker` | 觸發關鍵詞 | `Hi` |

### 觸發格式

**正確**:
```
Hi Accelerator    ✅
Hi Chöd           ✅
HI ACCELERATOR    ✅ (不區分大小寫)
```

**錯誤**:
```
Hello Accelerator ❌ (應使用 "Hi")
Hi accelerator    ❌ (Agent 名稱區分大小寫)
HiAccelerator     ❌ (缺少空格)
```

---

## 📁 文件說明

| 檔案 | 功能 |
|------|------|
| `gmail_auth_simple.py` | OAuth 認證腳本（一次性） |
| `gmail_listener.py` | 主監聽腳本（核心功能） |
| `whitelist.json` | 配置檔案 |
| `credentials.json` | Google OAuth 凭證 |
| `token.json` | OAuth 令牌（自動生成） |
| `requirements.txt` | Python 依賴 |

---

## 🔄 工作流程

```
發送郵件
  ↓
Gmail API
  ↓
gmail_test.py 檢測新郵件
  ↓
檢查白名單 → 不符合 → 跳過
  ↓ 符合
檢測 "Hi [Agent_name]"
  ↓ 找到
構建轉發訊息
  ↓
通過 tmux 發送給 Agent
  ↓
Agent 執行指令
  ↓
Agent 通過 telegram_notifier.py 回報
  ↓
Telegram 顯示結果
```

---

## 🔐 安全注意

⚠️ **重要**:
- `token.json` 包含敏感凭證，**永遠不要上傳**
- `credentials.json` 不要分享
- 白名單應只包含信任的寄件者

在 `.gitignore` 中添加:
```
token.json
credentials.json
.gmail_seen_messages
```

---

## 🆘 常見問題

### Q: "token.json 不存在"

A: 運行 OAuth 認證:
```bash
python3 gmail_auth_simple.py
```

### Q: "Agent tmux 窗口不存在"

A: 確認 Agent 已啟動:
```bash
tmux list-windows -t ai_telegram_session
```

### Q: "偵測不到 Agent 提及"

A: 確認郵件格式正確:
```
Hi [Agent_name]  ← 必須使用 "Hi"
(空一行)
郵件內容
```

---

## 📊 特性

✅ **安全的 OAuth 2.0 認證**
✅ **自動郵件監聽**（30 秒輪詢）
✅ **智能白名單過濾**
✅ **自動 Agent 轉發**
✅ **Tmux 集成**
✅ **繁體中文支援**
✅ **低 API 消耗**

---

**版本**: 1.0
**最後更新**: 2026-03-08
