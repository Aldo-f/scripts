# pi-monitor

## OVERVIEW
`pi3-monitor.sh` (46 lines). k3s node readiness monitor for node `"pi3"`. Runs every 5 min via cron.

## LOGIC
- Fetches `status.conditions[?type=="Ready"].status` via `sudo k3s kubectl get node pi3`.
- Falls back to `custom-columns` output if jsonpath fails.
- Logs status to `pi3-monitor.log` with timestamps.

## ALERT BEHAVIOR
- When pi3 transitions from NotReady/NotFound → Ready: writes `/tmp/pi3-alert.txt` and touches `/tmp/pi3-alerted`.
- Alert fires only once per transition; flag resets on NotReady so it alerts again on next recovery.
- Alert file content references freellmapi multi-node plan.

## COMMANDS
```bash
~/scripts/pi-monitor/pi3-monitor.sh
```

## NOTES
- Requires `sudo k3s kubectl` access.
- Log: `/home/aldo/scripts/pi3-monitor.log`.
- Cron: `*/5 * * * * /home/aldo/scripts/pi-monitor/pi3-monitor.sh`.