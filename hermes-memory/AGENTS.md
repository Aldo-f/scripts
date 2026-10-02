# hermes-memory

## OVERVIEW
`hermes_mem_manager.py` (155 lines) + `test_hermes_memory.py`. Qdrant mem0 CLI with Ollama embeddings.

## SUBCOMMANDS
- `--add TEXT` — embed and upsert a memory entry
- `--search QUERY` — vector search, prints top matches with scores
- `--list` — scroll and print all memories
- `--scan` — scan filesystem for candidate sources
- `--import` — interactive import from scan results

## CONNECTIONS
- Qdrant: `127.0.0.1:6333`, collection `"mem0"`
- Ollama embeddings: `localhost:11434`, model `nomic-embed-text:latest`
- IDs: `uuid5(NAMESPACE_DNS, text)` for deterministic dedup

## SCAN SOURCES
`scan_sources()` scans `~/.hermes/MEMORY.md`, `USER.md`, `memory/*.md`, `openviking/pending_sessions/*.json`, `config.yaml`, `mem0.json`, and one recent `~/dev/**/*.log`.

## COMMANDS
```bash
python3 hermes_mem_manager.py --add "text"
python3 hermes_mem_manager.py --search "query"
python3 hermes_mem_manager.py --list
python3 hermes_mem_manager.py --scan
python3 hermes_mem_manager.py --import
```

## DEPS
`qdrant-client`, `requests`. No API keys.