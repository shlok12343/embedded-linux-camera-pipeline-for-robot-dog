#!/usr/bin/env python3
"""
Minimal userspace helper to capture a single image using libcamera on Raspberry Pi.

This script is intentionally simple:
- It uses `subprocess` to invoke a libcamera CLI tool (e.g. `libcamera-still`).
- It captures exactly one still image to disk.

Userspace vs kernel driver:
- The actual sensor control, ISP, and data flow are handled by the kernel
  camera driver and related kernel subsystems.
- libcamera (and its CLI tools) run in userspace and communicate with those
  kernel drivers (via ioctl and other kernel interfaces) to configure the
  pipeline and request frames.
- This script does NOT implement any computer vision or image processing;
  it only exercises the capture path to produce a file.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_libcamera_tool() -> str:
    """
    Find a suitable libcamera CLI tool in PATH.

    We prefer `libcamera-still` for still image capture, but could be extended
    to support other tools if needed.
    """
    for tool in ("libcamera-still", "libcamera-jpeg"):
        path = shutil.which(tool)
        if path is not None:
            return path

    print(
        "ERROR: No libcamera still-capture tool found in PATH.\n"
        "Install `libcamera-apps` (e.g. `sudo apt-get install libcamera-apps`) "
        "to use this script.",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a single image using libcamera (userspace helper)."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("capture.jpg"),
        help="Output image file path (default: capture.jpg)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1000,
        help="Capture timeout in milliseconds (passed to libcamera-still, default: 1000).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tool = find_libcamera_tool()

    # Build a minimal libcamera command line.
    #
    # `libcamera-still` is a userspace application that:
    # - Negotiates with the libcamera pipeline handler.
    # - The pipeline handler, in turn, configures the kernel camera driver
    #   and associated hardware blocks (sensor, ISP, etc.).
    # - A single frame is requested from the kernel and then encoded/written
    #   to the output file.
    #
    # This script only orchestrates that call; it does not interpret or process
    # the image data itself.
    cmd = [
        tool,
        "-o",
        str(args.output),
        "--timeout",
        str(args.timeout),
    ]

    print(f"Using tool: {tool}")
    print(f"Capturing single image to: {args.output}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: libcamera capture command failed with exit code {e.returncode}",
            file=sys.stderr,
        )
        sys.exit(e.returncode)

    print("Capture complete.")


if __name__ == "__main__":
    main()


