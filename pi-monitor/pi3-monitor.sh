#!/bin/bash
# Monitor pi3 node readiness and alert when it comes back online.
# Runs via cron every 5 minutes. Alerts once when pi3 transitions from NotReady to Ready.

NODE="pi3"
ALERT_FILE="/tmp/pi3-alerted"
LOG="/home/aldo/scripts/pi3-monitor.log"
KUBECTL="sudo k3s kubectl"

echo "$(date '+%Y-%m-%d %H:%M:%S') === pi3 monitor check ===" >> "$LOG"

# Get node status (handle missing conditions gracefully)
STATUS=$($KUBECTL get node "$NODE" -o jsonpath='{.status.conditions[?type=="Ready"].status}' 2>/dev/null)
K3S_EXIT=$?

# If jsonpath fails (no conditions), check via custom-columns
if [ $K3S_EXIT -ne 0 ] || [ -z "$STATUS" ]; then
    STATUS=$($KUBECTL get node "$NODE" -o custom-columns='STATUS:.status.conditions[?type=="Ready"].status' --no-headers 2>/dev/null)
fi

# Also check if node exists at all
NODE_EXISTS=$($KUBECTL get node "$NODE" --no-headers 2>/dev/null | wc -l)

if [ "$NODE_EXISTS" -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') pi3 node not found in cluster" >> "$LOG"
    STATUS="NotFound"
elif [ "$STATUS" = "True" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') pi3 is Ready" >> "$LOG"

    # Check if we already alerted
    if [ ! -f "$ALERT_FILE" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') pi3 came back! Sending alert." >> "$LOG"
        touch "$ALERT_FILE"

        # Write alert content for monitoring job to pick up
        cat > /tmp/pi3-alert.txt <<EOF
✅ pi3 node is Ready!
You can now continue with the freellmapi multi-node plan.
Run: kubectl get node pi3
EOF
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') pi3 is NotReady (status: '$STATUS')" >> "$LOG"
    # Reset alert flag so we alert again if it comes back
    rm -f "$ALERT_FILE"
fi