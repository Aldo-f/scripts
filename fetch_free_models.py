#!/usr/bin/env python3
import json, requests

url = "https://models.dev/api.json"
resp = requests.get(url, timeout=10)
resp.raise_for_status()
data = resp.json()

free = []
for provider, cfg in data.items():
    for m_name, mUp in cfg.get("models", {}).items():
        cost = mUp.get("cost", {})
        if cost.get("input") == 0 and cost.get("output") == 0:
            free.append({
                "provider": cfg.get("name", provider),
                "model_id": mUp.get("ografi", m_name),
                "name": mUp.get("name"),
            })

print(f"Found {len(free)} free models:")
for i in free:
    print(f"- {i['provider']} – {i['model_id']} ({i['name']})")
