# opencode-init-deep

Automation utilities for hierarchical `AGENTS.md` initialization across `/home/aldo/dev`.

## Files

- **`init-deep-cron.sh`**: Nightly cron script that triggers `opencode run "/init-deep"` for `/home/aldo/dev` with a 5-minute safety timeout and detailed log captures to `init-deep.log`.
- **`trigger-both.sh`**: Utility script to sequentially execute both active cron tasks: credential synchronizations (`02-ai-llm-infra-sync`) and `init-deep` KB rebuilds.
- **`init-deep.log`**: Logging capture for `init-deep-cron.sh` (includes timestamps for every log line).
- **`direct-exec.log`**: Detailed logging output from executing `trigger-both.sh` (includes timestamps for every log line).

## Usage

### Nightly KB Init Cron Configuration

Recommended cron format (running daily at 02:00):

```cron
0 2 * * * /home/aldo/dev/scripts/opencode-init-deep/init-deep-cron.sh
```

### Manual Sequential Trigger

```bash
/home/aldo/dev/scripts/opencode-init-deep/trigger-both.sh
```

## Log Format

All log files include ISO-like timestamps for every line:
```
[2026-07-30 16:16:48] === Starting nightly init-deep initialization ===
[2026-07-30 16:16:48] Using opencode run /init-deep --dir /home/aldo/dev
```

The `log_line()` function in `init-deep-cron.sh` prepends timestamps to all output.
