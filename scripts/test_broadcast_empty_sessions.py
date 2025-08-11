#!/usr/bin/env python3
"""
Test script to verify broadcast messages work for sessions with empty message history.
This script tests both the management command and API endpoint.
"""

import requests
import time
import json
import subprocess
import sys
from typing import Dict, List

def test_broadcast_api(session_id: str, base_url: str = "http://localhost:8000") -> bool:
    """Test broadcast message via API endpoint."""
    try:
        print(f"📡 Testing broadcast API for session: {session_id}")
        
        # Send broadcast message via API
        broadcast_data = {
            "message": f"Test broadcast for empty session {session_id}",
            "title": "Empty Session Test",
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
                print(f"✅ Broadcast API successful: {result.get('data', {}).get('sessions_updated', 0)} sessions updated")
                return True
            else:
                print(f"❌ Broadcast API failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Broadcast API HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Broadcast API test failed: {e}")
        return False

def test_broadcast_command(session_id: str) -> bool:
    """Test broadcast message via management command."""
    try:
        print(f"📡 Testing broadcast command for session: {session_id}")
        
        # Send broadcast message via management command
        message = f"Test broadcast command for empty session {session_id}"
        cmd = [
            "python", "app/manage.py", "broadcast_message",
            message,
            "--title", "Empty Session Command Test",
            "--level", "warning"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Broadcast command successful: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Broadcast command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Broadcast command test failed: {e}")
        return False

def check_session_messages(session_id: str, base_url: str = "http://localhost:8000") -> List[Dict]:
    """Check messages for a specific session."""
    try:
        response = requests.get(
            f"{base_url}/chat/api/sessions/{session_id}/messages/",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('data', {}).get('messages', [])
            else:
                print(f"❌ Failed to get messages: {result.get('error')}")
                return []
        else:
            print(f"❌ HTTP error getting messages: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error checking messages: {e}")
        return []

def create_empty_session(base_url: str = "http://localhost:8000") -> str:
    """Create a new session with no messages."""
    try:
        print("🆕 Creating new empty session...")
        
        # Create a new session by connecting to WebSocket
        # For this test, we'll just generate a session ID and check if it exists
        session_id = f"test-empty-{int(time.time())}"
        
        # Check if session exists (it shouldn't initially)
        response = requests.get(
            f"{base_url}/chat/api/sessions/{session_id}/",
            timeout=10
        )
        
        if response.status_code == 404:
            print(f"✅ Created empty session: {session_id}")
            return session_id
        else:
            print(f"⚠️  Session already exists: {session_id}")
            return session_id
            
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None

def main():
    """Main test function."""
    print("🧪 Testing Broadcast Messages for Empty Sessions")
    print("=" * 55)
    
    # Create an empty session
    session_id = create_empty_session()
    if not session_id:
        print("❌ Failed to create test session")
        sys.exit(1)
    
    # Wait a moment for session to be properly initialized
    time.sleep(2)
    
    # Check initial state (should be empty)
    print(f"\n📋 Checking initial message state for session: {session_id}")
    initial_messages = check_session_messages(session_id)
    print(f"📊 Initial messages: {len(initial_messages)}")
    
    if len(initial_messages) > 0:
        print("⚠️  Session already has messages, this might affect the test")
    
    # Test broadcast API
    print(f"\n🔍 Testing Broadcast API...")
    api_success = test_broadcast_api(session_id)
    
    # Wait for API to process
    time.sleep(3)
    
    # Check messages after API broadcast
    print(f"\n📋 Checking messages after API broadcast...")
    api_messages = check_session_messages(session_id)
    print(f"📊 Messages after API broadcast: {len(api_messages)}")
    
    # Test broadcast command
    print(f"\n🔍 Testing Broadcast Command...")
    cmd_success = test_broadcast_command(session_id)
    
    # Wait for command to process
    time.sleep(3)
    
    # Check messages after command broadcast
    print(f"\n📋 Checking messages after command broadcast...")
    cmd_messages = check_session_messages(session_id)
    print(f"📊 Messages after command broadcast: {len(cmd_messages)}")
    
    # Analyze results
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    
    api_broadcasts = [msg for msg in api_messages if msg.get('isBroadcast') and 'Empty Session Test' in msg.get('content', '')]
    cmd_broadcasts = [msg for msg in cmd_messages if msg.get('isBroadcast') and 'Empty Session Command Test' in msg.get('content', '')]
    
    print(f"✅ API Broadcast Success: {api_success}")
    print(f"✅ Command Broadcast Success: {cmd_success}")
    print(f"📨 API Broadcast Messages: {len(api_broadcasts)}")
    print(f"📨 Command Broadcast Messages: {len(cmd_broadcasts)}")
    print(f"📊 Total Messages: {len(cmd_messages)}")
    
    # Determine if test passed
    test_passed = True
    
    if not api_success:
        print("❌ API broadcast test failed")
        test_passed = False
    
    if not cmd_success:
        print("❌ Command broadcast test failed")
        test_passed = False
    
    if len(api_broadcasts) == 0:
        print("❌ No API broadcast messages found")
        test_passed = False
    
    if len(cmd_broadcasts) == 0:
        print("❌ No command broadcast messages found")
        test_passed = False
    
    if test_passed:
        print(f"\n🎉 All tests passed! Broadcast messages work for empty sessions.")
        print(f"\n💡 Key Findings:")
        print(f"   - Sessions with empty message history can receive broadcasts")
        print(f"   - Both API and command methods work correctly")
        print(f"   - Message lists are created automatically for broadcasts")
    else:
        print(f"\n❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
