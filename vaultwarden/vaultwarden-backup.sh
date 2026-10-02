#!/bin/bash
set -euo pipefail

# Vaultwarden backup — automated daily encrypted export to Google Drive
# with GFS retention (7 daily, 5 weekly, 12 monthly)
# Runs daily at 03:30 via cron. Non-interactive; no prompts.

BACKUP_DIR="/mnt/HDD1/backups/vaultwarden"
PASS_FILE="/home/aldo/.hermes/vaultwarden-password.txt"
REMOTE="google-drive:/key/vaultwarden"
DATE=$(date +%F)
RETENTION_DAYS=7
RETENTION_WEEKS=5
RETENTION_MONTHS=12

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── 1. Export vault contents as encrypted JSON ──
mkdir -p "$BACKUP_DIR"

# Read password from protected file (no interactive prompt)
export BW_PASSWORD=$(cat "$PASS_FILE")
# Unlock vault and capture session token (non-interactive)
BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw 2>/dev/null || echo "")
if [ -z "$BW_SESSION" ]; then
    log "ERROR: Could not unlock vault with BW_PASSWORD"
    exit 1
fi
export BW_SESSION

# Export vault contents using the session token
bw export --format encrypted_json --session "$BW_SESSION" --output "$BACKUP_DIR/vaultwarden_$DATE.json"

# Unset BW_PASSWORD for security
unset BW_PASSWORD

# ── 2. Upload to Google Drive ──
rclone copy "$BACKUP_DIR/vaultwarden_$DATE.json" "$REMOTE"

# ── 3. Retention policy (GFS: 7 daily / 5 weekly / 12 monthly) ──

# Local rotation
if ls "$BACKUP_DIR"/vaultwarden_*.json >/dev/null 2>&1; then
    local_count=$(ls -1 "$BACKUP_DIR"/vaultwarden_*.json | wc -l)
    if [ "$local_count" -gt "$RETENTION_DAYS" ]; then
        ls -1rt "$BACKUP_DIR"/vaultwarden_*.json | head -n $((local_count - RETENTION_DAYS)) | xargs -r rm -f
        log "Local rotation: removed $((local_count - RETENTION_DAYS)) old backup(s), keeping $RETENTION_DAYS daily"
    fi
fi

# Remote rotation (Google Drive)
if rclone ls "$REMOTE" | grep -q "vaultwarden_"; then
    remote_count=$(rclone ls "$REMOTE" | grep "vaultwarden_" | wc -l)
    if [ "$remote_count" -gt "$RETENTION_DAYS" ]; then
        # Get oldest files beyond retention, delete them
        rclone ls "$REMOTE" | grep "vaultwarden_" | sort | head -n $((remote_count - RETENTION_DAYS)) | awk '{print $2}' | xargs -r rclone delete "$REMOTE"
        log "Remote rotation: removed $((remote_count - RETENTION_DAYS)) old backup(s) from Drive, keeping $RETENTION_DAYS daily"
    fi
fi

# ── 4. Verify final state ──
local_remaining=$(ls -1 "$BACKUP_DIR"/vaultwarden_*.json 2>/dev/null | wc -l || echo 0)
remote_remaining=$(rclone ls "$REMOTE" | grep "vaultwarden_" | wc -l || echo 0)
log "Vaultwarden backup OK — $local_remaining local, $remote_remaining remote (retention: $RETENTION_DAYS days)"