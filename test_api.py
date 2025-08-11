#!/usr/bin/env python3
"""
Simple test to verify API endpoints are accessible
"""

import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    # Test 1: Redis status endpoint
    print("Testing Redis status endpoint...")
    try:
        response = requests.get(f"{base_url}/chat/api/redis/status/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Session messages endpoint (with dummy session)
    print("Testing session messages endpoint...")
    try:
        response = requests.get(f"{base_url}/chat/api/sessions/test-session-123/messages/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
