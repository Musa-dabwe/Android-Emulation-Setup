#!/usr/bin/env python3
"""
android_setup.py — Full Android Emulation Setup Automation
Sets up the Android SDK, installs a system image, creates an AVD,
and configures it — all from scratch, interactively.
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import time
import platform

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
CMDLINE_TOOLS_URL  = "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"

# All Android versions: display name → API level
ANDROID_VERSIONS = {
    "Android 5.0  (Lollipop)    API 21": 21,
    "Android 5.1  (Lollipop)    API 22": 22,
    "Android 6.0  (Marshmallow) API 23": 23,
    "Android 7.0  (Nougat)      API 24": 24,
    "Android 7.1  (Nougat)      API 25": 25,
    "Android 8.0  (Oreo)        API 26": 26,
    "Android 8.1  (Oreo)        API 27": 27,
    "Android 9    (Pie)         API 28": 28,
    "Android 10                 API 29": 29,
    "Android 11                 API 30": 30,
    "Android 12                 API 31": 31,
    "Android 12L                API 32": 32,
    "Android 13   (Tiramisu)    API 33": 33,
    "Android 14   (UpsideDownCake) API 34": 34,
}

IMAGE_TAGS = {
    "default            — No Google apps. Lightest. Best for dev/testing.": "default",
    "google_apis        — Google APIs included. No Play Store.":             "google_apis",
    "google_apis_playstore — Full Play Store. Heaviest. System not writable.": "google_apis_playstore",
}

DEVICE_PROFILES = {
    "Phone   — Portrait, 1080x1920, density 420": {
        "width": 1080, "height": 1920, "density": 420,
        "orientation": "portrait", "screen_size": None,
    },
    "Tablet  — Landscape, 2560x1600, density 320": {
        "width": 2560, "height": 1600, "density": 320,
        "orientation": "landscape", "screen_size": "10.1",
    },
    "Custom  — I'll enter my own values": None,
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────

BOLD  = "\033[1m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

def banner(text):
    width = 60
    print(f"\n{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'─' * width}{RESET}\n")

def ok(text):
    print(f"{GREEN}  ✔  {text}{RESET}")

def info(text):
    print(f"{CYAN}  →  {text}{RESET}")

def warn(text):
    print(f"{YELLOW}  ⚠  {text}{RESET}")

def error(text):
    print(f"{RED}  ✘  {text}{RESET}")

def fatal(text):
    error(text)
    sys.exit(1)

def ask(prompt, default=None):
    """Prompt user for a yes/no answer. Returns True for yes."""
    hint = " [Y/n]" if default is True else " [y/N]" if default is False else " [y/n]"
    while True:
        val = input(f"{BOLD}  ?  {prompt}{hint}: {RESET}").strip().lower()
        if val == "" and default is not None:
            return default
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        print("     Please enter y or n.")

def ask_input(prompt, default=None):
    """Prompt user for a text value."""
    hint = f" [{default}]" if default else ""
    val = input(f"{BOLD}  ?  {prompt}{hint}: {RESET}").strip()
    if val == "" and default is not None:
        return default
    return val

def choose(prompt, options):
    """
    Present a numbered list of options and return the chosen value.
    options: list of strings (keys), returns the chosen string.
    """
    print(f"\n{BOLD}  {prompt}{RESET}\n")
    for i, opt in enumerate(options, 1):
        print(f"     {CYAN}{i}{RESET}. {opt}")
    print()
    while True:
        val = input(f"{BOLD}  →  Enter number (1–{len(options)}): {RESET}").strip()
        if val.isdigit() and 1 <= int(val) <= len(options):
            return list(options)[int(val) - 1]
        print(f"     Please enter a number between 1 and {len(options)}.")

def run(cmd, capture=False, input_text=None):
    """Run a shell command. Exits on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            input=input_text,
        )
        return result
    except FileNotFoundError:
        fatal(f"Command not found: {cmd[0]}")

def run_required(cmd, error_msg, input_text=None):
    """Run a command and exit with a message if it fails."""
    result = run(cmd, capture=True, input_text=input_text)
    if result.returncode != 0:
        fatal(f"{error_msg}\n     {result.stderr.strip()}")
    return result

def download_file(url, dest_path):
    """Download a file with a simple progress indicator."""
    filename = os.path.basename(url)
    info(f"Downloading {filename} ...")
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = int(count * block_size * 100 / total_size)
                pct = min(pct, 100)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                print(f"\r     [{bar}] {pct}%", end="", flush=True)
        urllib.request.urlretrieve(url, dest_path, reporthook)
        print()  # newline after progress bar
        ok(f"Downloaded {filename}")
    except Exception as e:
        fatal(f"Failed to download {url}: {e}")

def unzip_file(zip_path, dest_dir):
    """Unzip a file to a destination directory."""
    info(f"Extracting {os.path.basename(zip_path)} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    ok("Extraction complete")

# ─── STEPS ────────────────────────────────────────────────────────────────────

def check_prerequisites():
    banner("Step 1 — Checking Prerequisites")

    # OS check
    if platform.system() != "Linux":
        fatal("This script is designed for Linux only.")
    ok("Running on Linux")

    # Java
    result = run(["java", "--version"], capture=True)
    if result.returncode != 0:
        fatal(
            "Java is not installed. Install it first:\n"
            "     Debian/Ubuntu: sudo apt install openjdk-17-jdk\n"
            "     Arch:          sudo pacman -S jdk-openjdk\n"
            "     Fedora:        sudo dnf install java-17-openjdk"
        )
    java_ver = (result.stdout or result.stderr).splitlines()[0]
    ok(f"Java found: {java_ver.strip()}")

    # unzip
    if not shutil.which("unzip"):
        fatal("'unzip' is not installed. Run: sudo apt install unzip")
    ok("unzip found")

    # wget
    if not shutil.which("wget"):
        fatal("'wget' is not installed. Run: sudo apt install wget")
    ok("wget found")

    # KVM
    if os.path.exists("/dev/kvm"):
        ok("KVM available — hardware acceleration enabled")
    else:
        warn(
            "/dev/kvm not found. The emulator will work but may be very slow.\n"
            "     To enable KVM:\n"
            "       sudo modprobe kvm_intel   (Intel)\n"
            "       sudo modprobe kvm_amd     (AMD)\n"
            "       sudo usermod -aG kvm $USER  then log out and back in"
        )
        if not ask("Continue anyway?", default=False):
            fatal("Aborted by user.")


def get_install_dir():
    banner("Step 2 — Choose Install Location")
    default_dir = os.path.expanduser("~/android-sdk")
    print(f"     The Android SDK will be installed into a directory of your choice.")
    print(f"     Default: {default_dir}\n")
    chosen = ask_input("Install directory", default=default_dir)
    chosen = os.path.expanduser(chosen)

    if os.path.exists(chosen):
        warn(f"Directory already exists: {chosen}")
        contents = os.listdir(chosen)
        if contents:
            warn(f"It is not empty ({len(contents)} items found).")
            if not ask("Continue and install into this directory anyway?", default=False):
                fatal("Aborted by user.")
    else:
        os.makedirs(chosen, exist_ok=True)
        ok(f"Created directory: {chosen}")

    return chosen


def download_sdk_tools(sdk_dir):
    banner("Step 3 — Downloading SDK Tools")

    pt_zip  = os.path.join(sdk_dir, "platform-tools.zip")
    cmd_zip = os.path.join(sdk_dir, "cmdline-tools.zip")

    download_file(PLATFORM_TOOLS_URL, pt_zip)
    download_file(CMDLINE_TOOLS_URL,  cmd_zip)

    unzip_file(pt_zip,  sdk_dir)
    unzip_file(cmd_zip, sdk_dir)

    os.remove(pt_zip)
    os.remove(cmd_zip)
    ok("Zip files cleaned up")


def fix_directory_structure(sdk_dir):
    banner("Step 4 — Fixing Directory Structure")

    cmdline_dir = os.path.join(sdk_dir, "cmdline-tools")
    latest_dir  = os.path.join(cmdline_dir, "latest")

    if not os.path.exists(cmdline_dir):
        fatal(f"cmdline-tools directory not found at {cmdline_dir}. Download may have failed.")

    if os.path.exists(latest_dir):
        ok("cmdline-tools/latest/ already exists — skipping restructure")
    else:
        os.makedirs(latest_dir)
        for item in os.listdir(cmdline_dir):
            if item == "latest":
                continue
            shutil.move(os.path.join(cmdline_dir, item), os.path.join(latest_dir, item))
        ok("Moved cmdline-tools contents into latest/")

    platforms_dir = os.path.join(sdk_dir, "platforms")
    os.makedirs(platforms_dir, exist_ok=True)
    ok("platforms/ directory ready")


def get_sdkmanager(sdk_dir):
    """Return the full path to the sdkmanager binary."""
    return os.path.join(sdk_dir, "cmdline-tools", "latest", "bin", "sdkmanager")


def get_avdmanager(sdk_dir):
    """Return the full path to the avdmanager binary."""
    return os.path.join(sdk_dir, "cmdline-tools", "latest", "bin", "avdmanager")


def accept_licenses(sdk_dir):
    banner("Step 5 — Accepting SDK Licenses")
    sdkmanager = get_sdkmanager(sdk_dir)
    env = build_env(sdk_dir)
    info("Sending license acceptance to sdkmanager ...")
    # Feed a stream of 'y' answers for all license prompts
    yes_input = "\n".join(["y"] * 20)
    result = subprocess.run(
        [sdkmanager, "--licenses"],
        input=yes_input,
        text=True,
        capture_output=True,
        env=env,
    )
    ok("Licenses accepted")


def choose_system_image():
    banner("Step 6 — Choose Android Version & System Image")

    # Android version
    version_key = choose("Which Android version do you want to emulate?", ANDROID_VERSIONS.keys())
    api_level   = ANDROID_VERSIONS[version_key]
    ok(f"Selected: {version_key.strip()} (API {api_level})")

    # Image tag
    print()
    tag_key  = choose("Which system image type do you want?", IMAGE_TAGS.keys())
    tag      = IMAGE_TAGS[tag_key]
    ok(f"Selected tag: {tag}")

    image_path = f"system-images;android-{api_level};{tag};x86_64"
    return api_level, tag, image_path


def install_system_image(sdk_dir, image_path):
    banner("Step 7 — Installing System Image")
    sdkmanager = get_sdkmanager(sdk_dir)
    env = build_env(sdk_dir)
    info(f"Installing: {image_path}")
    info("This may take several minutes depending on your connection ...")
    result = subprocess.run(
        [sdkmanager, "--install", image_path],
        input="y\n",
        text=True,
        env=env,
    )
    if result.returncode != 0:
        fatal(
            f"Failed to install system image: {image_path}\n"
            "     Check your internet connection or try a different version/tag."
        )
    ok("System image installed")


def install_emulator(sdk_dir):
    banner("Step 8 — Installing Emulator")
    sdkmanager = get_sdkmanager(sdk_dir)
    env = build_env(sdk_dir)
    info("Downloading emulator binary ...")
    result = subprocess.run(
        [sdkmanager, "--channel=0", "emulator"],
        input="y\n",
        text=True,
        env=env,
    )
    if result.returncode != 0:
        fatal("Failed to install emulator.")
    ok("Emulator installed")


def choose_device_profile():
    banner("Step 9 — Choose Device Profile")
    profile_key = choose("What kind of device do you want to emulate?", DEVICE_PROFILES.keys())
    profile     = DEVICE_PROFILES[profile_key]

    if profile is None:
        # Custom profile
        print()
        info("Enter custom display settings:")
        width       = int(ask_input("Screen width  (pixels)", default="1080"))
        height      = int(ask_input("Screen height (pixels)", default="1920"))
        density     = int(ask_input("Screen density (dpi)  ", default="420"))
        orientation = ask_input("Initial orientation (portrait/landscape)", default="portrait")
        screen_size = ask_input("Screen size in inches (optional, press Enter to skip)", default="")
        profile = {
            "width": width, "height": height, "density": density,
            "orientation": orientation,
            "screen_size": screen_size if screen_size else None,
        }
    else:
        p = profile
        info(
            f"Profile: {p['width']}x{p['height']}, "
            f"density {p['density']}, "
            f"{p['orientation']}"
            + (f", {p['screen_size']} inch" if p.get("screen_size") else "")
        )

    return profile


def create_avd(sdk_dir, image_path, avd_name):
    banner("Step 10 — Creating Android Virtual Device")
    avdmanager = get_avdmanager(sdk_dir)
    env = build_env(sdk_dir)
    info(f"Creating AVD '{avd_name}' using {image_path} ...")
    result = subprocess.run(
        [avdmanager, "create", "avd", "-k", image_path, "-n", avd_name, "--force"],
        input="no\n",   # decline custom hardware profile — we configure manually
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        fatal(f"Failed to create AVD.\n     {result.stderr.strip()}")
    ok(f"AVD '{avd_name}' created")


def find_avd_home():
    """
    Detect where avdmanager actually stored the AVD files.
    Returns the avd home directory path.
    """
    candidates = [
        os.path.expanduser("~/.android/avd/"),
        os.path.expanduser("~/.config/.android/avd/"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Neither exists yet — return the default
    return candidates[0]


def configure_avd(avd_name, profile):
    banner("Step 11 — Configuring Virtual Device")

    avd_home   = find_avd_home()
    config_path = os.path.join(avd_home, f"{avd_name}.avd", "config.ini")

    if not os.path.exists(config_path):
        fatal(
            f"config.ini not found at {config_path}\n"
            "     The AVD may not have been created successfully."
        )

    # Read existing config
    with open(config_path, "r") as f:
        lines = f.readlines()

    # Build a dict of existing keys
    config = {}
    for line in lines:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, val = line.partition("=")
            config[key.strip()] = val.strip()

    # Apply our settings
    config["hw.lcd.width"]           = str(profile["width"])
    config["hw.lcd.height"]          = str(profile["height"])
    config["hw.lcd.density"]         = str(profile["density"])
    config["hw.initialOrientation"]  = profile["orientation"]
    config["hw.keyboard"]            = "yes"
    config["hw.ramSize"]             = "1536"
    config["hw.camera.back"]         = "none"
    config["hw.camera.front"]        = "none"

    if profile.get("screen_size"):
        config["hw.screen.size"] = profile["screen_size"]

    # Write back
    with open(config_path, "w") as f:
        for key, val in config.items():
            f.write(f"{key} = {val}\n")

    ok(f"config.ini written to {config_path}")
    info(f"  Resolution : {profile['width']}x{profile['height']}")
    info(f"  Density    : {profile['density']} dpi")
    info(f"  Orientation: {profile['orientation']}")
    info(f"  Keyboard   : enabled")
    info(f"  Camera     : disabled (saves resources)")


def build_env(sdk_dir):
    """Build an environment dict with ANDROID_HOME and AVD_HOME set."""
    avd_home = find_avd_home()
    env = os.environ.copy()
    env["ANDROID_HOME"]     = sdk_dir
    env["ANDROID_AVD_HOME"] = avd_home
    pt = os.path.join(sdk_dir, "platform-tools")
    em = os.path.join(sdk_dir, "emulator")
    cb = os.path.join(sdk_dir, "cmdline-tools", "latest", "bin")
    env["PATH"] = f"{cb}:{pt}:{em}:{env.get('PATH', '')}"
    return env


def update_bashrc(sdk_dir):
    banner("Step 12 — Updating Shell Configuration")

    avd_home  = find_avd_home()
    bashrc    = os.path.expanduser("~/.bashrc")
    zshrc     = os.path.expanduser("~/.zshrc")

    block = f"""
# Android SDK — added by android_setup.py
export ANDROID_HOME={sdk_dir}
export ANDROID_AVD_HOME={avd_home}
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/emulator
"""

    marker = "# Android SDK — added by android_setup.py"

    for rc_file in [bashrc, zshrc]:
        if not os.path.exists(rc_file):
            continue
        with open(rc_file, "r") as f:
            content = f.read()
        if marker in content:
            warn(f"Android SDK block already present in {rc_file} — skipping")
            continue
        with open(rc_file, "a") as f:
            f.write(block)
        ok(f"Updated {rc_file}")

    print()
    warn("Run the following to apply changes to your current session:")
    print(f"\n     source ~/.bashrc\n")


def print_summary(sdk_dir, avd_name, image_path, profile):
    banner("Setup Complete!")

    avd_home = find_avd_home()

    print(f"  {BOLD}SDK Location  :{RESET} {sdk_dir}")
    print(f"  {BOLD}AVD Home      :{RESET} {avd_home}")
    print(f"  {BOLD}AVD Name      :{RESET} {avd_name}")
    print(f"  {BOLD}System Image  :{RESET} {image_path}")
    print(f"  {BOLD}Resolution    :{RESET} {profile['width']}x{profile['height']} @ {profile['density']}dpi")
    print(f"  {BOLD}Orientation   :{RESET} {profile['orientation']}")

    emulator_bin = os.path.join(sdk_dir, "emulator", "emulator")

    print(f"\n  {BOLD}To launch your emulator:{RESET}")
    print(f"\n     export ANDROID_AVD_HOME={avd_home}")
    print(f"     {emulator_bin} -avd {avd_name} -scale 0.6 -writable-system -no-audio")

    print(f"\n  {BOLD}Or use launch_emulator.py with these settings:{RESET}")
    print(f"\n     ANDROID_HOME     = \"{sdk_dir}\"")
    print(f"     ANDROID_AVD_HOME = \"{avd_home}\"")
    print(f"     AVD_NAME         = \"{avd_name}\"")

    print(f"\n  {GREEN}{BOLD}Run 'source ~/.bashrc' then launch your emulator. Enjoy!{RESET}\n")


def ask_launch(sdk_dir, avd_name):
    """Offer to launch the emulator immediately."""
    print()
    if ask("Launch the emulator now?", default=True):
        emulator_bin = os.path.join(sdk_dir, "emulator", "emulator")
        env = build_env(sdk_dir)
        info("Launching emulator — this may take a minute to boot ...")
        subprocess.Popen(
            [emulator_bin, "-avd", avd_name, "-scale", "0.6", "-writable-system", "-no-audio"],
            env=env,
        )
        ok("Emulator launched in background.")
        info("Run 'adb devices' to confirm it's up.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}   Android Emulation Setup — Automated Installer{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(
        "\n  This script will guide you through setting up a complete\n"
        "  Android emulation environment from scratch.\n"
        "  No Android Studio required. No GUI. Just the terminal.\n"
    )

    if not ask("Ready to begin?", default=True):
        print("  Aborted. Run the script again when you're ready.\n")
        sys.exit(0)

    # ── Run all steps ──────────────────────────────────────────────
    check_prerequisites()

    sdk_dir = get_install_dir()

    download_sdk_tools(sdk_dir)

    fix_directory_structure(sdk_dir)

    accept_licenses(sdk_dir)

    api_level, tag, image_path = choose_system_image()

    install_system_image(sdk_dir, image_path)

    install_emulator(sdk_dir)

    profile = choose_device_profile()

    avd_name = ask_input(
        "Name your virtual device (no spaces)",
        default=f"android-{api_level}"
    )

    create_avd(sdk_dir, image_path, avd_name)

    configure_avd(avd_name, profile)

    update_bashrc(sdk_dir)

    print_summary(sdk_dir, avd_name, image_path, profile)

    ask_launch(sdk_dir, avd_name)


if __name__ == "__main__":
    main()
