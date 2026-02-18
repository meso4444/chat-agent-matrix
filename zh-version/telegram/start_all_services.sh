#!/bin/bash
# 啟動 Telegram → AI Agent 軍團 遠端控制系統

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
    echo "🔐 已載入 .env"
else
    echo "⚠️  警告: .env 檔案不存在"
fi

# 讀取配置
TMUX_SESSION_NAME=$(python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from config import TMUX_SESSION_NAME; print(TMUX_SESSION_NAME)")

echo "🚀 啟動 Chat Agent Matrix (Telegram Edition)"
echo "==========================================="

# 生成動態 Webhook Secret
SECRET_FILE="$SCRIPT_DIR/webhook_secret.token"
openssl rand -hex 32 > "$SECRET_FILE"
export WEBHOOK_SECRET_TOKEN=$(cat "$SECRET_FILE")

# 終止現有 session
if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
    echo "🔄 終止現有 session…"
    tmux kill-session -t "$TMUX_SESSION_NAME"
    sleep 1
fi

# 建立主 session
echo "🧬  建立 tmux session '$TMUX_SESSION_NAME'…"
tmux new-session -d -s "$TMUX_SESSION_NAME" -n "init" -c "$SCRIPT_DIR"

# 1. 初始化 Agent 環境
echo "🧬  正在初始化 Agent 生態環境…"
python3 "$SCRIPT_DIR/telegram_scripts/setup_agent_env.py"

# 2. 動態啟動 AI Agent 軍團
echo "🤖 正在部署 AI Agent 軍團…"
export SCRIPT_DIR
export TMUX_SESSION_NAME

python3 << 'EOF'
import sys
import os
import subprocess
import time
import re

script_dir = os.environ['SCRIPT_DIR']
session_name = os.environ['TMUX_SESSION_NAME']
sys.path.append(script_dir)

def wait_for_prompt(session_name, window_name, engine, max_wait=30):
    """等待 tmux pane 出現對應的 CLI 提示符

    Args:
        engine: 'claude' 或 'gemini'
        - claude → ❯
        - gemini → * 或 >
    """
    start_time = time.time()
    # 根據引擎選擇對應的提示符
    if engine == 'claude':
        prompt_markers = ['❯']
    else:  # gemini - 可能是 * 或 >
        prompt_markers = ['*', '>']

    while time.time() - start_time < max_wait:
        try:
            result = subprocess.run(
                ['tmux', 'capture-pane', '-t', f'{session_name}:{window_name}', '-p'],
                capture_output=True, text=True
            )
            output = result.stdout
            if not output:
                time.sleep(0.5)
                continue

            # 檢查整個 pane 內容是否包含任何預期的提示符
            for marker in prompt_markers:
                if marker in output:
                    print(f"       ✅ 檢測到 {engine} 提示符 '{marker}'")
                    return True
        except Exception as e:
            pass

        time.sleep(0.5)

    return False

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
            subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', name], check=True)

        # 設置 pipe-pane 監聽授權提示和卡住指令
        responder_script = os.path.join(script_dir, 'auto_permission_responder.py')
        subprocess.run(['tmux', 'pipe-pane', '-t', f'{session_name}:{name}',
                       f'python3 {responder_script} {session_name}:{name}'], check=True)

        # 📋 複製必要的工具腳本到 Agent home
        # 複製 telegram_notifier.py 到 agent_home（不放入 toolbox）
        telegram_notifier_src = os.path.join(script_dir, 'telegram_notifier.py')
        telegram_notifier_dst = os.path.join(home_path, 'telegram_notifier.py')
        if os.path.exists(telegram_notifier_src):
            subprocess.run(['cp', telegram_notifier_src, telegram_notifier_dst], check=True)

        # 建立共享空間、知識庫與記憶目錄
        shared_space_path = os.path.join(home_path, 'my_shared_space')
        os.makedirs(shared_space_path, exist_ok=True)

        knowledge_path = os.path.join(home_path, 'knowledge')
        os.makedirs(knowledge_path, exist_ok=True)

        memory_path = os.path.join(home_path, 'memory')
        os.makedirs(memory_path, exist_ok=True)

        # 初始化當日記憶檔
        from datetime import datetime
        today_memory_file = os.path.join(memory_path, 'memory.md')
        if not os.path.exists(today_memory_file):
            with open(today_memory_file, 'w', encoding='utf-8') as f:
                f.write(f"# {name} 的每日記憶\n\n")
                f.write(f"**日期**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write("## 今日任務記錄\n\n")

        # 📚 統一複製知識文檔邏輯
        # 複製規則和協議文件（直接到 agent_home）
        rule_files_to_copy = ['agent_home_rules.md', 'AGENT_PROTOCOL.md']
        for rule_file in rule_files_to_copy:
            src_file = os.path.join(script_dir, rule_file)
            dst_file = os.path.join(home_path, rule_file)
            if os.path.exists(src_file):
                subprocess.run(['cp', src_file, dst_file], check=True)

        # 複製知識庫文件（到 knowledge 目錄）
        knowledge_files_to_copy = ['SCHEDULER_FUNCTIONALITY.md']
        for knowledge_file in knowledge_files_to_copy:
            src_file = os.path.join(script_dir, knowledge_file)
            dst_file = os.path.join(knowledge_path, knowledge_file)
            if os.path.exists(src_file):
                subprocess.run(['cp', src_file, dst_file], check=True)

        # 複製 Template 文件（直接複製到 agent_home，不建立子目錄）
        template_src = os.path.join(script_dir, 'agent_home_rules_templates', 'agent_rule_gen_template.txt')
        template_dst = os.path.join(home_path, 'agent_rule_gen_template.txt')
        if os.path.exists(template_src):
            subprocess.run(['cp', template_src, template_dst], check=True)

        # 🎯 進入 Agent 工作目錄
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', f'cd {home_path}'], check=True)
        time.sleep(1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

        if engine == 'gemini':
            cmd = 'gemini --yolo'
            engine_doc_name = 'GEMINI.md'
        else:
            cmd = 'claude --permission-mode bypassPermissions'
            engine_doc_name = 'CLAUDE.md'

        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', cmd], check=True)
        time.sleep(1)
        subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

        # 等待 CLI 提示符出現（根據引擎類型檢查對應提示符，最多等待 60 秒）
        print(f"     ⏳ 等待 {name} CLI 啟動…")
        if not wait_for_prompt(session_name, name, engine, max_wait=60):
            print(f"     ⚠️ {name} 啟動超時（未檢測到 {engine} 提示符），仍然嘗試注入 prompt…")

        # ✅ 檢查規範文件是否已存在（避免重複注入與覆蓋）
        doc_path = os.path.join(home_path, engine_doc_name)
        if os.path.exists(doc_path):
            print(f"     ✅ {engine_doc_name} 已存在，跳過初始化注入（保護現有規範）")

            # 📋 注入 prompt：檢查規範是否完備
            print(f"     📋 注入規範檢查 prompt…")
            engine_upper = engine.upper()
            check_prompt = f"檢視AGENT_PROTOCOL.md內容,確認{engine_upper}.md的規範是否完備,並更新"

            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', check_prompt], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            # 🔒 雙重保險: 確保 prompt 被正確接收
            time.sleep(0.2)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)
        else:
            # 觸發 Agent 規範文件構建
            print(f"     ✨ 觸發 {name} 自我建構規範文件中…")

            # 指向 agent_home 中的本地副本
            rules_path = os.path.join(home_path, 'agent_home_rules.md')
            protocol_path = os.path.join(home_path, 'AGENT_PROTOCOL.md')  # 參考通知規則

            # 生成初始化 Prompt
            prompt = (gen_template.replace('{agent_name}', name)
                                 .replace('{agent_usecase}', usecase)
                                 .replace('{engine_doc_name}', engine_doc_name)
                                 .replace('{rules_path}', rules_path)
                                 .replace('{protocol_path}', protocol_path)
                                 .replace('{collaboration_context}', collab_context)
                                 .replace('{home_path}', home_path))

            prompt_file = os.path.join(script_dir, f".prompt_temp_{name}")
            with open(prompt_file, 'w') as f:
                f.write(prompt)

            with open(prompt_file, 'r') as pf:
                prompt_content = pf.read()

            # Use send-keys -l (literal) to simulate typing, bypassing paste mode
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', '-l', prompt_content], check=True)
            time.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            # 🔒 雙重保險: 所有 Agent 都需要粘貼模式確認
            # 這確保長 prompt 被正確發送
            time.sleep(0.2)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:{name}', 'Enter'], check=True)

            os.remove(prompt_file)

except Exception as e:
    print(f"❌ 部署過程中發生錯誤: {e}")
    sys.exit(1)
EOF

echo "   ✅ 所有 Agent 已就緒"

# Window: Flask Telegram API
echo "📱 啟動 Telegram Webhook API…"
tmux new-window -t "$TMUX_SESSION_NAME" -n "telegram" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:telegram" "python3 $SCRIPT_DIR/telegram_webhook_server.py"
sleep 1
tmux send-keys -t "$TMUX_SESSION_NAME:telegram" Enter

# 等待 Flask 啟動
sleep 3

# Window: ngrok Tunnel
echo "☁️  建立安全連線隧道 (ngrok)…"
tmux new-window -t "$TMUX_SESSION_NAME" -n "ngrok" -c "$SCRIPT_DIR"
tmux send-keys -t "$TMUX_SESSION_NAME:ngrok" "$SCRIPT_DIR/start_ngrok.sh"
sleep 1
tmux send-keys -t "$TMUX_SESSION_NAME:ngrok" Enter

echo "⏳ 正在同步網路位址與 Webhook…"
sleep 5

# 回到第一個 Agent window
tmux select-window -t "$TMUX_SESSION_NAME:0"

echo "==========================================="
echo "🎉 Chat Agent Matrix v1.0.0 已全員部署！"
echo ""
echo "📋 運行摘要:"
echo "   Session: $TMUX_SESSION_NAME"
echo "   已啟動 Agent 視窗:"
tmux list-windows -t "$TMUX_SESSION_NAME" -F "      • Window #{window_index}: #{window_name}"
echo ""
echo "🚀 連接 Session: tmux attach -t $TMUX_SESSION_NAME"
