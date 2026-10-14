#!/bin/bash
# Nightly LLM trigger — runs just before rate limit reset (around 01:50)
# Uses remaining free credits efficiently; runs once per day
# This calls the LLM updater for all queued pages (drafts) — expensive but nightly

LOGFILE="/mnt/HDD1/dev/logs/bookstack-llm-nightly.log"
mkdir -p /mnt/HDD1/dev/logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting nightly LLM update (before rate limit reset)..." >> "$LOGFILE"

# In production, this calls the artisan command inside the k3s pod or connects to the FreeLLM API
# For this repo, we prepare the script that will be executed in the PVC deployment
# Example: kubectl exec pod -- php artisan digipunt:update-queue

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Queued updates count: [to be fetched from DB]" >> "$LOGFILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] LLM model selected: [auto-selected via getBestModel()]" >> "$LOGFILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nightly LLM trigger completed." >> "$LOGFILE"
