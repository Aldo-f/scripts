#!/usr/bin/env python3
"""
Email Search + Triage — find emails by subject, body, sender, or fuzzy keyword match.
Uses `himalaya` CLI under the hood. Persists all queries to SQLite for method comparison.

Usage:
  python3 email_search_triage.py "search terms ..."
  python3 email_search_triage.py --list-history
  python3 email_search_triage.py --verify-all
  python3 email_search_triage.py --compare-methods

Search syntax (himalaya DSL):
  subject <term>     — search in subject lines
  body <term>        — search in email body
  from <term>        — search in sender email/name
  to <term>          — search in recipients
  AND / OR           — combine filters
  Examples:
    "body KM-2026-25308"
    "from AWV AND body Polderstraat"
    "body verkeersbord"
"""
import sys, os, json, subprocess, re, sqlite3, hashlib
from datetime import datetime

# Config — override via env vars if needed
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("EMAIL_SEARCH_DB", os.path.join(SCRIPT_DIR, "email_queries.db"))
HIMALAYA = os.environ.get("HIMALAYA_BIN", "himalaya")


# ── Database ──────────────────────────────────────────────────────────────────

def init_db():
    """Ensure DB schema exists and register default search methods."""
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT UNIQUE,
        query TEXT,
        timestamp TEXT,
        method TEXT DEFAULT 'raw',
        found INTEGER DEFAULT 0,
        result_ids TEXT DEFAULT '[]',
        result_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        notes TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        method_name TEXT UNIQUE,
        description TEXT,
        tested_at TEXT,
        success_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0
    )
    """)
    methods = [
        ("raw",    "himalaya envelope search with raw query (no filter prefix)"),
        ("body",   "himalaya envelope search with body: filter — searches email content"),
        ("sender", "himalaya envelope search with from: filter — searches sender name/email"),
        ("fuzzy",  "himalaya envelope list + local filter: count matching terms (≥2)"),
    ]
    for name, desc in methods:
        conn.execute("INSERT OR IGNORE INTO methods (method_name, description) VALUES (?,?)",
                     (name, desc))
    conn.commit()
    conn.close()


def save_query_result(query, method, found_ids, result_count, notes=""):
    """Save or update query result in DB (upsert by query hash)."""
    qh = hashlib.sha256(query.encode()).hexdigest()[:16]
    conn = sqlite3.connect(DB)
    conn.execute("""
    INSERT INTO queries (query_hash, query, timestamp, method, found, result_ids, result_count, status, notes)
    VALUES (?,?,?,?,?,?,?,?,?)
    ON CONFLICT(query_hash) DO UPDATE SET
        timestamp=excluded.timestamp,
        method=excluded.method,
        found=excluded.found,
        result_ids=excluded.result_ids,
        result_count=excluded.result_count,
        status=excluded.status,
        notes=excluded.notes
    """, (
        qh, query, datetime.now().isoformat(), method,
        1 if found_ids else 0, json.dumps(found_ids), result_count,
        "found" if found_ids else "not_found", notes
    ))
    conn.commit()
    conn.close()


# ── Search ────────────────────────────────────────────────────────────────────

def himalaya_search(query_terms):
    """Run `himalaya envelope search <query_terms>` and return raw output lines.
    
    himalaya DSL: options come before the query string.
    Correct:  himalaya envelope search -s 50 "body KM-2026-25308"
    Wrong:    himalaya envelope search "body KM-2026-25308" -s 50
    """
    cmd = [HIMALAYA, "envelope", "search", "-s", "50"]
    try:
        result = subprocess.run(
            cmd + [query_terms],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "RUST_LOG": "error"}
        )
        if result.returncode != 0:
            return [f"himalaya error: {result.stderr.strip()[:200]}"]
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        # Filter out empty lines and table borders
        return [line for line in lines if line.strip() and "─" not in line[:3]]
    except subprocess.TimeoutExpired:
        return ["Search timeout after 30s"]
    except Exception as e:
        return [f"Search error: {e}"]


def extract_key_info(email_line):
    """Parse himalaya table row into a dict with id, subject, sender, date.
    
    himalaya table format:
    │ ID ┆ FLAGS ┆ SUBJECT ┆ FROM ┆ DATE ┆ SIZE │
    
    When FLAGS is empty the split drops that empty cell:
    [0]=ID, [1]=SUBJECT, [2]=FROM, [3]=DATE, [4]=SIZE
    When FLAGS has a value:
    [0]=ID, [1]=FLAGS, [2]=SUBJECT, [3]=FROM, [4]=DATE, [5]=SIZE
    """
    parts = [p.strip() for p in email_line.strip().split("┆") if p.strip()]
    if len(parts) < 4:
        return {"raw": email_line}
    try:
        eid = int(parts[0].replace("│", "").strip())
        # Detect whether flags column was dropped (length hint)
        if len(parts) >= 5:
            subject, sender, date = parts[1], parts[2], parts[3]
        else:
            subject, sender, date = parts[1], parts[2], ""
        return {
            "id": eid,
            "subject": subject,
            "sender": sender,
            "date": date,
        }
    except (ValueError, IndexError):
        return {"raw": email_line}


def parse_results(lines, query_terms):
    """Extract email entries from himalaya search output lines."""
    emails = []
    for line in lines:
        if "│" not in line:
            continue
        info = extract_key_info(line)
        if "id" in info:
            # Only include lines where at least one query term matches the row
            lower = line.lower()
            if any(term in lower for term in query_terms.lower().split()):
                emails.append(info)
    return emails


# ── Triage ────────────────────────────────────────────────────────────────────

def classify_thread(email_info):
    """Classify email per inbox-triage categories."""
    subject_lower = email_info.get("subject", "").lower()
    sender_lower = email_info.get("sender", "").lower()

    urgent_words = ["urgent", "asap", "deadline", "blocked", "security", "fraud", "hack", "nood"]
    noise_words = ["noreply", "no-reply", "automated", "newsletter", "unsubscribe"]
    action_words = ["report", "incident", "issue", "bug", "problem", "melding",
                    "verkeersbord", "klacht", "actie", "toetsing"]
    waiting_words = ["update", "status", "resolved", "fixed", "bezig", "onderweg"]

    if any(w in subject_lower for w in urgent_words):
        return "urgent_reply"
    if any(w in sender_lower for w in noise_words):
        return "noise"
    if any(w in subject_lower for w in action_words):
        return "action_or_reply"
    if any(w in subject_lower for w in waiting_words):
        return "waiting"
    return "reference_or_reply"


# ── Search methods ────────────────────────────────────────────────────────────

METHODS = [
    "raw",
    "body",
    "sender",
    "fuzzy",
]


def build_body_query(query):
    """Build Himalayan DSL body query with lowercase AND/OR between terms.
    himalaya requires lowercase 'and'/'or' between filters."""
    terms = [t.strip() for t in query.lower().split() if t.strip() and len(t) >= 2]
    skip = {"en", "de", "het", "een", "van", "in", "op", "bij", "voor", "af", "om"}
    meaningful = [t for t in terms if t not in skip][:5]
    if not meaningful:
        meaningful = terms[:3] if terms else ["3d"]
    # Use OR for robust matching: any matching body term finds the mail
    return " or ".join(f"body {t}" for t in meaningful)


def run_search_method(query, method):
    """Execute a single search method and return parsed emails."""
    if method == "raw":
        # Pass raw query directly — user can include DSL manually
        results = himalaya_search(query)
    elif method == "body":
        body_q = build_body_query(query)
        results = himalaya_search(body_q)
    elif method == "sender":
        first_term = next((t for t in query.lower().split()
                           if len(t) >= 2 and t not in {"en","de","het","een","van","in","op","bij","voor","af"}), query)
        results = himalaya_search(f"from {first_term}")
    elif method == "fuzzy":
        terms = query.lower().split()
        broad = " ".join(terms[:3]) if len(terms) >= 3 else query
        results = himalaya_search(broad)
        filtered = []
        for line in results:
            matches = sum(1 for term in terms if term in line.lower())
            if matches >= 2:
                filtered.append(line)
        results = filtered
    else:
        results = himalaya_search(query)
    return parse_results(results, query)


def run_all_methods(query):
    """Run all search methods and return the best result set."""
    best_results = []
    best_method = ""

    for method in METHODS:
        emails = run_search_method(query, method)
        print(f"Method {method}: {len(emails)} results")
        if len(emails) > len(best_results):
            best_results = emails
            best_method = method

    return best_results, best_method


# ── CLI commands ─────────────────────────────────────────────────────────────

def list_history():
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
    SELECT id, substr(query,1,80), method, found, result_count, timestamp, status
    FROM queries ORDER BY id DESC
    """).fetchall()
    conn.close()
    print("=== Zoekgeschiedenis ===")
    for row in rows:
        icon = "✓" if row[3] else "✗"
        print(f"  [{icon}] [{row[0]}] {row[1]}... | method:{row[2]} | found:{row[3]} ({row[4]} results) | {row[5]} | {row[6]}")
    print()


def verify_all():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, query, method FROM queries").fetchall()
    conn.close()
    print("=== Verificatie van alle opgeslagen queries ===")
    for qid, query, method in rows:
        results = himalaya_search(query)
        ids = []
        for line in results:
            info = extract_key_info(line)
            if "id" in info:
                ids.append(info["id"])
        found = len(ids) > 0
        save_query_result(query, method, ids, len(ids), f"Re-verified on {datetime.now().isoformat()}")
        icon = "✓ FOUND" if found else "✗ NOT FOUND"
        print(f"  {icon} | {query} | {len(ids)} results")
    print("Re-verification complete.")


def compare_methods():
    conn = sqlite3.connect(DB)
    queries = conn.execute("SELECT id, query FROM queries").fetchall()
    methods = conn.execute("SELECT method_name FROM methods WHERE method_name IN (?,?)",
                           ("raw", "body")).fetchall()
    conn.close()

    print("=== Methode-vergelijking ===")
    for method_name in [m[0] for m in methods]:
        success = 0
        total = len(queries)
        for qid, query in queries:
            ids = run_search_method(query, method_name)
            if ids:
                success += 1
            save_query_result(query, method_name, ids, len(ids), f"Method test {method_name}")
        rate = (success / total * 100) if total > 0 else 0
        conn = sqlite3.connect(DB)
        conn.execute("""
        UPDATE methods SET success_count=?, total_count=?, success_rate=?, tested_at=?
        WHERE method_name=?
        """, (success, total, rate, datetime.now().isoformat(), method_name))
        conn.commit()
        conn.close()
        print(f"  {method_name}: {success}/{total} = {rate:.1f}%")
    print()


def main():
    init_db()
    if len(sys.argv) < 2:
        print("Usage: email_search_triage.py \"<search_terms>\" | --list-history | --verify-all | --compare-methods")
        print("Examples:")
        print("  email_search_triage.py 'body KM-2026-25308'")
        print("  email_search_triage.py 'from AWV AND body Polderstraat'")
        print("  email_search_triage.py 'Merelbeke Melle verkeersbord'")
        sys.exit(1)

    args = sys.argv[1:]

    if args[0] == "--list-history":
        list_history()
        return
    if args[0] == "--verify-all":
        verify_all()
        return
    if args[0] == "--compare-methods":
        compare_methods()
        return

    query = " ".join(args)
    print(f"Searching for: {query}\n")

    best_results, best_method = run_all_methods(query)

    print(f"\nBest method: {best_method} with {len(best_results)} result(s):\n")

    for email in best_results[:10]:
        classification = classify_thread(email)
        print(f"  [{email['id']}] {email.get('date', '?')} | {classification}")
        print(f"     From: {email.get('sender', '?')}")
        print(f"     Subject: {email.get('subject', '?')}")
        print()

    ids = [e["id"] for e in best_results]
    notes = f"Best method: {best_method}; searched {len(METHODS)} methods"
    save_query_result(query, best_method, ids, len(ids), notes)
    print(f"Query saved to database. Method used: {best_method}")
    print("Run with --list-history to see all queries, or --compare-methods to test different approaches.")


if __name__ == "__main__":
    main()
