# Chat Agent Matrix - WSL Installation Guide

## Overview

This installer automatically:
- ✅ Install WSL (if not already installed)
- ✅ Automatically enable Virtual Machine Platform (Hyper-V)
- ✅ Configure all necessary settings
- ✅ Prompt you to restart your computer

**Users simply need to double-click to run, then restart!**

## Installation Steps

### Step 1: Double-Click to Run

1. Find the **install_wsl.bat** file
2. **Double-click it**
3. If you see "Do you want to allow this app to make changes to your device?", click **Yes**

### Step 2: Wait for Installation to Complete

The installer will automatically:

1. **Check WSL status** - Verify if WSL is installed
2. **Check Virtual Machine Platform** - Verify if Hyper-V is enabled
3. **Enable features if needed** - Automatically enable Virtual Machine Platform if required
4. **Prompt for restart** - Ask if you want to restart your computer

### Step 3: Choose Restart Option

After installation completes, you'll see:

**Restart computer now? (Y/N)**

- Enter **Y** → Restart immediately (recommended)
- Enter **N** → Restart later manually

#### ⚠️ Important Notice

**Virtual Machine Platform settings only take effect after restart!**

Without restarting, WSL2 will not work properly.

### Step 4: Setup After Restart

After restart:

1. Open the **Start** menu
2. Search for and open **Ubuntu** application
3. First run will prompt you to create a username and password - follow the instructions

### Step 5: Install Git Tool

After initial setup, install Git in the Ubuntu window:

```bash
sudo apt update
sudo apt install git -y
```

The system will prompt for your password. Enter the password you set in Step 3 and press Enter (password won't be visible while typing).

### Step 6: Clone and Install Chat Agent Matrix

Once Git is installed, clone the repository:

```bash
git clone https://github.com/meso4444/chat-agent-matrix.git
```

Then choose which chat platform you want to install:

**For Telegram Bot:**
```bash
cd chat-agent-matrix/telegram
./install_dependencies.sh
```

**For Line Bot:**
```bash
cd chat-agent-matrix/line
./install_dependencies.sh
```

7. Follow the setup wizard to complete configuration

## Troubleshooting

### Problem 1: No Response After Double-Clicking

**Solution:**
1. Make sure both `install_wsl.bat` and `install_wsl.ps1` are in the same folder
2. Try right-clicking `install_wsl.bat`
3. Select "Run as administrator"

### Problem 2: See User Account Control Prompt

**Solution:**
This is normal. Click **Yes** to allow the installer to make necessary system changes.

### Problem 3: Ubuntu Won't Start After Virtual Machine Platform is Enabled

**Possible cause:** Virtualization not enabled in BIOS

**Solution:**

#### Step 1: Enter BIOS (choose key by your computer brand)

**Lenovo (ThinkPad/IdeaCentre/Yoga/Legion):**
- Restart your computer
- **During restart**, when you see the Lenovo logo:
  1. Press **Enter**
  2. After the menu appears, press **F1**
- You're now in BIOS

**Other brands:**
- **Dell**: Press **F2** or **Del**
- **HP/Pavilion**: Press **F2** or **Esc**
- **ASUS**: Press **Del** or **F2**
- **MSI**: Press **Del**
- **Other**: Try **Del**, **F2**, **F10**, or **F12**

#### Step 2: Find Virtualization Option

In BIOS settings, look for any of these options (names vary by brand):
- "Virtualization Technology" (Intel VT-x)
- "VT-x"
- "AMD-V" (for AMD processors)
- "SVM Mode" (for AMD processors)
- "Enable Virtualization"

Options are usually in these menus:
- **Security**
- **Processor**
- **Chipset**
- **Advanced**

#### Step 3: Enable Virtualization

1. Select the virtualization option using arrow keys
2. Press Enter to open the option menu
3. After menu appears, press F1
4. Select "On" to enable using arrow keys
5. Press F10 to save and exit BIOS
6. System will restart

#### Step 4: Retry

After restarting:
1. Open Ubuntu from Start Menu
2. Or open PowerShell and type: `wsl`
3. Ubuntu should now work properly

### Problem 3.5: Can't Find Virtualization Option in BIOS

**If you can't find the "Virtualization Technology" option:**

#### Possible Causes

**Cause 1: Different option name**
- Search for any of these names:
  - Virtualization Technology
  - Intel VT-x
  - VT-x Support
  - Virtualization Mode
  - AMD-V (AMD processors)
  - SVM Mode (AMD processors)

**Cause 2: In a different menu**
- Check these menus:
  - Security
  - Processor
  - CPU
  - Chipset
  - Advanced
  - Features

**Cause 3: Already enabled**
- Virtualization might already be on
- Return to Windows and try WSL again

**Cause 4: CPU doesn't support virtualization**
- Not all CPUs support virtualization
- Check your CPU specifications
- Alternative: Use WSL 1 instead (run `wsl --set-default-version 1`)

#### Solutions
1. Take screenshots of all BIOS CPU menu options
2. Check all the menus mentioned above
3. If CPU doesn't support virtualization, switch to WSL 1 (run `wsl --set-default-version 1`)

### Problem 4: Error Message "HCS_E_HYPERV_NOT_INSTALLED"

**Meaning:** Virtual Machine Platform is not enabled

**Solution:**
1. Make sure you completed Steps 2 and 3 above
2. **Must restart your computer**
3. If still not fixed, check BIOS virtualization setting (see Problem 3)

### Problem 5: Windows Version Not Compatible

**Requirement:**
- Windows 10 version 2004 or newer
- Or Windows 11

**Check method:**
1. Press **Win+R**
2. Type **winver**
3. Check the "OS Build" number
4. Should be 19041 or higher

If your Windows version is too old, please update Windows first.

## WSL 1 vs WSL 2 - Selection Guide

### When to Use WSL 1?

**WSL 1 is good for:**
- ✅ Simple command-line operations
- ✅ Text processing and editing
- ✅ Basic development (no Docker needed)
- ✅ System administration tasks
- ✅ Learning Linux commands

**WSL 1 is NOT good for:**
- ❌ Docker / containerized development
- ❌ Kubernetes or complex orchestration
- ❌ Some databases (PostgreSQL, etc)
- ❌ GPU acceleration applications
- ❌ Production environments

### WSL 1 Limitations

| Feature | WSL 1 | WSL 2 |
|---------|-------|-------|
| **Startup time** | Fast (1-2 sec) | Slower (3-5 sec) |
| **Performance** | Slow | Fast |
| **File I/O** | Slow (cross-system) | Fast (native) |
| **Docker support** | ❌ Not supported | ✅ Supported |
| **Linux compatibility** | 70% | 100% |
| **Resource usage** | Lightweight | Medium (VM) |
| **System calls** | Incomplete | Complete |
| **GPU acceleration** | ❌ Not supported | ✅ Supported |

### How to Use WSL 1

**Install WSL 1:**
```powershell
wsl --install -d Ubuntu --web-download
wsl --set-default-version 1
```

**Check current version:**
```powershell
wsl --list --verbose
```

### Which Should You Choose?

**Choose WSL 1 if:**
- Your CPU doesn't support virtualization
- You only need basic Linux tools
- You need the most lightweight environment

**Choose WSL 2 if:**
- Your computer supports virtualization
- You do software development
- You need Docker / container technology
- You need full Linux compatibility

## FAQ

### Q: Will this installer modify my computer?

**A:** Yes, it will:
- Install WSL (Windows Subsystem for Linux)
- Enable Virtual Machine Platform (Hyper-V)

These are required to use WSL2.

### Q: Do I need internet connection?

**A:** Yes.
- First-time WSL installation downloads the Ubuntu distribution
- Later `install_dependencies.sh` commands download dependencies

### Q: How long does installation take?

**A:** Usually 5-15 minutes, depending on your internet speed and system performance.

### Q: Can I restart later?

**A:** Yes.
- When the installer asks, enter **N**
- Restart manually later
- But without restarting, WSL won't work

### Q: How do I uninstall WSL?

**A:** If needed:
1. Press **Win+R**
2. Type **optionalfeatures**
3. Uncheck:
   - Virtual Machine Platform
   - Windows Subsystem for Linux
4. Click OK and restart

## Need Help?

For more information, visit:
- [Microsoft WSL Official Documentation](https://docs.microsoft.com/en-us/windows/wsl/install)
- [Virtualization Support Check](https://aka.ms/enablevirtualization)

---

**Version:** v3.4
**Last Updated:** 2026-02-09
**Supported Systems:** Windows 10 version 2004 or newer, Windows 11
