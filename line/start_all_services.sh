#!/bin/bash
# 啟動 LINE → AI Agent 軍團 遠端控制系統

set -e

# 解析為絕對路徑
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.py"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 載入環境變數
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "🔐 已載入 .env 環境變數"
else
    echo "⚠️  警告: .env 檔案不存在，將使用 config.yaml 中的明文設定"
    echo "💡 建議執行 ./setup_config.sh 遷移敏感資訊"
fi

# 讀取配置
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")
FLASK_PORT=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import FLASK_PORT; print(FLASK_PORT)")

echo "🚀 啟動 Chat Agent Matrix (LINE Edition)"
echo "📡 連線方案: Cloudflare Tunnel"
echo "⏰ 啟動時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==========================================="
echo ""

# 基礎檢查
for cmd in tmux cloudflared python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ 未找到指令: $cmd，請先安裝依賴。"
        exit 1
    fi
done

# 終止現有 session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "🔄 終止現有 session '$TMUX_SESSION_NAME'..."
    tmux kill-session -t "$TMUX_SESSION_NAME"
    sleep 1
fi

# 建立主 session
echo "🖥️  建立 tmux session '$TMUX_SESSION_NAME'..."
tmux new-session -d -s "$TMUX_SESSION_NAME" -n "init" -c "$SCRIPT_DIR"

# 1. 初始化 Agent 環境
echo "🧬  正在初始化 Agent 生態環境..."
python3 "$SCRIPT_DIR/line_scripts/setup_agent_env.py"

# 2. 動態啟動 AI Agent 軍團
echo "🤖 正在部署 AI Agent 軍團..."
export SCRIPT_DIR
export TMUX_SESSION_NAME

python3 << 'EOF'
import sys
import os
import subprocess
import time

script_dir = os.environ['SCRIPT_DIR']
session_name = os.environ['TMUX_SESSION_NAME']
sys.path.append(script_dir)

try:
    from config import AGENTS, COLLABORATION_GROUPS
    
    rules_path = os.path.join(script_dir, 'agent_home_rules.md')
    template_path = os.path.join(script_dir, 'agent_home_rules_templates', 'agent_rule_gen_template.txt')
    
    with open(template_path, 'r') as f:
        gen_template = f.read()

    for i, agent in enumerate(AGENTS):
        name = agent['name']
        engine = agent['engine']
        usecase = agent.get('usecase', '無描述')
        home_path = os.path.join(script_dir, 'agent_home', name)
        
        # 產生協作脈絡
        collab_context_lines = []
        for grp in COLLABORATION_GROUPS:
            if name in grp.get('members', []):
                collab_context_lines.append(f"- 所屬團隊: {grp.get('name')} ({grp.get('description', '')})")
                collab_context_lines.append("  團隊成員權責:")
                roles = grp.get('roles', {})
                for member, role in roles.items():
                    marker = " (你)" if member == name else ""
                    collab_context_lines.append(f"  * {member}{marker}: {role}")
                collab_context_lines.append("")
        
        collab_context = "\n".join(collab_context_lines) if collab_context_lines else "無特定協作團隊配置。"

        print(f"   ▸ 啟動 Agent: {name} ({engine})")
        
        if i == 0:
            subprocess.run(['tmux', 'rename-window', '-t', f'{session_name}:0', name], check=True)
        else:
            subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', name, '-c', home_path], check=True)
        
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', f'cd {home_path}', 'Enter'], check=True)
        
        if engine == 'gemini':
            cmd = 'gemini --yolo'
            protocol_file = 'GEMINI.md'
        else:
            cmd = 'claude --permission-mode bypassPermissions'
            protocol_file = 'CLAUDE.md'
            
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', cmd, 'Enter'], check=True)
        
        # 檢查規範是否存在
        target_rule_file = os.path.join(home_path, protocol_file)
        if not os.path.exists(target_rule_file):
            print(f"     ✨ 觸發 {name} 自我建構規範文件中 (等待 10 秒啟動)...")
            
            protocol_path = os.path.join(script_dir, protocol_file)
            
            prompt = (gen_template.replace('{agent_name}', name)
                                 .replace('{agent_usecase}', usecase)
                                 .replace('{engine_doc_name}', protocol_file)
                                 .replace('{rules_path}', rules_path)
                                 .replace('{protocol_path}', protocol_path)
                                 .replace('{collaboration_context}', collab_context)
                                 .replace('{home_path}', home_path))
            
            time.sleep(10) 
            
            prompt_file = os.path.join(script_dir, f".prompt_temp_{name}")
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            
            with open(prompt_file, 'r') as pf:
                prompt_content = pf.read()

            # Use send-keys -l (literal) to simulate typing, bypassing paste mode
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', prompt_content], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            os.remove(prompt_file)

except Exception as e:
    print(f"❌ 部署過程中發生錯誤: {e}")
    sys.exit(1)
EOF

echo "   ✅ 所有 Agent 已就緒"
echo ""

# Window: Flask API
echo "📱 啟動 LINE Webhook API..."
tmux new-window -t "$TMUX_SESSION_NAME" -n "line_api" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:line_api" "python3 $SCRIPT_DIR/webhook_server.py" Enter

# 等待 Flask 啟動
sleep 3

# Window: Cloudflare Tunnel
echo "☁️  啟動 Cloudflare Tunnel..."
tmux new-window -t "$TMUX_SESSION_NAME" -n "cloudflared" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:cloudflared" "$SCRIPT_DIR/start_cloudflare_tunnel.sh" Enter

echo "⏳ 服務啟動中..."
sleep 2

# 回到第一個 Agent window
tmux select-window -t "$TMUX_SESSION_NAME:0"

echo "==========================================="
echo "🎉 Chat Agent Matrix (LINE) 已全員部署！"
echo ""
echo "📋 運行摘要:"
echo "   Session: $TMUX_SESSION_NAME"
echo "   已啟動 Agent 視窗:"
tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
echo ""
echo "🚀 連接 Session: tmux attach -t $TMUX_SESSION_NAME"
