#!/usr/bin/env python3
"""
Embedded Linux camera system sanity check.

This script runs a few read-only checks to validate that the environment is
aligned with the expected Raspberry Pi + USB camera setup:
- Verifies presence of key tools (lsusb, v4l2-ctl, libcamera-still/libcamera-jpeg).
- Lists /dev/video* devices.
- Asks v4l2-ctl to list V4L2 devices (if available).

The goal is quick diagnostics, not capture or processing.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def banner(title: str) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)


def check_tools(tools: Iterable[str]) -> List[str]:
    missing = []
    for t in tools:
        path = shutil.which(t)
        status = "OK" if path else "MISSING"
        print(f"{t:16s}: {status}" + (f" ({path})" if path else ""))
        if not path:
            missing.append(t)
    return missing


def run_cmd(cmd: List[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"Command not found: {' '.join(cmd)}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(
            f"Command failed ({' '.join(cmd)}), exit code {e.returncode}",
            file=sys.stderr,
        )


def main() -> None:
    banner("Camera System Sanity Check")

    # 1. Tool availability
    print("\n[1] Checking required tools in PATH")
    required = ["lsusb", "v4l2-ctl", "libcamera-still", "libcamera-jpeg"]
    missing = check_tools(required)

    # 2. /dev/video* devices
    print("\n[2] Listing /dev/video* devices")
    dev_dir = Path("/dev")
    video_nodes = sorted(p for p in dev_dir.glob("video*") if p.is_char_device())
    if not video_nodes:
        print("No /dev/video* nodes found.")
    else:
        for p in video_nodes:
            print(f"- {p}")

    # 3. v4l2-ctl --list-devices (if available)
    print("\n[3] V4L2 devices via `v4l2-ctl --list-devices`")
    if shutil.which("v4l2-ctl"):
        run_cmd(["v4l2-ctl", "--list-devices"])
    else:
        print("v4l2-ctl not available; skipping V4L2 device listing.")

    # 4. Summary
    print("\n[4] Summary")
    if missing:
        print("Some tools are missing; install them to match the expected setup:")
        for t in missing:
            print(f"- {t}")
    else:
        print("All checked tools are present.")

    print("\nNote: This script performs only read-only inspection; it does not")
    print("capture images or modify device configuration.")


if __name__ == "__main__":
    main()


