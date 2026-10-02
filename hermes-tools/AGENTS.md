# hermes-tools

## OVERVIEW
`hermes_backup.sh` (32 lines). Daily skills push to GitHub + weekly full Hermes backup zip on Sunday.

## DAILY RUN
1. Skills → `cd $HOME/.hermes/skills` → `git add -A && git commit && git push` (quiet if nothing changed).
2. Sunday only: `hermes backup -o $HOME/backups/hermes-backup-YYYY-MM-DD.zip` (local only, contains `.env` secrets, never sync off-box).
3. Keeps newest 8 backups; older deleted via `ls -1t | tail -n +9 | xargs rm`.

## PATHS
- `$HOME/.hermes/skills` — git repo, pushed to GitHub
- `$HOME/backups` — weekly zips
- `$HOME/.local/bin/hermes` — Hermes CLI

## COMMANDS
```bash
~/scripts/hermes-tools/hermes_backup.sh
```

## NOTES
- Safe to run daily; idempotent.
- Zip contains secrets — keep local.
- Sunday detection: `date +%u` returns 7.