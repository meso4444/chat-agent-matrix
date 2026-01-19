# Chat Agent Matrix - Telegram Edition

> **Comprehensive Remote AI Agent System Based on Telegram Collaboration Interface**
>
> This project provides a complete automation framework that transforms Telegram into a high-performance remote AI command center. By integrating automated secure tunneling, dynamic Webhook binding, and terminal simulation technology, it achieves cross-regional system collaboration and information delegation.

## 🌟 Core Technical Advantages

*   **Automated Network Connection Management**: Built-in automation scripts solve ngrok dynamic URL changes, ensuring Webhook service continuity.
*   **Multi-Engine Collaboration Architecture**: Support dual-engine switching between Claude Code (deep logic and code processing) and Google Gemini (high-speed information retrieval).
*   **Multimodal Image Support**: Automated image download and analysis mechanism, support sending images for real-time summarization and text extraction.
*   **Interactive Component Support**: Full support for Telegram keyboard menus (Reply Keyboard) and custom command templates, optimizing operational efficiency.
*   **Asynchronous Notification Mechanism**: Real-time result reporting through monitoring terminal output.

---

## 🚀 Deployment Guide

### 1. Environment Initialization and Configuration
Execute the integrated installation script. The system will automatically configure the operating environment and launch an **interactive configuration wizard** to guide you through entering necessary credentials (ngrok Token, Telegram Token, etc.):

```bash
./install_dependencies.sh
```

> **Tip**: If you need to modify settings later, you can directly execute `./setup_config.sh` to launch the configuration wizard without manually editing files.

### 2. Getting Credentials Explanation
#### A. ngrok Authtoken (Required)
1. Register and log in to [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
2. Find **Your Authtoken** at the top of the page.
3. Copy that Token (a long string starting with `2...`), which you'll enter in the installation wizard later.

#### B. TELEGRAM_BOT_TOKEN
1. Search for the official account **@BotFather** in Telegram and open a conversation.
2. Send the `/newbot` command and follow the prompts to enter a bot name.
3. After successful creation, BotFather will provide you with an **HTTP API Token**.
4. **Important**: Click on the bot link and send at least one message (like `/start`) to activate communication.

#### C. Personal TELEGRAM_CHAT_ID
1. Make sure you've entered the Token in the configuration wizard.
2. Send any message (like `/start`) to your bot in Telegram.
3. **The configuration wizard will automatically detect** and retrieve your personal ID. You just need to press Enter to confirm.
4. If automatic detection fails, you can also enter it manually.

### 3. Advanced Configuration (Optional)
If you need to adjust the AI Agent list or customize menus, edit **`config.yaml`**:
```bash
nano config.yaml
```
> **Note**: Sensitive information (Token/ID) has been moved to `.env` file management. To modify credentials, execute `./setup_config.sh`.

### 4. Start Service
Execute the main startup script. The system will automatically complete tunnel creation, Webhook registration, and all service initialization:

```bash
./start_all_services.sh
```

---

## 🖥️ tmux Guide

This system uses tmux to maintain the operation of AI engines and Webhook servers in the background. Here are common operations:

### 1. Enter/Attach Session
To view AI operation status or debug, execute:
```bash
tmux attach -t ai_telegram_session
```

### 2. Window Switching and Common Shortcuts
After entering tmux, you can use the following key combinations (default prefix key is `Ctrl+B`):

*   **`Ctrl+B` followed by `0`**: Switch to AI engine window (Claude/Gemini).
*   **`Ctrl+B` followed by `1`**: Switch to Telegram API server window.
*   **`Ctrl+B` followed by `2`**: Switch to ngrok tunnel monitoring window.
*   **`Ctrl+B` followed by `D`**: **Detach** session. This operation will return you to the regular terminal, but services will continue running in the background.

---

## ⚙️ Advanced Configuration

### Customize Menu (menu)
This system supports customizing Telegram interactive menus through the `menu` array in `config.yaml`.

#### YAML Data Structure Example
```yaml
menu:
  # First row: has two buttons
  - - label: "🌤 Weather Query"
      command: "Query today's weather status"
    - label: "📊 System Monitoring"
      command: "/status"

  # Second row: has one button
  - - label: "🔄 Switch Target"
      command: "/switch"
      prompt: "Please enter Agent name:"
```

**💡 YAML Layout Rules (Keyboard Layout):**
*   `menu` corresponds to the Telegram keyboard and is a two-dimensional array.
*   **`- -` (double dash)**: Represents the **start of a new row (Row)**.
*   **`  -` (indent + single dash)**: Represents the **next button on the same row**.
*   By adjusting indentation and dashes, you can freely design various button layouts like 2x2, 3x1, etc.

*   **label**: The label text displayed on the button.
*   **command**: The command string sent to the AI engine when triggered.

### Multimodal Image Processing and Isolation
The system features automated image landing and isolation mechanisms:
*   **Isolated Storage**: Images are stored in each Agent's dedicated directory based on the currently active Agent: `agent_home/{name}/images_temp/`.
*   **Retention Mechanism**: Supports differentiated cleanup. You can configure `images_retention_days` in each Agent's settings (default 7 days). The system automatically scans and cleans up daily.

### AI Agent Team and Collaboration Configuration
You can define multiple Agents in `config.yaml` and use "collaboration groups" to let them share outputs:

```yaml
agents:
  - name: "Güpa"
    engine: "gemini"
    usecase: "Responsible for research and summarization..."
    cleanup_policy:
      images_retention_days: 3  # Differentiated cleanup

# Collaboration group: members automatically establish bidirectional shared spaces (symlinks)
collaboration_groups:
  - name: "core_team"
    members: ["Güpa", "Chöd"]
```

### Scheduled Tasks System (Scheduler)
Supports both Cron and Interval modes to allow Agents to actively execute tasks:

```yaml
scheduler:
  - name: "Daily cleanup"
    type: "system"
    action: "cleanup_images"
    trigger: "interval"
    hour: 24
  - name: "Regular reporting"
    type: "agent_command"
    agent: "Güpa"
    command: "Please provide the latest market summary"
    trigger: "cron"
    hour: 9
    minute: 0
```

#### Switching and Collaboration Commands
| Command | Purpose |
|------|------|
| `/switch [name]` | Switch the current conversation Agent (supports fuzzy search, e.g., `/switch chod`) |
| `/inspect [name]` | **Monitoring mode**: Dispatch current Agent to check target Agent's terminal screen |
| `/fix [name]` | **Emergency mode**: System directly intervenes to restart target Agent and attempt memory recovery |
| `/resume_latest` | **Memory Recovery**: Automatically restore the most recent conversation history of current Agent |

---

## 🛠️ Technical Architecture and Component Description

### 📂 Directory Structure
```text
telegram/
├── .env.example                # Environment variables template
├── agent_home/                 # [Core] Agent-specific workspace (auto-generated)
│   ├── Güpa/                   # Agent example: Güpa (Gemini)
│   │   ├── GEMINI.md           # Self-awareness and operation guidelines
│   │   ├── knowledge/          # Dedicated knowledge base
│   │   ├── my_shared_space/    # Work output storage area
│   │   └── Chöd_shared_space@  # Collaboration link (pointing to partner's shared area)
│   └── Chöd/                   # Agent example: Chöd (Claude)
├── config.yaml                 # [Core] System behavior and Agent definition file
├── config.py                   # Configuration loading and validation module
├── install_dependencies.sh     # Environment initialization installation script
├── message_templates.yaml      # Notification message template
├── setup_config.sh             # Interactive configuration wizard
├── start_all_services.sh       # Main startup script (tmux + Flask + Agent)
├── start_ngrok.sh              # ngrok tunnel launcher
├── status_telegram_services.sh # System status check tool
├── stop_telegram_services.sh   # System shutdown tool
├── telegram_notifier.py        # Telegram message sending module
├── telegram_webhook_server.py  # Flask Webhook server
└── telegram_scripts/           # Internal auxiliary scripts (Scheduler, Env Setup)
```

### Core Component Responsibilities
| Component | File | Function Description |
|------|------|----------|
| **Webhook Server** | `telegram_webhook_server.py` | Responsible for receiving Webhooks, distributing commands to tmux, and integrating Scheduler and ImageManager. |
| **Scheduler Manager** | `scheduler_manager.py` | Based on APScheduler, responsible for executing scheduled tasks (Cron/Interval) and system cleanup. |
| **Environment Initializer** | `setup_agent_env.py` | Automatically creates Agent directory structure, handles collaboration group symlinks (Shared Space). |
| **Notification Engine** | `telegram_notifier.py` | Responsible for calling Telegram Bot API for message delivery. |
| **Configuration Loader** | `config.py` | Reads `.env` and `config.yaml`, providing unified variable interface. |
| **Constitution and Standards** | `agent_home_rules.md` | Defines Agent self-awareness, directory structure permissions, and collaboration principles. |
| **Communication Protocol** | `CLAUDE.md` / `GEMINI.md` | Defines interaction specifications, command formats, and automated reporting standards between AI engines and notification systems. |

### Maintenance Scripts List
| File | Function Description |
|------|----------|
| `start_all_services.sh` | **Main startup script**. Creates tmux session, initializes environment, and guides Agents to auto-generate operation manuals. |
| `start_ngrok.sh` | **Connection automation**. Launches tunnel and automatically updates Webhook URL (Telegram-specific). |
| `status_telegram_services.sh` | **Health check**. Displays all Agents' alive status, Flask API health, and Tunnel information. |
| `stop_telegram_services.sh` | **One-click stop**. Gracefully shuts down all related processes and tmux session. |
| `setup_config.sh` | **Configuration wizard**. Interactive guide to create `.env` security configuration file. |
| `../auto-startup/install_systemd_telegram.sh` | **Service installation**. Register system as systemd service for automatic startup. |

---

## 🔒 Security

1.  **Authentication**: The system enforces `TELEGRAM_CHAT_ID` verification. Unless the sender ID matches the whitelist, the Webhook server will reject any command processing.
2.  **Isolated Environment**: AI engines run in independent tmux sessions, decoupled from API servers, ensuring system stability.
3.  **Encrypted Transmission**: All external communications are transmitted through ngrok-provided TLS 1.2+ encrypted tunnels.

## 📄 License
MIT License