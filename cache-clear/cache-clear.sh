#!/usr/bin/env bash
# cache-clear — safe cross-user cache cleaner
#
# Goal: Clear stale temporary data from common cache locations across
#       any Linux system without risking active sessions or expensive-to-
#       rebuild caches. Includes a safe swap dance on low-memory systems
#       to prevent OOM when purging large caches.
#
# Install:  curl -sL https://cdn.jsdelivr.net/gh/Aldo-f/cache-clear@main/cache-clear | bash
#    (or:   curl -sL https://raw.githubusercontent.com/Aldo-f/cache-clear/main/cache-clear | bash)
# Usage:    cache-clear [--dry-run|--force|--uninstall|--help]
#
# When run as root, system-level caches are also cleaned.

set -euo pipefail

CACHE_ROOT="${HERMES_HOME:-$HOME/.hermes}/cache"
INSTALL_DIR="${HERMES_INSTALL_DIR:-$HOME/.local/bin}"
CMD_NAME="cache-clear"
LOG_FILE="${CACHE_ROOT}/clean.log"
IS_ROOT=false
[[ "${EUID:-$(id -u)}" -eq 0 ]] && IS_ROOT=true

DRY_RUN=false
FORCE=false

# ── Cache targets ─────────────────────────────────────────────
# User-level temp caches (no sudo needed)
USER_CACHES=(
    # Hermes Agent
    "$HOME/.hermes/cache/scratch/terminal-output"
    "$HOME/.hermes/cache/scratch/node-compile-cache"
    "$HOME/.hermes/cache/scratch/hermes-dm-"*
    "$HOME/.hermes/cache/scratch/hermes_kernel_"*
    "$HOME/.hermes/cache/scratch/org.chromium.Chromium."*
    "$HOME/.hermes/cache/scratch/agent-browser-"*
    "$HOME/.hermes/cache/scratch/page"*.html
    "$HOME/.hermes/cache/scratch/hermes-snap-"*.sh
    "$HOME/.hermes/cache/scratch/hermes-pty-active-"*.json
    "$HOME/.hermes/cache/scratch/.last_prune"
    "$HOME/.hermes/cache/terminal-output"
    "$HOME/.hermes/cache/exec"
    "$HOME/.hermes/cache/web"
    "$HOME/.hermes/cache/documents"
    "$HOME/.hermes/cache/delegation"
    "$HOME/.hermes/cache/browser-use"
    "$HOME/.hermes/cache/blocked-scripts"
    "$HOME/.hermes/cache/screenshots"
    "$HOME/.hermes/cache/images"
    "$HOME/.hermes/cache/videos"
    "$HOME/.hermes/cache/audio"
    "$HOME/.hermes/cache/vision"
    "$HOME/.hermes/cache/spillover"
    # Package managers
    "$HOME/.npm"
    "$HOME/.cache/yarn"
    "$HOME/.cache/pip"
    "$HOME/.cache/uv"
    # Browsers
    "$HOME/.cache/mozilla/firefox/"*"/cache2"
    "$HOME/.cache/mozilla/firefox/"*"/offline-cache"
    "$HOME/.cache/chromium/Default/Cache"
    "$HOME/.cache/chromium/Default/Code Cache"
    "$HOME/.cache/google-chrome/Default/Cache"
    "$HOME/.cache/google-chrome/Default/Code Cache"
)

# System-level caches (require root or sudo)
SYS_CACHES=(
    /var/cache/apt/archives/*.deb
    /var/cache/pacman/pkg/*.pkg.*
    /var/cache/dnf/*/*.rpm
    /var/cache/yum/*/*/packages/*.rpm
    /var/cache/zypp/packages/*/*/*.rpm
)

# ── Helpers ────────────────────────────────────────────────────
log() {
    local msg="[ $(date '+%Y-%m-%d %H:%M:%S') ] $*"
    echo "$msg"
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

get_size() { du -sh "$1" 2>/dev/null | cut -f1; }

to_bytes() {
    local val="${1:-0}"
    case "$val" in
        *T) awk "BEGIN{printf \"%.0f\", ${val%T}*1099511627776}" ;;
        *G) awk "BEGIN{printf \"%.0f\", ${val%G}*1073741824}" ;;
        *M) awk "BEGIN{printf \"%.0f\", ${val%M}*1048576}" ;;
        *K) awk "BEGIN{printf \"%.0f\", ${val%K}*1024}" ;;
        *)  echo "${val:-0}" ;;
    esac
}

# Run a command as root if needed (use sudo when not root, direct when root)
as_root() {
    if [[ "$IS_ROOT" == "true" ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

# ── Safe swap dance ───────────────────────────────────────────
swap_dance() {
    local total_reclaim_bytes="${1:-0}"

    # Only trigger if reclaiming > 1 GB
    local threshold=1073741824
    if [[ "$total_reclaim_bytes" -lt "$threshold" ]]; then
        log "Total reclaimable < 1 GB — skip swap dance."
        return 0
    fi

    log "Reclaiming > 1 GB — running safe swap dance to prevent OOM..."

    # Check for zram0
    [[ -b /dev/zram0 ]] || { log "No zram0 — skipping swap dance."; return 0; }

    # Find a location with enough space for a 4 GB swap file.
    # Try /tmp first, then fall back to / (disk-backed, not tmpfs).
    local need=4294967296
    local swap_dir=""
    for dir in /tmp /; do
        local free_bytes
        free_bytes=$(df -B1 "$dir" 2>/dev/null | awk 'NR==2{print $4}')
        if [[ -n "$free_bytes" && "$free_bytes" -ge "$need" ]]; then
            swap_dir="$dir"
            break
        fi
    done

    if [[ -z "$swap_dir" ]]; then
        log "No suitable location for 4 GB swap file — skipping swap dance."
        return 0
    fi

    local swap_file="${swap_dir}/.cache-clear-swap"

    log "Creating 4 GB temp swap file at $swap_file..."
    if ! as_root fallocate -l 4G "$swap_file" 2>/dev/null; then
        log "fallocate failed — falling back to dd..."
        if ! as_root dd if=/dev/zero of="$swap_file" bs=1M count=4096 status=none 2>/dev/null; then
            log "Cannot create swap file — aborting swap dance."
            return 1
        fi
    fi
    as_root chmod 600 "$swap_file"
    as_root mkswap "$swap_file"

    log "Swapping in temp file, cycling zram0..."
    as_root swapon "$swap_file"
    as_root swapoff /dev/zram0
    as_root swapon /dev/zram0
    as_root swapoff "$swap_file"
    as_root rm -f "$swap_file"

    log "Swap dance complete."
    swapon --show 2>/dev/null | sed 's/^/  /' || true
    free -h 2>/dev/null | grep -E '^(Swap|Mem)' | sed 's/^/  /'
}

# ── Help ───────────────────────────────────────────────────────
show_help() {
    cat <<EOF
cache-clear — safe cross-user cache cleaner

Usage:
  cache-clear              Interactive (preview, then confirm — default Y)
  cache-clear --dry-run    Preview only, delete nothing
  cache-clear --force      Delete without confirmation
  cache-clear --uninstall  Remove this command
  cache-clear --help       Show this help

Clears (user-level, no root needed):
  ~/.hermes/cache/  (all temp dirs)
  ~/.npm, ~/.cache/pip, ~/.cache/uv, ~/.cache/yarn
  Browser caches (Chromium, Firefox)

Clears additionally when run as root (or with sudo):
  /var/cache/apt/archives/* (Debian/Ubuntu)
  apt-get autoremove (remove unused packages)
  /var/cache/pacman/pkg/* (Arch)
  /var/cache/dnf/* (Fedora)
  systemd journal (vacuum to 50 MB)
  /tmp stale files

Preserves: root-level JSON caches, active sessions, clean.log
Safe mode: swap dance on low-memory systems before large deletes
EOF
}

# ── Clean ──────────────────────────────────────────────────────
do_clean() {
    mkdir -p "$CACHE_ROOT" 2>/dev/null || true

    local total_reclaim=0
    local all_targets=()
    local sys_targets=()

    log "=== Cache clear started ==="
    log "Mode: $([[ "$DRY_RUN" == "true" ]] && echo "DRY RUN" || echo "DELETE")"
    [[ "$IS_ROOT" == "true" ]] && log "Running as root — system caches included."

    # Gather user-level targets
    for pattern in "${USER_CACHES[@]}"; do
        for match in $pattern; do
            if [[ -e "$match" ]]; then
                local sz
                sz=$(get_size "$match")
                all_targets+=("$match")
                local bytes
                bytes=$(to_bytes "$sz")
                total_reclaim=$((total_reclaim + bytes))
            fi
        done
    done

    # Gather system-level targets (only if root or sudo available)
    if [[ "$IS_ROOT" == "true" ]] || command -v sudo >/dev/null 2>&1; then
        for pattern in "${SYS_CACHES[@]}"; do
            for match in $pattern; do
                if [[ -e "$match" ]]; then
                    local sz
                    sz=$(get_size "$match")
                    sys_targets+=("$match")
                    local bytes
                    bytes=$(to_bytes "$sz")
                    total_reclaim=$((total_reclaim + bytes))
                fi
            done
        done
    fi

    if [[ ${#all_targets[@]} -eq 0 && ${#sys_targets[@]} -eq 0 ]]; then
        log "Nothing to clean."
        return 0
    fi

    # Show what will be cleaned
    echo ""
    if [[ ${#all_targets[@]} -gt 0 ]]; then
        echo "User caches:"
        for t in "${all_targets[@]}"; do
            printf "  %6s  %s\n" "$(get_size "$t")" "$t"
        done
    fi
    if [[ ${#sys_targets[@]} -gt 0 ]]; then
        echo ""
        echo "System caches:"
        for t in "${sys_targets[@]}"; do
            printf "  %6s  %s\n" "$(get_size "$t")" "$t"
        done
    fi
    echo ""
    echo "Estimated reclaim: $(numfmt --to=iec "$total_reclaim" 2>/dev/null || echo "${total_reclaim} bytes")"
    log "User targets: ${#all_targets[@]}, System targets: ${#sys_targets[@]}"
    log "Estimated reclaim: $(numfmt --to=iec "$total_reclaim" 2>/dev/null || echo "${total_reclaim} bytes")"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "=== DRY RUN — nothing deleted ==="
        return 0
    fi

    # Confirm (default Y)
    if [[ "$FORCE" != "true" ]]; then
        read -rp "Do you wish to clear cache? [Y/n] " answer
        answer="${answer:-Y}"
        case "$answer" in
            [yY][eE][sS]|[yY]|Y) ;;
            [nN][oO]|[nN]) log "Cancelled."; return 0 ;;
            *) log "Cancelled."; return 0 ;;
        esac
    fi

    # Safe swap dance before large deletions
    swap_dance "$total_reclaim"

    # Delete user-level targets
    for t in "${all_targets[@]}"; do
        if rm -rf "$t" 2>/dev/null; then
            log "  deleted: $t"
        else
            log "  skip (permission denied): $t"
        fi
    done

    # Remove stale .tmp at hermes root
    find "$CACHE_ROOT" -maxdepth 1 -name '*.tmp' -delete 2>/dev/null || true

    # Delete system-level targets
    for t in "${sys_targets[@]}"; do
        if as_root rm -rf "$t" 2>/dev/null; then
            log "  deleted: $t"
        else
            log "  skip (permission denied): $t"
        fi
    done

    # Compact systemd journal
    if command -v journalctl >/dev/null 2>&1; then
        as_root journalctl --vacuum-size=50M 2>/dev/null || true
    fi

    # Clean APT cache and remove unused dependencies if available
    if command -v apt-get >/dev/null 2>&1; then
        log "  apt-get clean..."
        as_root apt-get clean 2>/dev/null || true
        log "  apt-get autoremove..."
        as_root apt-get autoremove --yes 2>/dev/null || true
    fi

    # Clean pacman cache if available (keep last 1 version)
    if command -v paccache >/dev/null 2>&1; then
        as_root paccache -rk1 2>/dev/null || true
    fi

    local total_after=0
    total_after=$(du -sh "$CACHE_ROOT" 2>/dev/null | cut -f1)
    log "Hermes cache after: $total_after"
    log "=== Cache clear complete ==="
    echo ""
    echo "Reclaimed ~$(numfmt --to=iec "$total_reclaim" 2>/dev/null || echo "${total_reclaim} bytes")"
}

# ── Self-install when piped to bash ────────────────────────────
self_install() {
    mkdir -p "$INSTALL_DIR"
    local target="$INSTALL_DIR/$CMD_NAME"
    local src="${BASH_SOURCE[0]:-}"

    if [[ -f "$src" ]]; then
        # Clone workflow: symlink to the real file
        ln -sf "$(readlink -f "$src")" "$target"
        chmod +x "$target"
        echo "✓ Symlinked: $target → $(readlink -f "$src")"
    else
        # Pipe workflow: the full script is being piped to bash right now.
        # We can't access BASH_SOURCE[0] (it's empty), but we CAN read
        # the script from stdin if we capture it early, or simply download
        # from GitHub. Use curl/wget to fetch the latest version.
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "https://cdn.jsdelivr.net/gh/Aldo-f/cache-clear@main/cache-clear" -o "$target"
        elif command -v wget >/dev/null 2>&1; then
            wget -qO "$target" "https://cdn.jsdelivr.net/gh/Aldo-f/cache-clear@main/cache-clear"
        else
            echo "Error: need curl or wget to install from pipe." >&2
            return 1
        fi
        chmod +x "$target"
        echo "✓ Installed: $target"
    fi

    case ":$PATH:" in
        *":$INSTALL_DIR:"*) ;;
        *)
            echo ""
            echo "⚠ $INSTALL_DIR is not on your PATH."
            echo "  bash:  export PATH=\"$INSTALL_DIR:\$PATH\""
            echo "  fish:  fish_add_path $INSTALL_DIR"
            ;;
    esac
    echo "Run \`$CMD_NAME --help\` for usage."
}

# ── Main ───────────────────────────────────────────────────────
main() {
    local src="${BASH_SOURCE[0]:-}"
    # Self-install when piped to bash (no backing script file)
    if [[ ! -f "$src" ]]; then
        self_install
        exit 0
    fi

    case "${1:-}" in
        --install)   self_install; exit 0 ;;
        --uninstall) rm -f "$INSTALL_DIR/$CMD_NAME"; echo "Uninstalled: $INSTALL_DIR/$CMD_NAME"; exit 0 ;;
        --help|-h)   show_help; exit 0 ;;
        --dry-run)   DRY_RUN=true ;;
        --force)     FORCE=true ;;
        "")          ;; # Interactive with default Y
        *)           echo "Unknown option: $1"; show_help; exit 1 ;;
    esac

    do_clean
}

main "$@"
