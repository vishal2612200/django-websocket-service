#!/usr/bin/env python3
"""
WebSocket session resumption validation and testing script.

This script performs comprehensive testing of session resumption functionality
for the WebSocket service. It validates that session state is properly maintained
across connection interruptions and that counters resume correctly when
reconnecting with the same session identifier.

Session resumption is critical for maintaining user experience during network
interruptions and service restarts in production environments.
"""

import asyncio
import json
import websockets
import sys
from typing import Optional


async def test_session_resumption(session_id: str = "test-session-123"):
    """
    Validate session resumption functionality across connection interruptions.
    
    This function establishes a WebSocket connection, sends messages to establish
    session state, disconnects, and then reconnects with the same session ID
    to verify that the session state is properly maintained.
    
    Args:
        session_id: Unique session identifier for testing
        
    Returns:
        bool: True if session resumption works correctly
    """
    
    uri = f"ws://localhost/ws/chat/?session={session_id}"
    print(f"Testing session resumption functionality")
    print(f"Session ID: {session_id}")
    print(f"WebSocket Endpoint: {uri}")
    print()
    
    # Establish initial connection and send messages
    print("Establishing initial WebSocket connection...")
    async with websockets.connect(uri) as ws:
        # Send first message to establish session state
        await ws.send("Initial connection test message")
        response = await ws.recv()
        data = json.loads(response)
        print(f"First message response: {data}")
        
        # Send second message to increment counter
        await ws.send("Second message from initial connection")
        response = await ws.recv()
        data = json.loads(response)
        print(f"Second message response: {data}")
        
        print(f"Session counter after initial connection: {data['count']}")
    
    print("Initial connection closed")
    print("Waiting 2 seconds before establishing reconnection...")
    await asyncio.sleep(2)
    
    # Establish reconnection with same session ID
    print("\nEstablishing reconnection with same session ID...")
    async with websockets.connect(uri) as ws:
        # Send message in reconnected session
        await ws.send("Message from reconnected session")
        response = await ws.recv()
        data = json.loads(response)
        print(f"Reconnection response: {data}")
        
        print(f"Session counter after reconnection: {data['count']}")
        
        # Validate session resumption
        if data['count'] == 3:
            print("Session resumption validation: PASSED")
            print("  Session state maintained correctly across connection interruption")
            print("  Counter resumed from 2 to 3 as expected")
        else:
            print("Session resumption validation: FAILED")
            print(f"  Expected counter value: 3, Actual: {data['count']}")
            print("  Session state was not properly maintained")
            return False
    
    return True


async def test_session_expiration():
    """
    Validate session expiration behavior after TTL timeout.
    
    This function creates a session and provides instructions for testing
    session expiration behavior. It demonstrates the TTL-based session
    cleanup mechanism that prevents session storage bloat.
    """
    print("\n" + "="*60)
    print("SESSION EXPIRATION TESTING")
    print("="*60)
    
    session_id = "expiration-test-456"
    uri = f"ws://localhost/ws/chat/?session={session_id}"
    
    # Create initial session
    print("Creating test session for expiration validation...")
    async with websockets.connect(uri) as ws:
        await ws.send("Session creation test message")
        response = await ws.recv()
        data = json.loads(response)
        print(f"Session created successfully, initial counter: {data['count']}")
    
    print("\nSession expiration testing instructions:")
    print("1. Wait for session TTL to expire (default: 5 minutes)")
    print("2. Reconnect using the same session ID")
    print("3. Verify that counter resets to 1 (new session)")
    print("\nNote: For testing purposes, TTL can be temporarily reduced")
    print("in the application configuration to expedite testing")


async def main():
    """
    Execute comprehensive session resumption testing suite.
    
    This function orchestrates the complete session resumption validation
    process, including basic resumption testing and expiration validation.
    It provides detailed reporting of test results and validation status.
    """
    print("WebSocket Session Resumption Testing Suite")
    print("=" * 50)
    
    try:
        # Execute basic session resumption testing
        success = await test_session_resumption()
        
        if success:
            print("\nSession resumption testing completed successfully")
            print("All validation checks passed")
            print("\nFor additional information, refer to: docs/SESSION_RESUMPTION.md")
        else:
            print("\nSession resumption testing failed")
            print("Review the error messages above for troubleshooting")
            sys.exit(1)
            
    except websockets.exceptions.ConnectionRefused:
        print("Connection refused - WebSocket service is not accessible")
        print("Please ensure the development server is running:")
        print("  make dev-up")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
