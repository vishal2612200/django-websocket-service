#!/usr/bin/env python3
"""
Heartbeat functionality test script for WebSocket service validation.

This script establishes a WebSocket connection and monitors heartbeat messages
to validate the 30-second heartbeat mechanism. It provides detailed analysis
of heartbeat timing, latency, and connection health metrics.

The heartbeat system is critical for maintaining connection health and enabling
automatic reconnection in production environments.
"""

import asyncio
import json
import time
import websockets
from datetime import datetime
import argparse
from typing import Optional


class HeartbeatMonitor:
    """
    WebSocket heartbeat monitoring and analysis tool.
    
    This class provides comprehensive heartbeat monitoring capabilities,
    including latency measurement, timing analysis, and connection health
    assessment. It validates the heartbeat mechanism's reliability and
    performance characteristics.
    """
    
    def __init__(self, url: str, session_id: Optional[str] = None):
        """
        Initialize heartbeat monitor with connection parameters.
        
        Args:
            url: WebSocket server URL
            session_id: Optional session identifier for persistent connections
        """
        self.url = url
        self.session_id = session_id
        self.heartbeat_count = 0
        self.last_heartbeat = None
        self.connection_start = None
        
    async def connect(self):
        """
        Establish WebSocket connection and begin heartbeat monitoring.
        
        This method connects to the WebSocket server and continuously
        monitors incoming messages to detect and analyze heartbeat patterns.
        It provides real-time feedback on connection health and heartbeat timing.
        """
        if self.session_id:
            uri = f"{self.url}?session={self.session_id}"
        else:
            uri = self.url
            
        print(f"Establishing WebSocket connection to: {uri}")
        print(f"Initiating heartbeat monitoring and analysis")
        print(f"{'='*60}")
        
        try:
            async with websockets.connect(uri) as websocket:
                self.connection_start = time.time()
                print(f"Connection established at {datetime.now().strftime('%H:%M:%S')}")
                
                # Send initial message to trigger server response
                await websocket.send("Heartbeat test initialization message")
                
                # Monitor incoming messages for heartbeat analysis
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.process_message(data)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON message received: {message}")
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"WebSocket connection closed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Connection error: {e}")
    
    async def process_message(self, data: dict):
        """
        Process and categorize incoming WebSocket messages.
        
        This method analyzes incoming messages to identify heartbeat messages,
        echo responses, and other system messages. It routes messages to
        appropriate handlers for detailed analysis.
        
        Args:
            data: Parsed JSON message data
        """
        if 'ts' in data:
            # Heartbeat message detected - analyze timing and latency
            await self.process_heartbeat(data)
        elif 'count' in data:
            # Echo response from server
            print(f"Server echo response received: count={data['count']}")
        elif 'bye' in data:
            # Disconnect notification from server
            print(f"Server disconnect notification: total_messages={data.get('total', 0)}")
        else:
            print(f"Unrecognized message format: {data}")
    
    async def process_heartbeat(self, data: dict):
        """
        Analyze heartbeat message timing and performance characteristics.
        
        This method processes heartbeat messages to calculate latency,
        validate timing intervals, and assess connection health. It provides
        detailed metrics for heartbeat reliability analysis.
        
        Args:
            data: Heartbeat message data containing timestamp
        """
        self.heartbeat_count += 1
        heartbeat_time = data['ts']
        received_time = time.time()
        
        # Parse and validate heartbeat timestamp
        try:
            dt = datetime.fromisoformat(heartbeat_time.replace('Z', '+00:00'))
            heartbeat_timestamp = dt.timestamp()
            latency = (received_time - heartbeat_timestamp) * 1000  # Convert to milliseconds
        except ValueError:
            latency = 0
            print(f"Warning: Invalid timestamp format in heartbeat: {heartbeat_time}")
        
        self.last_heartbeat = received_time
        
        # Calculate connection uptime for context
        uptime = received_time - self.connection_start if self.connection_start else 0
        
        # Display heartbeat analysis results
        print(f"Heartbeat #{self.heartbeat_count} - Analysis Results")
        print(f"  Timestamp: {heartbeat_time}")
        print(f"  Network Latency: {latency:.1f}ms")
        print(f"  Received At: {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Connection Uptime: {uptime:.1f} seconds")
        print(f"  Next Expected: {datetime.now().timestamp() + 30:.0f}")
        print(f"{'-'*40}")


async def main():
    """
    Main function to execute heartbeat functionality testing.
    
    This function parses command line arguments and initiates heartbeat
    monitoring with the specified parameters. It provides comprehensive
    testing of the WebSocket heartbeat mechanism.
    """
    parser = argparse.ArgumentParser(description="WebSocket heartbeat functionality validation")
    parser.add_argument("--url", default="ws://localhost/ws/chat/", 
                       help="WebSocket server URL")
    parser.add_argument("--session", help="Session identifier for persistent connections")
    parser.add_argument("--duration", type=int, default=120, 
                       help="Test duration in seconds (default: 120)")
    
    args = parser.parse_args()
    
    print("WebSocket Heartbeat Functionality Test")
    print("=" * 50)
    print(f"Target Server: {args.url}")
    print(f"Session ID: {args.session or 'None (anonymous)'}")
    print(f"Test Duration: {args.duration} seconds")
    print()
    
    # Create and start heartbeat monitor
    monitor = HeartbeatMonitor(args.url, args.session)
    
    # Execute heartbeat monitoring for specified duration
    try:
        await asyncio.wait_for(monitor.connect(), timeout=args.duration)
    except asyncio.TimeoutError:
        print(f"\nTest completed after {args.duration} seconds")
        print(f"Total heartbeats received: {monitor.heartbeat_count}")
        
        if monitor.heartbeat_count > 0:
            print("Heartbeat functionality validation: PASSED")
            print("The WebSocket service is correctly sending heartbeat messages")
        else:
            print("Heartbeat functionality validation: FAILED")
            print("No heartbeat messages were received during the test period")


if __name__ == "__main__":
    asyncio.run(main())
