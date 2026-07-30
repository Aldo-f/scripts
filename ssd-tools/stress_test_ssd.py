#!/usr/bin/env python3
"""
Simple SSD stress test for Raspberry Pi with USB SSD.
Writes random data to a test file on the mounted SSD and reads it back,
checking for I/O errors.
Usage:
    python3 stress_test_ssd.py [duration_seconds] [file_size_mb]
Default: run for 300 seconds (5 min) with a 100 MB test file.
"""

import os
import sys
import time
import random
import argparse
import tempfile
import datetime

def human_size(num):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"

def main():
    parser = argparse.ArgumentParser(description="SSD stress test (write/read verify).")
    parser.add_argument('duration', nargs='?', type=int, default=300,
                        help='Duration of test in seconds (default: 300)')
    parser.add_argument('size_mb', nargs='?', type=int, default=100,
                        help='Size of test file in MB (default: 100)')
    args = parser.parse_args()

    # Ensure we are writing to the mounted SSD (assumed to be /dev/sda2 mounted at /)
    # Safer: create a test file in the current directory (should be on SSD if run from /home/aldo on SSD)
    test_dir = os.getcwd()
    test_file = os.path.join(test_dir, f"stress_test_{os.getpid()}.tmp")

    block_size = 4 * 1024  # 4KB blocks
    total_bytes = args.size_mb * 1024 * 1024
    block_count = total_bytes // block_size
    if block_count == 0:
        block_count = 1

    print(f"[{datetime.datetime.now().isoformat()}] Starting SSD stress test")
    print(f"  Duration: {args.duration} seconds")
    print(f"  File size: {human_size(total_bytes)} ({args.size_mb} MB)")
    print(f"  Block size: {human_size(block_size)}")
    print(f"  Working directory: {test_dir}")

    end_time = time.time() + args.duration
    iteration = 0
    errors = 0
    random.seed()

    try:
        while time.time() < end_time:
            iteration += 1
            # Write random data
            try:
                with open(test_file, 'wb') as f:
                    for _ in range(block_count):
                        f.write(os.urandom(block_size))
                # Flush to ensure data is written
                os.sync()
            except Exception as e:
                print(f"[{datetime.datetime.now().isoformat()}] WRITE ERROR iter {iteration}: {e}")
                errors += 1
                time.sleep(1)
                continue

            # Read back and verify (we can't verify random data unless we store it, so just check read succeeds)
            try:
                with open(test_file, 'rb') as f:
                    while f.read(block_size):
                        pass
                os.sync()
            except Exception as e:
                print(f"[{datetime.datetime.now().isoformat()}] READ ERROR iter {iteration}: {e}")
                errors += 1
                time.sleep(1)
                continue

            # Progress every 10 iterations or every 30 seconds
            if iteration % 10 == 0 or time.time() % 30 < 1:
                elapsed = int(time.time() - (end_time - args.duration))
                print(f"[{datetime.datetime.now().isoformat()}] Iter {iteration}, elapsed {elapsed}s, errors {errors}")

            # Small sleep to avoid pegging CPU 100%
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Clean up test file
        try:
            os.remove(test_file)
        except FileNotFoundError:
            pass

    print(f"[{datetime.datetime.now().isoformat()}] Stress test finished.")
    print(f"  Total iterations: {iteration}")
    print(f"  I/O errors: {errors}")
    if errors == 0:
        print("  RESULT: No I/O errors detected during test.")
    else:
        print("  RESULT: I/O errors encountered – investigate USB/SSD stability.")

if __name__ == '__main__':
    main()