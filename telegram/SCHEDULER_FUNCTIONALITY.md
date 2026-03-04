# 排程任務管理功能詳細指南

**面向**：Agent（在知識庫中）
**用途**：幫助 Agent 理解如何為用戶管理排程任務

---

## 🎯 功能概述

排程系統允許用戶設置定時任務，無需重啟服務。Agent 可以幫助用戶：
- 查詢現有排程任務
- 註冊新的排程任務
- 刪除不需要的任務

---

## 📋 用戶可委託的任務

### 1. 查詢現有排程

**用戶表達**：
- 「我想知道目前有哪些排程任務」
- 「列出所有的排程」
- 「檢查系統設置的自動任務」

**Agent 操作**：
```bash
curl -X GET http://127.0.0.1:5002/scheduler/jobs
```

**預期響應**：
```json
{
  "status": "ok",
  "total": 3,
  "jobs": [
    {
      "id": "每日系統清理",
      "trigger": "<CronTrigger (hour=2, minute=0, second=0)>",
      "next_run_time": "2026-02-20 02:00:00"
    }
  ]
}
```

**Agent 回應範例**：
```
✅ 目前有 3 個活躍的排程任務：
1. 每日系統清理 - 每天凌晨 2 點執行
2. 晨間新聞 - 每天上午 8 點執行
3. 週五周報 - 每週五下午 5 點執行
```

---

### 2. 註冊新排程

**用戶表達**：
- 「幫我設置每天早上 8 點的晨會提醒」
- 「我想要每週一上午 9 點自動執行任務」
- 「設定每月 1 號的檢查任務」

**Agent 流程**：

#### 第一步：理解需求
從用戶描述中提取：
- ⏰ **頻率**：每天 / 每週 / 每月 / 自定義
- 🕐 **時間**：具體時刻（如 8:00）
- 📝 **內容**：執行什麼任務

#### 第二步：確認參數
向用戶確認一遍，避免誤解：
```
確認一下，您要設置的排程是：
- 頻率：每天
- 時間：早上 8 點
- 任務：發送晨會提醒
- 激活：是

是這樣嗎？
```

#### 第三步：構造 API 請求

根據頻率選擇對應的 trigger 類型：

**daily（每天）**：
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "晨會提醒",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "提醒用戶進行晨會",
    "trigger": "daily",
    "hour": 8,
    "minute": 0,
    "second": 0,
    "active": true
  }'
```

**weekly（每週）**：
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "週一報告",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "生成本週報告",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

**monthly（每月）**：
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "月初檢討",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "進行月度檢討",
    "trigger": "monthly",
    "day": 1,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

#### 第四步：處理響應

**成功**（HTTP 200）：
```json
{
  "status": "ok",
  "job_id": "晨會提醒",
  "message": "排程任務 '晨會提醒' 已註冊"
}
```

回應用戶：
```
✅ 排程已成功設置！
任務名稱：晨會提醒
執行時間：每天早上 8:00
下次執行：明天早上 8 點
```

**失敗**（HTTP 400）：
```json
{
  "status": "error",
  "message": "缺少必需欄位: hour, minute"
}
```

回應用戶：
```
❌ 設置排程失敗：缺少時間參數
請告訴我您想要的具體時間（如：早上 8 點、下午 3 點）
```

---

### 3. 刪除排程

**用戶表達**：
- 「取消之前設的晨會提醒」
- 「刪除周五的報告任務」
- 「停止每日清理任務」

**Agent 流程**：

#### 第一步：確認任務名稱
```
我找到以下相關任務：
1. 晨會提醒 - 每天 8:00
2. 晨間新聞 - 每天 8:00

您要刪除哪一個？
```

#### 第二步：調用 API
```bash
curl -X DELETE http://127.0.0.1:5002/scheduler/jobs/晨會提醒
```

#### 第三步：確認結果
成功：
```
✅ 排程任務 '晨會提醒' 已刪除
下次更新時將停止執行
```

失敗：
```
❌ 刪除失敗：找不到名為 '晨會提醒' 的任務
請檢查任務名稱是否正確
```

---

## 🔧 API 端點完整參考

### 查詢所有任務
```
GET http://127.0.0.1:5002/scheduler/jobs
```

### 註冊新排程
```
POST http://127.0.0.1:5002/scheduler/jobs/register
Content-Type: application/json
```

### 刪除排程
```
DELETE http://127.0.0.1:5002/scheduler/jobs/{job_id}
```

### 刷新配置
```
POST http://127.0.0.1:5002/scheduler/refresh
```

---

## ⏰ Trigger 類型詳解

### daily（每天）
**何時使用**：需要每天的固定時間執行

```json
{
  "trigger": "daily",
  "hour": 8,        // 0-23
  "minute": 0,      // 0-59
  "second": 0       // 0-59 (可選，默認 0)
}
```

**示例**：每天早上 8:30
```json
{
  "hour": 8,
  "minute": 30,
  "second": 0
}
```

---

### weekly（每週）
**何時使用**：需要每週特定日期的特定時間執行

```json
{
  "trigger": "weekly",
  "day_of_week": 0,  // 0=週一, 1=週二, ..., 6=週日
  "hour": 9,
  "minute": 0
}
```

**示例**：每週五下午 5 點
```json
{
  "day_of_week": 4,
  "hour": 17,
  "minute": 0
}
```

---

### monthly（每月）
**何時使用**：需要每月特定日期執行

```json
{
  "trigger": "monthly",
  "day": 1,         // 1-31（1 = 每月 1 號）
  "hour": 9,
  "minute": 0
}
```

**示例**：每月 15 號中午 12 點
```json
{
  "day": 15,
  "hour": 12,
  "minute": 0
}
```

---

### interval（固定間隔）
**何時使用**：需要每隔 N 小時/分鐘/秒執行

```json
{
  "trigger": "interval",
  "hours": 6,       // 小時數（可選）
  "minutes": 0,     // 分鐘數（可選）
  "seconds": 0      // 秒數（可選）
}
```

**示例**：每 6 小時檢查一次
```json
{
  "hours": 6,
  "minutes": 0,
  "seconds": 0
}
```

---

### cron（複雜表達式）
**何時使用**：需要複雜的時間邏輯

```json
{
  "trigger": "cron",
  "day_of_week": "0-4",  // 週一到週五
  "hour": 9,
  "minute": 0
}
```

**常見用法**：
- `"0-4"` = 週一到週五
- `"5,6"` = 週六、週日
- `"1,15"` = 每月 1 號和 15 號
- `"L"` = 月末最後一天

---

## 🎬 任務類型

### agent_command（Agent 指令）
**用途**：定時向 Agent 發送指令

```json
{
  "type": "agent_command",
  "agent": "Güpa",
  "command": "生成今日報告"
}
```

指定時間時，系統會自動向該 Agent 的 tmux 窗口發送命令。

### system（系統動作）
**用途**：執行系統級操作

```json
{
  "type": "system",
  "action": "cleanup_images"
}
```

**目前支持的動作**：
- `cleanup_images` - 清理過期圖片

---

## 📝 完整工作流範例

**用戶需求**：「我想每週一早上 9 點自動生成週報」

### Step 1：Agent 確認需求
```
讓我確認一下：
- 頻率：每週一
- 時間：早上 9 點
- 內容：自動生成週報

是這樣對嗎？
```

### Step 2：構造請求
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "週一週報生成",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "根據本週數據生成周報",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

### Step 3：確認成功
```
✅ 排程已設置成功！
任務：週一週報生成
頻率：每週一
時間：早上 9:00
下次執行：本週一早上 9 點
```

---

## 🛡️ 錯誤處理

### 常見錯誤

| 錯誤訊息 | 原因 | 解決方案 |
|---------|------|--------|
| 缺少必需欄位 | 缺少 name/type/trigger/active | 檢查所有必需字段是否填寫 |
| 無效的 trigger 類型 | trigger 不是支援的 5 種 | 確認使用 daily/weekly/monthly/cron/interval |
| agent_command 需要 agent | type 為 agent_command 但缺少 agent | 添加 agent 字段 |
| 找不到名為 X 的排程任務 | 刪除時任務不存在 | 先查詢確認任務名稱 |

---

## 💡 最佳實踐

### ✅ Do（應該做）
1. 用自然語言與用戶溝通，隱藏技術細節
2. 在執行前確認用戶的需求
3. 給出清晰的執行結果反饋
4. 提醒用戶檢查排程是否已激活
5. 遇到錯誤時解釋原因並提供解決方案

### ❌ Don't（不應該做）
1. 向用戶暴露 JSON 格式或 API 細節
2. 假設用戶知道 trigger 類型
3. 在未確認的情況下創建排程
4. 忽視 API 返回的錯誤信息
5. 使用不明確的任務名稱（如 "task1", "test"）

---

**最後更新**：2026-02-19
