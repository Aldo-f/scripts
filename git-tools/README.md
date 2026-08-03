# git-tools

Git automation tools for the `scripts` repository.

## Files

- **`git_push.sh`**: Auto-push changes to the GitHub repository. It ensures Git identity is set, stages all changes, commits with a timestamp, pulls remote updates, and pushes to the `origin main` branch with `--force-with-lease`.
- **`git_push.log`**: Standard output log from the last git push run.

## Usage

Run the push script manually:
```bash
~/scripts/git-tools/git_push.sh
```

It is also run automatically via cron jobs or during system maintenance checks.
