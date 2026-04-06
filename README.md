# Android Emulation Setup (CLI Only)

A complete, annoyingly detailed guide to setting up an Android emulator from scratch using only command-line tools on Linux. No Android Studio. No GUI. Just the terminal.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Understanding the Tools](#understanding-the-tools)
- [Step 1 — Create the Working Directory](#step-1--create-the-working-directory)
- [Step 2 — Download the Tools](#step-2--download-the-tools)
- [Step 3 — Fix the Directory Structure](#step-3--fix-the-directory-structure)
- [Step 4 — Set Environment Variables](#step-4--set-environment-variables)
- [Step 5 — Choose and Install a System Image](#step-5--choose-and-install-a-system-image)
- [Step 6 — Install the Emulator Binary](#step-6--install-the-emulator-binary)
- [Step 7 — Create the Virtual Device (AVD)](#step-7--create-the-virtual-device-avd)
- [Step 8 — Configure the Virtual Device](#step-8--configure-the-virtual-device)
- [Step 9 — Start the Emulator](#step-9--start-the-emulator)
- [Android Version Reference](#android-version-reference)
- [System Image Tag Reference](#system-image-tag-reference)
- [Useful sdkmanager Commands](#useful-sdkmanager-commands)
- [Troubleshooting](#troubleshooting)
- [Optional: Build Tools](#optional-build-tools)

---

## Prerequisites

Before you do anything, make sure the following are in place.

### Java

The Android SDK tools require a working Java installation. OpenJDK 11 or newer will work. To verify:

```bash
java --version
```

You should see something like:

```
openjdk 22 2024-03-19
OpenJDK Runtime Environment (build 22)
OpenJDK 64-Bit Server VM (build 22, mixed mode, sharing)
```

If Java is not installed, install it via your package manager:

```bash
# Debian/Ubuntu
sudo apt install openjdk-17-jdk

# Arch Linux
sudo pacman -S jdk-openjdk

# Fedora
sudo dnf install java-17-openjdk
```

### unzip

The downloaded SDK packages are `.zip` files. Make sure `unzip` is available:

```bash
unzip --version
```

If not installed:

```bash
# Debian/Ubuntu
sudo apt install unzip

# Arch Linux
sudo pacman -S unzip
```

### wget

Used to download the SDK packages:

```bash
wget --version
```

### Hardware Virtualization (KVM)

The Android emulator relies on hardware virtualization for acceptable performance. Check if KVM is available:

```bash
ls /dev/kvm
```

If the file exists, you're good. If not, you'll need to enable virtualization in your BIOS/UEFI settings (look for "Intel VT-x" or "AMD-V"), then load the KVM kernel module:

```bash
# For Intel CPUs
sudo modprobe kvm_intel

# For AMD CPUs
sudo modprobe kvm_amd
```

Also make sure your user is in the `kvm` group:

```bash
sudo usermod -aG kvm $USER
# Log out and back in after this
```

---

## Understanding the Tools

Here's what each component does so you're not blindly running commands:

| Tool | What it does |
|---|---|
| `sdkmanager` | Downloads and manages SDK packages (system images, emulator, platform-tools, etc.) |
| `avdmanager` | Creates and manages Android Virtual Devices (AVDs) |
| `emulator` | The actual emulator binary that boots the virtual device |
| `adb` | Android Debug Bridge — connects to running emulators/devices for shell access, file transfer, app install, etc. |

---

## Step 1 — Create the Working Directory

Choose somewhere to keep your Android SDK files. This guide uses `/tmp/android` for simplicity, but if you want the setup to survive reboots, use a permanent location like `~/android-sdk` instead.

```bash
mkdir -p ~/android-sdk
cd ~/android-sdk
```

> **Note:** `/tmp` is cleared on reboot. If you use it, you'll have to redo all of this after restarting. Use `~/android-sdk` or similar for a permanent setup.

---

## Step 2 — Download the Tools

There are two packages you need to download: **platform-tools** and **commandline-tools**.

### platform-tools

Contains `adb` (Android Debug Bridge) and other low-level utilities.

```bash
wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip
unzip platform-tools-latest-linux.zip
```

This will create a `platform-tools/` directory.

### commandline-tools

Contains `sdkmanager` and `avdmanager`.

```bash
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
```

> **Heads up:** The version number in the filename (`11076708`) may change over time. Check [https://developer.android.com/studio#command-tools](https://developer.android.com/studio#command-tools) for the latest download link if this one fails.

This will create a `cmdline-tools/` directory.

---

## Step 3 — Fix the Directory Structure

This is a quirky but mandatory step. The `sdkmanager` tool expects to find itself inside a folder called `latest` within `cmdline-tools`. If you skip this, sdkmanager will refuse to run and give you cryptic errors.

```bash
cd cmdline-tools
mkdir latest
mv * latest 2>/dev/null || true
cd ..
```

> **Why `2>/dev/null || true`?** The `mv * latest` command will try to move the `latest` folder into itself, which throws an error. Redirecting stderr silences that specific error without hiding anything important.

After this, your directory structure should look like this:

```
android-sdk/
├── cmdline-tools/
│   └── latest/
│       ├── bin/
│       │   ├── sdkmanager
│       │   └── avdmanager
│       └── lib/
├── platform-tools/
│   ├── adb
│   └── ...
```

Also create the `platforms/` directory, which sdkmanager expects to exist:

```bash
mkdir -p platforms
```

---

## Step 4 — Set Environment Variables

These environment variables tell the SDK tools where everything lives. You need to set them every session, so consider adding them to your `~/.bashrc` or `~/.zshrc`.

```bash
export ANDROID_HOME=~/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/emulator
```

To apply immediately in your current session:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

To verify sdkmanager is now accessible:

```bash
sdkmanager --version
```

---

## Step 5 — Choose and Install a System Image

### List available system images

```bash
sdkmanager --list | grep "system-images"
```

This outputs a long list. You're looking for lines in the format:

```
system-images;android-<API_LEVEL>;<TAG>;<ABI>
```

For example:
```
system-images;android-34;google_apis;x86_64
system-images;android-28;default;x86_64
system-images;android-31;google_apis_playstore;x86_64
```

### Which version should I install?

See the [Android Version Reference](#android-version-reference) section below for a full table. Short answer:

- **Android 9 (API 28)** — lightest, great for low-resource machines
- **Android 12 (API 31)** — good balance of modern features and performance
- **Android 14 (API 34)** — latest, but heaviest on resources

### Which image tag should I use?

See the [System Image Tag Reference](#system-image-tag-reference) section. Short answer:

- `default` — no Google apps, lightest
- `google_apis` — includes Google APIs but no Play Store
- `google_apis_playstore` — includes full Play Store (heaviest)

### Install the image

Replace the image path below with whichever you chose:

```bash
# Android 9 (lightweight, recommended for low-end machines)
sdkmanager --install "system-images;android-28;default;x86_64"

# Android 12 (balanced)
sdkmanager --install "system-images;android-31;google_apis;x86_64"

# Android 14 (latest, resource-heavy)
sdkmanager --install "system-images;android-34;google_apis;x86_64"
```

On the first run, you'll be prompted to accept the license agreement. Read it (or don't) and type `y` to accept:

```
Accept? (y/N): y
```

---

## Step 6 — Install the Emulator Binary

The `emulator` binary is what actually boots and runs your virtual device. Install it via sdkmanager:

```bash
sdkmanager --channel=0 emulator
```

> **What is `--channel=0`?** This specifies the stable release channel. Channel 0 = stable, channel 1 = beta, channel 3 = canary. Always use channel 0 unless you have a specific reason not to.

After installation, an `emulator/` directory will appear in your SDK root containing the `emulator` binary.

---

## Step 7 — Create the Virtual Device (AVD)

An AVD (Android Virtual Device) is a configuration file that tells the emulator what hardware to simulate. Create one using `avdmanager`.

```bash
avdmanager create avd \
  -k "system-images;android-28;default;x86_64" \
  -n "android-9"
```

Explanation of flags:

| Flag | Meaning |
|---|---|
| `-k` | The system image to use (must match what you installed in Step 5) |
| `-n` | The name you want to give this AVD (you'll use this to launch it) |

When prompted:

```
Do you wish to create a custom hardware profile? [no]
```

Just press **Enter** to accept the default `no`. The defaults are fine for most use cases.

Verify the AVD was created:

```bash
avdmanager list avd
```

You should see output like:

```
Available Android Virtual Devices:
    Name: android-9
    Path: /home/youruser/.config/.android/avd/android-9.avd
  Target: Default Android System Image
Based on: Android 9.0 ("Pie") Tag/ABI: default/x86_64
  Sdcard: 512 MB
```

The AVD files live in `~/.config/.android/avd/` (or `~/.android/avd/` on some systems).

---

## Step 8 — Configure the Virtual Device

This step is optional but highly recommended. The AVD's config file lets you tweak hardware settings.

```bash
nano ~/.config/.android/avd/android-9.avd/config.ini
```

### Recommended tweaks

**Enable the hardware keyboard** (so you can type with your physical keyboard instead of clicking the on-screen one):

```ini
hw.keyboard = yes
```

**Set RAM size** (in MB). The default is often 1536MB. Lower it for better performance on weak machines:

```ini
hw.ramSize = 1024
```

**Set screen resolution** (width x height in pixels):

```ini
hw.lcd.width = 1080
hw.lcd.height = 1920
hw.lcd.density = 420
```

**Disable the camera** if you don't need it (saves resources):

```ini
hw.camera.back = none
hw.camera.front = none
```

**Set internal storage size:**

```ini
disk.dataPartition.size = 2048MB
```

Save and close the file when done.

---

## Step 9 — Start the Emulator

First, set the `ANDROID_AVD_HOME` variable so the emulator knows where your AVD files are:

```bash
export ANDROID_AVD_HOME=$HOME/.config/.android/avd/
```

Then launch the emulator:

```bash
emulator -avd android-9 -scale 0.6 -writable-system
```

Explanation of flags:

| Flag | Meaning |
|---|---|
| `-avd android-9` | Name of the AVD to boot (must match the `-n` you used in Step 7) |
| `-scale 0.6` | Scale the emulator window to 60% of its native resolution |
| `-writable-system` | Makes the `/system` partition writable (useful for advanced use cases) |

### Other useful launch flags

```bash
# Run without a window (headless mode, e.g. for CI or SSH sessions)
emulator -avd android-9 -no-window

# Disable audio (reduces resource usage)
emulator -avd android-9 -no-audio

# Allocate specific amount of RAM (overrides config.ini)
emulator -avd android-9 -memory 1024

# Wipe user data on boot (fresh start every time)
emulator -avd android-9 -wipe-data

# Show kernel logs in terminal
emulator -avd android-9 -show-kernel
```

### Verify the emulator is running via adb

Once the emulator is booted (the Android home screen appears), you can connect to it using adb:

```bash
adb devices
```

Output should show something like:

```
List of devices attached
emulator-5554   device
```

Open a shell on the emulator:

```bash
adb -s emulator-5554 shell
```

Install an APK:

```bash
adb -s emulator-5554 install myapp.apk
```

---

## Android Version Reference

| Android Version | API Level | RAM Usage (approx.) | Notes |
|---|---|---|---|
| Android 9 "Pie" | 28 | ~1 GB | Lightest modern option. Good app compatibility. |
| Android 10 | 29 | ~1.2 GB | Adds scoped storage, gesture nav. |
| Android 11 | 30 | ~1.3 GB | Chat bubbles, one-time permissions. |
| Android 12 | 31 | ~1.5 GB | Material You redesign. Solid balance. |
| Android 13 | 33 | ~1.8 GB | Per-app language, themed icons. |
| Android 14 | 34 | ~2+ GB | Latest. Heaviest. |

---

## System Image Tag Reference

When choosing a system image, the tag (the third segment of the image path) determines what's pre-installed:

| Tag | Google APIs | Play Store | Resource Usage | Best for |
|---|---|---|---|---|
| `default` | ❌ | ❌ | Lightest | App testing, dev work, low-end machines |
| `google_apis` | ✅ | ❌ | Medium | Apps that use Google APIs (Maps, Firebase, etc.) |
| `google_apis_playstore` | ✅ | ✅ | Heaviest | Full Android experience with Play Store |

> **Note:** `google_apis_playstore` images are also locked (the system partition is not writable) because of Play certification requirements. Use `google_apis` if you need write access.

---

## Useful sdkmanager Commands

```bash
# List all installed and available packages
sdkmanager --list

# List only installed packages
sdkmanager --list_installed

# Update all installed packages
sdkmanager --update

# Uninstall a package
sdkmanager --uninstall "system-images;android-28;default;x86_64"

# Accept all pending licenses at once
sdkmanager --licenses
```

---

## Troubleshooting

### `sdkmanager: command not found`

Your PATH doesn't include the SDK bin directory. Re-run:

```bash
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
```

Or check that the `latest/` folder structure was set up correctly (Step 3).

---

### `ANDROID_HOME` not set / SDK not found errors

Make sure you've exported `ANDROID_HOME` and that it points to the correct directory:

```bash
echo $ANDROID_HOME
ls $ANDROID_HOME
```

---

### Emulator is extremely slow

- Make sure KVM is enabled: `ls /dev/kvm`
- Make sure your user is in the `kvm` group: `groups $USER`
- Use a `default` tag image instead of `google_apis` — it's lighter
- Lower the API level (e.g. use Android 9 instead of 14)
- Reduce RAM in `config.ini`: `hw.ramSize = 1024`
- Disable the camera in `config.ini`

---

### `CANNOT LINK EXECUTABLE` or emulator crash on launch

Your emulator binary might be outdated or mismatched with the system image. Try updating:

```bash
sdkmanager --update
```

---

### `avdmanager list avd` shows "No AVDs available"

The AVD was not created successfully, or `ANDROID_AVD_HOME` is pointing to the wrong place. Check:

```bash
ls ~/.config/.android/avd/
# or
ls ~/.android/avd/
```

If the `.avd` folder and `.ini` file are there, just make sure `ANDROID_AVD_HOME` is set to the correct path.

---

### Emulator window doesn't appear

If you're on a headless server or SSH session without X forwarding, the emulator can't display a window. Either:

1. Run with `-no-window` flag and use `adb` to interact
2. Set up X11 forwarding in your SSH session: `ssh -X user@host`
3. Use a VNC setup to provide a display

---

## Optional: Build Tools

If you need to sign, align, or otherwise manipulate APKs, you'll also need the build tools (`zipalign`, `apksigner`, `aapt`).

### Install via sdkmanager

```bash
sdkmanager --install "build-tools;34.0.0"
```

Or download directly:

```bash
wget https://dl.google.com/android/repository/build-tools_r34-rc3-linux.zip
unzip build-tools_r34-rc3-linux.zip
```

### Add to PATH

```bash
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

### Common build tool usage

```bash
# Align an APK (required before signing)
zipalign -v 4 myapp-unaligned.apk myapp-aligned.apk

# Sign an APK with a keystore
apksigner sign \
  --ks my-release-key.jks \
  --ks-key-alias my-key-alias \
  --out myapp-signed.apk \
  myapp-aligned.apk

# Verify APK signature
apksigner verify myapp-signed.apk

# Inspect APK contents
aapt dump badging myapp.apk
```

---

## Full Environment Setup (Summary)

Add these lines to your `~/.bashrc` or `~/.zshrc` so everything persists across sessions:

```bash
# Android SDK
export ANDROID_HOME=~/android-sdk
export ANDROID_AVD_HOME=$HOME/.config/.android/avd/
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

Then reload:

```bash
source ~/.bashrc
```

---

*Based on the original guide by Leonardo Tamiano. Extended with Android version selection, image tag explanation, configuration options, troubleshooting, and build tool usage.*
