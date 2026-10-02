# Scripts

## OVERVIEW
Collection of 65 automation scripts across 12 subdirectories: music download (deezer), form automation (form-automation-v2), Git/Google/SSD/infra tooling, and agent KB management. Purely cron-driven — no CI/CD pipeline exists.

## STRUCTURE
```
scripts/
├── deezer/                # Deezer music download/search CLI (own venv, 46 tests) → AGENTS.md
├── form-automation-v2/    # Self-improving Google Forms bot (AI + CAPTCHA) → AGENTS.md
├── git-tools/             # Auto-push to GitHub (git_push.sh)
├── google-workspace/      # clasp + Stackdriver log utilities
├── opencode-init-deep/    # Nightly /init-deep KB initialization cron
├── ssd-tools/             # SSD health + stress testing (Pi 5 + USB SSD)
├── freellm-proxy/         # ABANDONED — proxy works, Cursor CLI incompatible
├── hermes-tools/          # Daily skills push + weekly Hermes backup zip
├── hermes-memory/         # Qdrant mem0 memory CLI
├── pi-monitor/            # k3s node readiness monitor (every 5 min)
├── model-fetcher/         # Lists free models from models.dev API
└── bookstack-checker/     # BookStack reference URL checker
```

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Download/search music | `deezer/` → `AGENTS.md` |
| Form automation + AI improvement | `form-automation-v2/` → `AGENTS.md` |
| Git auto-push | `git-tools/git_push.sh` |
| Google Apps Script | `google-workspace/` |
| KB init cron | `opencode-init-deep/init-deep-cron.sh` |
| SSD health checks | `ssd-tools/` |
| Hermes memory management | `hermes-memory/` |
| k3s node monitoring | `pi-monitor/` |

## COMMANDS
```bash
# Deezer (uses ~/.venvs/deezer venv)
~/scripts/deezer/scripts/deezer.py download-playlist "https://www.deezer.com/playlist/..." --workers 4
~/scripts/deezer/scripts/deezer.py search "artist track"
~/.venvs/deezer/bin/python -m pytest ~/scripts/deezer/tests/

# Form automation
~/scripts/form-automation-v2/scripts/run_automation.py --batch 5 --delay 2.0

# Git push
~/scripts/git-tools/git_push.sh

# Google dry-run (clasp)
cd ~/dev/06-apps-script-google/LabelReminder && clasp run dryRunWithMax

# KB init
~/scripts/opencode-init-deep/init-deep-cron.sh

# SSD health
python3 ~/scripts/ssd-tools/ssd_health.py
python3 ~/scripts/ssd-tools/stress_test_ssd.py 600 500

# Hermes backup
~/scripts/hermes-tools/hermes_backup.sh
```

## CONVENTIONS
- **Absolute paths** in all cron jobs — relative paths silently fail
- **Logs consolidated** per subdirectory (`ssd-tools/*.log`, `git-tools/git_push.log`, etc.)
- **Per-tool venv isolation** — each Python tool manages its own deps (`requirements.txt` + dedicated venv)
- **Timestamped logs** — `init-deep-cron.sh` uses a stamper script prefixing every line with `[YYYY-MM-DD HH:MM:SS]`

## ANTI-PATTERNS
- **No CI/CD** — no `.github/workflows/`, no Makefile, no tox. All automation is cron + manual
- **Hardcoded secrets in source** — API tokens in `bookstack-checker/bookstack_bronnen_check.py`, `freellm-proxy/custom_freellm_proxy.py`, `form-automation-v2/src/api_integration.py`
- **Committed `.env` files** — `deezer/.env` is tracked in git (should be gitignored); `.env.example` is safe to commit as a template
- **Cron path drift** — scripts referenced at `/home/aldo/scripts/` but actually live in subdirs (`git-tools/`, `ssd-tools/`); `cron.log` shows repeated failures
- **Abandoned infra still active** — `freellm-proxy/` marked ABANDONED but systemd service runs
- **Standalone "tests"** — `test_hermes_memory.py` and `test_api.py` use `test_` prefix but aren't pytest-discoverable

## NOTES
- `deezer/` is a git submodule (`Aldo-f/deezer.git`) but contains standalone scripts not from that submodule
- `form-automation-v2/src/browser_manager.py` is a simulation dummy — not production-ready
- `freellm-proxy/README.md` documents the full abandonment rationale
- Only `deezer/` has real tests (46 hermetic unittest tests via pytest)
