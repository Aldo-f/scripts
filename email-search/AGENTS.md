# Email Search & Triage Skill

Search email (via `himalaya`) by subject, body, sender, or fuzzy keyword match. All queries saved to SQLite for method comparison.

## Setup

Requires: `himalaya` CLI (IMAP/SMTP email client)

```bash
pip install  # no Python deps (stdlib only)
```

Set env: `EMAIL_SEARCH_DB=./email_queries.db` (default: local `.db`)

## Usage

```bash
python3 email_search_triage.py "body KM-2026-25308"
python3 email_search_triage.py --list-history
python3 email_search_triage.py --compare-methods
```

## Integration

As Hermes skill: place in `skills/email-search/` and reference `SKILL.md`.
