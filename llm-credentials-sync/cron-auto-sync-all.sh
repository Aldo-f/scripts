#!/bin/bash
# Automatische sync: scan alle sources (hermes, opencode, freellmapi DB, dotenv, etc.)
# en merge naar unified Source of Truth + terugschrijven naar opencode/hermes.

set -euo pipefail
LOGFILE="/home/aldo/dev/logs/sync-auto-$(date +%Y%m%d-%H%M%S).log"
mkdir -p /home/aldo/dev/logs

exec >> "$LOGFILE" 2>&1

echo "=== Auto sync start: $(date -Iseconds) ==="

# 1. Decrypt FreeLLMAPI DB keys
cd /home/aldo/dev/02-ai-llm-infra-sync
echo "[1/4] Decrypt FreeLLMAPI DB keys..."
/home/aldo/.bun/bin/bun run src/decrypt.js || echo "Decrypt completed (some may fail)"

# 2. Scan all sources and build unified Source of Truth
echo "[2/4] Scan all sources..."
python3 /tmp/scan-keys-fast.py

# 3. Run sync (reads sources + FreeLLMAPI DB + writes back)
echo "[3/4] Run sync..."
/home/aldo/.bun/bin/bun run src/index.ts

# 4. Export unified env for external tools
echo "[4/4] Export complete. Source of Truth at:"
ls -la src/source-of-truth.json src/freellmapi-decrypted.json

echo "=== Auto sync done: $(date -Iseconds) ==="
