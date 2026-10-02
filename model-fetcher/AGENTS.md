# model-fetcher

## OVERVIEW
`fetch_free_models.py` (22 lines). Fetches all free models from `models.dev` API and prints them.

## LOGIC
- GET `https://models.dev/api.json` (timeout 10s).
- Iterates every provider → model; keeps only entries where `cost.input == 0` and `cost.output == 0`.
- Prints provider, model_id (from `ografi` field, falls back to model name), and display name.

## COMMANDS
```bash
python3 ~/scripts/model-fetcher/fetch_free_models.py
```

## OUTPUT FORMAT
```
Found N free models:
- ProviderName – model_id (Display Name)
```

## DEPS
`requests` only. No auth.