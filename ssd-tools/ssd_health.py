#!/usr/bin/env python3
"""
SSD health monitoring script for Raspberry Pi 5 with USB SSD.
- Runs a quick write/read stress test
- Logs SoC temperature
- Appends results to a log file
"""

import os
import sys
import time
import random
import datetime
import subprocess

TEMP_FILE_PREFIX = "ssd_stress_test"
BLOCK_SIZE = 4 * 1024  # 4 KiB per block


def get_temperature():
    """Read Raspberry Pi SoC temperature via vcgencmd."""
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            raw = result.stdout.strip()
            # Expected format: "temp=45.2'C"
            return float(raw.replace("temp=", "").replace("'C", ""))
    except Exception:
        pass
    return None


def human_size(num):
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"


def run_stress_test(size_mb=100):
    """Write random data to a temp file then read it back.
    Returns the number of I/O errors encountered (0 means success).
    """
    total_bytes = size_mb * 1024 * 1024
    block_count = max(1, total_bytes // BLOCK_SIZE)
    test_file = os.path.join(
        os.getcwd(), f"{TEMP_FILE_PREFIX}_{os.getpid()}.tmp"
    )
    errors = 0

    # --- Write phase ---
    try:
        with open(test_file, "wb") as f:
            for _ in range(block_count):
                f.write(os.urandom(BLOCK_SIZE))
        os.sync()
    except Exception as e:
        print(f"[ERROR] Write failed: {e}", file=sys.stderr)
        errors += 1
        # Clean up partial file if it exists
        try:
            os.remove(test_file)
        except FileNotFoundError:
            pass
        return errors

    # --- Read phase ---
    try:
        with open(test_file, "rb") as f:
            while f.read(BLOCK_SIZE):
                pass
        os.sync()
    except Exception as e:
        print(f"[ERROR] Read failed: {e}", file=sys.stderr)
        errors += 1

    # --- Cleanup ---
    try:
        os.remove(test_file)
    except FileNotFoundError:
        pass

    return errors


def main():
    log_file = os.path.expanduser("~/scripts/ssd_health.log")

    timestamp = datetime.datetime.now().isoformat()
    temp = get_temperature()
    errors = run_stress_test(size_mb=100)

    temp_str = f"{temp:.1f}C" if temp is not None else "N/A"
    status = "OK" if errors == 0 else "ERRORS"

    log_line = (
        f"[{timestamp}] Temperature: {temp_str}, "
        f"Stress test: {status} (errors={errors})\n"
    )

    print(log_line.strip())

    with open(log_file, "a") as f:
        f.write(log_line)


if __name__ == "__main__":
    main()