#!/usr/bin/env python3
"""
Single heartbeat per session validation and testing script.

This script performs comprehensive testing to validate that each WebSocket
session receives exactly one heartbeat message every 30 seconds. It monitors
multiple concurrent sessions to verify heartbeat distribution and timing
consistency across the WebSocket service.

The single heartbeat validation ensures that the heartbeat mechanism is
functioning correctly without duplicate or missing heartbeats per session.
"""

import asyncio
import json
import time
import websockets
from datetime import datetime
import argparse
from typing import Dict, List, Optional
import uuid


class SingleHeartbeatTester:
    """
    Single heartbeat per session testing and validation tool.
    
    This class manages multiple WebSocket sessions and monitors
    heartbeat messages to validate that each session receives
    exactly one heartbeat per 30-second interval.
    """
    
    def __init__(self, url: str, num_sessions: int = 3):
        """
        Initialize the single heartbeat tester.
        
        Args:
            url: WebSocket server URL
            num_sessions: Number of concurrent sessions to test
        """
        self.url = url
        self.num_sessions = num_sessions
        self.sessions: Dict[str, Dict] = {}
        self.heartbeat_counts: Dict[str, int] = {}
        self.start_time = None
        
    async def create_session(self, session_id: str):
        """
        Establish a single WebSocket session for heartbeat monitoring.
        
        Args:
            session_id: Unique session identifier
        """
        uri = f"{self.url}?session={session_id}"
        
        try:
            websocket = await websockets.connect(uri)
            self.sessions[session_id] = {
                'websocket': websocket,
                'heartbeats': [],
                'connected_at': time.time()
            }
            self.heartbeat_counts[session_id] = 0
            
            print(f"Session {session_id[:8]}... established successfully")
            
            # Initialize session monitoring
            asyncio.create_task(self.monitor_session(session_id))
            
        except Exception as e:
            print(f"Failed to establish session {session_id[:8]}...: {e}")
    
    async def monitor_session(self, session_id: str):
        """
        Monitor a single session for heartbeat messages and validate timing.
        
        Args:
            session_id: Session identifier to monitor
        """
        session = self.sessions[session_id]
        websocket = session['websocket']
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if 'ts' in data:
                        # Process heartbeat message
                        current_time = time.time()
                        session['heartbeats'].append({
                            'timestamp': data['ts'],
                            'received_at': current_time
                        })
                        self.heartbeat_counts[session_id] += 1
                        
                        print(f"Session {session_id[:8]}... heartbeat #{self.heartbeat_counts[session_id]}")
                        
                        # Validate heartbeat timing consistency
                        if len(session['heartbeats']) > 1:
                            last_heartbeat = session['heartbeats'][-2]
                            time_diff = current_time - last_heartbeat['received_at']
                            if time_diff < 25:  # Less than 25 seconds between heartbeats
                                print(f"Warning: Session {session_id[:8]}... heartbeat interval too short: {time_diff:.1f}s")
                        
                except json.JSONDecodeError:
                    pass  # Ignore non-JSON messages
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Session {session_id[:8]}... connection closed")
        except Exception as e:
            print(f"Session {session_id[:8]}... monitoring error: {e}")
    
    async def run_test(self, duration: int = 120):
        """
        Execute the single heartbeat validation test.
        
        Args:
            duration: Test duration in seconds
        """
        print(f"Single Heartbeat Per Session Validation Test")
        print(f"Target URL: {self.url}")
        print(f"Number of Sessions: {self.num_sessions}")
        print(f"Test Duration: {duration} seconds")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Create multiple concurrent sessions
        print(f"\nEstablishing {self.num_sessions} concurrent sessions...")
        session_tasks = []
        
        for i in range(self.num_sessions):
            session_id = str(uuid.uuid4())
            task = asyncio.create_task(self.create_session(session_id))
            session_tasks.append(task)
        
        # Wait for all sessions to be established
        await asyncio.gather(*session_tasks)
        print(f"All sessions established successfully")
        
        # Monitor sessions for specified duration
        print(f"\nMonitoring sessions for {duration} seconds...")
        await asyncio.sleep(duration)
        
        # Close all sessions
        print(f"\nClosing all sessions...")
        close_tasks = []
        for session_id, session_data in self.sessions.items():
            task = asyncio.create_task(session_data['websocket'].close())
            close_tasks.append(task)
        
        await asyncio.gather(*close_tasks, return_exceptions=True)
        print("All sessions closed successfully")
        
        # Analyze test results
        print(f"\nAnalyzing test results...")
        self.analyze_results()
    
    def analyze_results(self):
        """
        Analyze single heartbeat test results and provide comprehensive reporting.
        
        This function processes the collected heartbeat data to validate
        that each session receives exactly one heartbeat per 30-second
        interval and identifies any timing inconsistencies.
        """
        print("\n" + "=" * 60)
        print("SINGLE HEARTBEAT TEST RESULTS")
        print("=" * 60)
        
        total_heartbeats = 0
        session_analyses = []
        
        for session_id, session_data in self.sessions.items():
            heartbeats = session_data['heartbeats']
            connected_at = session_data['connected_at']
            uptime = time.time() - connected_at
            
            # Calculate expected heartbeats
            expected_heartbeats = int(uptime / 30)
            
            # Analyze heartbeat intervals
            intervals = []
            for i in range(1, len(heartbeats)):
                interval = heartbeats[i]['received_at'] - heartbeats[i-1]['received_at']
                intervals.append(interval)
            
            session_analysis = {
                'session_id': session_id,
                'heartbeats_received': len(heartbeats),
                'expected_heartbeats': expected_heartbeats,
                'uptime': uptime,
                'avg_interval': sum(intervals) / len(intervals) if intervals else 0,
                'min_interval': min(intervals) if intervals else 0,
                'max_interval': max(intervals) if intervals else 0,
                'intervals': intervals
            }
            session_analyses.append(session_analysis)
            total_heartbeats += len(heartbeats)
            
            print(f"\nSession {session_id[:8]}... Analysis:")
            print(f"  Heartbeats received: {len(heartbeats)}")
            print(f"  Expected heartbeats: {expected_heartbeats}")
            print(f"  Session uptime: {uptime:.1f} seconds")
            
            if intervals:
                print(f"  Average interval: {session_analysis['avg_interval']:.1f}s")
                print(f"  Interval range: {session_analysis['min_interval']:.1f}s - {session_analysis['max_interval']:.1f}s")
            
            # Validate heartbeat count
            if len(heartbeats) == expected_heartbeats:
                print(f"  Heartbeat count: CORRECT")
            elif len(heartbeats) > expected_heartbeats:
                print(f"  Heartbeat count: TOO MANY (duplicates possible)")
            else:
                print(f"  Heartbeat count: TOO FEW (missing heartbeats)")
        
        # Overall validation
        print(f"\nOverall Validation Results:")
        print(f"  Total heartbeats across all sessions: {total_heartbeats}")
        print(f"  Active sessions: {len([s for s in session_analyses if s['heartbeats_received'] > 0])}")
        
        # Check for timing consistency
        consistent_sessions = 0
        for analysis in session_analyses:
            if analysis['intervals']:
                avg_interval = analysis['avg_interval']
                if 25 <= avg_interval <= 35:  # Allow 5-second tolerance
                    consistent_sessions += 1
        
        if consistent_sessions == len(session_analyses):
            print(f"  Timing consistency: PASSED")
            print(f"  All sessions have consistent 30-second intervals")
        else:
            print(f"  Timing consistency: FAILED")
            print(f"  {consistent_sessions}/{len(session_analyses)} sessions have consistent timing")
        
        # Final assessment
        active_sessions = [s for s in session_analyses if s['heartbeats_received'] > 0]
        if len(active_sessions) == self.num_sessions:
            print(f"  Single heartbeat functionality: PASSED")
            print(f"  All sessions received heartbeat messages")
        else:
            print(f"  Single heartbeat functionality: PARTIAL")
            print(f"  {len(active_sessions)}/{self.num_sessions} sessions received heartbeats")


async def main():
    """
    Execute single heartbeat validation testing.
    
    This function provides a command-line interface for configuring
    and running single heartbeat tests with multiple sessions.
    """
    parser = argparse.ArgumentParser(description="Single heartbeat per session validation")
    parser.add_argument("--url", default="ws://localhost/ws/chat/", 
                       help="WebSocket server URL")
    parser.add_argument("--sessions", type=int, default=3, 
                       help="Number of concurrent sessions")
    parser.add_argument("--duration", type=int, default=120, 
                       help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = SingleHeartbeatTester(args.url, args.sessions)
    await tester.run_test(args.duration)


if __name__ == "__main__":
    asyncio.run(main())
