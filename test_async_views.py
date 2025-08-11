#!/usr/bin/env python3
"""
Test script to verify async views are working correctly
"""

import requests
import json
import time

def test_async_views():
    base_url = "http://localhost:8000"
    
    print("Testing async views...")
    
    # Test 1: Redis status endpoint
    print("\n1. Testing Redis status endpoint...")
    try:
        response = requests.get(f"{base_url}/chat/api/redis/status/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f" Success: {json.dumps(data, indent=2)}")
        else:
            print(f" Error: {response.text}")
    except Exception as e:
        print(f" Exception: {e}")
    
    # Test 2: Session messages endpoint (with dummy session)
    print("\n2. Testing session messages endpoint...")
    try:
        session_id = f"test-session-{int(time.time())}"
        response = requests.get(f"{base_url}/chat/api/sessions/{session_id}/messages/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f" Success: {json.dumps(data, indent=2)}")
        else:
            print(f" Error: {response.text}")
    except Exception as e:
        print(f" Exception: {e}")
    
    # Test 3: Session info endpoint
    print("\n3. Testing session info endpoint...")
    try:
        session_id = f"test-session-{int(time.time())}"
        response = requests.get(f"{base_url}/chat/api/sessions/{session_id}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f" Success: {json.dumps(data, indent=2)}")
        elif response.status_code == 404:
            print(f" Expected 404 for non-existent session: {response.text}")
        else:
            print(f" Error: {response.text}")
    except Exception as e:
        print(f" Exception: {e}")

if __name__ == "__main__":
    test_async_views()
