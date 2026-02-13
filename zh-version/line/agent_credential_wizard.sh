#!/bin/bash
# agent_credential_wizard.sh - AI Agent 認證精靈 (LINE 本地版)
# 僅支援本地環境認證 (LINE 不支援容器部署)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "🔐 AI Agent 認證精靈"
echo "=========================================="
echo ""

# 本地環境認證函數
echo ""
echo "📍 環境：本地 (~)"
echo "🎯 目標：在本地家目錄中認證並儲存認證資訊"
echo ""

# 選擇 CLI 工具
echo "選擇 AI CLI 工具："
echo "1) Gemini"
echo "2) Claude"
echo ""
read -p "請輸入選擇 (1 或 2): " CLI_CHOICE

case "$CLI_CHOICE" in
  1)
    echo ""
    echo "🚀 正在啟動 Gemini CLI 認證..."
    echo "📂 HOME: $HOME"
    echo "💡 提示：認證後，認證資訊將儲存在 ~/.gemini"
    echo ""
    gemini --yolo
    echo ""
    echo "✅ Gemini 認證已完成！"
    echo "📦 認證資訊位置：$(eval echo ~)/.gemini"
    ;;
  2)
    echo ""
    echo "🚀 正在啟動 Claude CLI 認證..."
    echo "📂 HOME: $HOME"
    echo "💡 提示：認證後，認證資訊將儲存在 ~/.claude"
    echo ""
    claude --permission-mode bypassPermissions
    echo ""
    echo "✅ Claude 認證已完成！"
    echo "📦 認證資訊位置：$(eval echo ~)/.claude"
    ;;
  *)
    echo "❌ 無效的選擇"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "🎉 認證精靈已完成！"
echo "=========================================="
echo ""
