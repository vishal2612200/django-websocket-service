#!/usr/bin/env python3
"""
Simple heartbeat functionality validation script.

This script performs basic validation of the WebSocket heartbeat mechanism
by establishing a connection and waiting for the expected heartbeat message.
It validates that the 30-second heartbeat interval is functioning correctly
and that individual session heartbeats are being sent properly.

The simple heartbeat test is essential for validating the core heartbeat
functionality before more complex testing scenarios.
"""

import asyncio
import json
import time
import websockets
import uuid


async def test_heartbeat():
    """
    Validate individual heartbeat functionality.
    
    This function establishes a WebSocket connection with a unique session ID
    and waits for the expected heartbeat message to validate that the
    heartbeat mechanism is functioning correctly.
    
    Returns:
        bool: True if heartbeat is received within expected timeframe
    """
    session_id = str(uuid.uuid4())
    uri = f"ws://localhost/ws/chat/?session={session_id}"
    
    print(f"Establishing WebSocket connection with session: {session_id[:8]}...")
    
    try:
        async with websockets.connect(uri) as ws:
            print("WebSocket connection established successfully")
            
            # Send initial test message to establish session
            await ws.send("heartbeat validation message")
            print("Test message sent successfully")
            
            # Validate initial response
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"Initial response received: {data}")
            
            # Wait for heartbeat message (expected within 30 seconds)
            print("Waiting for heartbeat message...")
            start_time = time.time()
            
            while time.time() - start_time < 35:  # Wait up to 35 seconds
                try:
                    heartbeat = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    heartbeat_data = json.loads(heartbeat)
                    
                    if 'ts' in heartbeat_data:
                        print(f"Heartbeat message received: {heartbeat_data}")
                        print(f"Time since connection: {time.time() - start_time:.1f} seconds")
                        return True
                    else:
                        print(f"Non-heartbeat message received: {heartbeat_data}")
                        
                except asyncio.TimeoutError:
                    print("Continuing to wait for heartbeat...")
                    continue
            
            print("Heartbeat message not received within 35 seconds")
            return False
            
    except websockets.exceptions.ConnectionRefused:
        print("Connection refused - WebSocket service is not accessible")
        return False
    except Exception as e:
        print(f"Error during heartbeat validation: {e}")
        return False


async def main():
    """
    Execute simple heartbeat functionality validation.
    
    This function orchestrates the basic heartbeat testing process
    and provides clear reporting of the validation results.
    """
    print("Simple Heartbeat Functionality Validation")
    print("=" * 50)
    
    success = await test_heartbeat()
    
    if success:
        print("\nHeartbeat validation: PASSED")
        print("  - WebSocket connection established successfully")
        print("  - Heartbeat message received within expected timeframe")
        print("  - Individual session heartbeat mechanism is functioning")
    else:
        print("\nHeartbeat validation: FAILED")
        print("  - Review the error messages above for troubleshooting")
        print("  - Verify that the WebSocket service is running")
        print("  - Check heartbeat configuration in the application")
    
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
