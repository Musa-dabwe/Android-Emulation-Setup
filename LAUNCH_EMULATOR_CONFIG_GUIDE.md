# launch_emulator.py — Configuration Guide

A painfully detailed guide to configuring, understanding, and running the `launch_emulator.py` script. Every line explained. No assumptions made.

---

## Table of Contents

- [What the Script Does](#what-the-script-does)
- [Requirements](#requirements)
- [Getting the Script](#getting-the-script)
- [Making the Script Executable](#making-the-script-executable)
- [The CONFIG Block](#the-config-block)
  - [ANDROID_HOME](#android_home)
  - [ANDROID_AVD_HOME](#android_avd_home)
  - [AVD_NAME](#avd_name)
  - [SCALE](#scale)
  - [EXTRA_FLAGS](#extra_flags)
- [Running the Script](#running-the-script)
- [What Happens When You Run It](#what-happens-when-you-run-it)
- [Sanity Checks Explained](#sanity-checks-explained)
- [Extra Flags Reference](#extra-flags-reference)
- [Common Errors and Fixes](#common-errors-and-fixes)
- [Tips and Customization](#tips-and-customization)

---

## What the Script Does

In plain English, the script does four things in order:

1. **Checks for KVM** — warns you if hardware acceleration is unavailable
2. **Checks that your AVD exists** — exits early with a helpful message if the named device isn't found
3. **Sets environment variables** — so the emulator knows where the SDK and AVD files are
4. **Launches the emulator** — runs the exact same command you would type manually, but without you having to remember it

It is a convenience wrapper. Nothing more, nothing less. It does not install anything, modify any files, or require root access.

---

## Requirements

Before using the script, the following must already be in place. If any of these are missing, go back to the main setup guide first.

| Requirement | How to verify |
|---|---|
| Python 3 | `python3 --version` |
| Android SDK installed | `ls ~/android-sdk` (or wherever you installed it) |
| Emulator binary installed | `ls ~/android-sdk/emulator/emulator` |
| At least one AVD created | `avdmanager list avd` |

The script itself uses only Python standard library modules (`os`, `subprocess`, `sys`) — no pip installs required.

---

## Getting the Script

Place `launch_emulator.py` somewhere convenient. Good options:

```bash
# In your home directory
cp launch_emulator.py ~/launch_emulator.py

# In the SDK folder alongside everything else
cp launch_emulator.py ~/android-sdk/launch_emulator.py

# In a local bin folder (if you want to call it from anywhere)
mkdir -p ~/.local/bin
cp launch_emulator.py ~/.local/bin/launch_emulator.py
```

If you put it in `~/.local/bin/`, make sure that directory is in your PATH:

```bash
echo $PATH | grep -o '.local/bin'
```

If it's not, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH=$PATH:$HOME/.local/bin
```

Then reload:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

---

## Making the Script Executable

By default, a `.py` file downloaded or copied onto your system is not executable. You need to grant it execute permission before you can run it directly.

```bash
chmod +x launch_emulator.py
```

What `chmod +x` does: it adds the execute (`x`) bit to the file's permissions for all users. You can verify this worked:

```bash
ls -l launch_emulator.py
```

You should see something like:

```
-rwxr-xr-x 1 musa musa 1234 Apr 06 2026 launch_emulator.py
```

The `x` characters in `-rwxr-xr-x` confirm it is now executable.

> **Why does this matter?** Without the execute bit, running `./launch_emulator.py` gives you a "Permission denied" error. You can always work around this by running `python3 launch_emulator.py` directly — but making it executable is cleaner.

---

## The CONFIG Block

This is the only part of the script you ever need to touch. It lives at the very top of the file, clearly marked:

```python
# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANDROID_HOME     = os.path.expanduser("~/android-sdk")
ANDROID_AVD_HOME = os.path.expanduser("~/.config/.android/avd/")
AVD_NAME         = "android-9"
SCALE            = "0.6"
EXTRA_FLAGS      = ["-no-audio"]
# ──────────────────────────────────────────────────────────────────────────────
```

Each variable is explained in detail below.

---

### ANDROID_HOME

```python
ANDROID_HOME = os.path.expanduser("~/android-sdk")
```

**What it is:** The root directory of your Android SDK installation. This is the folder that contains `cmdline-tools/`, `emulator/`, `platform-tools/`, `system-images/`, etc.

**What `os.path.expanduser` does:** It replaces the `~` shorthand with your actual home directory path. For example, if your username is `musa`, then `~/android-sdk` becomes `/home/musa/android-sdk`. This is necessary because the emulator binary does not understand `~` — it needs the full absolute path.

**How to find the correct value:** Run:

```bash
ls ~/android-sdk
```

If you see folders like `emulator/`, `platform-tools/`, and `cmdline-tools/`, you're in the right place. If you installed the SDK somewhere else, use that path instead.

**Examples:**

```python
# Default — SDK is in your home directory
ANDROID_HOME = os.path.expanduser("~/android-sdk")

# SDK installed in /tmp (temporary, wiped on reboot)
ANDROID_HOME = "/tmp/android"

# SDK installed in /opt (system-wide install)
ANDROID_HOME = "/opt/android-sdk"

# SDK installed on an external drive
ANDROID_HOME = "/media/musa/external/android-sdk"
```

> **Important:** Do not include a trailing slash. `~/android-sdk` is correct. `~/android-sdk/` may cause path joining issues.

---

### ANDROID_AVD_HOME

```python
ANDROID_AVD_HOME = os.path.expanduser("~/.config/.android/avd/")
```

**What it is:** The directory where your Android Virtual Device (AVD) configuration files are stored. When you created your AVD with `avdmanager`, it saved two things here: a `.ini` file and a `.avd/` folder, both named after your device.

**How to verify the correct path:** Run:

```bash
ls ~/.config/.android/avd/
```

You should see something like:

```
android-9.avd/
android-9.ini
```

If that directory is empty or doesn't exist, try the alternative location:

```bash
ls ~/.android/avd/
```

Some Linux distributions store AVD files in `~/.android/avd/` instead of `~/.config/.android/avd/`. If your files are there, update the variable:

```python
# Alternative location used on some distros
ANDROID_AVD_HOME = os.path.expanduser("~/.android/avd/")
```

**Why this variable is needed:** Without it, the emulator looks for AVD files in a default location that may not match where `avdmanager` saved them. Setting it explicitly prevents "AVD not found" errors at launch time.

---

### AVD_NAME

```python
AVD_NAME = "android-9"
```

**What it is:** The name of the Android Virtual Device you want to boot. This must exactly match the name you gave the device when you created it with `avdmanager create avd -n "..."`.

**How to find your AVD name:** Run:

```bash
avdmanager list avd
```

Look for the `Name:` field in the output:

```
Available Android Virtual Devices:
    Name: android-9         ← this is your AVD_NAME
    Path: /home/musa/.config/.android/avd/android-9.avd
  Target: Default Android System Image
Based on: Android 9.0 ("Pie") Tag/ABI: default/x86_64
```

**Case sensitivity:** The name is case-sensitive. If your AVD is named `Android-9` and you set `AVD_NAME = "android-9"`, the script will not find it.

**Examples:**

```python
# A device named during creation with -n "android-9"
AVD_NAME = "android-9"

# A device named during creation with -n "google-34"
AVD_NAME = "google-34"

# A device with a custom name
AVD_NAME = "my-test-device"
```

> **Multiple AVDs:** If you have more than one AVD and want to switch between them, simply change this value. You could also duplicate the script and name each copy after the device it launches.

---

### SCALE

```python
SCALE = "0.6"
```

**What it is:** A multiplier that controls the size of the emulator window on your screen. The emulator renders at the device's native resolution, then scales the window by this factor for display.

**How to choose a value:**

| Value | Window size | Best for |
|---|---|---|
| `"0.3"` | Very small | High-res screens, saving screen space |
| `"0.5"` | Half size | Most desktop setups |
| `"0.6"` | 60% (default) | Comfortable general use |
| `"0.75"` | Three quarters | Larger monitors |
| `"1.0"` | Full native size | Pixel-accurate testing |
| `"auto"` | Fits the screen | Let the emulator decide |

**Note:** This setting only affects the window size on your display. It does not affect the resolution the emulated Android device thinks it has. Apps running inside the emulator still see the full native resolution.

**If running headless** (no window), this value is ignored. See `-no-window` in the [Extra Flags Reference](#extra-flags-reference).

---

### EXTRA_FLAGS

```python
EXTRA_FLAGS = ["-no-audio"]
```

**What it is:** A Python list of additional command-line flags to pass to the emulator binary. Each flag is a separate string in the list.

**Why it's a list:** The `subprocess.run()` call in the script expects a list of arguments, not a single string. Each flag must be its own list element.

**Correct formatting:**

```python
# One flag
EXTRA_FLAGS = ["-no-audio"]

# Multiple flags — each is a separate string in the list
EXTRA_FLAGS = ["-no-audio", "-no-window", "-wipe-data"]

# Flag with a value — the flag and its value are separate strings
EXTRA_FLAGS = ["-memory", "1024", "-no-audio"]

# No extra flags — use an empty list
EXTRA_FLAGS = []
```

**Incorrect formatting (do not do this):**

```python
# WRONG — this is one string, not two list elements
EXTRA_FLAGS = ["-memory 1024"]

# WRONG — this is a string, not a list
EXTRA_FLAGS = "-no-audio"
```

See the [Extra Flags Reference](#extra-flags-reference) section for a full list of available flags and what they do.

---

## Running the Script

Once the CONFIG block is set correctly, run the script one of two ways:

### Option A — Using python3 directly (always works)

```bash
python3 launch_emulator.py
```

### Option B — Running it directly (requires `chmod +x` first)

```bash
./launch_emulator.py
```

### Option C — From anywhere (requires it to be in your PATH)

If you placed the script in `~/.local/bin/` and that directory is in your PATH:

```bash
launch_emulator.py
```

---

## What Happens When You Run It

Here is exactly what the script does, step by step, in order:

### 1. KVM check

```python
def check_kvm():
    if not os.path.exists("/dev/kvm"):
        print("WARNING: /dev/kvm not found...")
```

The script checks whether `/dev/kvm` exists. This file is created by the Linux kernel when hardware virtualization (KVM) is available and your user has access to it.

- If `/dev/kvm` **exists**: the check passes silently, execution continues.
- If `/dev/kvm` **does not exist**: a warning is printed, but the script continues anyway. The emulator will still launch, just without hardware acceleration — expect it to be very slow.

This is a warning, not a hard stop. If you want it to be a hard stop, change `print(...)` to `sys.exit(1)`.

### 2. AVD existence check

```python
def check_avd():
    avd_path = os.path.join(ANDROID_AVD_HOME, f"{AVD_NAME}.avd")
    if not os.path.exists(avd_path):
        print(f"ERROR: AVD '{AVD_NAME}' not found at {avd_path}")
        sys.exit(1)
```

The script constructs the expected path to your AVD folder (`ANDROID_AVD_HOME/AVD_NAME.avd`) and checks whether it exists.

- If the folder **exists**: check passes, execution continues.
- If the folder **does not exist**: an error is printed showing exactly which path was checked, and the script exits with code 1. No emulator process is started.

This saves you from waiting for the emulator to start up only to fail with a cryptic error.

### 3. Environment setup

```python
env = os.environ.copy()
env["ANDROID_HOME"]     = ANDROID_HOME
env["ANDROID_AVD_HOME"] = ANDROID_AVD_HOME
```

The script copies your current environment variables and adds/overrides `ANDROID_HOME` and `ANDROID_AVD_HOME`. This environment is passed to the emulator process, so it knows where to find the SDK and AVD files even if you haven't set these variables in your shell session.

### 4. Command construction and launch

```python
cmd = [
    emulator_bin,
    "-avd", AVD_NAME,
    "-scale", SCALE,
    "-writable-system",
    *EXTRA_FLAGS,
]
subprocess.run(cmd, env=env)
```

The script assembles the final command as a list and prints it so you can see exactly what's being run. Then it hands off to `subprocess.run()`, which executes the emulator as a child process.

The script stays running (blocking) until the emulator window is closed. When you close the emulator, the script exits.

---

## Sanity Checks Explained

### Why check for `/dev/kvm`?

Running the emulator without KVM is technically possible but painfully slow — boot times can exceed 10 minutes and the device is barely usable. The check exists so you get an early warning rather than wondering why nothing is responding.

To fix KVM issues:

```bash
# Check if your CPU supports virtualization
egrep -c '(vmx|svm)' /proc/cpuinfo
# Output > 0 means yes

# Load the KVM module
sudo modprobe kvm_intel   # Intel
sudo modprobe kvm_amd     # AMD

# Add yourself to the kvm group
sudo usermod -aG kvm $USER
# Then log out and back in
```

### Why check for the AVD folder?

The emulator's own error messages when an AVD is missing are notoriously unhelpful. The script's check gives you the exact path it looked in, so you know immediately whether it's a typo in `AVD_NAME` or a wrong `ANDROID_AVD_HOME` path.

---

## Extra Flags Reference

These go in the `EXTRA_FLAGS` list. Mix and match as needed.

### Display

| Flag | Effect |
|---|---|
| `-no-window` | Run headless — no GUI window. Useful for SSH sessions or CI environments. |
| `-scale 0.5` | Already handled by the `SCALE` variable, but can be overridden here. |

### Performance

| Flag | Effect |
|---|---|
| `-no-audio` | Disables audio emulation. Reduces CPU load. Recommended if you don't need sound. |
| `-memory 1024` | Sets RAM available to the emulator in MB. Overrides `config.ini`. |
| `-cores 2` | Number of CPU cores to give the emulated device. |
| `-gpu auto` | GPU rendering mode. Options: `auto`, `host`, `swiftshader_indirect`, `off`. |

### Data and Storage

| Flag | Effect |
|---|---|
| `-wipe-data` | Wipes all user data and starts fresh on every boot. Useful for clean testing. |
| `-no-snapshot` | Disables snapshot saving/loading. Slower boot but cleaner state. |
| `-no-snapshot-save` | Loads snapshot on boot but doesn't save on exit. |
| `-no-snapshot-load` | Does a cold boot every time instead of resuming from snapshot. |

### System

| Flag | Effect |
|---|---|
| `-writable-system` | Already included by default in the script. Makes `/system` writable. |
| `-show-kernel` | Prints kernel log output to the terminal. Useful for debugging boot issues. |
| `-verbose` | Prints verbose emulator logs to the terminal. Very noisy but helpful for diagnosing crashes. |
| `-no-accel` | Disables hardware acceleration even if KVM is available. Useful for testing. |

### Networking

| Flag | Effect |
|---|---|
| `-no-dns` | Disables DNS lookup inside the emulator. |
| `-dns-server 8.8.8.8` | Sets a custom DNS server for the emulated device. |
| `-http-proxy http://host:port` | Routes emulator traffic through an HTTP proxy. |

### Example configurations

**Lightweight testing (low-end machine):**

```python
EXTRA_FLAGS = ["-no-audio", "-memory", "768", "-no-snapshot", "-gpu", "swiftshader_indirect"]
```

**Clean slate every boot:**

```python
EXTRA_FLAGS = ["-no-audio", "-wipe-data", "-no-snapshot"]
```

**Headless (no window, SSH session):**

```python
EXTRA_FLAGS = ["-no-window", "-no-audio"]
```

**Maximum debug output:**

```python
EXTRA_FLAGS = ["-verbose", "-show-kernel"]
```

---

## Common Errors and Fixes

### `ERROR: AVD 'android-9' not found at /home/musa/.config/.android/avd/android-9.avd`

**Cause:** Either `AVD_NAME` is wrong, or `ANDROID_AVD_HOME` is pointing to the wrong directory.

**Fix:**

```bash
# Step 1: Find where your AVDs actually are
find ~ -name "*.avd" -type d 2>/dev/null

# Step 2: Check what your AVDs are named
avdmanager list avd

# Step 3: Update AVD_NAME and ANDROID_AVD_HOME in the script to match
```

---

### `ERROR: Emulator binary not found at /home/musa/android-sdk/emulator/emulator`

**Cause:** The emulator was never installed, or `ANDROID_HOME` is pointing to the wrong location.

**Fix:**

```bash
# Install the emulator
sdkmanager --channel=0 emulator

# Or verify ANDROID_HOME is correct
ls $ANDROID_HOME/emulator/emulator
```

---

### `WARNING: /dev/kvm not found` followed by extremely slow emulator

**Cause:** KVM is not available. See [Sanity Checks Explained](#sanity-checks-explained) for the full fix.

---

### `Permission denied` when running `./launch_emulator.py`

**Cause:** The execute bit is not set on the file.

**Fix:**

```bash
chmod +x launch_emulator.py
```

---

### The emulator launches but immediately closes

**Cause:** Usually a misconfigured or corrupted AVD, or a missing system image.

**Fix:**

```bash
# Add -verbose to EXTRA_FLAGS temporarily to see what's going wrong
EXTRA_FLAGS = ["-verbose", "-no-audio"]

# Or check if the system image is still installed
sdkmanager --list_installed | grep system-images
```

---

### `subprocess.run` hangs and nothing happens

**Cause:** The emulator process started but is waiting for a display that doesn't exist (common in headless SSH sessions).

**Fix:** Add `-no-window` to `EXTRA_FLAGS`:

```python
EXTRA_FLAGS = ["-no-window", "-no-audio"]
```

Then interact with the emulator via adb from a separate terminal:

```bash
adb devices
adb shell
```

---

## Tips and Customization

### Switching between multiple AVDs

If you have more than one AVD, the quickest approach is to pass the AVD name as a command-line argument to the script. Here's how to modify the script to support that:

```python
import sys

# At the bottom of the CONFIG block, add:
if len(sys.argv) > 1:
    AVD_NAME = sys.argv[1]
```

Then you can run:

```bash
python3 launch_emulator.py android-9
python3 launch_emulator.py google-34
```

### Adding a launch shortcut (alias)

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
alias emulator-android9='python3 ~/android-sdk/launch_emulator.py'
```

Reload and use:

```bash
source ~/.bashrc
emulator-android9
```

### Running the emulator in the background

By default the script blocks your terminal until the emulator closes. To run it in the background and free your terminal immediately:

```bash
python3 launch_emulator.py &
```

Or modify the script to use `subprocess.Popen` instead of `subprocess.run`:

```python
# Replace:
subprocess.run(cmd, env=env)

# With:
subprocess.Popen(cmd, env=env)
print("Emulator launched in background.")
```

### Auto-starting adb after launch

Add this after `subprocess.Popen` if you want adb to connect automatically:

```python
import time
time.sleep(10)  # wait for emulator to boot enough
subprocess.run(["adb", "wait-for-device"])
print("Device ready.")
subprocess.run(["adb", "devices"])
```
