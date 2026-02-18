#!/usr/bin/env python3
import sys
import subprocess
import time
import re
import os

TARGET = sys.argv[1]              # 例如 session:0.0
KEYWORDS = ["allow", "approve", "trust", "apply"]

MAX_RETRY = 9                     # 最多重試 9 次（覆蓋 40 秒等待: 8 × 5秒 = 40秒 + 1次緩衝）
INTERVAL = 5                      # 每次間隔 5 秒
ATTEMPT_TIMEOUT = 40              # 單次觸發的總超時時間（秒），需要覆蓋 MAX_RETRY × INTERVAL

monitoring = False
last_alert_time = {}  # 記錄各 agent 的上次告警時間，冷卻時間為 300 秒（5分鐘）
ALERT_COOLDOWN = 300  # 5 分鐘冷卻時間

# 調試日誌（DEBUG=1 時啟用）
DEBUG = os.getenv('DEBUG', '0') == '1'
log_file = f"/tmp/monitor_{TARGET.replace(':', '_')}.log"

def log(msg):
    if not DEBUG:
        return  # 平常不寫日誌，零開銷

    with open(log_file, 'a') as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        f.flush()

if DEBUG:
    log("Monitor started (DEBUG MODE)")

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def clean(text):
    text = ansi_escape.sub('', text)
    return text.lower()

def capture():
    result = subprocess.run(
        ["tmux", "capture-pane", "-pt", TARGET],
        capture_output=True,
        text=True
    )
    return clean(result.stdout)

def send_enter():
    subprocess.run(
        ["tmux", "send-keys", "-t", TARGET, "Enter"]
    )

def get_screen_hash():
    """獲取屏幕的哈希值，用於比較屏幕內容是否改變"""
    screen = capture()
    return hash(screen)

def contains_keyword(text):
    """檢測文本是否包含授權關鍵詞（整字匹配，避免誤觸發）"""
    import re
    for keyword in KEYWORDS:
        # 使用 \b（單詞邊界）確保是獨立單詞，不是子字符串
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            return True
    return False

def has_stuck_command_pattern(text):
    """檢測是否符合卡住指令的 pattern（提示符後面有指令未執行）
    例如："* show output", "❯ command"
    """
    import re
    # 檢測 *, ❯ 後面跟有文本的情況（需要中間有空格）
    # 注：MULTILINE 模式讓 ^ 匹配每行的開頭，而不只是字符串開頭
    pattern = r'^\s*[*❯]\s+\S'  # 提示符 + 空格 + 非空格字符
    return bool(re.search(pattern, text, re.MULTILINE))


def should_interrupt_stuck_command(previous_hash, current_hash, text):
    """判斷是否應該中斷卡住指令
    條件：
    1. 符合卡住指令 pattern（提示符後有文字）
    2. 畫面哈希值已 30 秒無變化（說明真的卡住了）
    """
    # 檢查是否符合卡住指令 pattern
    if not has_stuck_command_pattern(text):
        return False

    # 檢查畫面哈希值是否一致（30 秒內無變化）
    # 注：實際需要通過調用端追蹤時間，這裡只做 pattern 和哈希值檢查
    if previous_hash != current_hash:
        return False

    return True


def should_send_alert(agent_name):
    """檢查是否應該發送告警（考慮冷卻時間）"""
    global last_alert_time

    current_time = time.time()

    # 若是第一次告警或已過冷卻時間
    if agent_name not in last_alert_time or \
       (current_time - last_alert_time[agent_name]) > ALERT_COOLDOWN:
        last_alert_time[agent_name] = current_time
        return True

    return False


def send_telegram_notification(agent_name, event_type):
    """發送 Telegram 通知給用戶（需先檢查冷卻時間）"""
    try:
        telegram_script = os.path.join(os.path.dirname(__file__), "telegram_notifier.py")

        if event_type == "Sudo 密碼中斷":
            message = f"⚠️ [Agent: {agent_name}] 偵測到 Sudo 密碼提示\n\n請指示 agent 進行下一步"
        else:  # 授權操作
            message = f"⚠️ [Agent: {agent_name}] 已執行 {event_type}\n\n若有疑慮可對 agent 中斷操作或提問"

        subprocess.run(
            ["python3", telegram_script, message],
            timeout=10,
            capture_output=True
        )
        log(f"Telegram notification sent for {event_type}")
    except Exception as e:
        log(f"Failed to send Telegram notification: {e}")

try:
    for line in sys.stdin:
        clean_line = clean(line)
        log(f"Input: {repr(line.strip())} -> {repr(clean_line[:100])}")

        if monitoring:
            log("Already monitoring, skip")
            continue

        if contains_keyword(clean_line):
            log(f"Keyword detected! Triggering...")
            monitoring = True
            start_time = time.time()

            try:
                # 提取 agent 名稱
                agent_name = TARGET.split(':')[1] if ':' in TARGET else TARGET

                initial_hash = get_screen_hash()

                for attempt in range(MAX_RETRY):
                    # 🛡️ 安全檢查：超過總超時時間就強制停止
                    if time.time() - start_time > ATTEMPT_TIMEOUT:
                        log(f"Attempt timeout ({ATTEMPT_TIMEOUT}s), stopping")
                        break

                    screen = capture()
                    log(f"  Attempt {attempt+1}/{MAX_RETRY}: screen has keyword = {contains_keyword(screen)}")

                    if not contains_keyword(screen):
                        log(f"  Keyword disappeared, stopping")
                        break

                    send_enter()
                    log(f"  Sent Enter")
                    time.sleep(INTERVAL)

                final_hash = get_screen_hash()
                if final_hash == initial_hash:
                    log(f"Screen unchanged after {MAX_RETRY} attempts, stopping")

                log(f"Trigger cycle complete")

                # 發送 Telegram 通知（檢查冷卻時間）
                if should_send_alert(agent_name):
                    send_telegram_notification(agent_name, "授權操作")
                else:
                    log(f"Alert for {agent_name} in cooldown, skipping")

            finally:
                # 🛡️ 無論如何都要重置 monitoring 標誌
                monitoring = False

        elif has_stuck_command_pattern(clean_line):
            log(f"Stuck command pattern detected, waiting 30s to confirm...")
            monitoring = True

            try:
                initial_hash = get_screen_hash()
                time.sleep(30)
                final_hash = get_screen_hash()

                if initial_hash == final_hash:
                    log(f"Screen confirmed stuck (30s unchanged), sending Enter")
                    send_enter()
                else:
                    log(f"Screen changed, pattern resolved")
            finally:
                monitoring = False

except (EOFError, KeyboardInterrupt, BrokenPipeError):
    # stdin 關閉或進程被中斷時乾淨退出
    if DEBUG:
        log("Monitor stopped (stdin closed or interrupted)")
    sys.exit(0)
except Exception as e:
    # 其他異常也要乾淨退出
    if DEBUG:
        log(f"Monitor error: {e}")
    sys.exit(1)
