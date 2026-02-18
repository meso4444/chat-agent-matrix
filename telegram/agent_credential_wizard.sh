#!/bin/bash
# agent_credential_wizard.sh - AI Agent Credential Wizard (Universal Version)
# Supports authentication configuration for both local and container environments

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "🔐 AI Agent Credential Wizard"
echo "=========================================="
echo ""

# Local environment authentication function
run_local_auth() {
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
}

# Container environment authentication function
run_container_auth() {
  echo ""
  echo "📍 Environment: Container"
  echo "🎯 Goal: Authenticate and store credentials in container instance directory"
  echo ""
  echo "💡 Naming suggestions:"
  echo "   • Environment: dev, staging, production, test, sandbox"
  echo "   • Use case: travel_planner, investment_advisor, meditation_coach"
  echo "   • Project code: gupta, chod, omega, alpha, nexus"
  echo "   • Personal use: work, hobby, research, learning, experiment"
  echo ""

  # Enter instance name
  read -p "Enter instance name: " INSTANCE_NAME

  if [ -z "$INSTANCE_NAME" ]; then
    echo "❌ Instance name cannot be empty"
    exit 1
  fi

  # Create instance directory
  DOCKER_DEPLOY_DIR="$SCRIPT_DIR/docker-deploy"
  CONTAINER_HOME="$DOCKER_DEPLOY_DIR/container_home/$INSTANCE_NAME"

  echo "📁 Creating instance directory..."
  mkdir -p "$CONTAINER_HOME"
  echo "✅ Instance directory created: $CONTAINER_HOME"
  echo ""

  # Choose CLI tool
  echo "Select AI CLI tool:"
  echo "1) Gemini"
  echo "2) Claude"
  echo ""
  read -p "Enter choice (1 or 2): " CLI_CHOICE

  # Ensure correct directory permissions (standard home directory 750)
  mkdir -p "$CONTAINER_HOME"
  chmod 750 "$CONTAINER_HOME" 2>/dev/null || sudo chmod 750 "$CONTAINER_HOME" 2>/dev/null || true

  case "$CLI_CHOICE" in
    1)
      echo ""
      echo "🚀 Starting Gemini CLI authentication..."
      echo "📂 Authentication path: $CONTAINER_HOME"
      echo "💡 Tip: Credentials will be stored in $CONTAINER_HOME/.gemini"
      echo ""
      if HOME="$CONTAINER_HOME" gemini --yolo; then
        echo ""
        echo "✅ Gemini authentication completed!"
        echo "📦 Credentials stored at: $CONTAINER_HOME/.gemini"
      else
        echo ""
        echo "⚠️  Error during authentication, please check directory permissions"
        echo "   Try: sudo chmod 777 $CONTAINER_HOME"
      fi
      ;;
    2)
      echo ""
      echo "🚀 Starting Claude CLI authentication..."
      echo "📂 Authentication path: $CONTAINER_HOME"
      echo "💡 Tip: Credentials will be stored in $CONTAINER_HOME/.claude"
      echo ""
      if HOME="$CONTAINER_HOME" claude --permission-mode bypassPermissions; then
        echo ""
        echo "✅ Claude authentication completed!"
        echo "📦 Credentials stored at: $CONTAINER_HOME/.claude"
      else
        echo ""
        echo "⚠️  Error during authentication, please check directory permissions"
        echo "   Try: sudo chmod 777 $CONTAINER_HOME"
      fi
      ;;
    *)
      echo "❌ Invalid choice"
      exit 1
      ;;
  esac

  echo ""
  echo "📋 Container startup command:"
  echo "  docker compose -f docker-compose.${INSTANCE_NAME}.yml up -d bot"
}

# Step 1: Choose environment
echo ""
echo "Select execution environment:"
echo "1) Local environment (Local)"
echo "2) Container environment (Container)"
echo ""
read -p "Enter choice (1 or 2): " ENV_CHOICE

case "$ENV_CHOICE" in
  1)
    echo "🖥️  Selected: Local environment"
    run_local_auth
    ;;
  2)
    echo "🐳 Selected: Container environment"
    run_container_auth
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
