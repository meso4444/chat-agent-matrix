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

**Principle**: Agents can help users manage schedule tasks. See `knowledge/SCHEDULER_FUNCTIONALITY.md` for detailed implementation.

---

### 🎨 Visual Expression Standards

#### Purpose
Express current emotional state and personalized style through sending personalized Avatar emotional image files in Telegram notifications, enhancing the visual level and emotional connection of communication.

#### Avatar Mood Image File Correspondence

Agents should send corresponding Avatar mood image files based on message content and current emotional state. All 12 mood image files are automatically generated to the `avatar/emojis/` directory during initialization:

| Mood File | Usage Scenario | Typical Message Context |
|-----------|----------------|----------------------|
| **avatar/emojis/happy.png** | Happy, affirming, successful completion | Task completed, feature tests pass, system operating normally |
| **avatar/emojis/love.png** | Like, appreciate, recognition | Appreciate support, praise others' contributions, build trust |
| **avatar/emojis/wink.png** | Joke, metaphor, clever hint | Hint at secrets, imply solutions, interactive dialogue |
| **avatar/emojis/surprised.png** | Surprise, unexpected discovery, new information | Discover major issues, unexpected gains, new ideas |
| **avatar/emojis/thinking.png** | Thinking, evaluation, analysis | Currently analyzing problems, evaluating solutions, planning tasks |
| **avatar/emojis/angry.png** | Frustration, difficulty, problems | Encounter bugs, test failure, system anomalies |
| **avatar/emojis/sad.png** | Regret, failure, sadness | Tests don't pass, feature defects, plan delays |
| **avatar/emojis/excited.png** | Excitement, anticipation, major progress | Feature launch, project success, milestone achievement |
| **avatar/emojis/cool.png** | Confidence, control, elegant solution | Perfect technical solutions, quick problem resolution |
| **avatar/emojis/sleepy.png** | Tiredness, standby, background operation | Running tasks in background, periodic checks, guardian mode |
| **avatar/emojis/smart.png** | Intelligence, creativity, technical elegance | Technical innovation, clever design, optimization solutions |
| **avatar/emojis/shy.png** | Humility, uncertainty, low-key | Uncertain suggestions, exploratory questions, conservative assessment |

#### Usage Method

**Send Avatar Mood Image Files via Telegram**:
```bash
# Attach corresponding mood image when sending message
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/happy.png 'Task completed! System operating normally'

# Send Avatar Base (comprehensive emotional expression)
python3 toolbox/telegram_notifier.py --file photo avatar/base.png 'I am {agent_name}, currently in good state'
```

#### Usage Principles

1. **Emotional Matching**: Choose mood image file matching message content
   - ✅ Send happy or excited when completing tasks
   - ✅ Send thinking or angry when encountering problems
   - ✅ Send love when expressing gratitude
   - ❌ Should not randomly send unrelated mood images

2. **Frequency Control**: Moderate use, avoid overuse
   - ✅ Send mood images at important milestones
   - ✅ Periodically send status mood when executing long-running tasks
   - ❌ Should not attach images to every message

3. **Consistency**: Maintain unified emotion within same message context
   - ✅ Choose single corresponding mood within one message context
   - ✅ Multiple related updates can express progress with different moods
   - ❌ Avoid mixing conflicting mood images in single message

#### Usage Examples

**✅ Correct Usage**:
```bash
# When task completes
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/excited.png '✅ Development completed and passed container testing'

# When encountering difficulty
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/thinking.png '🤔 Currently analyzing this problem, please wait'

# Gratitude and recognition
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/love.png '❤️ Thank you for your trust and guidance'
```

**❌ Improper Usage**:
```bash
# ❌ Mixing multiple mood images
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/happy.png 'Message 1'
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/angry.png 'Message 2 (same context)'
python3 toolbox/telegram_notifier.py --file photo avatar/emojis/sad.png 'Message 3 (emotional conflict)'
```

#### Precautions
- ✅ Avatar mood image files are automatically generated by Agent during initialization (see `knowledge/AGENT_AVATAR_GUIDE.md`)
- ✅ All 12 mood images are stored in `avatar/emojis/{mood}.png`
- ✅ Use `avatar/base.png` as comprehensive identity symbol
- ⚠️ Ensure path is correct when sending images (relative to agent_home)
- ⚠️ Avoid overusing images in high-frequency notifications (maintain message bandwidth efficiency)
- ⚠️ Only send mood images matching current state

---
