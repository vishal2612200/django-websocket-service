#!/usr/bin/env python3
"""
Test script to verify broadcast duplicate detection fix.
"""

import requests
import json
import time
import subprocess
import sys
from typing import Dict, List

def test_multiple_broadcasts(base_url: str = "http://localhost:8000") -> List[Dict]:
    """Test multiple broadcasts with the same content to verify duplicate detection."""
    results = []
    
    # Test 1: First broadcast
    print("📡 Test 1: First broadcast")
    broadcast_data = {
        "message": "Test duplicate detection fix",
        "title": "Duplicate Test",
        "level": "info"
    }
    
    response = requests.post(
        f"{base_url}/chat/api/broadcast/",
        json=broadcast_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            sessions_updated = result.get('data', {}).get('sessions_updated', 0)
            results.append({
                'test': 'First broadcast',
                'sessions_updated': sessions_updated,
                'success': True
            })
            print(f"   ✅ First broadcast: {sessions_updated} sessions updated")
        else:
            results.append({
                'test': 'First broadcast',
                'error': result.get('error'),
                'success': False
            })
            print(f"   ❌ First broadcast failed: {result.get('error')}")
    else:
        results.append({
            'test': 'First broadcast',
            'error': f'HTTP {response.status_code}',
            'success': False
        })
        print(f"   ❌ First broadcast HTTP error: {response.status_code}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Second broadcast with same content (should be allowed now)
    print("📡 Test 2: Second broadcast (same content)")
    response = requests.post(
        f"{base_url}/chat/api/broadcast/",
        json=broadcast_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            sessions_updated = result.get('data', {}).get('sessions_updated', 0)
            results.append({
                'test': 'Second broadcast',
                'sessions_updated': sessions_updated,
                'success': True
            })
            print(f"   ✅ Second broadcast: {sessions_updated} sessions updated")
        else:
            results.append({
                'test': 'Second broadcast',
                'error': result.get('error'),
                'success': False
            })
            print(f"   ❌ Second broadcast failed: {result.get('error')}")
    else:
        results.append({
            'test': 'Second broadcast',
            'error': f'HTTP {response.status_code}',
            'success': False
        })
        print(f"   ❌ Second broadcast HTTP error: {response.status_code}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 3: Third broadcast with different content
    print("📡 Test 3: Third broadcast (different content)")
    broadcast_data_2 = {
        "message": "Test different content broadcast",
        "title": "Different Test",
        "level": "warning"
    }
    
    response = requests.post(
        f"{base_url}/chat/api/broadcast/",
        json=broadcast_data_2,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            sessions_updated = result.get('data', {}).get('sessions_updated', 0)
            results.append({
                'test': 'Third broadcast',
                'sessions_updated': sessions_updated,
                'success': True
            })
            print(f"   ✅ Third broadcast: {sessions_updated} sessions updated")
        else:
            results.append({
                'test': 'Third broadcast',
                'error': result.get('error'),
                'success': False
            })
            print(f"   ❌ Third broadcast failed: {result.get('error')}")
    else:
        results.append({
            'test': 'Third broadcast',
            'error': f'HTTP {response.status_code}',
            'success': False
        })
        print(f"   ❌ Third broadcast HTTP error: {response.status_code}")
    
    return results

def test_management_command() -> Dict:
    """Test management command broadcast."""
    try:
        print("📡 Test 4: Management command broadcast")
        
        # Send broadcast via management command
        message = "Test management command broadcast"
        cmd = [
            "python", "app/manage.py", "broadcast_message",
            message,
            "--title", "Management Test",
            "--level", "success"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"   ✅ Management command: {result.stdout.strip()}")
            return {
                'test': 'Management command',
                'success': True,
                'output': result.stdout.strip()
            }
        else:
            print(f"   ❌ Management command failed: {result.stderr}")
            return {
                'test': 'Management command',
                'success': False,
                'error': result.stderr
            }
            
    except Exception as e:
        print(f"   ❌ Management command test failed: {e}")
        return {
            'test': 'Management command',
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function."""
    print("🧪 Testing Broadcast Duplicate Detection Fix")
    print("=" * 55)
    
    base_url = "http://localhost:8000"
    
    # Test API broadcasts
    print("\n🔍 Testing API Broadcasts:")
    api_results = test_multiple_broadcasts(base_url)
    
    # Test management command
    print("\n🔍 Testing Management Command:")
    cmd_result = test_management_command()
    
    # Analyze results
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    
    all_results = api_results + [cmd_result]
    
    for result in all_results:
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        test_name = result.get('test', 'Unknown')
        
        if result.get('success'):
            if 'sessions_updated' in result:
                print(f"{status} {test_name}: {result['sessions_updated']} sessions updated")
            else:
                print(f"{status} {test_name}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"{status} {test_name}: {error}")
    
    # Check if the fix worked
    print(f"\n🎯 Fix Verification:")
    
    # Check if second broadcast was allowed (should have sessions_updated > 0)
    second_broadcast = next((r for r in api_results if r.get('test') == 'Second broadcast'), None)
    
    if second_broadcast and second_broadcast.get('success'):
        sessions_updated = second_broadcast.get('sessions_updated', 0)
        if sessions_updated > 0:
            print(f"   ✅ SUCCESS: Second broadcast was allowed ({sessions_updated} sessions updated)")
            print(f"   💡 The duplicate detection fix is working correctly!")
        else:
            print(f"   ⚠️  WARNING: Second broadcast had 0 sessions updated")
            print(f"   💡 This might indicate no active sessions or other issues")
    else:
        print(f"   ❌ FAILED: Second broadcast test failed")
        print(f"   💡 The duplicate detection fix may not be working")
    
    # Check if all tests passed
    all_passed = all(r.get('success') for r in all_results)
    
    if all_passed:
        print(f"\n🎉 All tests passed! Broadcast duplicate detection fix is working.")
    else:
        print(f"\n❌ Some tests failed. Check the results above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
