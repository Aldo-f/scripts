# SSD Health Monitor

This repository contains scripts to monitor the health of a USB-connected SSD on a Raspberry Pi 5.

## Scripts

- **`ssd_health.py`** - Runs a short stress test, logs temperature, and writes results to `~/scripts/ssd_health.log`.
- **`git_push.sh`** - Commits any changes (e.g., updated log file) and pushes them to GitHub.

## Schedule

- **Health check**: Runs daily at **03:00** via cron.
- **Git push**: Runs daily at **05:00** to sync any changes to GitHub.

## Logs

- `~/scripts/ssd_health.log` – Timestamped temperature and error status.
- `~/scripts/git_push.log` – Output from the push operation.

## GitHub

View on GitHub: [github.com/yourusername/aldo-ssd-monitor](https://github.com/yourusername/aldo-ssd-monitor)