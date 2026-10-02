#!/bin/bash
set -euo pipefail

# Graphify baseline scan — records which ~/dev/ projects have graphify analysis
# Output: JSON array to ~/.hermes/cron/output/graphify-baseline-<timestamp>.json
# Cron tag: # HOME: graphify-baseline

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${HOME}/.hermes/cron/output"
mkdir -p "$OUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_FILE="${OUT_DIR}/graphify-baseline-${TIMESTAMP}.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Directories to skip (non-projects, host state, local-only)
SKIP_DIRS=(
    "archives"
    "scripts"
    "specs"
    "tests"
    "torrent"
    "urbanfix"
    "okf-home-lab"
)

# Check if a directory name matches any skip pattern
should_skip() {
    local dirname="$1"
    for skip in "${SKIP_DIRS[@]}"; do
        if [[ "$dirname" == "$skip" ]]; then
            return 0
        fi
    done
    return 1
}

# Start JSON array
echo "[" > "$OUT_FILE"
first=true

# Iterate over direct subdirectories of ~/dev
for proj_dir in "$REPO_DIR"/*/; do
    # Get bare directory name
    proj_name=$(basename "$proj_dir")
    proj_name=${proj_name%/}

    # Skip non-project dirs
    if should_skip "$proj_name"; then
        continue
    fi

    # Skip hidden dirs
    if [[ "$proj_name" == .* ]]; then
        continue
    fi

    # Check for graphify output
    has_graphify=false
    graph_json="${proj_dir}graphify-out/graph.json"
    if [[ -f "$graph_json" ]]; then
        has_graphify=true
    fi

    # Get last modified of graph.json if exists
    last_modified=""
    if [[ "$has_graphify" == true ]]; then
        last_modified=$(stat -c '%Y' "$graph_json" 2>/dev/null || stat -f '%m' "$graph_json" 2>/dev/null || echo "")
    fi

    # Build JSON object - use null for missing last_modified
    if [[ "$first" == true ]]; then
        first=false
    else
        echo "," >> "$OUT_FILE"
    fi

    if [[ -z "$last_modified" ]]; then
        last_modified_val="null"
    else
        last_modified_val="$last_modified"
    fi

    cat <<EOF >> "$OUT_FILE"
  {
    "project": "$proj_name",
    "path": "$proj_dir",
    "has_graphify": $has_graphify,
    "graph_json": "$graph_json",
    "last_modified": $last_modified_val,
    "scanned_at": "$(date -Iseconds)"
  }
EOF

    log "Scanned $proj_name — graphify: $has_graphify"
done

# Close JSON array
echo "]" >> "$OUT_FILE"

# Pretty-print with jq if available, else leave as-is
if command -v jq >/dev/null 2>&1; then
    jq . "$OUT_FILE" > "${OUT_FILE}.tmp" && mv "${OUT_FILE}.tmp" "$OUT_FILE"
fi

log "Baseline written to $OUT_FILE"