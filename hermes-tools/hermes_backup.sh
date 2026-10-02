#!/usr/bin/env bash
# Hermes backup: daily skills push to GitHub + weekly full Hermes backup zip.
# Safe to run every day; quiet when there is nothing to do.
set -u

SKILLS_DIR="$HOME/.hermes/skills"
BACKUP_DIR="$HOME/backups"
HERMES_BIN="$HOME/.local/bin/hermes"

# 1) Skills -> git -> GitHub (quiet if nothing changed)
cd "$SKILLS_DIR" || { echo "ERROR: cannot cd to $SKILLS_DIR"; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "backup $(date '+%F %T')"
  git push -q origin main
  echo "skills pushed: $(git rev-parse --short HEAD)"
fi

# 2) Weekly full Hermes backup zip (local only -- zip contains .env secrets,
#    do NOT sync off-box). Runs on Sunday.
DOW=$(date +%u)
if [ "$DOW" -eq 7 ]; then
  mkdir -p "$BACKUP_DIR"
  OUT="$BACKUP_DIR/hermes-backup-$(date +%F).zip"
  if [ ! -f "$OUT" ]; then
    "$HERMES_BIN" backup -o "$OUT" >/dev/null 2>&1 && echo "hermes backup: $OUT"
  fi
  # keep the newest 8
  ls -1t "$BACKUP_DIR"/hermes-backup-*.zip 2>/dev/null | tail -n +9 | xargs -r rm -f
fi

exit 0
