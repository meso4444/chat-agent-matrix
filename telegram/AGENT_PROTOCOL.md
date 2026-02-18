# Notification System Operation Guide

---

### 🚨 Mandatory Notification Rules

**Important**: The following situations require immediate Telegram notification without exception:

**System Prompt Instructions**: When instructions contain `【System Prompt】` or `This instruction is from Telegram`, you must report the results after task completion.

### 💻 Message Sending Standards

To ensure message content displays completely (especially when containing `$`, `"`, `` ` `` and other symbols), strictly follow these sending methods:

1. **Use Script Parameter Mode**:
   - ✅ **Correct**: `python3 telegram_notifier.py 'message content'`
   - ❌ **Avoid**: `python3 -c "from telegram_notifier..."` (prone to escaping errors)

2. **Quotation Mark Usage Principles**:
   - Use **single quotes** `'` to wrap the outermost layer consistently.
   - Double quotes `"`, dollar signs `$` and other characters can be used freely inside messages without additional escaping.
   - If the message itself contains single quotes, it's recommended to wrap the outer layer with double quotes, or escape inner single quotes (`\'`).
   - Do not use \*\* for text emphasis in messages, as Telegram does not support it

**Sending Examples**:

```bash
# Send test notification
python3 telegram_notifier.py '🧪 {agent_name} Test message: System operating normally!'

# General response
python3 telegram_notifier.py '💬 Hello! I am {agent_name}\nReceived your message and responding'

# System interaction confirmation
python3 telegram_notifier.py '🤖 {agent_name} Received instruction\nProcessing your request...'
```
---

### 🕐 Notification Sending Timing
- **All User Interactions**: Send Telegram notification immediately when user sends any message
- **General Conversation**: All conversations including greetings, questions, and chat should respond via Telegram
- **System Interaction Start**: Send Telegram notification immediately to confirm receipt when user makes request
- **Service Status Check**: Must notify results when performing any system checks or service management
- **Task Start**: Explain what task is being executed, estimated completion time
- **When Encountering Difficulties**: Describe the problem and solutions being attempted
- **Task Completion/Error**: Summarize results or error messages

### 🛡️ Security Notes

- Avoid including sensitive information in notifications, such as personal data, passwords, etc.

---

### 🔗 URL Link Handling Standards (Preventing Hallucinations)

1. **Reject Guessing**: Never self-"infer" or "combine" URLs (e.g., guessing based on date format). Only use links explicitly returned by search tools.
2. **Parse Redirects**: If search results return redirect links (such as `google.com/url?...` or `vertexaisearch...`), **must** use Python `requests.head()` or `curl -I` to resolve the original true URL (Canonical URL).
3. **Verify Validity**: Before sending to users, must confirm the URL is accessible (returns HTTP 200/301/302).
4. **Source Verification**: Confirm the domain of the final URL matches the claimed news source (e.g., if source says PR Newswire, URL domain should be `prnewswire.com`).

---

### 📎 File Transfer Feature

#### Purpose
Send generated files, reports, logs, etc. directly to users to improve collaboration efficiency.

#### Supported File Types

| Type | Description | Examples |
|------|------|------|
| `document` | Documents (PDF, TXT, MD, etc.) | Technical reports, log files |
| `photo` | Image files | Screenshots, charts |
| `video` | Video files | Demonstrations, tutorials |
| `audio` | Audio files | Voice messages, music |

#### Usage Method

**1. Send Files Directly**:
```bash
# Send documents (with description)
python3 telegram_notifier.py --file document /path/to/report.pdf '📄 Task completion report'

# Send images
python3 telegram_notifier.py --file photo /tmp/screenshot.png 'Screenshot verification'

# Send video
python3 telegram_notifier.py --file video /tmp/demo.mp4 'Demo video\nDuration: 5 minutes'

# Send audio
python3 telegram_notifier.py --file audio /tmp/notification.wav 'Voice confirmation'
```

**2. Call from Python Code**:
```python
from telegram_notifier import send_file

# Send file
send_file('/path/to/file.pdf', 'document', '📊 Analysis report generated')

# Return True for success, False for failure
```

#### Precautions

- ✅ **Files must exist**: Confirm file path is correct and file exists before using
- ✅ **Keep descriptions concise**: Title/description character limit is 1024 characters
- ✅ **File size limit**: Telegram limits individual files ≤ 2GB (practically ≤ 50MB more stable)
- ⚠️ **Privacy protection**: Avoid sending files containing sensitive information (passwords, keys, personal data)
- ⚠️ **Format support**: Confirm receiving end supports that file format

#### Example Scenarios

**Scenario 1: Task completion report**
```bash
# Generate report and send
python3 generate_report.py > report.md
python3 telegram_notifier.py --file document report.md '✅ {agent_name} Task completed\nReport generated'
```

**Scenario 2: Monitor system status (screenshot)**
```bash
# Capture system status
tmux capture-pane -t session:window -p > screen.txt
python3 telegram_notifier.py --file document screen.txt '📊 System status screenshot - {timestamp}'
```

**Scenario 3: Share analysis results**
```bash
# Create analysis chart
python3 analysis.py --output chart.png
python3 telegram_notifier.py --file photo chart.png '📈 Analysis result chart'
```

---

### 📅 Schedule Task Management

**Principle**: Agents can help users manage schedule tasks. See `SCHEDULER_FUNCTIONALITY.md` for detailed implementation.

---
