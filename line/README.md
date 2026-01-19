# ☀️🌙 Chat Agent Matrix - LINE Edition

> **Take the Red Pill. Control your AI Matrix through LINE.**

---

## 🎯 System Overview

**Chat Agent Matrix (LINE Edition)** uses **Cloudflare Tunnel** as the connection solution, providing Webhook services based on a fixed domain. This version is adapted to LINE Messaging API features, using Quick Reply as the main interaction interface.

### 🌟 LINE Edition Core Features
*   **Multi-Agent Matrix**: Control **Güpa (Gemini)** and **Chöd (Claude)** simultaneously.
*   **Fixed Domain**: Establish a fixed Webhook URL via Cloudflare Tunnel, no need to update LINE Console settings after each restart.
*   **Quick Reply Menu**: Adapted to LINE interface, providing quick command buttons above the chat box.
*   **Scheduling System**: Support automatic monitoring and differentiated image cleanup.

---

## 🔑 Prerequisites

### 1. Prepare Domain (Cloudflare)
This system relies on Cloudflare Tunnel to let LINE Webhook connect to your local computer.
1.  Go to [Cloudflare](https://www.cloudflare.com/) and register a free account.
2.  **Requirement**: You need to own a domain and host its DNS on Cloudflare (e.g., `example.com`).
3.  **Decide Webhook URL**: Choose a subdomain, e.g., `webhook.example.com`. This will be the `CLOUDFLARE_CUSTOM_DOMAIN` you fill in later.
    *   **Note**: This URL must be a subdomain of your own domain, you cannot arbitrarily use a URL that doesn't belong to you.

### 2. Create LINE Bot (Get Credentials)
1.  Go to [LINE Developers Console](https://developers.line.biz/) and log in.
2.  Click **Create a new provider**, enter a name and create it.
3.  Click **Create a LINE Official Account** (this will open a new window to Official Account Manager).
4.  Follow the instructions to complete creating your official account.
5.  **Enable Messaging API (in OA Manager)**:
    *   Click **Settings** in the top right corner of LINE Official Account Manager.
    *   Find **Messaging API** in the left menu and click to enable.
    *   Select the Provider you just created to complete the binding.
6.  **Get Credentials (back to Developers Console)**:
    *   Return to LINE Developers Console and click into your Provider and Channel.
    *   **Basic settings** tab: Scroll to the bottom and copy **Channel secret**.
    *   **Messaging API** tab: Scroll to the bottom **Channel access token** area, click **Issue** button to generate and copy the Token.
7.  **Configure Response Mode (in OA Manager)**:
    *   Click **Settings** in the top right corner of LINE Official Account Manager.
    *   Click **Response settings** in the left menu.
    *   In the **Messaging API** tab, turn off "Auto-reply messages" and "Greeting messages", and enable "Use webhooks".

---

## 🚀 Deployment Guide

### 1. Environment Initialization
Run the installation script, the system will automatically install Node.js, Claude Code, Gemini CLI and all Python dependencies:

```bash
./install_dependencies.sh
```

### 2. Configure Credentials (Security Setup)
We strongly recommend using the configuration wizard to encrypt and manage your tokens, which will automatically generate a `.env` file and prevent credential leakage:

```bash
./setup_config.sh
```
*   Enter LINE Token and Secret in sequence.
*   **Cloudflare Tunnel Name**: Give your tunnel a name (e.g., `line-bot-tunnel`).
*   **Cloudflare Domain**: Enter the complete subdomain you want to use (e.g., `webhook.example.com`).

### 3. Cloudflare Tunnel Setup (One-time)
If you haven't created a Tunnel and bound a custom domain yet, execute the guided script:
```bash
./setup_cloudflare_fixed_url.sh
```
*   **Authorization Process**: The script will automatically open your browser. Please log in to Cloudflare and select the main domain (Zone) where you own the subdomain for authorization.

### 4. Configure Webhook (Final Step)
*   After completing Tunnel setup, go back to the **Messaging API** tab in LINE Developers Console.
*   Paste the Tunnel URL (with `/webhook` appended) into the **Webhook URL** field and update it.
*   After starting the local service, click **Verify** to confirm the connection is successful.

### 5. Start Service
Execute the main startup script, the system will automatically load environment variables and initialize the ecosystem:

```bash
./start_all_services.sh
```

---

## ⚙️ Advanced Configuration

Edit `config.yaml` to customize system behavior.

### Customize Menu (Quick Reply)
This system supports customizing LINE quick reply buttons through the `menu` array.

```yaml
menu:
  # First row
  - - label: "🌤 Weather Query"
      command: "Query today's weather status"
    - label: "📊 System Monitoring"
      command: "/status"

  # Second row
  - - label: "🔄 Switch Target"
      command: "/switch {input}"
      prompt: "Please enter Agent name:"
```

### AI Agent Team and Collaboration
Define multiple agents and establish collaboration relationships:

```yaml
agents:
  - name: "Güpa"
    engine: "gemini"
    usecase: "Responsible for research and summarization..."
    cleanup_policy:
      images_retention_days: 3

# Collaboration group: members automatically establish bidirectional shared spaces (symlinks)
collaboration_groups:
  - name: "core_team"
    members: ["Güpa", "Chöd"]
```

### Scheduled Tasks (Scheduler)
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

---

## 🖥️ tmux Guide

This system uses tmux to maintain the operation of AI engines and Webhook servers in the background.

### 1. Enter/Attach Session
To view AI operation status or debug, execute:
```bash
tmux attach -t ai_line_session
```

### 2. Window Switching and Common Shortcuts
After entering tmux, you can use the following key combinations (default prefix key is `Ctrl+B`):

*   **`Ctrl+B` followed by `0`**: Switch to Agent 1 (Güpa).
*   **`Ctrl+B` followed by `1`**: Switch to Agent 2 (Chöd).
*   **`Ctrl+B` followed by `2`**: Switch to LINE Webhook API.
*   **`Ctrl+B` followed by `3`**: Switch to Cloudflare Tunnel monitoring.
*   **`Ctrl+B` followed by `D`**: **Detach** session, allowing services to continue running in the background.

---

## 📊 System Management and Commands

| Command | Description |
|------|------|
| `/status` | Check all agents' alive status, current role, and scheduled tasks. |
| `/switch [name]` | Switch the current conversation agent (supports fuzzy search). |
| `/inspect [name]` | **Monitoring mode**: Dispatch current agent to check target agent's terminal screen. |
| `/fix [name]` | **Emergency mode**: System directly intervenes to restart target agent and attempt to recover memory. |
| `/resume_latest` | **Recover memory**: Automatically restore the most recent conversation history of current agent. |

---

## 🛠️ Technical Architecture and Components

### 📂 Directory Structure
```text
line/
├── agent_home/                 # [Core] Agent's exclusive workspace (auto-generated)
│   ├── Güpa/                   # Agent example: Güpa (Gemini)
│   │   ├── GEMINI.md           # Self-awareness and operation guidelines
│   │   ├── knowledge/          # Exclusive knowledge base
│   │   ├── my_shared_space/    # Work output storage area
│   │   └── Chöd_shared_space@  # Collaboration link (pointing to partner's shared area)
│   └── Chöd/                   # Agent example: Chöd (Claude)
├── config.yaml                 # [Core] System behavior and agent definition file
├── config.py                   # Configuration loading and validation module
├── install_dependencies.sh     # Environment initialization script
├── line_notifier.py            # LINE message and Quick Reply sending module
├── line_scripts/               # Internal helper scripts (Scheduler, Env Setup)
├── setup_cloudflare_fixed_url.sh # Cloudflare Tunnel configuration script
├── setup_config.sh             # Interactive configuration wizard
├── start_all_services.sh       # Main startup script
├── status_all_services.sh      # System status check tool
├── stop_all_services.sh        # System shutdown tool
└── webhook_server.py           # Flask Webhook server
```

### Core Components Responsibilities
| Component | File | Function Description |
|------|------|----------|
| **Webhook Server** | `webhook_server.py` | Responsible for receiving LINE webhooks, handling Quick Replies, distributing commands to tmux, and integrating Scheduler. |
| **Scheduler Manager** | `scheduler_manager.py` | Based on APScheduler, responsible for executing scheduled tasks (Cron/Interval) and system cleanup. |
| **Environment Initializer** | `setup_agent_env.py` | Automatically creates agent directory structure, handles collaboration group symlinks (Shared Space). |
| **Notification Engine** | `line_notifier.py` | Responsible for calling LINE Messaging API for message and Quick Reply push. |
| **Configuration Loader** | `config.py` | Reads `.env` and `config.yaml`, providing unified variable interface. |
| **Constitution and Standards** | `agent_home_rules.md` | Defines agent self-awareness, directory structure permissions, and collaboration principles. |
| **Communication Protocol** | `CLAUDE.md` / `GEMINI.md` | Defines interaction specifications, command formats, and automated reporting standards between AI engines and notification systems. |

### Maintenance Scripts List
| File | Function Description |
|------|----------|
| `start_all_services.sh` | **Main startup script**. Creates tmux session, initializes environment, and guides agents to auto-generate operation manuals. |
| `setup_cloudflare_fixed_url.sh` | **Connection automation**. Guides Cloudflare login and creates fixed Webhook URL (LINE exclusive). |
| `status_all_services.sh` | **Health check**. Displays all agents' alive status, Flask API health, and Tunnel information. |
| `stop_all_services.sh` | **One-click stop**. Gracefully shut down all related processes and tmux session. |
| `setup_config.sh` | **Configuration wizard**. Interactive guide to create `.env` security configuration file. |
| `../auto-startup/install_systemd_line.sh` | **Service installation**. Register system as systemd service for automatic startup. |

---

## 📄 License
MIT License

