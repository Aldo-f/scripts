# CONTRIBUTING

Thank you for your interest in **cache-clear**!

## Goal

A portable, safe bash script that clears stale temporary data from common cache locations on any Linux system — without breaking active sessions, expensive-to-rebuild caches, or requiring root on typical usage.

## What this is

- A small, opinionated cache cleaner
- Works on any Linux system (Raspberry Pi, desktop, server)
- Safe by default: previews before deleting, preserves active JSON caches and sessions
- Includes a safe swap dance on low-memory systems to prevent OOM
- Installable via one-liner: `curl -sL https://raw.githubusercontent.com/Aldo-f/cache-clear/main/cache-clear | bash`

## What this is not

- A system maintenance suite
- A replacement for package manager cache tools (`apt clean`, `pacman -Sc`, etc.)
- Something that requires `sudo` for normal operation

## How to contribute

### Reporting issues
1. Search existing issues first
2. Include: OS/distro, `uname -a`, output of `cache-clear --dry-run`
3. Mention which caches are failing (or unexpectedly cleared)

### Suggesting features
- New cache locations to support?
- Platform-specific behavior?
- Better dry-run output?

Open an issue with `enhancement` label.

### Submitting changes
1. Fork + clone the repo
2. Create a branch: `git checkout -b feature/safe-add-npm`
3. Make changes — keep it simple, add no new dependencies
4. Test with `bash cache-clear --dry-run`
5. Commit with clear message: `add: include ~/.cache/uv in user targets`
6. Push and open a PR

### Code style
- Bash only, no external deps beyond coreutils/find/du
- Follow existing style: 4-space indent, `local` for all variables
- Test on Debian/Ubuntu and Arch if possible

### Review process
- I'll test on my Pi 5 (Raspberry Pi OS, Debian-based)
- Cross-check on Ubuntu/Arch before merging
- CI isn't set up yet — manual testing only

## License

MIT — free to use, modify, redistribute.

## Acknowledgments

Built for the Hermes Agent project but designed to work everywhere.
Inspired by the pain of `rm -rf ~/.cache/*` on a headless Pi with 4 GB RAM.
