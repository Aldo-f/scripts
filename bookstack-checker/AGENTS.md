# bookstack-checker

## OVERVIEW
`bookstack_bronnen_check.py` (171 lines). Verifies BookStack "Bronnen" (Sources) sections are up-to-date across 8 pages.

## LOGIC
- Fetches 8 pages from `bookstack.aldof.duckdns.org` using API token auth.
- Extracts external source URLs from each page's Bronnen section (after `<hr>` + heading).
- Hashes each URL's content via SHA-256; compares against stored state.
- Appends changelog with changes / errors / unchanged to `~/bookstack/CHANGELOG.md`.
- Saves new state to `~/bookstack/state/sources.json`.

## API TOKEN
Hardcoded: `cliImport:bkstack_cdf53670f0c357ec31caf9a35e963c37` — rotate before production.

## DUPLICATE DETECTION
`find_duplicates(pages_text)` compares page texts pairwise using `difflib.SequenceMatcher` on 3-sentence windows; flags pairs with >70% similarity.

## COMMANDS
```bash
python3 ~/scripts/bookstack-checker/bookstack_bronnen_check.py
```

## DEPS
`requests`, `BeautifulSoup` (bs4). No other dependencies.