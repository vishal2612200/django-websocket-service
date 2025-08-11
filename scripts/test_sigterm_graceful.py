#!/usr/bin/env python3
"""
Simple test script to verify SIGTERM graceful shutdown functionality.
"""

import asyncio
import websockets
import json
import time
import sys

async def test_graceful_shutdown():
    """Test graceful shutdown by connecting and observing behavior."""
    
    print("🧪 Testing Graceful Shutdown")
    print("=" * 40)
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws/chat/?session=graceful-test"
    
    try:
        print("📡 Connecting to WebSocket...")
        websocket = await websockets.connect(uri)
        print("✅ Connected successfully")
        
        # Send a test message
        print("📤 Sending test message...")
        await websocket.send("Hello from graceful shutdown test")
        
        # Listen for messages
        print("👂 Listening for messages...")
        message_count = 0
        
        async for message in websocket:
            try:
                data = json.loads(message)
                message_count += 1
                print(f"📥 Message {message_count}: {data}")
                
                # Check for bye message
                if data.get("bye"):
                    print("👋 Received bye message - graceful shutdown detected!")
                    break
                    
            except json.JSONDecodeError:
                print(f"📥 Raw message: {message}")
        
        print(f"📊 Received {message_count} messages")
        
    except websockets.exceptions.ConnectionClosed as e:
        print(f"🔌 Connection closed with code: {e.code}")
        if e.code == 1001:
            print("✅ Connection closed with code 1001 (going away) - graceful shutdown confirmed!")
        else:
            print(f"⚠️ Connection closed with unexpected code: {e.code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Graceful shutdown test completed!")

if __name__ == "__main__":
    asyncio.run(test_graceful_shutdown())
