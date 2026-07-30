# Scripts

## OVERVIEW
Scripts for infrastructure, Git automation, and agent knowledge base management.

## STRUCTURE
```
scripts/
├── git-tools/            # Git workflow automation
├── opencode-init-deep/   # init-deep automated knowledge base
└── ssd-tools/            # SSD health and stress testing
```

## COMMANDS
```bash
# Initialize knowledge base
~/scripts/opencode-init-deep/init-deep-cron.sh

# Run Git push
~/scripts/git-tools/git_push.sh
```

## NOTES
- Always use the absolute path in cron jobs.
- Keep logs consolidated within the respective subdirectories.
