# Scripts Knowledge Base

A collection of automation, infrastructure maintenance, and development helper scripts.

## Directory Structure

- `git-tools/` : Git automation (pushing, hooks)
- `opencode-init-deep/` : Hierarchical AGENTS.md initialization automation
- `ssd-tools/` : SSD health monitoring and stress testing

## Common Usage

### Automated Knowledge Base Initialization
- Run: `~/scripts/opencode-init-deep/init-deep-cron.sh`
- Cron entry (02:00 nightly): `0 2 * * * /home/aldo/scripts/opencode-init-deep/init-deep-cron.sh`

### SSD Maintenance
- Check health: `./ssd-tools/ssd_health.py`
- Stress test: `./ssd-tools/stress_test_ssd.py`

### Git Maintenance
- Push changes: `./git-tools/git_push.sh`
