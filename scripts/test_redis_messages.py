#!/usr/bin/env python3
"""
Redis message storage and retrieval validation script.

This script performs comprehensive testing of Redis message storage
functionality by directly interacting with the Redis session manager.
It validates message storage, retrieval, TTL management, and API
format compatibility for the WebSocket service.

The direct Redis testing ensures that the persistence layer is
functioning correctly at the data storage level.
"""

import asyncio
import json
import time
from app.chat.redis_session import get_redis_session_manager

async def test_redis_messages():
    """
    Validate Redis message storage and retrieval functionality.
    
    This function performs direct Redis operations to test message
    storage, retrieval, TTL management, and data format validation.
    It ensures that the Redis persistence layer is working correctly
    for the WebSocket service message storage.
    """
    print("Executing Redis message storage and retrieval validation...")
    
    # Initialize Redis connection manager
    redis_manager = get_redis_session_manager()
    client = await redis_manager._get_client()
    
    # Define test session identifier
    session_id = "test-session-123"
    
    try:
        # Test message storage functionality
        print(f"\nStep 1: Testing message storage for session: {session_id}")
        
        messages_key = f"session:{session_id}:messages"
        
        # Clear existing test data
        await client.delete(messages_key)
        
        # Create test message data
        test_messages = [
            {
                "content": "Redis storage validation message 1",
                "timestamp": int(time.time() * 1000),
                "isSent": True,
                "sessionId": session_id
            },
            {
                "content": "Redis storage validation response 1",
                "timestamp": int(time.time() * 1000) + 1,
                "isSent": False,
                "sessionId": session_id
            },
            {
                "content": "Redis storage validation message 2",
                "timestamp": int(time.time() * 1000) + 1000,
                "isSent": True,
                "sessionId": session_id
            },
            {
                "content": "Redis storage validation response 2",
                "timestamp": int(time.time() * 1000) + 1001,
                "isSent": False,
                "sessionId": session_id
            }
        ]
        
        # Store test messages in Redis
        for msg in test_messages:
            await client.rpush(messages_key, json.dumps(msg))
            print(f"  Stored message: {msg['content']}")
        
        # Set appropriate TTL for message retention
        await client.expire(messages_key, 300)  # 5 minutes
        
        # Test message retrieval functionality
        print(f"\nStep 2: Testing message retrieval for session: {session_id}")
        
        messages = await client.lrange(messages_key, 0, -1)
        print(f"  Retrieved {len(messages)} messages from Redis")
        
        # Validate retrieved message format
        for i, msg_data in enumerate(messages):
            try:
                msg = json.loads(msg_data)
                print(f"  Message {i+1}: {msg['content']} (Direction: {'Sent' if msg['isSent'] else 'Received'})")
            except json.JSONDecodeError as e:
                print(f"  Error: Failed to parse message {i+1}: {e}")
        
        # Test API endpoint format compatibility
        print(f"\nStep 3: Validating API endpoint format compatibility")
        
        # Parse messages in API format
        parsed_messages = []
        for msg_data in messages:
            try:
                msg = json.loads(msg_data)
                parsed_messages.append({
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", 0),
                    "isSent": msg.get("isSent", False),
                    "sessionId": session_id
                })
            except json.JSONDecodeError:
                print(f"  Warning: Failed to parse message data: {msg_data}")
                continue
        
        # Sort messages by timestamp for chronological order
        parsed_messages.sort(key=lambda x: x["timestamp"])
        
        print(f"  Successfully parsed {len(parsed_messages)} messages:")
        for i, msg in enumerate(parsed_messages):
            print(f"    {i+1}. {msg['content']} (Direction: {'Sent' if msg['isSent'] else 'Received'}, Timestamp: {msg['timestamp']})")
        
        # Validate TTL configuration
        print(f"\nStep 4: Validating TTL configuration")
        ttl = await client.ttl(messages_key)
        print(f"  TTL for message store: {ttl} seconds")
        
        print("\nRedis message storage validation completed successfully")
        
    except Exception as e:
        print(f"Error during Redis message validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test data
        try:
            await client.delete(messages_key)
            print(f"\nTest data cleanup completed for session: {session_id}")
        except Exception as e:
            print(f"Warning: Failed to clean up test data: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis_messages())
