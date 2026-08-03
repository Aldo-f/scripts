# opencode-init-deep

Automation utilities for hierarchical `AGENTS.md` initialization.

## Files

- **`init-deep-cron.sh`**: A nightly cron script that triggers the `opencode run "/init-deep"` command for `/home/aldo/dev` with a 5-minute safety timeout and detailed log captures to `init-deep.log`.
- **`trigger-both.sh`**: A utility script to sequentially execute both active cron tasks: credential synchronizations (`02-ai-llm-infra-sync`) and `init-deep` KB rebuilds.
- **`init-deep.log`**: Logging capture for `init-deep-cron.sh`.
- **`direct-exec.log`**: Detailed logging output from executing `trigger-both.sh`.

## Usage

### Nightly KB Init Cron Configuration:
Recommended cron format (running daily at 02:00):
```cron
0 2 * * * /home/aldo/scripts/opencode-init-deep/init-deep-cron.sh
```

### Manual Sequential Trigger:
```bash
/home/aldo/scripts/opencode-init-deep/trigger-both.sh
```
