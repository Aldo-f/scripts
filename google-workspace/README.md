# google-workspace

Google Workspace clasp deployment and execution helper utilities.

## Files

- **`capture-logs.sh`**: Captures Google Apps Script execution logs to `~/dev/06-apps-script-google/logs/` without truncation, showing statistics for drafts and sent emails.
- **`run-dryrun.sh`**: Executes the `dryRun` function using `clasp run` and immediately tails the log output.
- **`setup-clasp-creds.sh`**: Links clasp with your custom OAuth 2.0 Desktop Client credentials, allowing script execution via local commands.

## Usage

### Linking your Google OAuth credentials with clasp:
```bash
~/scripts/google-workspace/setup-clasp-creds.sh /path/to/downloaded_oauth_credentials.json
```

### Capturing Stackdriver logs:
```bash
~/scripts/google-workspace/capture-logs.sh
```

### Running dryRun and checking logs:
```bash
~/scripts/google-workspace/run-dryrun.sh
```
