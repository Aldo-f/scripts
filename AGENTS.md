# Scripts

## OVERVIEW
Scripts for infrastructure, Git automation, and agent knowledge base management.

## STRUCTURE
```
scripts/
├── deezer/               # Deezer playlist and search tool
├── git-tools/            # Git workflow automation
├── google-workspace/     # Google Workspace clasp & log utilities
├── opencode-init-deep/   # init-deep automated knowledge base
└── ssd-tools/            # SSD health and stress testing
```

## COMMANDS
```bash
# Initialize knowledge base
~/scripts/opencode-init-deep/init-deep-cron.sh

# Run Git push
~/scripts/git-tools/git_push.sh

# Run Google dry-run with default limit (3)
cd ~/dev/06-apps-script-google/LabelReminder && clasp run dryRunWithMax

# Deezer music download (uses ~/.venvs/deezer venv)
~/scripts/deezer/scripts/deezer.py download-playlist "https://www.deezer.com/playlist/..." --workers 4
~/scripts/deezer/scripts/deezer.py search "artist track"
~/scripts/deezer/scripts/deezer.py whoami

# Run deezer tests
~/.venvs/deezer/bin/python -m pytest ~/scripts/deezer/tests/
```

## NOTES
- Always use absolute paths in cron jobs.
- Keep logs consolidated within the respective subdirectories (`ssd-tools/*.log`, etc.).
