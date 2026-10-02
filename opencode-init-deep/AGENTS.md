# opencode-init-deep AGENTS

This directory provides automation for hierarchical `AGENTS.md` generation across the codebase at `/home/aldo/dev`.

## Goal
- Discover project structure, entry points, conventions, and anti‑patterns.
- Determine appropriate locations for `AGENTS.md` files (root and sub‑directories).
- Generate, deduplicate, validate and trim those `AGENTS.md` files.

## Files
- `init-deep-cron.sh` – Nightly cron wrapper that runs `opencode run "/init-deep" --dir /home/aldo/dev` with a 5‑minute timeout. All output is logged to `init-deep.log` with a timestamp prefix on every line.
- `trigger-both.sh` – Manual helper to run the credential‑sync job and the init‑deep job sequentially, also timestamped.
- `init-deep.log` – Log of the nightly run; each line begins with `[YYYY-MM-DD HH:MM:SS]`.
- `direct-exec.log` – Log of manual execution of `trigger-both.sh`; also timestamped.

## Log format
All logs use the `log()` helper defined in `init-deep-cron.sh` which prefixes each message:
```
[2026-07-30 16:16:48] === Starting nightly init-deep initialization ===
[2026-07-30 16:16:48] Using opencode run /init-deep --dir /home/aldo/dev
```
This guarantees chronological traceability for debugging and audit purposes.
