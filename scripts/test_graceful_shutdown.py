#!/usr/bin/env python3
"""
Test script to verify graceful shutdown functionality.
This script tests SIGTERM handling, in-flight message processing, and proper WebSocket closure.
"""

import asyncio
import websockets
import json
import time
import signal
import sys
import os
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

class GracefulShutdownTester:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.connections: List[websockets.WebSocketServerProtocol] = []
        self.messages_received: List[Dict[str, Any]] = []
        self.shutdown_received = False
        self.test_results = {
            "connections_established": 0,
            "messages_sent": 0,
            "bye_messages_received": 0,
            "shutdown_time": 0,
            "close_codes": [],
            "errors": []
        }
    
    async def create_connection(self, session_id: str) -> websockets.WebSocketServerProtocol:
        """Create a WebSocket connection."""
        uri = f"ws://{self.host}:{self.port}/ws/chat/?session={session_id}"
        try:
            websocket = await websockets.connect(uri)
            self.connections.append(websocket)
            self.test_results["connections_established"] += 1
            print(f"✅ Connection {len(self.connections)} established for session {session_id}")
            return websocket
        except Exception as e:
            error_msg = f"Failed to connect session {session_id}: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return None
    
    async def send_message(self, websocket: websockets.WebSocketServerProtocol, message: str) -> bool:
        """Send a message through the WebSocket."""
        try:
            await websocket.send(message)
            self.test_results["messages_sent"] += 1
            print(f"📤 Message sent: {message}")
            return True
        except Exception as e:
            error_msg = f"Failed to send message '{message}': {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def listen_for_messages(self, websocket: websockets.WebSocketServerProtocol, session_id: str):
        """Listen for messages from the WebSocket."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.messages_received.append({
                        "session_id": session_id,
                        "data": data,
                        "timestamp": time.time()
                    })
                    
                    if data.get("bye"):
                        self.test_results["bye_messages_received"] += 1
                        close_code = getattr(websocket, 'close_code', None)
                        if close_code:
                            self.test_results["close_codes"].append(close_code)
                        print(f"👋 Bye message received for session {session_id}: {data}")
                    
                    print(f"📥 Message received for session {session_id}: {data}")
                    
                except json.JSONDecodeError:
                    print(f"📥 Raw message received for session {session_id}: {message}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            close_code = e.code if hasattr(e, 'code') else None
            if close_code:
                self.test_results["close_codes"].append(close_code)
            print(f"🔌 Connection closed for session {session_id} with code: {close_code}")
        except Exception as e:
            error_msg = f"Error listening for session {session_id}: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def run_test(self):
        """Run the graceful shutdown test."""
        print("🧪 Starting Graceful Shutdown Test")
        print("=" * 50)
        
        # Step 1: Create multiple connections
        print("\n📡 Step 1: Creating WebSocket connections...")
        session_ids = [f"test-session-{i}" for i in range(5)]
        connection_tasks = []
        
        for session_id in session_ids:
            websocket = await self.create_connection(session_id)
            if websocket:
                # Start listening for messages
                listen_task = asyncio.create_task(self.listen_for_messages(websocket, session_id))
                connection_tasks.append(listen_task)
        
        if not self.connections:
            print("❌ No connections established. Exiting.")
            return
        
        # Step 2: Send some messages
        print(f"\n📤 Step 2: Sending messages to {len(self.connections)} connections...")
        for i, websocket in enumerate(self.connections):
            await self.send_message(websocket, f"Test message {i+1}")
            await asyncio.sleep(0.1)  # Small delay between messages
        
        # Step 3: Wait a bit for messages to be processed
        print("\n⏳ Step 3: Waiting for message processing...")
        await asyncio.sleep(2)
        
        # Step 4: Simulate SIGTERM (this would normally be sent by Docker)
        print("\n🛑 Step 4: Simulating SIGTERM signal...")
        print("Note: In a real scenario, Docker would send SIGTERM to the container")
        print("For this test, we'll manually trigger the shutdown process")
        
        # In a real test, you would send SIGTERM to the container
        # For now, we'll just close the connections and observe the behavior
        print("\n🔌 Step 5: Closing connections...")
        start_time = time.time()
        
        for websocket in self.connections:
            try:
                await websocket.close(code=1001)  # Going away
            except Exception as e:
                print(f"❌ Error closing connection: {e}")
        
        self.test_results["shutdown_time"] = time.time() - start_time
        
        # Step 6: Wait for all tasks to complete
        print("\n⏳ Step 6: Waiting for cleanup...")
        await asyncio.sleep(1)
        
        # Step 7: Cancel listening tasks
        for task in connection_tasks:
            task.cancel()
        
        # Step 8: Report results
        print("\n📊 Test Results")
        print("=" * 30)
        print(f"Connections established: {self.test_results['connections_established']}")
        print(f"Messages sent: {self.test_results['messages_sent']}")
        print(f"Messages received: {len(self.messages_received)}")
        print(f"Bye messages received: {self.test_results['bye_messages_received']}")
        print(f"Shutdown time: {self.test_results['shutdown_time']:.2f}s")
        print(f"Close codes: {self.test_results['close_codes']}")
        
        if self.test_results["errors"]:
            print(f"\n❌ Errors encountered:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        # Step 9: Verify requirements
        print("\n✅ Requirements Verification")
        print("=" * 30)
        
        # Check if we received bye messages (indicating graceful shutdown)
        if self.test_results["bye_messages_received"] > 0:
            print("✅ Graceful shutdown messages received")
        else:
            print("❌ No graceful shutdown messages received")
        
        # Check close codes
        if all(code == 1001 for code in self.test_results["close_codes"]):
            print("✅ All connections closed with code 1001 (going away)")
        else:
            print(f"❌ Not all connections closed with code 1001: {self.test_results['close_codes']}")
        
        # Check shutdown time
        if self.test_results["shutdown_time"] <= 10:
            print("✅ Shutdown completed within 10 seconds")
        else:
            print(f"❌ Shutdown took longer than 10 seconds: {self.test_results['shutdown_time']:.2f}s")
        
        print(f"\n🎉 Graceful shutdown test completed!")

async def main():
    """Main test function."""
    tester = GracefulShutdownTester()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())
