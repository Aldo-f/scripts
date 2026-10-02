#!/bin/bash

# Direct execution script for both cron jobs
# This simulates both cron jobs running
#
# IMPORTANT (user requirement): every line written to the log file is
# prefixed with a timestamp "[YYYY-MM-DD HH:MM:SS] ".

SCRIPT_DIR="/home/aldo/dev/scripts"
LOG_DIR="$SCRIPT_DIR/opencode-init-deep"
LOG_FILE="$LOG_DIR/direct-exec.log"

# stamp: read lines from stdin and prefix each with a timestamp.
stamp() {
    while IFS= read -r line; do
        printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
    done
}

logged() {
    stamp | tee -a "$LOG_FILE"
}

{
    echo "=== Starting both cron jobs ===" | logged

    # First, run the sync script (existing job)
    echo "Running sync script (existing job)..." | logged
    ( cd /home/aldo/dev/02-ai-llm-infra-sync && /home/aldo/.bun/bin/bun run src/index.ts ) 2>&1 | logged
    SYNC_EXIT_CODE=${PIPESTATUS[0]}
    echo "Sync script completed with exit code: $SYNC_EXIT_CODE" | logged

    # Second, run the init-deep script (new job)
    echo "Running init-deep script (new job)..." | logged
    "$SCRIPT_DIR/opencode-init-deep/init-deep-cron.sh" 2>&1 | logged
    INIT_EXIT_CODE=${PIPESTATUS[0]}
    echo "Init-deep script completed with exit code: $INIT_EXIT_CODE" | logged

    echo "=== Both cron jobs completed ===" | logged
    echo "Sync exit code: $SYNC_EXIT_CODE" | logged
    echo "Init-deep exit code: $INIT_EXIT_CODE" | logged
}
