#!/usr/bin/env python3
"""
Snapshot V4L2 camera capabilities to a JSON file for offline inspection.

This script is read-only: it does not modify device state or capture frames.
It is intended to complement the interactive inspection tools by recording
what the kernel V4L2 drivers expose at a point in time.
"""

import json
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


def find_v4l2_ctl() -> str:
    path = shutil.which("v4l2-ctl")
    if path is None:
        print(
            "ERROR: `v4l2-ctl` not found in PATH.\n"
            "Install `v4l-utils` (e.g. `sudo apt-get install v4l-utils`) "
            "to use this tool.",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def run_v4l2_ctl(v4l2_ctl: str, args: List[str]) -> str:
    cmd = [v4l2_ctl] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # Store stderr for debugging; return empty string for this section.
        return f"ERROR (exit {result.returncode}): {result.stderr.strip()}"
    return result.stdout


def is_char_device(path: str) -> bool:
    try:
        st = os.stat(path)
    except OSError:
        return False
    return (st.st_mode & 0o170000) == 0o020000


def list_video_devices() -> List[str]:
    devs = sorted(glob.glob("/dev/video*"))
    return [d for d in devs if is_char_device(d)]


def snapshot_caps(output_path: Path) -> None:
    v4l2_ctl = find_v4l2_ctl()
    devices = list_video_devices()

    data: Dict[str, Any] = {
        "tool": "camera_caps_snapshot",
        "v4l2_ctl": v4l2_ctl,
        "devices": [],
    }

    for dev in devices:
        entry: Dict[str, Any] = {
            "device": dev,
            "all": run_v4l2_ctl(v4l2_ctl, ["--device", dev, "--all"]),
            "formats_ext": run_v4l2_ctl(
                v4l2_ctl, ["--device", dev, "--list-formats-ext"]
            ),
        }
        data["devices"].append(entry)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote capability snapshot to {output_path}")
    print(
        "Note: This reflects what the kernel driver and V4L2 layer expose to "
        "userspace at this moment; it can be versioned alongside robotics configs."
    )


def main() -> None:
    # Default output path can be overridden via CLI arg if needed.
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("camera_caps_snapshot.json")
    snapshot_caps(out)


if __name__ == "__main__":
    main()


