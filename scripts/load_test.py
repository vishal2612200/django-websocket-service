#!/usr/bin/env python3
"""
WebSocket load testing script for performance validation.

This script performs concurrent WebSocket connection testing to validate
service performance under load. It establishes multiple connections simultaneously
and measures connection success rates and latency characteristics.

The load test is essential for validating non-functional requirements and
ensuring the service can handle expected production loads.
"""

import argparse
import asyncio
import json
import os
import random
import string
import time
from typing import Tuple

import websockets


async def worker(host: str, path: str, idx: int) -> Tuple[int, float]:
    """
    Individual worker function to establish a WebSocket connection and measure performance.
    
    This function creates a single WebSocket connection, sends a test message,
    and measures the round-trip time. It validates the connection by checking
    the server's response format and content.
    
    Args:
        host: Target host for WebSocket connection
        path: WebSocket endpoint path
        idx: Worker index for identification and logging
        
    Returns:
        Tuple of (success_flag, total_connection_time)
    """
    uri = f"ws://{host}{path}"
    start = time.perf_counter()
    try:
        async with websockets.connect(uri) as ws:
            # Send test message and measure response time
            await ws.send("load_test_message")
            msg = await ws.recv()
            data = json.loads(msg)
            
            # Validate server response indicates successful message processing
            if int(data.get("count", 0)) < 1:
                return 0, time.perf_counter() - start
            return 1, time.perf_counter() - start
    except Exception:
        # Connection failed or message processing error
        return 0, time.perf_counter() - start


async def main() -> int:
    """
    Main function to execute comprehensive load testing.
    
    This function orchestrates the load testing process by creating multiple
    concurrent worker tasks, executing them simultaneously, and analyzing
    the results to determine service performance characteristics.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="WebSocket load testing and performance validation")
    parser.add_argument("--host", default=os.environ.get("HOST", "localhost"),
                       help="Target host for load testing")
    parser.add_argument("--path", default=os.environ.get("PATH", "/ws/chat/"),
                       help="WebSocket endpoint path")
    parser.add_argument("--concurrency", type=int, default=int(os.environ.get("N", "6000")),
                       help="Number of concurrent connections to establish")
    args = parser.parse_args()

    print(f"WebSocket Load Test Configuration")
    print(f"Target: {args.host}{args.path}")
    print(f"Concurrency: {args.concurrency:,} connections")
    print(f"Test Type: Concurrent connection establishment with message exchange")
    print()

    # Create worker tasks for concurrent execution
    tasks = [worker(args.host, args.path, i) for i in range(args.concurrency)]
    
    # Execute all connections concurrently to simulate real-world load
    results = await asyncio.gather(*tasks)
    
    # Analyze results and calculate performance metrics
    successful_connections = sum(1 for success, _ in results if success == 1)
    latency_measurements = [duration for _, duration in results]
    
    # Calculate latency percentiles for performance analysis
    p50 = sorted(latency_measurements)[int(0.5 * len(latency_measurements))] if latency_measurements else 0
    p90 = sorted(latency_measurements)[int(0.9 * len(latency_measurements))] if latency_measurements else 0
    p99 = sorted(latency_measurements)[int(0.99 * len(latency_measurements))] if latency_measurements else 0
    
    # Output results in machine-readable format for CI/CD integration
    print(f"Load Test Results:")
    print(f"  Successful Connections: {successful_connections}/{len(results)}")
    print(f"  Success Rate: {(successful_connections/len(results)*100):.1f}%")
    print(f"  Latency P50: {p50:.3f}s")
    print(f"  Latency P90: {p90:.3f}s")
    print(f"  Latency P99: {p99:.3f}s")
    
    # Return appropriate exit code based on success rate
    # Consider test successful if at least 95% of connections succeed
    success_threshold = 0.95
    success_rate = successful_connections / len(results)
    
    if success_rate >= success_threshold:
        print(f"Load test PASSED: Success rate {success_rate:.1%} >= {success_threshold:.1%}")
        return 0
    else:
        print(f"Load test FAILED: Success rate {success_rate:.1%} < {success_threshold:.1%}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
