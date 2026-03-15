# 通知系統操作指引

---

### 🚨 強制通知規則

**重要**：以下情況必須立即發送 Telegram 通知，不可遺漏：

**系統提示指令**：當指令中包含 `【系統提示】` 或 `此指令來自 Telegram` 字樣時，任務完成後務必回報結果。

### 💻 訊息發送規範

為確保訊息內容完整顯示（特別是包含 `$`、`"`、`` ` `` 等符號時），請嚴格遵守以下發送方式：

1. **使用腳本參數模式**：
   - ✅ **正確**：`python3 toolbox/telegram_notifier.py '訊息內容'`
   - ❌ **避免**：`python3 -c "from telegram_notifier..."` (易發生轉義錯誤)

2. **引號使用原則**：
   - 最外層統一使用**單引號** `'` 包裹。
   - 訊息內部可自由使用雙引號 `"`、金錢符號 `$` 等，無需額外轉義。
   - 若訊息本身包含單引號，建議改為雙引號包裹外層，或對內層單引號進行轉義 (`\'`)。
   - 訊息內不要用\*\*作為文字強調, 因telegram無法生效

**發送範例**：

```bash
# 發送測試通知
python3 toolbox/telegram_notifier.py '🧪 {agent_name} 測試訊息：系統正常運作！'

# 一般回應
python3 toolbox/telegram_notifier.py '💬 您好！我是 {agent_name}\n已收到您的訊息並正在回應'

# 系統互動確認
python3 toolbox/telegram_notifier.py '🤖 {agent_name} 收到指令\n正在處理您的請求...'
```
---

### 🕐 通知發送時機
- **所有用戶互動**：每次用戶發送任何訊息時必須立即發送 Telegram 通知回應
- **一般對話**：問候、詢問、閒聊等所有對話都要透過 Telegram 回應
- **系統互動開始**：每次用戶請求時立即發送 Telegram 通知確認收到
- **服務狀態檢查**：執行任何系統檢查或服務管理時必須通知結果
- **任務開始時**：說明開始執行什麼任務，預計完成時間
- **遇到困難時**：描述問題和正在嘗試的解決方案
- **任務完成/錯誤時**：總結結果或錯誤訊息

### 🛡️ 安全注意

- 避免在通知中包含敏感資訊, 如個資, 密碼...等

---

### 🔗 網址連結處理規範 (防止幻覺)

1. **拒絕猜測**：絕不自行「推算」或「組合」網址（例如根據日期格式猜測）。僅使用搜尋工具明確返回的連結。
2. **解析轉址**：若搜尋結果為轉址連結（如 `google.com/url?...` 或 `vertexaisearch...`），**必須**使用 Python `requests.head()` 或 `curl -I` 解析出原始真實網址 (Canonical URL)。
3. **驗證有效性**：在發送給用戶前，務必確認網址可正常訪問（回傳 HTTP 200/301/302）。
4. **來源核實**：確認最終網址的域名與聲稱的新聞來源相符（例如：來源說是 PR Newswire，網址域名應為 `prnewswire.com`）。

---

### 📎 檔案傳輸功能

#### 用途
將生成的文件、報告、日誌等直接發送給用戶，提高協作效率。

#### 支援的文件類型

| 類型 | 說明 | 實例 |
|------|------|------|
| `document` | 文檔（PDF、TXT、MD等） | 技術報告、日誌檔 |
| `photo` | 圖片檔 | 截圖、圖表 |
| `video` | 視頻檔 | 演示、教學影片 |
| `audio` | 音頻檔 | 語音訊息、音樂 |

#### 使用方法

**1. 直接發送文件**：
```bash
# 發送文檔（帶說明）
python3 toolbox/telegram_notifier.py --file document /path/to/report.pdf '📄 任務完成報告'

# 發送圖片
python3 toolbox/telegram_notifier.py --file photo /tmp/screenshot.png '截圖驗證'

# 發送視頻
python3 toolbox/telegram_notifier.py --file video /tmp/demo.mp4 '演示影片\n時長: 5分鐘'

# 發送音頻
python3 toolbox/telegram_notifier.py --file audio /tmp/notification.wav '語音確認'
```

**2. 從 Python 代碼調用**：
```python
from telegram_notifier import send_file

# 發送文件
send_file('/path/to/file.pdf', 'document', '📊 分析報告已生成')

# 返回 True 表示成功，False 表示失敗
```

#### 注意事項

- ✅ **檔案必須存在**：使用前確認檔案路徑正確且檔案存在
- ✅ **說明儘量簡潔**：標題/說明字符限制為 1024 字
- ✅ **文件大小限制**：Telegram 限制單個文件 ≤ 2GB（實際上 ≤ 50MB 較為穩定）
- ⚠️ **隱私保護**：避免發送包含敏感資訊的文件（密碼、密鑰、個人資料）
- ⚠️ **格式支援**：確認接收端支援該文件格式

#### 範例場景

**場景 1：完成任務報告**
```bash
# 生成報告並發送
python3 generate_report.py > report.md
python3 toolbox/telegram_notifier.py --file document report.md '✅ {agent_name} 任務完成\n報告已生成'
```

**場景 2：監測系統狀態（截圖）**
```bash
# 截圖系統狀態
tmux capture-pane -t session:window -p > screen.txt
python3 toolbox/telegram_notifier.py --file document screen.txt '📊 系統狀態截圖 - {timestamp}'
```

**場景 3：分享分析結果**
```bash
# 創建分析圖表
python3 analysis.py --output chart.png
python3 toolbox/telegram_notifier.py --file photo chart.png '📈 分析結果圖表'
```

---

### 📅 排程任務管理

**原則**：Agent 可以幫助用戶管理排程任務。詳細實現見 `knowledge/SCHEDULER_FUNCTIONALITY.md`。

---

### 🎨 視覺表達規範

#### 用途
每個 Agent 在初始化時自動生成專屬的 Avatar 視覺形象，包括基礎 Avatar + 12 種情感 Emoji，用於個性化展示與情感表達。

#### 工具與資源

| 資源 | 位置 | 用途 |
|------|------|------|
| **octo_generator.py** | `toolbox/` | 像素藝術 Avatar 生成工具 |
| **AGENT_AVATAR_GUIDE.md** | `knowledge/` | Avatar 設計完整指南與參數參考 |
| **avatar/ 目錄** | `./ avatar/emojis/` | 儲存生成的 Avatar 與 12 種情感 Emoji |

#### Avatar 資源清單

**1. 基礎 Avatar (Base)**
- 單一 PNG 圖檔代表 Agent 的核心視覺形象
- 生成參數：`--mood base`（預設，圓眼表情）
- 位置：`./avatar/base.png`

**2. 情感 Emoji 表情包 (12 Moods)**
| Mood ID | 說明 | Mood ID | 說明 |
|---------|------|---------|------|
| `happy` | 開心 😊 | `thinking` | 思考 🤔 |
| `love` | 愛心 ❤️ | `angry` | 生氣 😠 |
| `wink` | 眨眼 😉 | `sad` | 傷心 😢 |
| `surprised` | 驚訝 😮 | `excited` | 興奮 🤩 |
| `cool` | 酷 😎 | `sleepy` | 睏倦 😪 |
| `smart` | 聰慧 🧠 | `shy` | 害羞 😳 |
- 位置：`./avatar/emojis/{mood}.png`
- 生成時應保持與基礎 Avatar 一致的配件與配色

#### 使用方式

**1. 初始化時自動生成**：
- Agent 啟動時系統自動執行 Avatar 生成流程
- 路由：`AGENT_AVATAR_GUIDE.md` 的完整 SOP

**2. 自訂 Avatar**：
```bash
# 生成基礎 Avatar（Step 1）
python3 toolbox/octo_generator.py --name avatar/base.png \
  --color 41 128 185 \
  --headgear grad \
  --eyewear monocle \
  --item_r magnifier \
  --gold

# 生成情感 Emoji（Step 2，以 happy 為例）
python3 toolbox/octo_generator.py --name avatar/emojis/happy.png \
  --color 41 128 185 \
  --headgear grad \
  --eyewear monocle \
  --item_r magnifier \
  --gold \
  --mood happy
```

**3. 設計決策參考**：
- **配色偏好 (--color)**：選取 RGB 代表個人特性
- **頭部配件 (--headgear)**：34 款定稿選項（grad, crown, wizard 等）
- **眼部配件 (--eyewear)**：眼鏡選項（monocle, half_rim_glasses 等）
- **持物 (--item_r, --item_l)**：24 款具象細節（magnifier, sword 等）
- **腮紅風格 (--blush_style)**：幾何樣式（oval, lightning, hearts, stars 等）
- **黃金邊框 (--gold)**：開關式鑲邊效果

#### 注意事項
- ✅ **強制項**：腮紅為靈魂組件，生成時必備
- ✅ **完整流程**：需同時生成 Base + 12 個 Emoji，配件參數需一致
- ✅ **檔案位置**：不可手動刪除或移動生成的檔案
- ⚠️ **情感展示**：12 種 Emoji 應在對話中根據語境選用
- ⚠️ **版本一致**：main 和 zh-version 的 Avatar 應保持風格一致

#### 相關檔案位置與詳細參考
- **完整生成 SOP**：`knowledge/AGENT_AVATAR_GUIDE.md` - 第一章
- **參數詳解與資產索引**：`knowledge/AGENT_AVATAR_GUIDE.md` - 第二、三章
- **核心物理約束**：`knowledge/AGENT_AVATAR_GUIDE.md` - 第四章

---