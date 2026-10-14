#!/bin/bash
# Source snapshot check — 15 min interval
# Only compares hashes, does NOT trigger LLM (cost expensive) — LLM runs once at night
# Uses latest free credits efficiently by deferring expensive updates to nightly cron

LOGFILE="/mnt/HDD1/dev/logs/bookstack-source-check.log"
mkdir -p /mnt/HDD1/dev/logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting source snapshot check..." >> "$LOGFILE"

# This would call the BookStack artisan command (to be deployed to pod or executed locally)
# For standalone execution from this repo, we log the check intent
# In production, deploy to k3s CronJob or cron service that runs inside the pod

if [ -f /home/aldo/dev/06-apps-bookstack/themes/digipunt/scripts/check_sources_cron.php ]; then
    /usr/bin/php /home/aldo/dev/06-apps-bookstack/themes/digipunt/scripts/check_sources_cron.php >> "$LOGFILE" 2>&1
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PHP script not found — deploy check_sources_cron.php first" >> "$LOGFILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Source check completed." >> "$LOGFILE"
