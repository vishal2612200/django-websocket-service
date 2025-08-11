#!/usr/bin/env python3
"""
Heartbeat timing verification and analysis script.

This script performs detailed analysis of WebSocket heartbeat timing
to validate that heartbeats are being sent at consistent 30-second
intervals. It monitors heartbeat messages and provides comprehensive
timing analysis for production debugging and validation.

The timing verification ensures that the heartbeat mechanism is
functioning correctly and maintaining consistent intervals.
"""

import asyncio
import json
import time
import websockets
from datetime import datetime
import argparse
from typing import List, Optional


class HeartbeatTimingVerifier:
    """
    Heartbeat timing verification and analysis tool.
    
    This class monitors WebSocket heartbeat messages and analyzes
    timing patterns to validate that heartbeats are being sent
    at consistent 30-second intervals.
    """
    
    def __init__(self, url: str, session_id: Optional[str] = None):
        """
        Initialize the heartbeat timing verifier.
        
        Args:
            url: WebSocket server URL
            session_id: Optional session identifier
        """
        self.url = url
        self.session_id = session_id
        self.heartbeat_times: List[float] = []
        self.connection_start = None
        
    async def connect_and_verify(self):
        """
        Establish WebSocket connection and verify heartbeat timing.
        
        This function connects to the WebSocket service and monitors
        heartbeat messages for timing analysis over a 2-minute period.
        """
        if self.session_id:
            uri = f"{self.url}?session={self.session_id}"
        else:
            uri = self.url
            
        print(f"Establishing WebSocket connection: {uri}")
        print(f"Verifying heartbeat timing (expected: ~30 second intervals)")
        print("=" * 60)
        
        try:
            async with websockets.connect(uri) as websocket:
                self.connection_start = time.time()
                print(f"Connection established at {datetime.now().strftime('%H:%M:%S')}")
                
                # Send initial message to establish session
                await websocket.send("Heartbeat timing verification message")
                
                # Monitor messages for 2 minutes (expected: ~4 heartbeats)
                timeout = 120  # 2 minutes
                start_time = time.time()
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if 'ts' in data:
                            await self.process_heartbeat(data)
                            
                            # Perform timing analysis when sufficient data is available
                            if len(self.heartbeat_times) >= 2:
                                self.analyze_timing()
                                
                            # Terminate after timeout period
                            if time.time() - start_time > timeout:
                                break
                                
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON message received: {message}")
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"WebSocket connection closed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Error during timing verification: {e}")
    
    async def process_heartbeat(self, data: dict):
        """
        Process heartbeat message and record timing information.
        
        Args:
            data: Heartbeat message data containing timestamp
        """
        current_time = time.time()
        self.heartbeat_times.append(current_time)
        
        heartbeat_time = data['ts']
        print(f"Heartbeat #{len(self.heartbeat_times)} received at {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Server timestamp: {heartbeat_time}")
        
        if len(self.heartbeat_times) > 1:
            interval = current_time - self.heartbeat_times[-2]
            print(f"  Interval since previous: {interval:.1f} seconds")
            
            # Validate interval against expected 30-second timing
            if 25 <= interval <= 35:
                print(f"  Timing validation: ACCEPTABLE (~30s)")
            else:
                print(f"  Timing validation: OUTSIDE RANGE (expected ~30s, actual {interval:.1f}s)")
        
        print("-" * 40)
    
    def analyze_timing(self):
        """
        Analyze heartbeat timing patterns and provide comprehensive reporting.
        
        This function processes the collected heartbeat timing data to
        provide insights into timing consistency and accuracy.
        """
        if len(self.heartbeat_times) < 2:
            return
            
        print(f"\nHEARTBEAT TIMING ANALYSIS")
        print("=" * 40)
        
        # Calculate timing intervals
        intervals = []
        for i in range(1, len(self.heartbeat_times)):
            interval = self.heartbeat_times[i] - self.heartbeat_times[i-1]
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        print(f"Total heartbeats analyzed: {len(self.heartbeat_times)}")
        print(f"Average interval: {avg_interval:.1f} seconds")
        print(f"Minimum interval: {min_interval:.1f} seconds")
        print(f"Maximum interval: {max_interval:.1f} seconds")
        
        # Validate timing accuracy
        if 25 <= avg_interval <= 35:
            print(f"Heartbeat timing accuracy: CORRECT (average ~30s)")
        else:
            print(f"Heartbeat timing accuracy: INCORRECT (average {avg_interval:.1f}s, expected ~30s)")
        
        # Validate timing consistency
        interval_variation = max_interval - min_interval
        if interval_variation > 10:
            print(f"Timing consistency: INCONSISTENT (variation: {interval_variation:.1f}s)")
        else:
            print(f"Timing consistency: CONSISTENT")
        
        print("=" * 40)
        print()


async def main():
    """
    Execute heartbeat timing verification.
    
    This function provides a command-line interface for configuring
    and running heartbeat timing verification tests.
    """
    parser = argparse.ArgumentParser(description="WebSocket heartbeat timing verification")
    parser.add_argument("--url", default="ws://localhost/ws/chat/", 
                       help="WebSocket server URL")
    parser.add_argument("--session", help="Session identifier (optional)")
    
    args = parser.parse_args()
    
    verifier = HeartbeatTimingVerifier(args.url, args.session)
    
    print(f"Heartbeat Timing Verification Test")
    print(f"Target URL: {args.url}")
    print(f"Session ID: {args.session or 'None (anonymous)'}")
    print(f"Test Duration: 2 minutes")
    print("=" * 60)
    
    try:
        await verifier.connect_and_verify()
    except KeyboardInterrupt:
        print(f"\nVerification interrupted by user")
    
    print("=" * 60)
    print("Timing verification completed")


if __name__ == "__main__":
    asyncio.run(main())
