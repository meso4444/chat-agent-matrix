#!/bin/bash
# agent_credential_wizard.sh - AI Agent Credential Wizard (LINE Local Edition)
# Local environment authentication only (LINE does not support container deployment)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "🔐 AI Agent Credential Wizard"
echo "=========================================="
echo ""

# Local environment authentication function
echo ""
echo "📍 Environment: Local (~)"
echo "🎯 Goal: Authenticate and store credentials in local home directory"
echo ""

# Choose CLI tool
echo "Select AI CLI tool:"
echo "1) Gemini"
echo "2) Claude"
echo ""
read -p "Enter choice (1 or 2): " CLI_CHOICE

case "$CLI_CHOICE" in
  1)
    echo ""
    echo "🚀 Starting Gemini CLI authentication..."
    echo "📂 HOME: $HOME"
    echo "💡 Tip: After authentication, credentials will be stored in ~/.gemini"
    echo ""
    gemini --yolo
    echo ""
    echo "✅ Gemini authentication completed!"
    echo "📦 Credential location: $(eval echo ~)/.gemini"
    ;;
  2)
    echo ""
    echo "🚀 Starting Claude CLI authentication..."
    echo "📂 HOME: $HOME"
    echo "💡 Tip: After authentication, credentials will be stored in ~/.claude"
    echo ""
    claude --permission-mode bypassPermissions
    echo ""
    echo "✅ Claude authentication completed!"
    echo "📦 Credential location: $(eval echo ~)/.claude"
    ;;
  *)
    echo "❌ Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "🎉 Credential wizard completed!"
echo "=========================================="
echo ""
