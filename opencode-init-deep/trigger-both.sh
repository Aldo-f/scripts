#!/bin/bash

# Direct execution script for both cron jobs
# This simulates both cron jobs running

SCRIPT_DIR="/home/aldo/scripts"
LOG_DIR="$SCRIPT_DIR/opencode-init-deep"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== Starting both cron jobs ===" | tee "$LOG_DIR/direct-exec.log"

# First, run the sync script (existing job)
echo "[$DATE] Running sync script (existing job)..." | tee -a "$LOG_DIR/direct-exec.log"
cd /home/aldo/dev/02-ai-llm-infra-sync && /home/aldo/.bun/bin/bun run src/index.ts 2>&1 | tee -a "$LOG_DIR/direct-exec.log"
SYNC_EXIT_CODE=${PIPESTATUS[0]}
echo "[$DATE] Sync script completed with exit code: $SYNC_EXIT_CODE" | tee -a "$LOG_DIR/direct-exec.log"

# Second, run the init-deep script (new job)
echo "[$DATE] Running init-deep script (new job)..." | tee -a "$LOG_DIR/direct-exec.log"
$SCRIPT_DIR/opencode-init-deep/init-deep-cron.sh 2>&1 | tee -a "$LOG_DIR/direct-exec.log"
INIT_EXIT_CODE=${PIPESTATUS[0]}
echo "[$DATE] Init-deep script completed with exit code: $INIT_EXIT_CODE" | tee -a "$LOG_DIR/direct-exec.log"

echo "=== Both cron jobs completed ===" | tee -a "$LOG_DIR/direct-exec.log"
echo "Sync exit code: $SYNC_EXIT_CODE" | tee -a "$LOG_DIR/direct-exec.log"
echo "Init-deep exit code: $INIT_EXIT_CODE" | tee -a "$LOG_DIR/direct-exec.log"