#!/usr/bin/env python3
"""
Redis session persistence validation and testing script.

This script performs comprehensive testing of Redis-based session persistence
functionality for the WebSocket service. It validates session storage, retrieval,
extension, and reconnection capabilities to ensure reliable session management
in production environments.

The persistence testing is critical for validating session continuity and
data integrity across connection interruptions and service restarts.
"""

import asyncio
import json
import time
import websockets
import requests
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat/"
TEST_SESSION_ID = "test-redis-session-123"

async def test_redis_connection():
    """
    Validate Redis connection and configuration status.
    
    This function tests the Redis connection through the application's
    health check endpoint to ensure the persistence layer is properly
    configured and accessible.
    
    Returns:
        bool: True if Redis connection is successful
    """
    print("Validating Redis connection and configuration...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/redis/status/")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("redis_connected"):
                print("Redis connection established successfully")
                print(f"  Connection URL: {data.get('redis_url')}")
                print(f"  Default TTL: {data.get('default_ttl')} seconds")
                return True
            else:
                print("Redis connection validation failed")
                print(f"  Error: {data.get('error')}")
                return False
        else:
            print(f"Failed to validate Redis status: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during Redis connection validation: {e}")
        return False

async def test_websocket_with_redis(session_id: str):
    """
    Test WebSocket connection with Redis persistence enabled.
    
    This function establishes a WebSocket connection with Redis persistence
    and validates that session data is properly stored and maintained.
    It sends test messages and verifies the persistence mechanism.
    
    Args:
        session_id: Unique session identifier for testing
        
    Returns:
        int: Message count from the session
    """
    print(f"\nTesting WebSocket connection with Redis persistence")
    print(f"Session ID: {session_id}")
    
    # Establish connection with Redis persistence enabled
    uri = f"{WS_URL}?session={session_id}&redis_persistence=true"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connection established with Redis persistence")
            
            # Send initial test message
            test_message = "Redis persistence test message"
            await websocket.send(test_message)
            print(f"Sent message: {test_message}")
            
            # Validate response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received response: {data}")
            
            # Send additional message for persistence validation
            test_message2 = "Second message for persistence validation"
            await websocket.send(test_message2)
            print(f"Sent message: {test_message2}")
            
            # Validate second response
            response2 = await websocket.recv()
            data2 = json.loads(response2)
            print(f"Received response: {data2}")
            
            # Close connection gracefully
            await websocket.close()
            print("WebSocket connection closed")
            
            return data.get("count", 0)
            
    except Exception as e:
        print(f"WebSocket persistence test failed: {e}")
        return 0

async def test_session_retrieval(session_id: str):
    """
    Validate session data retrieval from Redis storage.
    
    This function tests the session retrieval API to ensure that
    session data is properly stored in Redis and can be accessed
    through the application's session management interface.
    
    Args:
        session_id: Session identifier to retrieve
        
    Returns:
        bool: True if session retrieval is successful
    """
    print(f"\nValidating session data retrieval from Redis...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                session_info = data.get("data", {})
                print("Session data retrieved successfully from Redis")
                print(f"  Message count: {session_info.get('data', {}).get('count')}")
                print(f"  Created timestamp: {session_info.get('created_at')}")
                print(f"  TTL configuration: {session_info.get('ttl')} seconds")
                print(f"  Remaining TTL: {session_info.get('remaining_ttl')} seconds")
                return True
            else:
                print("Session retrieval failed")
                print(f"  Error: {data.get('error')}")
                return False
        else:
            print(f"Session retrieval request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during session retrieval: {e}")
        return False

async def test_session_extension(session_id: str):
    """
    Test session TTL extension functionality.
    
    This function validates that session TTL can be extended
    to maintain session continuity for long-running connections.
    
    Args:
        session_id: Session identifier to extend
        
    Returns:
        bool: True if session extension is successful
    """
    print(f"\nTesting session TTL extension functionality...")
    
    try:
        # Extend session TTL
        extension_data = {"ttl": 3600}  # Extend to 1 hour
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/extend/",
            json=extension_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("Session TTL extended successfully")
                print(f"  New TTL: {data.get('data', {}).get('ttl')} seconds")
                print(f"  Remaining TTL: {data.get('data', {}).get('remaining_ttl')} seconds")
                return True
            else:
                print("Session extension failed")
                print(f"  Error: {data.get('error')}")
                return False
        else:
            print(f"Session extension request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during session extension: {e}")
        return False

async def test_session_deletion(session_id: str):
    """
    Test session deletion and cleanup functionality.
    
    This function validates that sessions can be properly deleted
    from Redis storage and that cleanup operations work correctly.
    
    Args:
        session_id: Session identifier to delete
        
    Returns:
        bool: True if session deletion is successful
    """
    print(f"\nTesting session deletion and cleanup...")
    
    try:
        response = requests.delete(f"{BASE_URL}/api/sessions/{session_id}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("Session deleted successfully from Redis")
                return True
            else:
                print("Session deletion failed")
                print(f"  Error: {data.get('error')}")
                return False
        else:
            print(f"Session deletion request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during session deletion: {e}")
        return False

async def test_reconnection_with_redis(session_id: str):
    """
    Test WebSocket reconnection with session persistence.
    
    This function validates that session state is maintained
    across WebSocket connection interruptions and reconnections.
    
    Args:
        session_id: Session identifier for reconnection testing
        
    Returns:
        bool: True if reconnection with persistence is successful
    """
    print(f"\nTesting WebSocket reconnection with session persistence...")
    
    try:
        # First connection
        uri = f"{WS_URL}?session={session_id}&redis_persistence=true"
        async with websockets.connect(uri) as websocket1:
            print("Initial WebSocket connection established")
            
            # Send message on first connection
            await websocket1.send("Message from first connection")
            response1 = await websocket1.recv()
            data1 = json.loads(response1)
            print(f"First connection message count: {data1.get('count')}")
            
            # Close first connection
            await websocket1.close()
            print("First connection closed")
        
        # Brief delay to simulate connection interruption
        await asyncio.sleep(1)
        
        # Second connection with same session
        async with websockets.connect(uri) as websocket2:
            print("Reconnection established with same session")
            
            # Send message on second connection
            await websocket2.send("Message from reconnection")
            response2 = await websocket2.recv()
            data2 = json.loads(response2)
            print(f"Reconnection message count: {data2.get('count')}")
            
            # Validate session continuity
            if data2.get('count') > data1.get('count'):
                print("Session persistence validated: Message count incremented")
                await websocket2.close()
                return True
            else:
                print("Session persistence failed: Message count not maintained")
                await websocket2.close()
                return False
                
    except Exception as e:
        print(f"Reconnection test failed: {e}")
        return False

async def main():
    """
    Execute comprehensive Redis persistence testing suite.
    
    This function orchestrates the complete Redis persistence validation
    process, including connection testing, session management, and
    reconnection validation. It provides detailed reporting of test results.
    """
    print("Redis Session Persistence Testing Suite")
    print("=" * 50)
    
    # Test Redis connection
    redis_ok = await test_redis_connection()
    if not redis_ok:
        print("Redis connection test failed - aborting persistence tests")
        return 1
    
    # Test WebSocket with Redis persistence
    message_count = await test_websocket_with_redis(TEST_SESSION_ID)
    if message_count == 0:
        print("WebSocket persistence test failed")
        return 1
    
    # Test session retrieval
    retrieval_ok = await test_session_retrieval(TEST_SESSION_ID)
    if not retrieval_ok:
        print("Session retrieval test failed")
        return 1
    
    # Test session extension
    extension_ok = await test_session_extension(TEST_SESSION_ID)
    if not extension_ok:
        print("Session extension test failed")
        return 1
    
    # Test reconnection with persistence
    reconnection_ok = await test_reconnection_with_redis(TEST_SESSION_ID)
    if not reconnection_ok:
        print("Reconnection persistence test failed")
        return 1
    
    # Test session cleanup
    cleanup_ok = await test_session_deletion(TEST_SESSION_ID)
    if not cleanup_ok:
        print("Session cleanup test failed")
        return 1
    
    # Test summary
    print("\n" + "=" * 50)
    print("REDIS PERSISTENCE TEST RESULTS")
    print("=" * 50)
    print("All persistence tests completed successfully")
    print("Redis session persistence is functioning correctly")
    print("\nThe WebSocket service is ready for production deployment")
    print("with reliable session persistence capabilities.")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
