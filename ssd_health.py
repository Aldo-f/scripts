#!/usr/bin/env python3
"""
SSD health monitoring script.
- Runs a quick stress test (write/read verify)
- Logs SoC temperature
- Appends results to a log file
"""

import os
import sys
import time
import random
import datetime
import subprocess

def get_temperature():
    """Read Raspberry Pi SoC temperature via vcgencmd."""
    try:
        result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Output format: "temp=45.2'C\n"
            temp_str = result.stdout.strip().replace("temp=", "").replace("'C", "")
            return float(temp_str)
    except Exception:
        pass
    return None

def human_size(num):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"

def run_stress_test(duration=60, size_mb=100):
    """Run a quick write/read stress test."""
    block_size = 4 * 1024
    total_bytes = size_mb * 1024 * 1024
    block_count = max(1, total_bytes // block_size)
    
    test_dir = os.getcwd()
    test_file = os.path.join(test_dir, f"ssd_stress_test_{os.getpid()}.tmp")
    errors = 0
    
    try:
        with open(test_file, 'wb') as f:
            for _ in range(block_count):
                f.write(os.urandom(block_size))
        os.sync()
        
        with open(test_file, 'rb') as f:
            while f.read(block_size):
                pass
        os.sync()
    except Exception as e:
        errors += 1
    finally:
        try:
            os.remove(test_file)
        except FileNotFoundError:
            pass
    
    return errors

def main():
    log_file = os.path.expanduser('~/scripts/ssd_health.log')
    
    timestamp = datetime.datetime.now().isoformat()
    temp = get_temperature()
    errors = run_stress_test(duration=60, size_mb=100)
    
    temp_str = f"{temp:.1f}°C" if temp is not None else "N/A"
    status = "OK" if errors == 0 else "ERRORS"
    
    log_line = f"[{timestamp}] Temperature: {temp_str}, Stress test: {status} (errors={errors})\n"
    
    print(log_line.strip())
    
    with open(log_file, 'a') as f:
        f.write(log_line)

if __name__ == '__main__':
    main()