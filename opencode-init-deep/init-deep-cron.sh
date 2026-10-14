#!/bin/bash
# init-deep-cron.sh - Main cron script that runs the init-deep agent
# This is called by the cron job to initialize the opencode environment

# Ensure the opencode-init-deep directory exists
SCRIPT_DIR="$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR"

# Run the init-deep command via opencode
# --pure ensures we don't hang if opencode is not fully initialized
# --dir specifies the directory where the opencode project lives
opencode run --pure "/init-deep" --dir "$SCRIPT_DIR" 2>&1 | tee "$SCRIPT_DIR/init-deep.log"
