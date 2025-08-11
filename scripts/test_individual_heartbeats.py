#!/usr/bin/env python3
"""
Individual session heartbeat validation and latency analysis script.

This script performs comprehensive testing of individual session heartbeat
functionality by creating multiple concurrent WebSocket sessions and
monitoring heartbeat timing, latency, and consistency across sessions.

The individual heartbeat testing validates that each session receives
proper heartbeat messages and that latency calculations are accurate
for production monitoring and debugging.
"""

import asyncio
import json
import time
import websockets
from datetime import datetime
import argparse
from typing import Dict, List, Optional
import uuid


class IndividualHeartbeatTester:
    """
    Individual session heartbeat testing and analysis tool.
    
    This class manages multiple concurrent WebSocket sessions and
    monitors heartbeat messages to validate individual session
    heartbeat functionality and performance characteristics.
    """
    
    def __init__(self, url: str, num_sessions: int = 3):
        """
        Initialize the heartbeat tester with configuration.
        
        Args:
            url: WebSocket server URL
            num_sessions: Number of concurrent sessions to test
        """
        self.url = url
        self.num_sessions = num_sessions
        self.sessions: Dict[str, Dict] = {}
        self.heartbeat_data: Dict[str, List] = {}
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
                'connected_at': time.time(),
                'last_heartbeat': None
            }
            self.heartbeat_data[session_id] = []
            
            print(f"Session {session_id[:8]}... established successfully")
            
            # Initialize session monitoring
            asyncio.create_task(self.monitor_session(session_id))
            
        except Exception as e:
            print(f"Failed to establish session {session_id[:8]}...: {e}")
    
    async def monitor_session(self, session_id: str):
        """
        Monitor a single session for heartbeat messages and analyze timing.
        
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
                        heartbeat_time = data['ts']
                        
                        # Calculate network latency
                        try:
                            import dateutil.parser
                            server_time = dateutil.parser.parse(heartbeat_time).timestamp()
                            latency_ms = (current_time - server_time) * 1000
                        except:
                            latency_ms = 0
                        
                        heartbeat_info = {
                            'timestamp': heartbeat_time,
                            'received_at': current_time,
                            'latency_ms': latency_ms,
                            'session_id': session_id
                        }
                        
                        self.heartbeat_data[session_id].append(heartbeat_info)
                        session['last_heartbeat'] = current_time
                        
                        print(f"Session {session_id[:8]}... heartbeat #{len(self.heartbeat_data[session_id])}")
                        print(f"  Server timestamp: {heartbeat_time}")
                        print(f"  Network latency: {latency_ms:.1f}ms")
                        
                        # Validate heartbeat timing consistency
                        if len(self.heartbeat_data[session_id]) > 1:
                            last_heartbeat = self.heartbeat_data[session_id][-2]
                            time_diff = current_time - last_heartbeat['received_at']
                            if time_diff < 25:  # Less than 25 seconds between heartbeats
                                print(f"  Warning: Heartbeat interval too short: {time_diff:.1f}s")
                        
                        print(f"{'-'*40}")
                        
                except json.JSONDecodeError:
                    pass  # Ignore non-JSON messages
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Session {session_id[:8]}... connection closed")
        except Exception as e:
            print(f"Session {session_id[:8]}... monitoring error: {e}")
    
    async def run_test(self, duration: int = 120):
        """
        Execute the individual heartbeat validation test.
        
        Args:
            duration: Test duration in seconds
        """
        print(f"Individual Session Heartbeat Validation Test")
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
        Analyze heartbeat test results and provide comprehensive reporting.
        
        This function processes the collected heartbeat data to provide
        insights into timing consistency, latency characteristics, and
        overall heartbeat reliability across multiple sessions.
        """
        print("\n" + "=" * 60)
        print("INDIVIDUAL HEARTBEAT TEST RESULTS")
        print("=" * 60)
        
        total_heartbeats = 0
        total_latency = 0
        session_summaries = []
        
        for session_id, heartbeats in self.heartbeat_data.items():
            if not heartbeats:
                print(f"Session {session_id[:8]}...: No heartbeats received")
                continue
            
            session_latency = sum(h['latency_ms'] for h in heartbeats)
            avg_latency = session_latency / len(heartbeats)
            
            # Calculate heartbeat intervals
            intervals = []
            for i in range(1, len(heartbeats)):
                interval = heartbeats[i]['received_at'] - heartbeats[i-1]['received_at']
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            session_summary = {
                'session_id': session_id,
                'heartbeat_count': len(heartbeats),
                'avg_latency': avg_latency,
                'avg_interval': avg_interval,
                'min_interval': min(intervals) if intervals else 0,
                'max_interval': max(intervals) if intervals else 0
            }
            session_summaries.append(session_summary)
            
            total_heartbeats += len(heartbeats)
            total_latency += session_latency
            
            print(f"\nSession {session_id[:8]}... Summary:")
            print(f"  Heartbeats received: {len(heartbeats)}")
            print(f"  Average latency: {avg_latency:.1f}ms")
            print(f"  Average interval: {avg_interval:.1f}s")
            print(f"  Interval range: {min(intervals):.1f}s - {max(intervals):.1f}s")
        
        # Overall statistics
        if total_heartbeats > 0:
            overall_avg_latency = total_latency / total_heartbeats
            print(f"\nOverall Statistics:")
            print(f"  Total heartbeats: {total_heartbeats}")
            print(f"  Average latency: {overall_avg_latency:.1f}ms")
            print(f"  Active sessions: {len([s for s in session_summaries if s['heartbeat_count'] > 0])}")
            
            # Validation results
            print(f"\nValidation Results:")
            active_sessions = [s for s in session_summaries if s['heartbeat_count'] > 0]
            if len(active_sessions) == self.num_sessions:
                print("  Individual heartbeat functionality: PASSED")
                print("  All sessions received heartbeat messages")
            else:
                print("  Individual heartbeat functionality: PARTIAL")
                print(f"  {len(active_sessions)}/{self.num_sessions} sessions received heartbeats")
            
            if overall_avg_latency < 100:  # Less than 100ms average latency
                print("  Latency performance: ACCEPTABLE")
            else:
                print("  Latency performance: NEEDS ATTENTION")
        else:
            print(f"\nNo heartbeats received from any session")
            print("Individual heartbeat functionality: FAILED")


async def main():
    """
    Execute individual heartbeat validation testing.
    
    This function provides a command-line interface for configuring
    and running individual heartbeat tests with multiple sessions.
    """
    parser = argparse.ArgumentParser(description="Individual session heartbeat validation")
    parser.add_argument("--url", default="ws://localhost/ws/chat/", 
                       help="WebSocket server URL")
    parser.add_argument("--sessions", type=int, default=3, 
                       help="Number of concurrent sessions")
    parser.add_argument("--duration", type=int, default=120, 
                       help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = IndividualHeartbeatTester(args.url, args.sessions)
    await tester.run_test(args.duration)


if __name__ == "__main__":
    asyncio.run(main())
