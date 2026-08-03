# Scripts Knowledge Base

A collection of automation, infrastructure maintenance, and development helper scripts.

## Directory Structure

- **`deezer/`**: Download/search Deezer tracks and playlists as MP3s via login cookies (ARL).
- **`git-tools/`**: Git workflow automation (such as `git_push.sh`).
- **`google-workspace/`**: Google Workspace helper scripts (clasp, tailing logs, dry-runs).
- **`opencode-init-deep/`**: Hierarchical `AGENTS.md` initialization automation.
- **`ssd-tools/`**: SSD health monitoring and stress testing optimized for Pi 5 with USB SSDs.

## Root Scripts

- **`hermes_backup.sh`**: Daily skills push to GitHub + weekly full Hermes backup zip (saved locally).
- **`fetch_free_models.py`**: Fetches and lists all active free models from providers.

## Common Usage

### Automated Knowledge Base Initialization
- Run: `~/scripts/opencode-init-deep/init-deep-cron.sh`
- Cron entry (02:00 nightly): `0 2 * * * /home/aldo/scripts/opencode-init-deep/init-deep-cron.sh`

### SSD Maintenance
- Check health: `python3 ~/scripts/ssd-tools/ssd_health.py`
- Stress test: `python3 ~/scripts/ssd-tools/stress_test_ssd.py 600 500`

### Git Maintenance
- Push changes: `~/scripts/git-tools/git_push.sh`

### Google Workspace & clasp
- Custom credentials setup: `~/scripts/google-workspace/setup-clasp-creds.sh /path/to/credentials.json`
- Dry run with limit of 3 (default): `cd ~/dev/06-apps-script-google/LabelReminder && clasp run dryRunWithMax`
- Capture stackdriver logs: `~/scripts/google-workspace/capture-logs.sh`
