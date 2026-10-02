#!/bin/bash
set -euo pipefail

# Graphify automatic update — idempotent cron wrapper
# Tag: # HOME: graphify-update
# Runs daily at 02:00 (after the general backup)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_TAG="# HOME: graphify-update"
# Uses nohup so the long-running job survives logout and isn't killed by terminal timeouts
CRON_LINE="0 2 * * * nohup /home/aldo/dev/scripts/graphify-update.sh >> /home/aldo/dev/scripts/graphify-update.log 2>&1 &"

ensure_cron_entry() {
    if crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
        echo "[graphify-update] cron entry already present — skipping" >&2
        return 0
    fi

    local current
    current="$(crontab -l 2>/dev/null | grep -v "$CRON_TAG" | grep -v "graphify-update" || true)"
    { echo "$current"; echo "$CRON_TAG"; echo "$CRON_LINE"; } | grep -v '^$' | crontab -
    echo "[graphify-update] cron entry added" >&2
}

ensure_cron_entry
