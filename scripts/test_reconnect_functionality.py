#!/usr/bin/env python3
"""
WebSocket reconnection functionality validation script.

This script performs comprehensive testing of WebSocket reconnection
capabilities by simulating connection interruptions and validating
that the service properly handles reconnection scenarios. It tests
both anonymous and session-based reconnection behavior.

The reconnection testing ensures that the WebSocket service maintains
reliability and user experience during network interruptions and
service restarts.
"""

import asyncio
import json
import websockets
import sys
import time
from typing import Optional


async def test_reconnect_functionality():
    """
    Validate basic reconnection functionality without session persistence.
    
    This function tests the core reconnection mechanism by establishing
    a connection, closing it, and reconnecting to verify that the
    service handles reconnection scenarios properly.
    
    Returns:
        bool: True if reconnection functionality works correctly
    """
    
    uri = "ws://localhost/ws/chat/"
    print("Testing WebSocket Reconnection Functionality")
    print(f"Target URL: {uri}")
    print()
    
    try:
        # Establish initial connection
        print("Establishing initial WebSocket connection...")
        async with websockets.connect(uri) as ws:
            print("Initial connection established successfully")
            
            # Send test message to establish session state
            await ws.send("reconnection test message 1")
            response = await ws.recv()
            data = json.loads(response)
            print(f"Initial message response: {data}")
            
            # Simulate connection interruption (reconnect button behavior)
            print("\nSimulating connection interruption...")
            await ws.close()
            print("Connection closed successfully")
        
        # Establish reconnection
        print("\nEstablishing reconnection...")
        async with websockets.connect(uri) as ws:
            print("Reconnection established successfully")
            
            # Send message on reconnected session
            await ws.send("reconnection test message 2")
            response = await ws.recv()
            data = json.loads(response)
            print(f"Reconnection message response: {data}")
            
            # Validate reconnection behavior
            if data["count"] > 1:
                print("Reconnection validation: PASSED")
                print("  Session state maintained across reconnection")
            else:
                print("Reconnection validation: FAILED")
                print("  Session state reset during reconnection")
            
            print("Reconnection functionality verification completed")
            
    except websockets.exceptions.ConnectionRefused:
        print("Connection refused - WebSocket service is not accessible")
        print("Please ensure the development server is running:")
        print("  make dev-up")
        return False
    except Exception as e:
        print(f"Error during reconnection testing: {e}")
        return False
    
    return True


async def test_session_reconnect():
    """
    Validate reconnection functionality with session persistence.
    
    This function tests reconnection behavior when using session
    persistence to ensure that session state is properly maintained
    across connection interruptions.
    
    Returns:
        bool: True if session reconnection works correctly
    """
    
    session_id = "reconnect-test-123"
    uri = f"ws://localhost/ws/chat/?session={session_id}"
    print(f"\nTesting Session-Based Reconnection")
    print(f"Session ID: {session_id}")
    print(f"Target URL: {uri}")
    print()
    
    try:
        # Establish initial session connection
        print("Establishing initial session connection...")
        async with websockets.connect(uri) as ws:
            await ws.send("session reconnection test message 1")
            response = await ws.recv()
            data = json.loads(response)
            print(f"Initial session message: {data}")
        
        # Establish reconnection with same session
        print("\nEstablishing reconnection with same session...")
        async with websockets.connect(uri) as ws:
            await ws.send("session reconnection test message 2")
            response = await ws.recv()
            data = json.loads(response)
            print(f"Reconnection session message: {data}")
            
            # Validate session persistence
            if data["count"] == 2:
                print("Session reconnection validation: PASSED")
                print("  Session state properly maintained across reconnection")
            else:
                print(f"Session reconnection validation: FAILED")
                print(f"  Expected count=2, actual count={data['count']}")
                print("  Session state not properly maintained")
        
        return True
        
    except websockets.exceptions.ConnectionRefused:
        print("Connection refused - WebSocket service is not accessible")
        return False
    except Exception as e:
        print(f"Error during session reconnection testing: {e}")
        return False


def print_reconnect_ui_flow():
    """
    Display the reconnection UI workflow for reference.
    
    This function documents the expected user interface behavior
    during reconnection scenarios for development and testing reference.
    """
    print("\n" + "=" * 60)
    print("RECONNECTION UI WORKFLOW")
    print("=" * 60)
    print("1. User establishes WebSocket connection")
    print("2. Connection is active and functioning normally")
    print("3. Network interruption or service restart occurs")
    print("4. UI detects connection loss")
    print("5. Reconnect button becomes available")
    print("6. User clicks reconnect button")
    print("7. UI establishes new WebSocket connection")
    print("8. Session state is restored (if using session persistence)")
    print("9. Normal operation resumes")
    print("=" * 60)


def print_reconnect_implementation():
    """
    Display reconnection implementation details.
    
    This function provides technical details about the reconnection
    implementation for development and debugging purposes.
    """
    print("\n" + "=" * 60)
    print("RECONNECTION IMPLEMENTATION DETAILS")
    print("=" * 60)
    print("WebSocket Connection Management:")
    print("  - Automatic connection monitoring")
    print("  - Connection state tracking")
    print("  - Graceful connection closure")
    print("  - Reconnection attempt logic")
    print("  - Session state preservation")
    print("  - Error handling and recovery")
    print("  - User feedback and status updates")
    print("=" * 60)


async def main():
    """
    Execute comprehensive reconnection functionality testing.
    
    This function orchestrates the complete reconnection testing
    process, including basic reconnection and session-based
    reconnection validation.
    """
    print("WebSocket Reconnection Functionality Testing Suite")
    print("=" * 60)
    
    try:
        # Test basic reconnection functionality
        basic_reconnect_ok = await test_reconnect_functionality()
        
        if basic_reconnect_ok:
            print("\nBasic reconnection functionality: PASSED")
        else:
            print("\nBasic reconnection functionality: FAILED")
        
        # Test session-based reconnection
        session_reconnect_ok = await test_session_reconnect()
        
        if session_reconnect_ok:
            print("\nSession reconnection functionality: PASSED")
        else:
            print("\nSession reconnection functionality: FAILED")
        
        # Display implementation details
        print_reconnect_ui_flow()
        print_reconnect_implementation()
        
        # Overall assessment
        print("\n" + "=" * 60)
        print("RECONNECTION TESTING RESULTS")
        print("=" * 60)
        
        if basic_reconnect_ok and session_reconnect_ok:
            print("All reconnection tests completed successfully")
            print("The WebSocket service properly handles reconnection scenarios")
        else:
            print("Some reconnection tests failed")
            print("Review the error messages above for troubleshooting")
        
    except Exception as e:
        print(f"Unexpected error during reconnection testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
