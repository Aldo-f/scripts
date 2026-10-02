#!/bin/bash
set -euo pipefail

# Graphify automatic update — runs graphify . --code-only for each ~/dev/ project.
# Updates missing analyses and refreshes existing ones.
# Tag: # HOME: graphify-update
# Log: ~/.hermes/cron/output/graphify-update-<timestamp>.log
# Uses background jobs with job control for parallel processing.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve symlink to get actual repo directory
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
OUT_DIR="${HOME}/.hermes/cron/output"
mkdir -p "$OUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${OUT_DIR}/graphify-update-${TIMESTAMP}.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

SKIP_DIRS=(
    "archives"
    "scripts"
    "specs"
    "tests"
    "torrent"
    "urbanfix"
    "okf-home-lab"
    "02-ai-hermes-skills"
    "02-ai-opencode"
    "05-media-jellyfin"
    "05-media-nextcloud"
    "02-ai-mem0"
    "05-media-qbittorrent"
    "06-apps-mailrelay"
    "07-security-cockpit"
    "07-security-portainer"
    "07-security-vaultwarden"
    "08-infra-k3s"
    "Nocturna"
)

should_skip() {
    local dirname="$1"
    for skip in "${SKIP_DIRS[@]}"; do
        if [[ "$dirname" == "$skip" ]]; then
            return 0
        fi
    done
    return 1
}

# Test mode: only process a single project for validation
if [[ "${TEST:-}" == "true" ]]; then
    TARGET_DIR="/home/aldo/dev/06-apps-clock"
    TOTAL=0
    UPDATED=0
    FAILED=0
    if [[ -d "$TARGET_DIR" ]]; then
        log "TEST MODUS: werk alleen bij met $TARGET_DIR"
        TOTAL=1
        if (cd "$TARGET_DIR" && graphify . --code-only >> "$LOG_FILE" 2>&1); then
            log "Bijgewerkt $TARGET_DIR — OK"
            UPDATED=1
        else
            log "Bijgewerkt $TARGET_DIR — MISLUKT"
            FAILED=1
        fi
    else
        log "Testmap niet gevonden: $TARGET_DIR"
    fi
    log "Graphify update complete — total: $TOTAL, updated: $UPDATED, failed: $FAILED"
    echo "Graphify update summary: total=$TOTAL updated=$UPDATED failed=$FAILED timestamp=$TIMESTAMP" >> "${OUT_DIR}/graphify-update-summary.json"
    exit 0
fi

# Build list of project directories to process
mapfile -t PROJECTS < <(
    find "$REPO_DIR" -mindepth 1 -maxdepth 1 -type d \
        ! -name ".*" \
        | sort
)

# Filter out skipped projects
FILTERED=()
for proj in "${PROJECTS[@]}"; do
    proj_name=$(basename "$proj")
    should_skip "$proj_name" || FILTERED+=("$proj")
done

TOTAL=${#FILTERED[@]}
UPDATED=0
FAILED=0

if [[ "$TOTAL" -eq 0 ]]; then
    log "Geen projecten om bij te werken"
    echo "Graphify update summary: total=0 updated=0 failed=0 timestamp=$TIMESTAMP" >> "${OUT_DIR}/graphify-update-summary.json"
    exit 0
fi

log "Start parallel update van $TOTAL projecten (max 4 parallel)"

# Function to process a single project
process_project() {
    local proj_dir="$1"
    local log_file="$2"
    local proj_name=$(basename "$proj_dir")
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $proj_name ..." >> "$log_file"
    if (cd "$proj_dir" && graphify . --code-only >> "$log_file" 2>&1); then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updated $proj_name — OK" >> "$log_file"
        echo "OK"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updated $proj_name — FAILED" >> "$log_file"
        echo "FAIL"
    fi
}
export -f process_project

# Run up to 4 parallel jobs using xargs
printf '%s\0' "${FILTERED[@]}" | xargs -0 -P 4 -I {} bash -c 'process_project "$1" "$2"' _ {} "$LOG_FILE" > "${LOG_FILE}.results" 2>&1

# Count results
UPDATED=$(grep -c "^OK$" "${LOG_FILE}.results" || true)
FAILED=$(grep -c "^FAIL$" "${LOG_FILE}.results" || true)

log "Graphify update complete — total: $TOTAL, updated: $UPDATED, failed: $FAILED"
echo "Graphify update summary: total=$TOTAL updated=$UPDATED failed=$FAILED timestamp=$TIMESTAMP" >> "${OUT_DIR}/graphify-update-summary.json"

# Cleanup
rm -f "${LOG_FILE}.results"