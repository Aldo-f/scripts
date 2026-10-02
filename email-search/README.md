# Email Search & Triage

Search emails via `himalaya` CLI by subject, body, sender, or fuzzy keyword match. All queries persisted to SQLite for method comparison.

## Features

- **4 search methods**: `raw`, `body`, `sender`, `fuzzy`
- **Triage classification**: `urgent_reply`, `action_or_reply`, `waiting`, `noise`, `reference_or_reply`
- **Persistent query history**: SQLite tracks every query, method, result count, and status
- **Method comparison**: `--compare-methods` runs all methods against all past queries

## Requirements

- `himalaya` CLI (IMAP/SMTP email client)
- Python 3.10+ (stdlib only, no pip install needed)

## Usage

```bash
cd email-search
python3 email_search_triage.py "body KM-2026-25308"
python3 email_search_triage.py --list-history
python3 email_search_triage.py --compare-methods
```

## Configuration

| Env Var             | Default                          | Description              |
| ------------------- | -------------------------------- | ------------------------ |
| `EMAIL_SEARCH_DB`   | `./email_queries.db`             | SQLite database path     |
| `HIMALAYA_BIN`      | `himalaya`                       | Path to himalaya binary  |

## License

MIT
