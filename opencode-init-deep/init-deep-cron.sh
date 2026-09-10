#!/bin/bash
# Nightly cron job for hierarchical AGENTS.md initialization
# Usage: opencode run "/init-deep" --dir ~/dev
#
# IMPORTANT (user requirement):
#   1. Every line written to the log is prefixed with a timestamp "[YYYY-MM-DD HH:MM:SS]".
#   2. `opencode run "/init-deep"` must NOT be time-limited: it legitimately runs far
#      longer than 5 minutes on a large workspace (62k files). We run it to completion.
#   3. When it completes, send a desktop notification (notify-send) with the outcome.

set -euo pipefail

SCRIPT_DIR="/home/aldo/dev"
BASE_DIR="$(dirname "$(readlink -f "$0")")"
LOG_FILE="$BASE_DIR/init-deep.log"
TEMP_DIR="$BASE_DIR/temp"

mkdir -p "$TEMP_DIR"

# A tiny standalone stamper so we can stream + timestamp long-running output
# without relying on a pipeline exit-code trap. It prefixes each stdout line
# with a "[YYYY-MM-DD HH:MM:SS] " timestamp.
STAMPER="${TEMP_DIR}/init-deep-stamp.sh"
cat > "$STAMPER" <<'INNER'
#!/bin/bash
while IFS= read -r line; do
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
done
INNER
chmod +x "$STAMPER"

log_line() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

# send a desktop notification; silently ignore failures (e.g. cron without DBus).
notify() {
    if command -v notify-send > /dev/null 2>&1; then
        notify-send "opencode /init-deep" "$*" 2>/dev/null || true
    fi
}

log_line "=== Starting nightly init-deep initialization ==="
log_line "Using opencode run /init-deep --dir $SCRIPT_DIR"

if ! command -v opencode > /dev/null 2>&1; then
    log_line "ERROR: opencode command not found"
    notify "opencode not found"
    exit 1
fi

log_line "Executing (no timeout): opencode run \"/init-deep\" --dir $SCRIPT_DIR"

# Run WITHOUT timeout so the long-running job streams to completion.
# PIPESTATUS[0] captures opencode's real exit code (the stamper/tee are passthrough).
opencode run "/init-deep" --dir "$SCRIPT_DIR" 2>&1 | "$STAMPER" | tee -a "$LOG_FILE"
RC=${PIPESTATUS[0]}
DONE="$(date '+%Y-%m-%d %H:%M:%S')"

if [ "$RC" -eq 0 ]; then
    log_line "SUCCESS: init-deep completed at $DONE (exit 0)."
    notify "init-deep completed at $DONE (exit 0)."
    exit 0
else
    log_line "ERROR: init-deep exited with code $RC at $DONE."
    notify "init-deep failed with exit code $RC at $DONE."
    exit "$RC"
fi