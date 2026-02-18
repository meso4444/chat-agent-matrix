#!/usr/bin/env python3
import sys
import subprocess
import time
import re
import os

TARGET = sys.argv[1]              # e.g., session:0.0
KEYWORDS = ["allow", "approve", "trust", "apply"]

MAX_RETRY = 9                     # Maximum 9 retries (covering 40 second wait: 8 × 5s = 40s + 1 buffer)
INTERVAL = 5                      # 5 second interval between attempts
ATTEMPT_TIMEOUT = 40              # Total timeout for single trigger (seconds), needs to cover MAX_RETRY × INTERVAL

monitoring = False
last_alert_time = {}  # Track last alert time for each agent, cooldown time is 300 seconds (5 minutes)
ALERT_COOLDOWN = 300  # 5 minute cooldown time

# Debug logging (enabled when DEBUG=1)
DEBUG = os.getenv('DEBUG', '0') == '1'
log_file = f"/tmp/monitor_{TARGET.replace(':', '_')}.log"

def log(msg):
    if not DEBUG:
        return  # Don't log normally, zero overhead

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
    """Get hash of screen content, used to compare if screen content changed"""
    screen = capture()
    return hash(screen)

def contains_keyword(text):
    """Detect if text contains authorization keywords (whole word match, avoid false triggers)"""
    import re
    for keyword in KEYWORDS:
        # Use \b (word boundary) to ensure it's an independent word, not a substring
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            return True
    return False

def has_stuck_command_pattern(text):
    """Detect if pattern matches stuck command (prompt followed by unexecuted command)
    Examples: "* show output", "❯ command"
    """
    import re
    # Detect *, ❯ followed by text (need space in between)
    # Note: MULTILINE mode makes ^ match line start, not just string start
    pattern = r'^\s*[*❯]\s+\S'  # Prompt + space + non-space character
    return bool(re.search(pattern, text, re.MULTILINE))


def should_interrupt_stuck_command(previous_hash, current_hash, text):
    """Determine if stuck command should be interrupted
    Conditions:
    1. Matches stuck command pattern (prompt followed by text)
    2. Screen hash unchanged for 30 seconds (indicates truly stuck)
    """
    # Check if matches stuck command pattern
    if not has_stuck_command_pattern(text):
        return False

    # Check if screen hash is consistent (no change within 30 seconds)
    # Note: Actually need to track time on caller side, here only check pattern and hash
    if previous_hash != current_hash:
        return False

    return True


def should_send_alert(agent_name):
    """Check if alert should be sent (considering cooldown time)"""
    global last_alert_time

    current_time = time.time()

    # If first alert or cooldown time has passed
    if agent_name not in last_alert_time or \
       (current_time - last_alert_time[agent_name]) > ALERT_COOLDOWN:
        last_alert_time[agent_name] = current_time
        return True

    return False


def send_telegram_notification(agent_name, event_type):
    """Send Telegram notification to user (must check cooldown time first)"""
    try:
        telegram_script = os.path.join(os.path.dirname(__file__), "telegram_notifier.py")

        if event_type == "Sudo password interrupt":
            message = f"⚠️ [Agent: {agent_name}] Detected Sudo password prompt\n\nPlease instruct agent on next step"
        else:  # Authorization action
            message = f"⚠️ [Agent: {agent_name}] Executed {event_type}\n\nInterrupt or question agent if concerned"

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
                # Extract agent name
                agent_name = TARGET.split(':')[1] if ':' in TARGET else TARGET

                initial_hash = get_screen_hash()

                for attempt in range(MAX_RETRY):
                    # 🛡️ Safety check: force stop if total timeout exceeded
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

                # Send Telegram notification (check cooldown time)
                if should_send_alert(agent_name):
                    send_telegram_notification(agent_name, "Authorization action")
                else:
                    log(f"Alert for {agent_name} in cooldown, skipping")

            finally:
                # 🛡️ Always reset monitoring flag
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
    # Clean exit when stdin closes or process is interrupted
    if DEBUG:
        log("Monitor stopped (stdin closed or interrupted)")
    sys.exit(0)
except Exception as e:
    # Other exceptions also exit cleanly
    if DEBUG:
        log(f"Monitor error: {e}")
    sys.exit(1)
