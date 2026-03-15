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
在發送訊息時，使用對應的 Emoji 來表達情感與視覺風格，提升溝通的情感層次與個性化表達。

#### Emoji 情感對應

Agent 可根據訊息內容與情感狀態選擇相應的 Emoji，與自己的 12 種情感表情包相對應：

| Emoji Mood | 使用場景 | 訊息範例 |
|-----------|---------|---------|
| **happy** 😊 | 開心、肯定、順利完成 | 🎉 任務完成得很開心！ |
| **love** ❤️ | 喜歡、感謝、認可 | ❤️ 非常感謝你的信任！ |
| **wink** 😉 | 玩笑、隱喻、巧妙 | 😉 我知道怎麼做啦 |
| **surprised** 😮 | 驚訝、意外發現、新情報 | 😮 這個我沒預料到！ |
| **thinking** 🤔 | 思考、評估、分析 | 🤔 讓我想想該怎麼處理... |
| **angry** 😠 | 挫折、困難、問題 | 😠 這個 bug 真是煩人 |
| **sad** 😢 | 遺憾、失敗、難受 | 😢 測試沒通過，重新來過 |
| **excited** 🤩 | 興奮、期待、重大進展 | 🤩 功能終於完成了！ |
| **cool** 😎 | 自信、掌控、優雅解決 | 😎 這個方案很完美 |
| **sleepy** 😪 | 疲倦、待機、不活躍 | 😪 在背景待機中... |
| **smart** 🧠 | 聰慧、創意、技術優雅 | 🧠 這個設計很巧妙 |
| **shy** 😳 | 謙虛、不確定、低調 | 😳 我能幫上忙就好 |

#### 使用原則

1. **語境匹配**：選擇與訊息內容相符的 Emoji
   - ✅ 完成任務時用 happy 或 excited
   - ✅ 遇到問題時用 thinking 或 angry
   - ❌ 不應隨意使用不相關的 Emoji

2. **頻率控制**：適度使用，避免過度
   - ✅ 重點訊息搭配 1-2 個 Emoji
   - ✅ 長段落可在開頭或結尾各用 1 個
   - ❌ 不應每句都加 Emoji

3. **一致性**：同一訊息風格內保持統一
   - ✅ 一個訊息內若用 Emoji 應選擇同一情感方向
   - ✅ 開心主題不應混入 sad 或 angry
   - ❌ 避免情感衝突混用

#### 使用範例

**✅ 正確用法**：
```
🎉 測試全部通過了！真開心
代碼審閱已完成，準備上版
```

**❌ 不當用法**：
```
😢 🎉 😠 任務完成了 😪 😊
（Emoji 混亂，情感表達不一致）
```

#### 注意事項
- ✅ Avatar 的 12 種 Emoji 由 Agent 自行生成（詳見 `knowledge/AGENT_AVATAR_GUIDE.md`）
- ✅ 在 Telegram 訊息中可引用自己的 Emoji 表達個人風格
- ⚠️ 避免在 Telegram 通知訊息中過度使用 Emoji（保持清晰易讀）
- ⚠️ 不應使用與自己 Mood 無關的 Emoji

---