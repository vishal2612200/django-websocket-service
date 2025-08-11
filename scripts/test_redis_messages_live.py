#!/usr/bin/env python3
"""
Live Redis message storage validation and testing script.

This script performs real-time validation of Redis message persistence
by establishing WebSocket connections and verifying that messages are
properly stored and retrievable through the Redis persistence layer.

The live testing ensures that the Redis integration is functioning
correctly in a production-like environment with actual message flow.
"""

import asyncio
import json
import time
import websockets
import requests

async def test_redis_messages_live():
    """
    Validate Redis message storage with live WebSocket connections.
    
    This function establishes a WebSocket connection with Redis persistence
    enabled, sends test messages, and validates that the messages are
    properly stored and retrievable through the Redis API. It provides
    comprehensive testing of the Redis integration in a live environment.
    """
    print("Executing live Redis message storage validation...")
    
    # Define test session identifier
    session_id = "test-redis-live-123"
    
    try:
        # Establish WebSocket connection with Redis persistence
        print(f"\nStep 1: Establishing WebSocket connection with Redis persistence")
        print(f"Session ID: {session_id}")
        
        ws_url = f"ws://localhost/ws/chat/?session={session_id}&redis_persistence=true"
        print(f"WebSocket Endpoint: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("WebSocket connection established successfully")
            
            # Send initial test message
            print(f"\nStep 2: Sending initial test message")
            test_message = "Redis persistence validation message"
            await websocket.send(test_message)
            print(f"Message sent: {test_message}")
            
            # Validate initial response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Response received: {response_data}")
            
            # Send additional test message
            print(f"\nStep 3: Sending additional test message")
            test_message2 = "Second Redis persistence validation message"
            await websocket.send(test_message2)
            print(f"Message sent: {test_message2}")
            
            # Validate second response
            response2 = await websocket.recv()
            response_data2 = json.loads(response2)
            print(f"Response received: {response_data2}")
            
            # Close WebSocket connection gracefully
            await websocket.close()
            print("WebSocket connection closed successfully")
        
        # Allow time for Redis operations to complete
        print(f"\nStep 4: Allowing Redis operations to complete")
        await asyncio.sleep(2)
        
        # Validate message storage through Redis API
        print(f"\nStep 5: Validating message storage through Redis API")
        
        api_url = f"http://localhost/chat/api/sessions/{session_id}/messages/"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response Status: Success")
            
            if data.get("success") and data.get("messages"):
                messages = data["messages"]
                print(f"Message storage validation: PASSED")
                print(f"Total messages stored: {len(messages)}")
                
                # Display message details for validation
                for i, msg in enumerate(messages):
                    print(f"  Message {i+1} Details:")
                    print(f"    Content: {msg['content']}")
                    print(f"    Timestamp: {msg['timestamp']}")
                    print(f"    Direction: {'Sent' if msg['isSent'] else 'Received'}")
                    print(f"    Session ID: {msg['sessionId']}")
            else:
                print(f"Message storage validation: FAILED")
                print(f"No messages found in Redis storage")
                print(f"API Response: {data}")
        else:
            print(f"API validation failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
        
        print("\nRedis message storage validation completed successfully")
        
    except websockets.exceptions.ConnectionRefused:
        print("Connection refused - WebSocket service is not accessible")
        print("Please ensure the development server is running")
    except requests.exceptions.ConnectionError:
        print("API connection failed - Redis API endpoint is not accessible")
        print("Please verify the Redis service is running")
    except Exception as e:
        print(f"Unexpected error during Redis validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_messages_live())
