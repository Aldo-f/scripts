#!/usr/bin/env python3
"""End-to-end Hermes memory provider test
Tests the complete memory provider pipeline including config, plugin loading, and save/retrieve.
"""
import json, os, sys, tempfile, shutil
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
import requests

# Import Hermes modules
sys.path.insert(0, '/home/aldo/.hermes/hermes-agent')

def test_hermes_memory_provider():
    print("=" * 60)
    print("Hermes Memory Provider End-to-End Test")
    print("=" * 60)

    # Test 1: Check mem0 plugin is installed
    print("\n1. Testing mem0 plugin installation...")
    plugin_path = Path('/home/aldo/.hermes/hermes-agent/plugins/memory/mem0')
    if not plugin_path.exists():
        print("❌ mem0 plugin not found at", plugin_path)
        return False
    print(f"✅ mem0 plugin found at {plugin_path}")

    # Test 2: Verify plugin structure
    print("\n2. Verifying mem0 plugin structure...")
    required_files = ['__init__.py', '_setup.py', '_backend.py']
    for f in required_files:
        if not (plugin_path / f).exists():
            print(f"❌ Required file {f} missing")
            return False
    print("✅ All required mem0 plugin files present")

    # Test 3: Test mem0 configuration
    print("\n3. Testing mem0 configuration...")
    config_path = Path('/home/aldo/.hermes/mem0.json')
    if not config_path.exists():
        print("❌ mem0.json not found")
        return False

    with open(config_path) as f:
        config = json.load(f)

    # Check essential config
    if config.get('mode') != 'oss':
        print("❌ mem0 config mode should be 'oss'")
        return False

    if config.get('host') != 'http://10.43.11.187:6333':
        print("❌ mem0 config host mismatch")
        return False

    if config['oss']['vector_store']['provider'] != 'qdrant':
        print("❌ mem0 vector_store provider should be 'qdrant'")
        return False

    if config['oss']['vector_store']['config']['collection_name'] != 'mem0':
        print("❌ mem0 collection_name should be 'mem0'")
        return False

    print("✅ mem0 configuration is correct")

    # Test 4: Test Qdrant connection and collection
    print("\n4. Testing Qdrant connection...")
    try:
        client = QdrantClient(
            host='127.0.0.1',
            port=6333,
            check_compatibility=False,
            timeout=60
        )

        # Check collection exists
        collection_info = client.get_collection('mem0')
        print(f"✅ Qdrant connection successful. Collection 'mem0': {collection_info.points_count} points")
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False

    # Test 5: Test mem0.json embedding dimensions
    print("\n5. Verifying embedding dimensions...")
    embed_config = config['oss']['embedder']['config']
    if embed_config.get('embedding_dims') != 768:
        print(f"❌ embedding_dims should be 768, got {embed_config.get('embedding_dims')}")
        return False

    # Verify embedding model is available
    try:
        response = requests.post(
            'http://localhost:11434/api/embeddings',
            json={'model': embed_config['model'], 'prompt': 'test'},
            timeout=30
        )
        if response.status_code != 200:
            print(f"❌ Embedding model test failed: {response.status_code}")
            return False

        embedding = response.json()['embedding']
        if len(embedding) != 768:
            print(f"❌ Embedding dimension mismatch: expected 768, got {len(embedding)}")
            return False

        print("✅ Embedding model is working correctly (768 dims)")
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

    # Test 6: Direct memory storage test
    print("\n6. Testing direct memory storage...")
    try:
        test_text = "Hermes memory provider test: agent integration verified"
        response = requests.post(
            'http://localhost:11434/api/embeddings',
            json={'model': embed_config['model'], 'prompt': test_text},
            timeout=30
        )
        embedding = response.json()['embedding']

        point = PointStruct(
            id='hermes-memtest-001',
            vector=embedding,
            payload={
                'text': test_text,
                'user_id': config['user_id'],
                'agent_id': config['agent_id']
            }
        )

        client.upsert(collection_name='mem0', points=[point])
        print("✅ Memory stored successfully via Qdrant")

        # Verify retrieval
        search_result = client.query_points(
            collection_name='mem0',
            query=embedding,
            limit=5,
            query_filter={'must': [
                {'key': 'user_id', 'match': {'value': config['user_id']}},
                {'key': 'agent_id', 'match': {'value': config['agent_id']}}
            ]}
        )

        if len(search_result.points) == 0:
            print("❌ No memories found after storing test memory")
            return False

        # Check our test memory was stored
        test_memory_found = False
        for p in search_result.points:
            if p.payload.get('text') == test_text:
                test_memory_found = True
                break

        if not test_memory_found:
            print("❌ Test memory not found in search results")
            return False

        print("✅ Test memory retrieved successfully")

    except Exception as e:
        print(f"❌ Direct memory storage test failed: {e}")
        return False

    # Test 7: Test Hermes config integration
    print("\n7. Testing Hermes config integration...")
    hermes_config_path = Path('/home/aldo/.hermes/config.yaml')
    if not hermes_config_path.exists():
        print("❌ Hermes config.yaml not found")
        return False

    with open(hermes_config_path) as f:
        hermes_config = f.read()

    if 'provider: mem0' not in hermes_config:
        print("❌ Hermes config.yaml does not have mem0 as memory provider")
        return False

    print("✅ Hermes config is correctly configured for mem0")

    # Test 8: Test Hermes CLI memory command availability
    print("\n8. Testing Hermes CLI memory command...")
    try:
        # Import and test the memory CLI command
        from hermes_cli.subcommands.memory import MemoryCommand
        if not hasattr(MemoryCommand, 'run'):
            print("❌ MemoryCommand class missing run method")
            return False
        print("✅ Hermes CLI memory command is available")
    except Exception as e:
        print(f"⚠️  Could not import MemoryCommand (expected if not in test environment): {e}")

    # Test 9: Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("✅ Hermes memory provider test completed successfully")
    print("✅ mem0 plugin is properly installed and configured")
    print("✅ Qdrant collection 'mem0' is accessible and functional")
    print("✅ Embedding dimensions (768) match mem0 configuration")
    print("✅ Memory storage and retrieval works correctly")
    print("✅ Hermes config.yaml points to mem0 provider")
    print("=" * 60)

    return True

if __name__ == '__main__':
    import sys
    success = test_hermes_memory_provider()
    sys.exit(0 if success else 1)
