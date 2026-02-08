#!/bin/bash
# agent_credential_wizard.sh - AI Agent 認證精靈 (通用版)
# 支持本地和容器兩種環境的認證配置

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "🔐 AI Agent 認證精靈 (Credential Wizard)"
echo "=========================================="
echo ""

# 本地環境認證函數
run_local_auth() {
  echo ""
  echo "📍 環境: 本地 (~)"
  echo "🎯 目標: 直接認證存放在本地 home 目錄"
  echo ""

  # 選擇 CLI 工具
  echo "請選擇 AI CLI 工具："
  echo "1) Gemini"
  echo "2) Claude"
  echo ""
  read -p "請輸入選擇 (1 或 2): " CLI_CHOICE

  case "$CLI_CHOICE" in
    1)
      echo ""
      echo "🚀 啟動 Gemini CLI 認證..."
      echo "📂 HOME: $HOME"
      echo "💡 提示: 完成認證後，凭证將存放在 ~/.gemini"
      echo ""
      gemini --yolo
      echo ""
      echo "✅ Gemini 認證完成！"
      echo "📦 凭证位置: $(eval echo ~)/.gemini"
      ;;
    2)
      echo ""
      echo "🚀 啟動 Claude CLI 認證..."
      echo "📂 HOME: $HOME"
      echo "💡 提示: 完成認證後，凭证將存放在 ~/.claude"
      echo ""
      claude --permission-mode bypassPermissions
      echo ""
      echo "✅ Claude 認證完成！"
      echo "📦 凭证位置: $(eval echo ~)/.claude"
      ;;
    *)
      echo "❌ 無效選擇"
      exit 1
      ;;
  esac
}

# 容器環境認證函數
run_container_auth() {
  echo ""
  echo "📍 環境: 容器"
  echo "🎯 目標: 認證存放在容器 instance 目錄"
  echo ""
  echo "💡 命名建議範例："
  echo "   • 技術環境：dev, staging, production, test, sandbox"
  echo "   • 應用場景：travel_planner, investment_advisor, meditation_coach"
  echo "   • 專案代號：gupta, chod, omega, alpha, nexus"
  echo "   • 個人用途：work, hobby, research, learning, experiment"
  echo ""

  # 輸入 instance 名稱
  read -p "請輸入 instance 名稱: " INSTANCE_NAME

  if [ -z "$INSTANCE_NAME" ]; then
    echo "❌ Instance 名稱不能為空"
    exit 1
  fi

  # 建立 instance 目錄
  DOCKER_DEPLOY_DIR="$SCRIPT_DIR/docker-deploy"
  CONTAINER_HOME="$DOCKER_DEPLOY_DIR/container_home/$INSTANCE_NAME"

  echo "📁 正在建立 instance 目錄..."
  mkdir -p "$CONTAINER_HOME"
  echo "✅ Instance 目錄已建立: $CONTAINER_HOME"
  echo ""

  # 選擇 CLI 工具
  echo "請選擇 AI CLI 工具："
  echo "1) Gemini"
  echo "2) Claude"
  echo ""
  read -p "請輸入選擇 (1 或 2): " CLI_CHOICE

  # 確保 container_home 目錄權限正確（比照標準 home 目錄 750）
  mkdir -p "$CONTAINER_HOME"
  chmod 750 "$CONTAINER_HOME" 2>/dev/null || sudo chmod 750 "$CONTAINER_HOME" 2>/dev/null || true

  case "$CLI_CHOICE" in
    1)
      echo ""
      echo "🚀 啟動 Gemini CLI 認證..."
      echo "📂 認證路徑: $CONTAINER_HOME"
      echo "💡 提示: 認證將存放在 $CONTAINER_HOME/.gemini"
      echo ""
      if HOME="$CONTAINER_HOME" gemini --yolo; then
        echo ""
        echo "✅ Gemini 認證完成！"
        echo "📦 凭证已存放至: $CONTAINER_HOME/.gemini"
      else
        echo ""
        echo "⚠️  認證過程中出現錯誤，請檢查目錄權限"
        echo "   嘗試執行: sudo chmod 777 $CONTAINER_HOME"
      fi
      ;;
    2)
      echo ""
      echo "🚀 啟動 Claude CLI 認證..."
      echo "📂 認證路徑: $CONTAINER_HOME"
      echo "💡 提示: 認證將存放在 $CONTAINER_HOME/.claude"
      echo ""
      if HOME="$CONTAINER_HOME" claude --permission-mode bypassPermissions; then
        echo ""
        echo "✅ Claude 認證完成！"
        echo "📦 凭证已存放至: $CONTAINER_HOME/.claude"
      else
        echo ""
        echo "⚠️  認證過程中出現錯誤，請檢查目錄權限"
        echo "   嘗試執行: sudo chmod 777 $CONTAINER_HOME"
      fi
      ;;
    *)
      echo "❌ 無效選擇"
      exit 1
      ;;
  esac

  echo ""
  echo "📋 容器啟動指令:"
  echo "  docker compose -f docker-compose.yml -f docker-compose.${INSTANCE_NAME}.yml up -d bot"
}

# Step 1: 選擇環境
echo ""
echo "請選擇執行環境："
echo "1) 本地環境 (Local)"
echo "2) 容器環境 (Container)"
echo ""
read -p "請輸入選擇 (1 或 2): " ENV_CHOICE

case "$ENV_CHOICE" in
  1)
    echo "🖥️  選擇：本地環境"
    run_local_auth
    ;;
  2)
    echo "🐳 選擇：容器環境"
    run_container_auth
    ;;
  *)
    echo "❌ 無效選擇"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "🎉 認證精靈執行完成！"
echo "=========================================="
echo ""
