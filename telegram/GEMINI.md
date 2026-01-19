# Notification System Operation Guide

---

### 🚨 Mandatory Notification Rules

**Important**: The following situations must immediately send Telegram notifications without omission:

**System Prompt Commands**: When commands contain `【System Prompt】` or `This command is from Telegram`, you must report the results after task completion.

### 💻 Message Sending Specifications

To ensure message content displays completely (especially when containing `$`, `"`, `` ` `` and other symbols), please strictly follow these sending methods:

1. **Use Script Parameter Mode**:
   - ✅ **Correct**: `python3 telegram_notifier.py 'message content'`
   - ❌ **Avoid**: `python3 -c "from telegram_notifier..."` (prone to escape errors)

2. **Quote Usage Principles**:
   - Wrap the outermost layer uniformly with **single quotes** `'`.
   - Message content can freely use double quotes `"`, dollar signs `$`, etc., without additional escaping.
   - If the message itself contains single quotes, it's recommended to wrap with double quotes instead, or escape inner single quotes (`\'`).
   - Do not use `**` for text emphasis in messages, as it won't work in Telegram

**Sending Examples**:

```bash
# Send test notification
python3 telegram_notifier.py '🧪 {agent_name} Test message: System is operating normally!'

# General response
python3 telegram_notifier.py '💬 Hello! I am {agent_name}\nReceived your message and responding'

# System interaction confirmation
python3 telegram_notifier.py '🤖 {agent_name} received command\nProcessing your request...'
```
---

### 🕐 Notification Sending Timing
- **All user interactions**: Must immediately send Telegram notification response each time user sends any message
- **General conversation**: All conversations including greetings, inquiries, and chat must be responded via Telegram
- **System interaction start**: Immediately send Telegram notification to confirm receipt each time user makes a request
- **Service status checks**: Must notify results when performing any system checks or service management
- **Task start**: Explain what task is being executed and estimated completion time
- **When encountering difficulties**: Describe the problem and solutions being attempted
- **Task completion/errors**: Summarize results or error messages

### 🛡️ Security Notes

- Avoid including sensitive information in notifications, such as personal data, passwords, etc.

---

### 🔗 URL Link Processing Specifications (Preventing Hallucinations)

1. **Reject Guessing**: Never "calculate" or "combine" URLs on your own (e.g., guessing based on date formats). Only use links explicitly returned by search tools.
2. **Parse Redirects**: If search results are redirect links (such as `google.com/url?...` or `vertexaisearch...`), **must** use Python `requests.head()` or `curl -I` to resolve the original real URL (Canonical URL).
3. **Verify Validity**: Before sending URLs to users, must confirm they can be accessed normally (returning HTTP 200/301/302).
4. **Verify Source**: Confirm the final URL's domain matches the claimed news source (e.g., if source says PR Newswire, URL domain should be `prnewswire.com`).

---