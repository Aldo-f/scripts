#!/usr/bin/env python3
"""
BookStack Bronnen Check — verifies all pages' Bronnen sections
are up-to-date by comparing source URLs and tracking a changelog.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

PAGES = {
    3: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/home-overzicht",
    4: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/digitale-collectie",
    5: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/veelgestelde-vragen",
    6: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/compatibele-apparaten-en-apps",
    7: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/inloggen-op-de-publiekspcs",
    8: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/cinebib-online-films-streamen",
    9: "https://bookstack.aldof.duckdns.org/books/digitale-collectie-gent/page/digipunt-digitale-hulp-in-de-bibliotheek",
}
TOKEN = "cliImport:bkstack_cdf53670f0c357ec31caf9a35e963c37"
STATE_FILE = os.path.expanduser("~/bookstack/state/sources.json")
CHANGELOG = os.path.expanduser("~/bookstack/CHANGELOG.md")


def load_state() -> Dict[str, str]:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_bronnen(html: str) -> Tuple[List[str], str]:
    """Return (list of source URLs, 'Laatst gecontroleerd: ...' text)"""
    soup = BeautifulSoup(html, "html.parser")
    sources = []
    gecontroleerd = ""

    # Look for horizontal rule followed by Bronnen heading
    for hr in soup.find_all("hr"):
        heading = hr.find_next(["h2", "h3", "h4"])
        if heading and re.search(r"Bronnen", heading.get_text()) or (heading and heading.find_next(string=re.compile(r"Bronnen"))):
            # Find all links in the Bronnen section
            next_heading = heading.find_next(["h2", "h3", "h4"])
            section = heading
            while section and (next_heading is None or section is not next_heading):
                for a in section.find_all("a", href=True):
                    href = a.get("href") or ""
                    if href.startswith("http") and "bookstack.aldof.duckdns.org" not in href and href not in sources:
                        sources.append(href)
                # Look for "Laatst gecontroleerd" text
                text = section.get_text()
                match = re.search(r"Laatst gecontroleerd:\s*(\d{4}-\d{2}-\d{2})", text)
                if match:
                    gecontroleerd = match.group(0)
                section = section.find_next()
                if section == next_heading:
                    break
    return sources, gecontroleerd


def hash_url(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "BookStack-Bronnen-Checker/1.0"})
        resp.raise_for_status()
        return hashlib.sha256(resp.content).hexdigest()
    except Exception as e:
        return f"ERROR:{str(e)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default=STATE_FILE)
    parser.add_argument("--changelog", default=CHANGELOG)
    parser.add_argument("--token", default=TOKEN)
    args = parser.parse_args()

    state = load_state()
    headers = {"Authorization": f"Token {args.token}"}

    changes = []
    errors = []
    unchanged = []
    current_state = {}

    for page_id, url in PAGES.items():
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text
            sources, gecontroleerd = fetch_bronnen(html)
            if sources:
                for src in sources:
                    current_state[src] = hash_url(src)
                    old = state.get(src, "")
                    if current_state[src].startswith("ERROR:"):
                        errors.append(f"{src} — {current_state[src]}")
                    elif old != "" and current_state[src] != old and not current_state[src].startswith("ERROR:"):
                        changes.append(f"- {src} (changed) — referenced by page id={page_id}")
                    elif old == current_state[src] and not current_state[src].startswith("ERROR:"):
                        unchanged.append(src)
            else:
                # No sources found — log it but don't treat as error
                pass
        except Exception as exc:
            errors.append(f"Page {page_id}: {str(exc)}")

    # Write changelog if anything changed
    if changes or errors:
        with open(args.changelog, "a", encoding="utf-8") as f:
            f.write(f"\n---\n\n## {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
            f.write("### Changes\n")
            for c in changes:
                f.write(f"{c}\n")
            if errors:
                f.write("\n### Errors / Timeouts\n")
                for e in errors:
                    f.write(f"- {e}\n")
            f.write(f"\n### Unchanged ({len(set(unchanged))})\n")
            for src in sorted(set(unchanged)):
                f.write(f"- {src}\n")
            f.write(f"\n### Pages checked: {len(PAGES)}\n")

    save_state(current_state)
    print(f"Checked {len(PAGES)} pages. Changes: {len(changes)}. Unchanged: {len(unchanged)}. Errors: {len(errors)}. State: {args.state}")


if __name__ == "__main__":
    main()

# Duplicate detection module

def find_duplicates(pages_text: dict) -> list:
    """Compare all page texts and find duplicate content."""
    import difflib
    duplicates = []
    texts = list(pages_text.items())  # (id, text)
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            id_a, text_a = texts[i]
            id_b, text_b = texts[j]
            # Compare text blocks in 3-sentence windows
            lines_a = [line.strip() for line in text_a.split('.') if len(line) > 20]
            lines_b = [line.strip() for line in text_b.split('.') if len(line) > 20]
            for la in lines_a:
                for lb in lines_b:
                    ratio = difflib.SequenceMatcher(None, la, lb).ratio()
                    if ratio > 0.7 and len(la) > 50:
                        duplicates.append({
                            "pages": f"{id_a} ↔ {id_b}",
                            "similarity": f"{ratio:.0%}",
                            "excerpt_a": la[:120],
                            "excerpt_b": lb[:120],
                        })
    return duplicates
