# Chat Agent Matrix - Telegram Edition

> **Comprehensive Remote AI Agent System Based on Telegram Collaboration Interface**
>
> This project provides a complete automation framework that transforms Telegram into a high-performance remote AI command center. By integrating automated secure tunneling, dynamic Webhook binding, and terminal emulation technology, it enables cross-regional system collaboration and information brokerage.

## 🌟 Core Technical Advantages

*   **Automated Network Connection Management**: Built-in automation scripts resolve ngrok dynamic URL changes, ensuring continuous Webhook service availability.
*   **Multi-Engine Collaboration Architecture**: Supports switching between Claude Code (deep logic and code processing) and Google Gemini (high-speed information retrieval).
*   **Multimodal Image Support**: Equipped with automated image landing and analysis mechanisms, supporting image submission for real-time summarization and text extraction.
*   **Interactive Component Support**: Complete support for Telegram keyboard menus (Reply Keyboard) and custom command templates, optimizing operational efficiency.
*   **Asynchronous Notification Mechanism**: Implements real-time result reporting through terminal output monitoring.
*   **Multi-Instance Independent Deployment**: Run multiple completely independent instances on the same machine, each with its own configuration, environment variables, and ngrok tunnel, without duplicating code.
*   **Configuration and Environment Isolation**: Each Agent's authentication and configuration are completely separated. Changes inside containers do not affect the host source code, making management and maintenance easier.

---

## 🚀 Deployment Guide

### 1. Environment Initialization and Configuration

Run the integrated installation script, which will automatically configure the operating environment and launch an **interactive configuration wizard** to guide you through entering necessary credentials (ngrok Token, Telegram Token, etc.):

```bash
./install_dependencies.sh
```

> **Tip**: If you need to modify settings later, you can directly run `./setup_config.sh` to launch the configuration wizard without manually editing files.

### 2. Credential Instructions

#### A. ngrok Authtoken (Required)

1. Register and log in to [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
2. Find **Your Authtoken** at the top of the page.
3. Copy that Token (a long string starting with `2...`), you'll enter it in the installation wizard later.

#### B. TELEGRAM_BOT_TOKEN

1. Search for the official account **@BotFather** on Telegram and open a conversation.
2. Send the `/newbot` command and follow the prompts to enter your bot name.
3. After successful creation, BotFather will provide you with an **HTTP API Token**.
4. **Important**: Click the bot link and send at least one message (e.g., `/start`) to activate communication.

#### C. Personal TELEGRAM_CHAT_ID

1. Ensure you've entered the Token in the configuration wizard.
2. Send any message (e.g., `/start`) to your bot on Telegram.
3. **The configuration wizard will automatically detect** and retrieve your personal ID; you just need to press Enter to confirm.
4. If automatic detection fails, you can enter it manually.

### 3. Advanced Configuration (Optional)

To adjust the AI Agent list or customize the menu, edit **`config.yaml`**:

```bash
nano config.yaml
```

> **Note**: Sensitive information (Token/ID) has been moved to `.env` file management. To modify credentials, run `./setup_config.sh`.

### 4. Start Services

Run the main startup script, which will automatically complete tunnel establishment, Webhook registration, and all service initialization:

```bash
./start_all_services.sh
```

---

## 🐳 Containerized Deployment

This project supports Docker-based, highly isolated deployment solutions using the **ISC (Instance-Specific Config)** architecture, ensuring physical isolation and environment consistency across multiple deployment instances.

> **Tip**: For large-scale instance deployment needs, refer to [ngrok Plans and Limitations](https://ngrok.com/docs/pricing-limits) to assess connection bandwidth and tunnel requirements.

### 1. Deployment Procedure

#### A. Initialize Instance Configuration

Enter the deployment directory and launch the wizard, entering an instance name (e.g., `dev`):

```bash
cd docker-deploy
./setup_docker.sh
```

> **Output Files**: The system will generate `.env.dev`, `config.dev.yaml`, and `docker-compose.dev.yml`.

#### B. Execute "Host-Side Pre-warming" Authentication

To ensure AI engine tokens are correctly synchronized to the container, complete OAuth authorization on the host side first:

```bash
bash ./agent_credential_wizard.sh
```

*   **Function**: Authentication data will be stored directly in the host's `agent_home/` directory, ready for the container to mount and inherit after startup.

#### C. Build and Start Container

Use Docker Compose to solidify the image and start the service:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 2. Core Technical Features

*   **UAH (User Agent Home) Physical Isolation**: Each Agent has an independent mounted home directory, with the `HOME` variable precisely hijacked in the container to prevent credential cross-contamination.
*   **Image Hardening**: Source code is `COPY`ed into the image during the build phase, so changes within the container won't affect the host source code, achieving true operational environment isolation.
*   **Isolated Mapping**: Through Volume mounting, instance-specific `config.{inst}.yaml` and `.env.{inst}` are automatically aligned to standard paths in the container, implementing "one codebase, multiple instances".

---

## 🖥️ tmux Operation Guide

This system uses tmux in the background to maintain the operation of AI engines and Webhook servers. The following are common operations:

### 1. Enter/Attach Session

To view AI engine status or debug, run:

```bash
tmux attach -t ai_telegram_session
```

### 2. Window Switching and Common Shortcuts

After entering tmux, you can use the following key combinations (default prefix key is `Ctrl+B`):

*   **Press `Ctrl+B` followed by `0`**: Switch to AI engine window (Claude/Gemini).
*   **Press `Ctrl+B` followed by `1`**: Switch to Telegram API server window.
*   **Press `Ctrl+B` followed by `2`**: Switch to ngrok tunnel monitoring window.
*   **Press `Ctrl+B` followed by `D`**: **Detach** Session. This operation will return you to a normal terminal, but services will continue running in the background.

---

## ⚙️ Advanced Configuration

### Custom Menu

This system supports customizing Telegram's interactive menu through the `menu` array in `config.yaml`.

#### YAML Data Structure Example

```yaml
menu:
  # First row: two buttons
  - - label: "🌤 Weather Query"
      command: "Check today's weather status"
    - label: "📊 System Monitoring"
      command: "/status"

  # Second row: one button
  - - label: "🔄 Switch Agent"
      command: "/switch"
      prompt: "Enter Agent name:"
```

**💡 YAML Formatting Rules (Keyboard Layout):**

*   `menu` corresponds to the Telegram keyboard and is a 2D array.
*   **`- -` (double dash)**: Indicates the **start of a new row**.
*   **`  -` (indentation + single dash)**: Indicates the **next button in the same row**.
*   By adjusting indentation and dashes, you can freely design various button arrangements like 2x2, 3x1, etc.

*   **label**: The display text of the button.
*   **command**: The command string sent to the AI engine when triggered.

### Multimodal Image Processing and Isolation

The system has automated image landing and isolation mechanisms:

*   **Isolated Storage**: Images are stored in agent-specific directories based on the currently active Agent: `agent_home/{name}/images_temp/`.
*   **Retention Mechanism**: Supports differentiated cleanup, allowing you to set `images_retention_days` in each Agent's configuration (default 7 days). The system automatically scans and deletes files daily.

### AI Agent Network and Collaboration Configuration

You can define multiple Agents in `config.yaml` and enable them to share outputs through "collaboration groups":

```yaml
agents:
  - name: "Güpa"
    engine: "gemini"
    usecase: "Responsible for research and summarization..."
    cleanup_policy:
      images_retention_days: 3  # Differentiated cleanup

# Collaboration groups: members automatically establish bidirectional shared spaces (soft links)
collaboration_groups:
  - name: "core_team"
    members: ["Güpa", "Chöd"]
```

### Scheduler System

Supports both Cron and Interval modes, allowing Agents to actively execute tasks:

```yaml
scheduler:
  - name: "Daily Cleanup"
    type: "system"
    action: "cleanup_images"
    trigger: "interval"
    hour: 24
  - name: "Regular Report"
    type: "agent_command"
    agent: "Güpa"
    command: "Please provide the latest market summary"
    trigger: "cron"
    hour: 9
    minute: 0
```

#### Switch and Collaboration Commands

| Command | Purpose |
|---------|---------|
| `/switch [name]` | Switch the current dialogue Agent (supports fuzzy search, e.g., `/switch chod`) |
| `/inspect [name]` | **Monitoring Mode**: Dispatch the current Agent to check the target Agent's terminal screen |
| `/fix [name]` | **Emergency Mode**: System directly intervenes to restart the target Agent and attempt to recover memory |
| `/resume_latest` | **Resume Memory**: Automatically recover the current Agent's most recent conversation record |

---

## 🛠️ Technical Architecture and Component Overview

### 📂 Directory Structure

```text
telegram/
├── .env                             # Environment variables file (auto-generated)
├── agent_credential_wizard.sh       # AI engine authentication assistant (host-side pre-warming)
├── config.py                        # Configuration loading and validation module
├── config.yaml                      # System behavior and Agent definition file
├── install_dependencies.sh          # Environment initialization installation script
├── message_templates.yaml           # Notification message templates
├── setup_config.sh                  # Interactive configuration wizard (native environment)
├── start_all_services.sh            # Main startup script (tmux + Flask + Agent)
├── start_ngrok.sh                   # ngrok tunnel launcher
├── status_telegram_services.sh      # System status check tool
├── stop_telegram_services.sh        # System stop tool
├── telegram_notifier.py             # Telegram message sending module
├── telegram_webhook_server.py       # Flask Webhook server
├── agent_home/                      # Agent-specific working space (auto-generated)
│   ├── Güpa/                        # Agent example: Güpa (Gemini)
│   │   ├── GEMINI.md                # Self-awareness and operation guidelines
│   │   ├── knowledge/               # Proprietary knowledge base
│   │   ├── my_shared_space/         # Work output storage area
│   │   └── Chöd_shared_space@       # Collaboration link (pointing to partner's shared area)
│   └── Chöd/                        # Agent example: Chöd (Claude)
├── docker-deploy/                   # Container deployment resources
│   ├── scripts/
│   │   └── entrypoint.sh            # Container startup entry script
│   ├── setup_docker.sh              # Instance deployment wizard
│   ├── generate_config.py           # ISC configuration generation engine
│   ├── Dockerfile                   # Image hardening definition (multi-instance isolation)
│   ├── docker-compose.template.yml  # Multi-instance orchestration template
│   ├── docker-compose.{inst}.yml    # Service orchestration
│   ├── config.{inst}.yaml           # Instance configuration example (isolated file)
│   └── .env.{inst}                  # Instance environment variables example (isolated file)
└── telegram_scripts/                # Auxiliary scripts (Scheduler, Env Setup)
```

### Core Component Responsibilities

| Component Name | File Path | Function Description |
| :--- | :--- | :--- |
| **Configuration Loader** | `config.py` | Reads `.env` and `config.yaml`, supporting three-layer stacking (Base YAML → Instance YAML → Environment). |
| **Configuration Generator** | `docker-deploy/generate_config.py` | **(Container-specific)** Generates ISC instance configuration and docker-compose physical mount mappings. |
| **Entry Script** | `docker-deploy/scripts/entrypoint.sh` | **(Container-specific)** Initializes the container environment and delegates startup commands to `start_all_services.sh`. |
| **Image Definition** | `docker-deploy/Dockerfile` | Defines AI Agent operating environment, system dependencies, and code hardening logic (supports dynamic BUILD_USER). |
| **Service Orchestration** | `docker-deploy/docker-compose.template.yml` | Multi-instance orchestration template, auto-generates `docker-compose.{instance}.yml` instance configuration. |
| **Authentication Assistant** | `agent_credential_wizard.sh` | Host-side OAuth pre-warming, completes AI engine authentication before container mounting (Gemini/Claude). |

### Maintenance Scripts List

| File Name | Function Description |
| :--- | :--- |
| `start_all_services.sh` | **Main Startup Script**. Creates tmux session, initializes environment, and awakens all Agents. |
| `start_ngrok.sh` | **Connection Automation**. Launches tunnel and automatically updates Webhook URL. |
| `setup_config.sh` | **Configuration Wizard**. Interactively configures Bot Token, Chat ID, and environment variables. |
| `setup_docker.sh` | **Deployment Wizard**. **(Located in docker-deploy/)** One-click instance configuration, credentials, and image building. |
| `agent_credential_wizard.sh` | **Authentication Assistant**. Completes AI authentication on host side to prevent container interactive blocking. |

---

## 🔒 Security

1.  **Identity Authentication**: System enforces `TELEGRAM_CHAT_ID` checking. Webhook requests require dynamic Secret Token verification.
2.  **Sensitive Information Isolation**: Tokens stored in `.env` file (never commit to Git), using interactive wizards to avoid exposure.
3.  **Authentication Isolation**: Gemini/Claude tokens stored separately in `agent_home/{name}/.gemini/` and `.claude/`.
4.  **Process Isolation**: AI engine and API server run independently, communicating asynchronously through Telegram.
5.  **Encrypted Transmission**: All external communication transmitted through ngrok TLS 1.2+ encrypted tunnels.
6.  **Local Binding**: Flask server bound to `127.0.0.1` by default, not exposed to external networks.
7.  **Permission Management**: `agent_home` set to `750` permissions, containers run as non-root users.

## 📄 License

MIT License
