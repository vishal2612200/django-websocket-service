#!/usr/bin/env python3
"""
Debug script to analyze broadcast coverage issues.
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
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        return int(float(parts[1]))
        return 0
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")
        return 0

def get_redis_session_details() -> Dict[str, any]:
    """Get detailed Redis session information."""
    try:
        cmd = ["python", "app/manage.py", "shell", "-c", """
import os
import redis
import json
from app.chat.redis_session import get_redis_session_manager
import asyncio

async def analyze_redis_sessions():
    redis_manager = get_redis_session_manager()
    
    # Get session client
    session_client = await redis_manager._get_client()
    message_client = await redis_manager._get_message_client()
    
    # Get all session keys
    all_session_keys = await session_client.keys("session:*")
    message_list_keys = await message_client.keys("session:*:messages")
    
    # Analyze session data keys
    session_data_keys = [k for k in all_session_keys if not k.decode('utf-8').endswith(':messages')]
    session_ids = set()
    session_details = {}
    
    for key in session_data_keys:
        try:
            session_id = key.decode('utf-8').split(':')[1]
            session_ids.add(session_id)
            
            # Get session data
            data = await session_client.get(key)
            if data:
                session_data = json.loads(data)
                session_details[session_id] = {
                    'data': session_data,
                    'ttl': await session_client.ttl(key),
                    'has_message_list': False
                }
        except Exception as e:
            print(f"Error processing session key {key}: {e}")
    
    # Analyze message list keys
    message_session_ids = set()
    for key in message_list_keys:
        try:
            session_id = key.decode('utf-8').split(':')[1]
            message_session_ids.add(session_id)
            
            # Get message count
            message_count = await message_client.llen(key)
            ttl = await message_client.ttl(key)
            
            if session_id in session_details:
                session_details[session_id]['has_message_list'] = True
                session_details[session_id]['message_count'] = message_count
                session_details[session_id]['message_ttl'] = ttl
            else:
                session_details[session_id] = {
                    'data': None,
                    'ttl': None,
                    'has_message_list': True,
                    'message_count': message_count,
                    'message_ttl': ttl
                }
        except Exception as e:
            print(f"Error processing message key {key}: {e}")
    
    # Get active sessions from consumers
    from app.chat.consumers import get_active_sessions
    active_sessions = get_active_sessions()
    
    print(f"Total session data keys: {len(session_data_keys)}")
    print(f"Total message list keys: {len(message_list_keys)}")
    print(f"Unique session IDs (data): {len(session_ids)}")
    print(f"Unique session IDs (messages): {len(message_session_ids)}")
    print(f"Combined unique sessions: {len(session_ids.union(message_session_ids))}")
    print(f"Active WebSocket sessions: {len(active_sessions)}")
    print(f"Active session IDs: {list(active_sessions)}")
    
    print("\\nSession Details:")
    for session_id, details in session_details.items():
        print(f"  Session {session_id}:")
        print(f"    Has session data: {details['data'] is not None}")
        print(f"    Has message list: {details['has_message_list']}")
        print(f"    Message count: {details.get('message_count', 0)}")
        print(f"    Session TTL: {details['ttl']}")
        print(f"    Message TTL: {details.get('message_ttl')}")
        print(f"    Is active: {session_id in active_sessions}")
        if details['data']:
            print(f"    Last activity: {details['data'].get('last_activity', 'N/A')}")
            print(f"    Count: {details['data'].get('count', 'N/A')}")
        print()
    
    await session_client.close()
    await message_client.close()
    
    return {
        'session_details': session_details,
        'active_sessions': list(active_sessions),
        'total_sessions': len(session_ids.union(message_session_ids))
    }

result = asyncio.run(analyze_redis_sessions())
print(f"RESULT: {json.dumps(result)}")
        """]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Extract the JSON result from the output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('RESULT: '):
                    json_str = line.replace('RESULT: ', '')
                    return json.loads(json_str)
            return {}
        else:
            print(f"❌ Error running Redis analysis: {result.stderr}")
            return {}
            
    except Exception as e:
        print(f"❌ Error analyzing Redis: {e}")
        return {}

def test_broadcast_with_tracking(base_url: str = "http://localhost:8000") -> Dict[str, any]:
    """Test broadcast and track exactly what happens."""
    try:
        print("📡 Testing broadcast with detailed tracking...")
        
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
    print("🔍 Debugging Broadcast Coverage Issue")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. Get active WebSocket connections
    print("\n📊 Active WebSocket Connections:")
    active_connections = get_active_sessions_from_metrics(base_url)
    print(f"   Active connections: {active_connections}")
    
    # 2. Get detailed Redis session analysis
    print("\n📊 Redis Session Analysis:")
    redis_details = get_redis_session_details()
    
    if redis_details:
        total_sessions = redis_details.get('total_sessions', 0)
        active_sessions = redis_details.get('active_sessions', [])
        session_details = redis_details.get('session_details', {})
        
        print(f"   Total sessions in Redis: {total_sessions}")
        print(f"   Active WebSocket sessions: {len(active_sessions)}")
        print(f"   Active session IDs: {active_sessions}")
        
        # Analyze session details
        sessions_with_data = 0
        sessions_with_messages = 0
        sessions_with_ttl = 0
        
        for session_id, details in session_details.items():
            if details.get('data'):
                sessions_with_data += 1
            if details.get('has_message_list'):
                sessions_with_messages += 1
            if details.get('ttl', -1) > 0:
                sessions_with_ttl += 1
        
        print(f"   Sessions with data: {sessions_with_data}")
        print(f"   Sessions with message lists: {sessions_with_messages}")
        print(f"   Sessions with valid TTL: {sessions_with_ttl}")
    
    # 3. Test broadcast coverage
    print("\n📡 Broadcast Coverage Test:")
    broadcast_result = test_broadcast_with_tracking(base_url)
    
    if broadcast_result.get('success'):
        sessions_updated = broadcast_result.get('sessions_updated', 0)
        print(f"   Broadcast successful: {sessions_updated} sessions updated")
        
        # Analyze the coverage issue
        print(f"\n📊 Coverage Analysis:")
        print(f"   Active WebSocket connections: {active_connections}")
        print(f"   Total sessions in Redis: {total_sessions}")
        print(f"   Sessions targeted by broadcast: {sessions_updated}")
        
        if sessions_updated < total_sessions:
            print(f"   ⚠️  ISSUE: Only {sessions_updated}/{total_sessions} sessions were updated")
            
            # Identify potential causes
            print(f"\n🔍 Potential Causes:")
            
            if active_connections == 0:
                print(f"   - No active WebSocket connections (broadcast only stores in Redis)")
            elif sessions_updated < active_connections:
                print(f"   - Some active sessions weren't included in broadcast")
            elif sessions_updated < total_sessions:
                print(f"   - Inactive sessions (no WebSocket connection) weren't stored")
            
            # Check for TTL issues
            expired_sessions = 0
            for session_id, details in session_details.items():
                if details.get('ttl', -1) <= 0:
                    expired_sessions += 1
            
            if expired_sessions > 0:
                print(f"   - {expired_sessions} sessions may have expired TTL")
            
            # Check for message list issues
            sessions_without_messages = 0
            for session_id, details in session_details.items():
                if not details.get('has_message_list'):
                    sessions_without_messages += 1
            
            if sessions_without_messages > 0:
                print(f"   - {sessions_without_messages} sessions don't have message lists")
        else:
            print(f"   ✅ Perfect coverage: {sessions_updated} sessions updated")
    else:
        print(f"   ❌ Broadcast failed: {broadcast_result.get('error')}")
    
    # 4. Recommendations
    print(f"\n💡 Recommendations:")
    print(f"   1. Check if sessions have valid TTL (not expired)")
    print(f"   2. Verify that sessions have message lists created")
    print(f"   3. Ensure WebSocket connections are active for real-time delivery")
    print(f"   4. Check for duplicate broadcast detection (messages already exist)")
    print(f"   5. Monitor Redis memory and connection limits")

if __name__ == "__main__":
    main()
