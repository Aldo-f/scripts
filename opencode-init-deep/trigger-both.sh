#!/bin/bash
# trigger-both.sh - Runs both the sync and init-deep scripts

# Run the sync job (if it exists)
if [ -f /home/aldo/dev/scripts/opencode-init-deep/sync.sh ]; then
    echo "Running sync job..."
    /home/aldo/dev/scripts/opencode-init-deep/sync.sh
fi

# Run the init-deep job
if [ -f /home/aldo/dev/scripts/opencode-init-deep/init-deep-cron.sh ]; then
    echo "Running init-deep job..."
    /home/aldo/dev/scripts/opencode-init-deep/init-deep-cron.sh
fi
