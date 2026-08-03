# ssd-tools

SSD health monitoring and stress testing utilities optimized for Raspberry Pi 5 with USB SSDs.

## Files

- **`ssd_health.py`**: A lightweight Python daemon/cron script that monitors health, performs a quick write/read stress test (100MB by default), logs the SoC temperature via `vcgencmd`, and appends formatted reports to `~/scripts/ssd_health.log`.
- **`stress_test_ssd.py`**: A CLI tool that performs an extended write/read verification stress test. You can customize duration and file sizes to identify any transient USB SSD dropouts or performance quirks.
- **`ssd_health.log`**: A log file where standard outputs from the health monitoring checks are stored.

## Usage

### Run a Health Check:
```bash
python3 ~/scripts/ssd-tools/ssd_health.py
```

### Run an Extended Stress Test:
```bash
# Format: python3 stress_test_ssd.py [duration_seconds] [file_size_mb]
# Example: Run for 10 minutes (600s) with a 500 MB file
python3 ~/scripts/ssd-tools/stress_test_ssd.py 600 500
```
