#!/bin/bash
# ============================================================================
# Chat Agent Matrix - [Entrypoint] 精簡委派版
# ============================================================================
set -e

echo "🧬 [Entrypoint] 容器覺醒中..."

# 1. 環境變數準備
export SCRIPT_DIR="/app/telegram"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
cd "$SCRIPT_DIR"

# 2. 核心權力委派：呼叫 start_all_services.sh
# 這樣能確保 100% 載入容器內掛載的 config.yaml (對齊 ISC 架構)
if [ -f "./start_all_services.sh" ]; then
    echo "🚀 偵測到啟動腳本，正在委派啟動任務..."
    bash ./start_all_services.sh
else
    echo "❌ 致命錯誤: 找不到 /app/telegram/start_all_services.sh"
    exit 1
fi

echo "🏁 [Entrypoint] 啟動序列執行完畢。容器進入守護模式。"
# 保持容器運行
tail -f /dev/null
