#!/usr/bin/env python3
"""
Testcases for email_search_triage.py — queries that were NOT found immediately.
These test the body-search capability and triage classification.

Run: python3 ~/dev/scripts/test_email_search.py
"""
import sys, os, json, subprocess, sqlite3, hashlib
from datetime import datetime

SCRIPT = os.path.expanduser("~/.hermes/email_search_triage.py")
DB = os.path.expanduser("~/.hermes/email_queries.db")

# Queries that failed with initial search methods and need body search
UNFOUND_QUERIES = [
    {
        "query": "Merelbeke Melle verkeersbord Polderstraat Cornelius Sneyssenslaan",
        "expected_ids": [571735],
        "expected_subject_contains": "KM-2026-25308",
        "expected_body_contains": "Cornelius Sneyssenslaan",
        "notes": "Verkeersbord Melle — straatnaam in body, niet subject"
    },
    {
        "query": "KW-2026-25308",
        "expected_ids": [571735],
        "expected_subject_contains": "KM-2026-25308",
        "notes": "Typo variant KW vs KM — moet toch vinden"
    },
]


def run_search(query):
    """Run the search script and return parsed results."""
    result = subprocess.run(
        ["python3", SCRIPT, query],
        capture_output=True, text=True, timeout=60,
    )
    return result.stdout + result.stderr


def test_body_search():
    """Test that body search finds emails where keywords are in body, not subject."""
    print("=" * 60)
    print("TEST: body search voor verkeersbord Melle")
    print("=" * 60)

    for tc in UNFOUND_QUERIES:
        print(f"\nQuery: {tc['query']}")
        output = run_search(tc["query"])

        # Check if expected mail ID appears in output
        found_ids = [str(eid) for eid in tc.get("expected_ids", [])]
        found_any = any(fid in output for fid in found_ids)

        status = "✓ PASS" if found_any else "✗ FAIL"
        print(f"  {status} — expected ID {tc.get('expected_ids')}")

        if not found_any:
            print(f"  Output snippet: {output[:300]}")

        # Verify subject contains expected dossier
        if "expected_subject_contains" in tc:
            subject_ok = tc["expected_subject_contains"] in output
            print(f"  {'✓' if subject_ok else '✗'} Subject contains '{tc['expected_subject_contains']}'")

    print("\n" + "=" * 60)


def test_triage_classification():
    """Verify triage categories are applied correctly."""
    print("\nTEST: triage classification")
    print("=" * 60)

    # Run a known query and check classification in output
    output = run_search("Merelbeke Melle verkeersbord")

    categories = ["urgent_reply", "action_or_reply", "waiting", "noise", "reference_or_reply"]
    for cat in categories:
        if cat in output.lower():
            print(f"  ✓ Category '{cat}' found in output")

    print()


def test_query_persistence():
    """Verify queries are saved to SQLite DB."""
    print("TEST: query persistence in SQLite")
    print("=" * 60)

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT COUNT(*) FROM queries").fetchone()
    conn.close()

    print(f"  Queries in DB: {rows[0]}")
    if rows[0] > 0:
        print("  ✓ PASS — queries persisted")
    else:
        print("  ✗ FAIL — no queries in DB")
    print()


def test_compare_methods():
    """Run --compare-methods and verify all methods are tested."""
    print("TEST: --compare-methods")
    print("=" * 60)

    result = subprocess.run(
        ["python3", SCRIPT, "--compare-methods"],
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr

    methods = ["himalaya_raw", "himalaya_fuzzy", "himalaya_awv", "himalaya_body"]
    for method in methods:
        if method in output:
            print(f"  ✓ Method '{method}' tested")
        else:
            print(f"  ✗ Method '{method}' missing")

    print()


def main():
    print("\nEmail Search Triage — Testcases")
    print(f"Script: {SCRIPT}")
    print(f"DB: {DB}\n")

    test_body_search()
    test_triage_classification()
    test_query_persistence()
    test_compare_methods()

    print("=" * 60)
    print("Test run complete.")
    print("Re-run with: python3 ~/dev/scripts/test_email_search.py")


if __name__ == "__main__":
    main()