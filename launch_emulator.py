#!/usr/bin/env python3

import os
import subprocess
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANDROID_HOME     = os.path.expanduser("~/android-sdk")
ANDROID_AVD_HOME = os.path.expanduser("~/.android/avd/")
AVD_NAME         = "android-9"       # change to your AVD name
SCALE            = "0.6"
EXTRA_FLAGS      = ["-no-audio"]     # add/remove flags as needed
# ──────────────────────────────────────────────────────────────────────────────

def check_kvm():
    if not os.path.exists("/dev/kvm"):
        print("WARNING: /dev/kvm not found. Emulator will run without hardware acceleration and may be very slow.")

def check_avd():
    avd_path = os.path.join(ANDROID_AVD_HOME, f"{AVD_NAME}.avd")
    if not os.path.exists(avd_path):
        print(f"ERROR: AVD '{AVD_NAME}' not found at {avd_path}")
        print("Run: avdmanager list avd   to see available devices.")
        sys.exit(1)

def launch():
    emulator_bin = os.path.join(ANDROID_HOME, "emulator", "emulator")

    if not os.path.exists(emulator_bin):
        print(f"ERROR: Emulator binary not found at {emulator_bin}")
        print("Run: sdkmanager --channel=0 emulator")
        sys.exit(1)

    env = os.environ.copy()
    env["ANDROID_HOME"]     = ANDROID_HOME
    env["ANDROID_AVD_HOME"] = ANDROID_AVD_HOME

    cmd = [
        emulator_bin,
        "-avd", AVD_NAME,
        "-scale", SCALE,
        "-writable-system",
        *EXTRA_FLAGS,
    ]

    print(f"Launching AVD: {AVD_NAME}")
    print(f"Command: {' '.join(cmd)}\n")

    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    check_kvm()
    check_avd()
    launch()
