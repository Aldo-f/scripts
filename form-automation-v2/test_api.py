#!/usr/bin/env python3
"""
Test FreLLM API connectivity with configured authentication
"""
import sys
import os
sys.path.insert(0, os.path.expanduser("~/scripts/form-automation-v2/src"))

import requests
import json
from pathlib import Path

API_BASE_URL = "http://192.168.0.5:3001/v1"
API_TOKEN = "freellmapi-893cc5a20ad598f62880e287ac46914c7f8cd0611f1890fe"

def test_health_endpoint():
    """Test the health endpoint."""
    print("Testing /healthz endpoint...")
    url = f"{API_BASE_URL}/healthz"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON: {json.dumps(data, indent=2)}")
                return data
            except:
                print("Response is not JSON")
                return {"status_code": 200, "raw": response.text}
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_streaming_endpoint():
    """Test streaming endpoint (what AI uses)."""
    print("\n\nTesting POST /stream/chat/completions...")
    url = f"{API_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Streaming connection established")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_improve_endpoint():
    """Test the improve endpoint for AI patches."""
    print("\n\nTesting POST /ai/improve...")
    url = f"{API_BASE_URL}/ai/improve"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "failure_patterns": [
            {"error": "selector_not_found", "count": 5},
            {"error": "timeout", "count": 3}
        ],
        "model": "auto"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:1000]}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("FreLLM API Connectivity Test")
    print("=" * 60)
    
    health = test_health_endpoint()
    streaming = test_streaming_endpoint()
    improve = test_improve_endpoint()
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Health endpoint: {'OK' if health else 'FAILED'}")
    print(f"  Streaming endpoint: {'OK' if streaming else 'FAILED'}")
    print(f"  Improve endpoint: {'OK' if improve else 'FAILED'}")
    print("=" * 60)