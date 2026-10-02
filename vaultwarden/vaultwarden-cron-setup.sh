#!/bin/bash
set -euo pipefail

# Vaultwarden backup — idempotent cron wrapper
# Tag: # HOME: vaultwarden-backup
# Runs daily at 03:30 (after the 03:00 general backup)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CRON_TAG="# HOME: vaultwarden-backup"
CRON_LINE="30 3 * * * /home/aldo/dev/scripts/vaultwarden-backup.sh >> /home/aldo/dev/scripts/vaultwarden-backup.log 2>&1"

ensure_cron_entry() {
    if crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
        echo "[vaultwarden-backup] cron entry already present — skipping" >&2
        return 0
    fi

    # Remove any stale entries for this tag first (idempotent refresh)
    local current
    current="$(crontab -l 2>/dev/null | grep -v "$CRON_TAG" | grep -v "vaultwarden-backup" || true)"
    { echo "$current"; echo "$CRON_TAG"; echo "$CRON_LINE"; } | grep -v '^$' | crontab -
    echo "[vaultwarden-backup] cron entry added" >&2
}

ensure_cron_entry