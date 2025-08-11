#!/usr/bin/env python3
"""
Test script to verify that the reconnect button functionality works correctly.
This script will test WebSocket connections and reconnections.
"""

import asyncio
import json
import time
import websockets
import requests
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_metrics() -> Dict[str, float]:
    """Get current metrics from the application."""
    try:
        response = requests.get("http://localhost/metrics", timeout=5)
        metrics_text = response.text
        
        # Parse metrics
        metrics = {}
        for line in metrics_text.split('\n'):
            if line.startswith('app_') and not line.startswith('#'):
                try:
                    key, value = line.split(' ', 1)
                    metrics[key] = float(value)
                except ValueError:
                    continue
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {}

def print_metrics(metrics: Dict[str, float], label: str = ""):
    """Print metrics in a readable format."""
    logger.info(f"=== {label} ===")
    for key in ['app_active_connections', 'app_sessions_tracked', 'app_connections_opened_total', 'app_connections_closed_total', 'app_messages_total']:
        value = metrics.get(key, 0.0)
        logger.info(f"{key}: {value}")

async def test_reconnect_functionality():
    """Test the reconnect functionality."""
    
    # Get baseline metrics
    baseline_metrics = get_metrics()
    print_metrics(baseline_metrics, "Baseline Metrics")
    
    # Test 1: Establish connection with session ID
    logger.info("Test 1: Establishing connection with session ID")
    session_id = "test_reconnect_session"
    
    try:
        async with websockets.connect(f"ws://localhost/ws/chat/?session={session_id}") as websocket:
            # Wait for connection to be established
            await asyncio.sleep(2)
            
            # Check metrics after connection
            metrics_after_connect = get_metrics()
            print_metrics(metrics_after_connect, "After Connection")
            
            # Send a message
            await websocket.send(json.dumps({"message": "test message before reconnect"}))
            await asyncio.sleep(1)
            
            # Check metrics after message
            metrics_after_message = get_metrics()
            print_metrics(metrics_after_message, "After Message")
            
            # Simulate reconnect by closing and reopening
            logger.info("Simulating reconnect...")
            await websocket.close()
            
            # Wait a moment for the close to be processed
            await asyncio.sleep(1)
            
            # Check metrics after close
            metrics_after_close = get_metrics()
            print_metrics(metrics_after_close, "After Close")
            
            # Reconnect with same session ID
            logger.info("Reconnecting with same session ID...")
            async with websockets.connect(f"ws://localhost/ws/chat/?session={session_id}") as websocket2:
                # Wait for reconnection
                await asyncio.sleep(2)
                
                # Check metrics after reconnection
                metrics_after_reconnect = get_metrics()
                print_metrics(metrics_after_reconnect, "After Reconnect")
                
                # Send another message
                await websocket2.send(json.dumps({"message": "test message after reconnect"}))
                await asyncio.sleep(1)
                
                # Check final metrics
                final_metrics = get_metrics()
                print_metrics(final_metrics, "Final Metrics")
                
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
    
    # Wait a moment for cleanup
    await asyncio.sleep(3)
    
    # Final check
    cleanup_metrics = get_metrics()
    print_metrics(cleanup_metrics, "Cleanup Metrics")
    
    # Summary
    logger.info("=== Test Summary ===")
    if cleanup_metrics.get('app_active_connections', 0) == 0:
        logger.info("✓ All connections closed properly")
    else:
        logger.warning("⚠ Some connections may still be active")
    
    if cleanup_metrics.get('app_connections_opened_total', 0) > baseline_metrics.get('app_connections_opened_total', 0):
        logger.info("✓ Connections were opened during test")
    else:
        logger.error("✗ No connections were opened during test")

if __name__ == "__main__":
    asyncio.run(test_reconnect_functionality())
