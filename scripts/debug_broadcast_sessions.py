#!/usr/bin/env python3
"""
Debug script to understand active vs all sessions for broadcast targeting.
"""

import requests
import json
import time
import subprocess
import sys
from typing import Dict, List, Set

def get_active_sessions_from_metrics(base_url: str = "http://localhost:8000") -> int:
    """Get active sessions count from metrics endpoint."""
    try:
        response = requests.get(f"{base_url}/metrics", timeout=10)
        if response.status_code == 200:
            for line in response.text.split('\n'):
                if line.startswith('app_active_connections'):
                    # Extract the value
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        return int(float(parts[1]))
        return 0
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")
        return 0

def get_redis_sessions_count() -> Dict[str, int]:
    """Get session counts from Redis."""
    try:
        # Use Django management command to check Redis status
        cmd = ["python", "app/manage.py", "shell", "-c", """
import os
import redis
from app.chat.redis_session import get_redis_session_manager
import asyncio

async def check_redis():
    redis_manager = get_redis_session_manager()
    
    # Get session client
    session_client = await redis_manager._get_client()
    message_client = await redis_manager._get_message_client()
    
    # Count different types of keys
    all_session_keys = await session_client.keys("session:*")
    session_data_keys = [k for k in all_session_keys if not k.decode('utf-8').endswith(':messages')]
    message_list_keys = await message_client.keys("session:*:messages")
    
    # Extract unique session IDs
    session_ids = set()
    for key in session_data_keys:
        try:
            session_id = key.decode('utf-8').split(':')[1]
            session_ids.add(session_id)
        except:
            pass
    
    message_session_ids = set()
    for key in message_list_keys:
        try:
            session_id = key.decode('utf-8').split(':')[1]
            message_session_ids.add(session_id)
        except:
            pass
    
    print(f"Total session data keys: {len(session_data_keys)}")
    print(f"Total message list keys: {len(message_list_keys)}")
    print(f"Unique session IDs (data): {len(session_ids)}")
    print(f"Unique session IDs (messages): {len(message_session_ids)}")
    print(f"Combined unique sessions: {len(session_ids.union(message_session_ids))}")
    
    await session_client.close()
    await message_client.close()

asyncio.run(check_redis())
        """]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            counts = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    counts[key.strip()] = int(value.strip())
            return counts
        else:
            print(f"❌ Error running Redis check: {result.stderr}")
            return {}
            
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
        return {}

def test_broadcast_coverage(base_url: str = "http://localhost:8000") -> Dict[str, any]:
    """Test broadcast and see how many sessions it targets."""
    try:
        print("📡 Testing broadcast coverage...")
        
        # Send a test broadcast
        broadcast_data = {
            "message": f"Debug broadcast test at {int(time.time())}",
            "title": "Debug Test",
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
                return {
                    'success': True,
                    'sessions_updated': result.get('data', {}).get('sessions_updated', 0),
                    'message': result.get('data', {}).get('message', ''),
                    'timestamp': result.get('data', {}).get('timestamp', 0)
                }
            else:
                return {'success': False, 'error': result.get('error')}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """Main debug function."""
    print("🔍 Debugging Broadcast Session Coverage")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. Check active WebSocket connections
    print("\n📊 Active WebSocket Connections:")
    active_connections = get_active_sessions_from_metrics(base_url)
    print(f"   Active connections: {active_connections}")
    
    # 2. Check Redis session counts
    print("\n📊 Redis Session Counts:")
    redis_counts = get_redis_sessions_count()
    for key, value in redis_counts.items():
        print(f"   {key}: {value}")
    
    # 3. Test broadcast coverage
    print("\n📡 Broadcast Coverage Test:")
    broadcast_result = test_broadcast_coverage(base_url)
    
    if broadcast_result.get('success'):
        sessions_updated = broadcast_result.get('sessions_updated', 0)
        print(f"   Broadcast successful: {sessions_updated} sessions updated")
        
        # Analyze the coverage
        print(f"\n📊 Coverage Analysis:")
        print(f"   Active WebSocket connections: {active_connections}")
        print(f"   Sessions targeted by broadcast: {sessions_updated}")
        
        if active_connections > 0 and sessions_updated > active_connections:
            print(f"   ⚠️  Broadcast targeted {sessions_updated} sessions but only {active_connections} are actively connected")
            print(f"   💡 This means some sessions exist in Redis but have no live WebSocket connection")
        elif active_connections > 0 and sessions_updated < active_connections:
            print(f"   ⚠️  Only {sessions_updated} sessions were targeted but {active_connections} are actively connected")
            print(f"   💡 This suggests some active sessions weren't included in the broadcast")
        elif active_connections == 0:
            print(f"   ℹ️  No active WebSocket connections - broadcasts will only be stored in Redis")
        else:
            print(f"   ✅ Perfect match: {sessions_updated} sessions targeted, {active_connections} actively connected")
    else:
        print(f"   ❌ Broadcast failed: {broadcast_result.get('error')}")
    
    # 4. Recommendations
    print(f"\n💡 Recommendations:")
    print(f"   1. Ensure you have multiple browser tabs/windows open with WebSocket connections")
    print(f"   2. Check that sessions are using Redis persistence (redis_persistence=true)")
    print(f"   3. Verify that sessions are being created and maintained in Redis")
    print(f"   4. Monitor the WebSocket connection status in browser dev tools")

if __name__ == "__main__":
    main()
