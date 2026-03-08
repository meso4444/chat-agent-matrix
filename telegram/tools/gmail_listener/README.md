# 📧 Gmail Email Listener & Agent Forwarding System

**Function**: Gmail email monitoring → Intelligent Agent forwarding → Telegram reporting

---

## ⚙️ Prerequisites: Google Cloud Setup

### 1. Create Google Cloud Project

1. Open [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New project"
3. Enter project name (e.g., `chat-agent-matrix`)
4. Click "Create"

### 2. Enable Gmail API

1. In Google Cloud Console, left menu click "APIs and Services"
2. Click "Enable APIs and Services"
3. Search for "Gmail API"
4. Click "Gmail API"
5. Click "Enable" button

### 3. Create OAuth 2.0 Credentials

1. Left menu click "APIs and Services" → "Credentials"
2. Click "Create Credentials" → "OAuth Client ID"
3. If prompted to configure OAuth consent screen, click "Configure"
   - Application name: Enter `chat-agent-matrix`
   - User support email: Enter your Gmail
   - Click "Save and Continue"
4. On "Credentials" page, click "Create OAuth 2.0 Client ID"
5. Application type select "Desktop application"
6. Name: Enter `gmail-listener`
7. Click "Create"

### 4. Download credentials.json

1. Find the OAuth 2.0 Client ID you just created
2. Click the download button (down arrow icon) on the right
3. Select "Download as JSON"
4. Rename the downloaded `client_secret_*.json` file to `credentials.json`
5. Copy to this directory

### 5. Set Authorized Redirect URI (Optional but recommended)

1. Find the OAuth 2.0 Client ID you created, click Edit
2. In "Authorized redirect URIs" add:
   ```
   http://localhost:8080/
   ```
3. Click "Save"

---

## 🚀 Quick Start (5 Minutes)

### 1️⃣ Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2️⃣ OAuth Authentication (One-time)
```bash
python3 gmail_auth_simple.py
```
- Authorize Gmail access in browser
- Auto-generates `token.json`

### 3️⃣ Configure Whitelist
Edit `whitelist.json`:

```json
{
  "whitelist_senders": [
    {
      "email": "your-email@example.com",
      "agents": ["Güpa", "Chöd"]
    }
  ],
  "tmux_session": "ai_telegram_session",
  "email_marker": "Hi"
}
```

### 4️⃣ Start Listener
```bash
python3 gmail_listener.py
```

---

## 📋 Usage Examples

### Send Email to Agent

**Email Content**:
```
To: your-email@example.com
Subject: Market Analysis
Content:

Hi Güpa

Please analyze the market trends from the past week
```

### System Auto-Process

✅ Detect email
✅ Check sender in whitelist
✅ Detect "Hi Güpa"
✅ Forward to Güpa's tmux
✅ Güpa executes command
✅ Report result via Telegram

---

## ⚙️ Configuration Guide

### whitelist.json

| Field | Description | Example |
|-------|-------------|---------|
| `email` | Sender email | `your-email@example.com` |
| `agents` | Triggerable agents | `["Accelerator", "Chöd"]` |
| `tmux_session` | tmux session name | `ai_telegram_session` |
| `email_marker` | Trigger keyword | `Hi` |

### Trigger Format

**Correct**:
```
Hi Accelerator    ✅
Hi Chöd           ✅
HI ACCELERATOR    ✅ (case-insensitive)
```

**Incorrect**:
```
Hello Accelerator ❌ (must use "Hi")
Hi accelerator    ❌ (agent name is case-sensitive)
HiAccelerator     ❌ (missing space)
```

---

## 📁 File Descriptions

| File | Function |
|------|----------|
| `gmail_auth_simple.py` | OAuth authentication script (one-time) |
| `gmail_listener.py` | Main listener script (core functionality) |
| `whitelist.json` | Configuration file |
| `credentials.json` | Google OAuth credentials |
| `token.json` | OAuth token (auto-generated) |
| `requirements.txt` | Python dependencies |

---

## 🔄 Workflow

```
Send email
  ↓
Gmail API
  ↓
gmail_listener.py detects new email
  ↓
Check whitelist → Not match → Skip
  ↓ Match
Detect "Hi [Agent_name]"
  ↓ Found
Build forwarding message
  ↓
Send to Agent via tmux
  ↓
Agent executes command
  ↓
Agent reports via telegram_notifier.py
  ↓
Telegram displays result
```

---

## 🔐 Security Notes

⚠️ **Important**:
- `token.json` contains sensitive credentials, **never upload**
- `credentials.json` do not share
- Whitelist should only contain trusted senders

Add to `.gitignore`:
```
token.json
credentials.json
.gmail_seen_messages
```

---

## 🆘 FAQ

### Q: "token.json does not exist"

A: Run OAuth authentication:
```bash
python3 gmail_auth_simple.py
```

### Q: "Agent tmux window does not exist"

A: Confirm Agent is running:
```bash
tmux list-windows -t ai_telegram_session
```

### Q: "Cannot detect Agent mention"

A: Confirm email format is correct:
```
Hi [Agent_name]  ← Must use "Hi"
(blank line)
Email content
```

---

## 📊 Features

✅ **Secure OAuth 2.0 Authentication**
✅ **Automatic Email Monitoring** (30-second polling)
✅ **Intelligent Whitelist Filtering**
✅ **Automatic Agent Forwarding**
✅ **Tmux Integration**
✅ **Multi-language Support**
✅ **Low API Consumption**

---

**Version**: 1.0
**Last Updated**: 2026-03-08
