#!/usr/bin/env python3
"""
Test script to verify that the metrics fix works correctly.
This script will test connections with and without session IDs.
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

async def test_metrics_fix():
    """Test that metrics are consistent when connections are established."""
    
    # Get baseline metrics
    baseline_metrics = get_metrics()
    print_metrics(baseline_metrics, "Baseline Metrics")
    
    # Test 1: Connection without session ID
    logger.info("Test 1: Establishing connection without session ID")
    try:
        async with websockets.connect("ws://localhost/ws/chat/") as websocket:
            # Wait a moment for connection to be established
            await asyncio.sleep(2)
            
            # Check metrics after connection
            metrics_after_connect = get_metrics()
            print_metrics(metrics_after_connect, "After Connection (no session)")
            
            # Verify that active_connections increased but sessions_tracked stayed 0
            if metrics_after_connect.get('app_active_connections', 0) > baseline_metrics.get('app_active_connections', 0):
                logger.info("✓ Active connections increased correctly")
            else:
                logger.error("✗ Active connections did not increase")
                
            if metrics_after_connect.get('app_sessions_tracked', 0) == 0:
                logger.info("✓ Sessions tracked remained 0 (correct for no session ID)")
            else:
                logger.error("✗ Sessions tracked should be 0 for connection without session ID")
            
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
    
    # Wait a moment
    await asyncio.sleep(3)
    
    # Test 2: Connection with session ID
    logger.info("Test 2: Establishing connection with session ID")
    try:
        session_id = "test_session_123"
        async with websockets.connect(f"ws://localhost/ws/chat/?session={session_id}") as websocket:
            # Wait a moment for connection to be established
            await asyncio.sleep(2)
            
            # Check metrics after connection
            metrics_after_connect = get_metrics()
            print_metrics(metrics_after_connect, "After Connection (with session)")
            
            # Verify that both active_connections and sessions_tracked increased
            if metrics_after_connect.get('app_active_connections', 0) > 0:
                logger.info("✓ Active connections increased correctly")
            else:
                logger.error("✗ Active connections did not increase")
                
            if metrics_after_connect.get('app_sessions_tracked', 0) > 0:
                logger.info("✓ Sessions tracked increased correctly")
            else:
                logger.error("✗ Sessions tracked should increase for connection with session ID")
            
    except Exception as e:
        logger.error(f"Test 2 failed: {e}")
    
    # Wait a moment
    await asyncio.sleep(3)
    
    # Final metrics
    final_metrics = get_metrics()
    print_metrics(final_metrics, "Final Metrics")
    
    # Summary
    logger.info("=== Test Summary ===")
    if final_metrics.get('app_active_connections', 0) == 0 and final_metrics.get('app_sessions_tracked', 0) == 0:
        logger.info("✓ All connections closed properly, metrics are consistent")
    else:
        logger.warning("⚠ Some connections may still be active")

if __name__ == "__main__":
    asyncio.run(test_metrics_fix())
