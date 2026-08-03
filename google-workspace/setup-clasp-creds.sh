#!/bin/bash
# Reusable Setup Helper for Google Workspace OAuth Credentials
# This script configures clasp to use a custom client ID and secret for local execution.
# It can be used across all your scripts and Google Skills.

CREDS_JSON="$1"

if [ -z "$CREDS_JSON" ]; then
  echo "Usage: $0 /path/to/downloaded/oauth_credentials.json"
  echo ""
  echo "Please download your Desktop OAuth 2.0 Credentials from Google Cloud Console first:"
  echo "1. Go to https://console.cloud.google.com/apis/credentials"
  echo "2. Download the Desktop OAuth Client credentials JSON file."
  exit 1
fi

if [ ! -f "$CREDS_JSON" ]; then
  echo "Error: Credentials file not found at '$CREDS_JSON'"
  exit 1
fi

echo "=== Configuring clasp with your custom Google Workspace OAuth Credentials ==="
echo "Credential file: $CREDS_JSON"
echo ""

# Log out of any active clasp sessions
echo "Logging out of existing clasp sessions..."
clasp logout 2>/dev/null

# Log in using your custom client secret and ID
echo "Starting login process..."
clasp login --creds "$CREDS_JSON"

echo ""
echo "=== Success ==="
echo "clasp is now logged in with your custom OAuth 2.0 Client credentials."
echo "Your script execution will now use your custom Workspace scopes!"
echo ""
echo "To test script execution, go to any clasp project and run:"
echo "  clasp run dryRunWithMax"
