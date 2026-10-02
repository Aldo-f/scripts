#!/usr/bin/env bash
# test-swap-dance — test the swap dance logic from cache-clear
#
# Validates the safe swap dance (swapon/swapoff cycling) that prevents OOM
# when purging large caches on zram-backed systems like Raspberry Pi.
#
# Usage:  sudo ./test-swap-dance.sh
#         ./test-swap-dance.sh --dry-run   (check preconditions only)
#
# Requires: /dev/zram0 present, root or sudo, ~4 GB free on /tmp

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

IS_ROOT=false
[[ "${EUID:-$(id -u)}" -eq 0 ]] && IS_ROOT=true

as_root() {
    if [[ "$IS_ROOT" == "true" ]]; then "$@"; else sudo "$@"; fi
}

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; FAILURES=$((FAILURES + 1)); }
info() { echo "  → $1"; }

FAILURES=0
SWAP_FILE="/tmp/.cache-clear-test-swap"

echo "=== Swap Dance Test ==="
echo ""

# ── Test 1: zram0 exists ──────────────────────────────────────
echo "Test 1: /dev/zram0 exists"
if [[ -b /dev/zram0 ]]; then
    pass "/dev/zram0 is a block device"
else
    fail "/dev/zram0 not found — swap dance will skip on this system"
    echo ""
    echo "Result: Cannot test swap dance without zram0."
    exit 1
fi

# ── Test 2: root or sudo available ─────────────────────────────
echo ""
echo "Test 2: root privileges"
if [[ "$IS_ROOT" == "true" ]]; then
    pass "running as root"
else
    if sudo -n true 2>/dev/null; then
        pass "sudo available (non-interactive)"
    else
        fail "need root or passwordless sudo"
        exit 1
    fi
fi

# ── Test 3: find a location with enough space (4 GB) ───────────
echo ""
echo "Test 3: find location for 4 GB swap file (try /tmp, then /)"
NEED=4294967296
SWAP_DIR=""

for dir in /tmp /; do
    DIR_FREE=$(df -B1 "$dir" 2>/dev/null | awk 'NR==2{print $4}')
    if [[ -n "$DIR_FREE" && "$DIR_FREE" -ge "$NEED" ]]; then
        SWAP_DIR="$dir"
        pass "$dir has $(numfmt --to=iec "$DIR_FREE") free"
        break
    else
        info "$dir has only $(numfmt --to=iec "${DIR_FREE:-0}") — skip"
    fi
done

if [[ -z "$SWAP_DIR" ]]; then
    fail "no location with 4 GiB free found"
    echo ""
    echo "Result: Not enough space for swap dance test."
    exit 1
fi

SWAP_FILE="${SWAP_DIR}/.cache-clear-test-swap"

# ── Test 4: current swap state ────────────────────────────────
echo ""
echo "Test 4: current swap state"
BEFORE_SWAP=$(swapon --show 2>/dev/null)
if [[ -n "$BEFORE_SWAP" ]]; then
    pass "swap active before test:"
    echo "$BEFORE_SWAP" | sed 's/^/    /'
else
    fail "no swap active"
fi

BEFORE_FREE=$(free -h 2>/dev/null | awk '/^Mem:/{print $4}')
BEFORE_SWAP_FREE=$(free -h 2>/dev/null | awk '/^Swap:/{print $4}')
info "mem free before: $BEFORE_FREE, swap free before: $BEFORE_SWAP_FREE"

if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "=== DRY RUN — preconditions checked, no swap dance performed ==="
    exit 0
fi

# ── Test 5: create temp swap file ─────────────────────────────
echo ""
echo "Test 5: create 4 GB temp swap file"
if as_root fallocate -l 4G "$SWAP_FILE" 2>/dev/null; then
    pass "fallocate succeeded"
elif as_root dd if=/dev/zero of="$SWAP_FILE" bs=1M count=4096 status=none 2>/dev/null; then
    pass "dd fallback succeeded"
else
    fail "cannot create swap file"
    exit 1
fi

as_root chmod 600 "$SWAP_FILE"
as_root mkswap "$SWAP_FILE" 2>&1 | sed 's/^/    /'
pass "swap file created and formatted"

# ── Test 6: swap dance (swapon/swapoff cycle) ─────────────────
echo ""
echo "Test 6: swap dance (swapon → swapoff zram0 → swapon zram0 → swapoff temp)"

if as_root swapon "$SWAP_FILE" 2>/dev/null; then
    pass "swapon temp file"
else
    fail "swapon temp file failed"
    as_root rm -f "$SWAP_FILE"
    exit 1
fi

if as_root swapoff /dev/zram0 2>/dev/null; then
    pass "swapoff /dev/zram0"
else
    fail "swapoff /dev/zram0 failed"
    as_root swapoff "$SWAP_FILE" 2>/dev/null || true
    as_root rm -f "$SWAP_FILE"
    exit 1
fi

if as_root swapon /dev/zram0 2>/dev/null; then
    pass "swapon /dev/zram0 (reactivated)"
else
    fail "swapon /dev/zram0 failed — zram0 may need re-init"
    as_root swapoff "$SWAP_FILE" 2>/dev/null || true
    as_root rm -f "$SWAP_FILE"
    exit 1
fi

if as_root swapoff "$SWAP_FILE" 2>/dev/null; then
    pass "swapoff temp file"
else
    fail "swapoff temp file failed (non-fatal)"
fi

# ── Test 7: cleanup ────────────────────────────────────────────
echo ""
echo "Test 7: cleanup"
as_root rm -f "$SWAP_FILE"
if [[ ! -f "$SWAP_FILE" ]]; then
    pass "temp swap file removed"
else
    fail "temp swap file still exists at $SWAP_FILE"
fi

# ── Test 8: verify post-dance state ────────────────────────────
echo ""
echo "Test 8: post-dance verification"
AFTER_SWAP=$(swapon --show 2>/dev/null)
if echo "$AFTER_SWAP" | grep -q "zram0"; then
    pass "zram0 is active after dance"
else
    fail "zram0 is NOT active after dance — manual recovery needed!"
    exit 1
fi

if echo "$AFTER_SWAP" | grep -q "$SWAP_FILE"; then
    fail "temp swap file is still active — leftover detected"
    FAILURES=$((FAILURES + 1))
else
    pass "temp swap file is not active (clean)"
fi

AFTER_FREE=$(free -h 2>/dev/null | awk '/^Mem:/{print $4}')
AFTER_SWAP_FREE=$(free -h 2>/dev/null | awk '/^Swap:/{print $4}')
info "mem free after: $AFTER_FREE, swap free after: $AFTER_SWAP_FREE"

echo ""
echo "$AFTER_SWAP" | sed 's/^/  /'
echo ""

# ── Summary ───────────────────────────────────────────────────
echo "=== Summary ==="
if [[ "$FAILURES" -eq 0 ]]; then
    echo "  All tests passed — swap dance is safe."
    exit 0
else
    echo "  $FAILURES test(s) failed."
    exit 1
fi
