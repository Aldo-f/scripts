#!/usr/bin/env python3
"""
Hermes Memory Manager - Direct Qdrant mem0 integration
Usage: python3 hermes_mem_manager.py [--add <text>] [--search <query>] [--list] [--scan]
"""
import argparse, json, requests, uuid, sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

# Config
QDRANT_HOST = "127.0.0.1"
QDRANT_PORT = 6333
COLLECTION = "mem0"
OLLAMA_EMBED = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text:latest"
USER_ID = "hermes-user"
AGENT_ID = "hermes"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False, timeout=60)

def embed(text: str):
    r = requests.post(OLLAMA_EMBED, json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
    r.raise_for_status()
    return r.json()["embedding"]

def add_memory(text: str):
    vec = embed(text)
    pt = PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, text)),
        vector=vec,
        payload={"text": text, "user_id": USER_ID, "agent_id": AGENT_ID}
    )
    client.upsert(collection_name=COLLECTION, points=[pt])
    print(f"✅ Added: {text[:80]}...")
    return pt.id

def search_memory(query: str, limit: int = 10):
    vec = embed(query)
    res = client.query_points(
        collection_name=COLLECTION,
        query=vec,
        limit=limit,
        query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=USER_ID))])
    )
    for p in res.points:
        print(f"  [{p.score:.3f}] {p.payload.get('text', '')}")

def list_memories(limit: int = 50):
    res, _ = client.scroll(collection_name=COLLECTION, limit=limit, with_payload=True, with_vectors=False)
    for i, p in enumerate(res, 1):
        print(f"  [{i}] {p.payload.get('text', '')}")

def scan_sources():
    """Scan filesystem for potential memory candidates"""
    print("=== Scanning for memory candidates ===\n")

    sources = []

    # 1. Built-in memory files
    for f in [Path("~/.hermes/MEMORY.md"), Path("~/.hermes/USER.md")]:
        f = f.expanduser()
        if f.exists() and f.stat().st_size > 0:
            content = f.read_text().strip()
            if content:
                sources.append((f"file:{f}", content[:500]))

    # 2. Project notes
    for f in Path("~/.hermes/memory").expanduser().glob("*.md"):
        if f.exists():
            content = f.read_text().strip()
            if content:
                sources.append((f"file:{f}", content[:500]))

    # 3. OpenViking sessions
    ov_sessions = Path("~/.hermes/openviking/pending_sessions").expanduser()
    if ov_sessions.exists():
        for f in ov_sessions.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                # Extract relevant text
                text = json.dumps(data, indent=2)[:1000]
                sources.append((f"openviking:{f.name}", text))
            except:
                pass

    # 4. Config files
    for f in [Path("~/.hermes/config.yaml"), Path("~/.hermes/mem0.json")]:
        f = f.expanduser()
        if f.exists():
            content = f.read_text().strip()[:500]
            sources.append((f"config:{f.name}", content))

    # 5. Log files (recent)
    for f in Path("~/dev").expanduser().rglob("*.log"):
        try:
            content = f.read_text()[-1000:]
            sources.append((f"log:{f.relative_to(Path('~/dev').expanduser())}", content))
            break  # just one recent
        except:
            pass

    # Print candidates
    print(f"Found {len(sources)} candidate sources:\n")
    for i, (src, content) in enumerate(sources, 1):
        print(f"  {i}. {src}")
        print(f"     Preview: {content[:120].replace(chr(10), ' ')}...\n")

    return sources

def main():
    parser = argparse.ArgumentParser(description="Hermes mem0 memory manager")
    parser.add_argument("--add", metavar="TEXT", help="Add memory entry")
    parser.add_argument("--search", metavar="QUERY", help="Search memories")
    parser.add_argument("--list", action="store_true", help="List all memories")
    parser.add_argument("--scan", action="store_true", help="Scan for memory candidates")
    parser.add_argument("--import", dest="import_mem", action="store_true", help="Interactive import from scan")
    args = parser.parse_args()

    if args.add:
        add_memory(args.add)
    elif args.search:
        search_memory(args.search)
    elif args.list:
        info = client.get_collection(COLLECTION)
        print(f"Total memories: {info.points_count}")
        list_memories()
    elif args.scan:
        scan_sources()
    elif args.import_mem:
        sources = scan_sources()
        if not sources:
            print("No candidates found.")
            return
        print("Select entries to import (comma-separated numbers, 'all', or Enter to skip):")
        choice = input("> ").strip()
        if choice == "all":
            to_import = sources
        elif choice:
            try:
                idxs = [int(x)-1 for x in choice.split(",")]
                to_import = [sources[i] for i in idxs if 0 <= i < len(sources)]
            except:
                print("Invalid selection.")
                return
        else:
            return
        for src, content in to_import:
            add_memory(f"[{src}] {content}")
        print(f"Imported {len(to_import)} entries.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()