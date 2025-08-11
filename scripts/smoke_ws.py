#!/usr/bin/env python3
"""
WebSocket service smoke test for deployment validation.

This script performs basic connectivity and functionality testing
of the WebSocket service to validate deployment readiness. It
establishes a connection, sends a test message, and validates
the response format and content.

Smoke tests are essential for validating service health during
deployment processes and CI/CD pipelines.
"""

import argparse
import asyncio
import json
import sys
import websockets


async def main(host: str, path: str, expect: int, timeout: float = 2.0) -> int:
    """
    Execute WebSocket service smoke test.
    
    This function establishes a WebSocket connection, sends a test message,
    and validates the response to ensure the service is functioning correctly.
    
    Args:
        host: Target host for WebSocket connection
        path: WebSocket endpoint path
        expect: Expected message count in response
        timeout: Connection timeout in seconds
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    uri = f"ws://{host}{path}"
    
    try:
        async with websockets.connect(uri) as ws:
            # Send test message to validate service functionality
            await ws.send("smoke_test_message")
            
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                print("Smoke test failed: Timeout waiting for response", file=sys.stderr)
                return 1
                
            try:
                data = json.loads(msg)
            except Exception:
                print("Smoke test failed: Invalid JSON response format", file=sys.stderr)
                return 1
                
            if int(data.get("count", -1)) != expect:
                print(f"Smoke test failed: Unexpected response count {data}", file=sys.stderr)
                return 1
                
        return 0
        
    except websockets.exceptions.ConnectionClosed:
        print("Smoke test failed: WebSocket connection was closed", file=sys.stderr)
        return 1
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Smoke test failed: Invalid status code - {e}", file=sys.stderr)
        return 1
    except ConnectionRefusedError:
        print("Smoke test failed: WebSocket service is not accessible", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Smoke test failed: Unexpected error - {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebSocket service smoke test")
    parser.add_argument("--host", default="localhost", help="Target host for testing")
    parser.add_argument("--path", default="/ws/chat/", help="WebSocket endpoint path")
    parser.add_argument("--expect", type=int, default=1, help="Expected message count")
    args = parser.parse_args()
    
    exit_code = asyncio.run(main(args.host, args.path, args.expect))
    sys.exit(exit_code)
