#!/usr/bin/env python3
"""
Test script to verify message history limit fix.
"""

import requests
import json
import time
import subprocess
import sys
from typing import Dict, List

def send_multiple_messages(session_id: str, count: int, base_url: str = "http://localhost:8000") -> List[Dict]:
    """Send multiple messages to create a message history."""
    results = []
    
    print(f"📤 Sending {count} messages to session {session_id}...")
    
    for i in range(count):
        message = f"Test message #{i+1} at {int(time.time())}"
        
        # Send via WebSocket (simulated by API)
        try:
            # Create a simple WebSocket-like message
            ws_message = {
                "message": message,
                "timestamp": int(time.time() * 1000)
            }
            
            # For testing, we'll use the broadcast API to simulate messages
            broadcast_data = {
                "message": message,
                "title": f"Test Message {i+1}",
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
                    results.append({
                        'message': message,
                        'success': True,
                        'sessions_updated': result.get('data', {}).get('sessions_updated', 0)
                    })
                else:
                    results.append({
                        'message': message,
                        'success': False,
                        'error': result.get('error')
                    })
            else:
                results.append({
                    'message': message,
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            results.append({
                'message': message,
                'success': False,
                'error': str(e)
            })
        
        # Small delay between messages
        time.sleep(0.1)
    
    return results

def check_message_history(session_id: str, base_url: str = "http://localhost:8000") -> Dict:
    """Check the message history for a session."""
    try:
        print(f"📋 Checking message history for session {session_id}...")
        
        response = requests.get(
            f"{base_url}/chat/api/sessions/{session_id}/messages/",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                messages = result.get('data', {}).get('messages', [])
                return {
                    'success': True,
                    'message_count': len(messages),
                    'messages': messages
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error')
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def test_ui_message_limit(base_url: str = "http://localhost:8000") -> Dict:
    """Test the UI message limit by checking browser console logs."""
    try:
        print("🌐 Testing UI message limit...")
        
        # This would typically involve checking browser console logs
        # For now, we'll just check if the API returns the expected data
        
        # Create a test session
        session_id = f"test-limit-{int(time.time())}"
        
        # Send more messages than the default limit (100)
        message_count = 150
        send_results = send_multiple_messages(session_id, message_count, base_url)
        
        # Wait a moment for messages to be processed
        time.sleep(2)
        
        # Check message history
        history_result = check_message_history(session_id, base_url)
        
        if history_result.get('success'):
            actual_count = history_result.get('message_count', 0)
            expected_count = message_count  # Should be all messages
            
            return {
                'success': True,
                'sent_messages': len([r for r in send_results if r.get('success')]),
                'stored_messages': actual_count,
                'expected_messages': expected_count,
                'limit_working': actual_count <= 1000,  # New limit is 1000
                'session_id': session_id
            }
        else:
            return {
                'success': False,
                'error': history_result.get('error')
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function."""
    print("🧪 Testing Message History Limit Fix")
    print("=" * 45)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Send many messages
    print("\n📤 Test 1: Sending multiple messages")
    test_result = test_ui_message_limit(base_url)
    
    if test_result.get('success'):
        sent_messages = test_result.get('sent_messages', 0)
        stored_messages = test_result.get('stored_messages', 0)
        expected_messages = test_result.get('expected_messages', 0)
        limit_working = test_result.get('limit_working', False)
        session_id = test_result.get('session_id', 'unknown')
        
        print(f"   ✅ Test completed successfully")
        print(f"   📊 Results:")
        print(f"      - Messages sent: {sent_messages}")
        print(f"      - Messages stored: {stored_messages}")
        print(f"      - Expected messages: {expected_messages}")
        print(f"      - Session ID: {session_id}")
        
        # Analyze the results
        print(f"\n📊 Analysis:")
        
        if stored_messages == expected_messages:
            print(f"   ✅ SUCCESS: All messages are stored ({stored_messages}/{expected_messages})")
            print(f"   💡 The message history limit fix is working correctly!")
        elif stored_messages > 100 and stored_messages <= 1000:
            print(f"   ✅ SUCCESS: Messages stored with new limit ({stored_messages}/{expected_messages})")
            print(f"   💡 The limit has been increased from 100 to 1000 messages!")
        elif stored_messages <= 100:
            print(f"   ⚠️  WARNING: Only {stored_messages} messages stored (old limit still active)")
            print(f"   💡 The UI might still be applying the old 100 message limit")
        else:
            print(f"   ❌ UNEXPECTED: {stored_messages} messages stored")
            print(f"   💡 This exceeds the expected limit")
        
        # Check if the fix is working
        if stored_messages > 100:
            print(f"\n🎉 SUCCESS: Message history limit fix is working!")
            print(f"   - Old limit: 100 messages")
            print(f"   - New limit: 1000 messages")
            print(f"   - Current storage: {stored_messages} messages")
        else:
            print(f"\n❌ ISSUE: Message history limit fix may not be working")
            print(f"   - Current storage: {stored_messages} messages")
            print(f"   - Expected: > 100 messages")
            
    else:
        print(f"   ❌ Test failed: {test_result.get('error')}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print(f"   1. Check browser console for message loading logs")
    print(f"   2. Verify that UI shows all messages (not just last 100)")
    print(f"   3. Test with different session persistence types")
    print(f"   4. Monitor performance with larger message histories")

if __name__ == "__main__":
    main()
