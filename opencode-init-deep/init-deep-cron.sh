#!/bin/bash
# Nightly cron job for hierarchical AGENTS.md initialization
# Usage: opencode run "/init-deep" --dir ~/dev

set -euo pipefail

# Configuration (self-contained in script directory)
SCRIPT_DIR="/home/aldo/dev"
BASE_DIR="$(dirname "$(readlink -f "$0")")"
LOG_FILE="$BASE_DIR/init-deep.log"
TEMP_DIR="$BASE_DIR/temp"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$TEMP_DIR"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

log "=== Starting nightly init-deep initialization ==="
log "Using opencode run /init-deep --dir $SCRIPT_DIR"

if ! command -v opencode &> /dev/null; then
    log "ERROR: opencode command not found"
    exit 1
fi

# Run the command with timeout to avoid hanging indefinitely
log "Executing: opencode run \"/init-deep\" --dir $SCRIPT_DIR"

if timeout 300 opencode run "/init-deep" --dir "$SCRIPT_DIR" 2>&1 | tee -a "$LOG_FILE"; then
    log "SUCCESS: init-deep completed."
    exit 0
else
    log "ERROR: init-deep failed or timed out."
    exit 1
fi