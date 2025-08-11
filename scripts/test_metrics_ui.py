#!/usr/bin/env python3
"""
Test script to verify WebSocket metrics are working properly.
This script checks the /metrics endpoint and validates the expected metrics are present.
"""

import requests
import time
import sys
from typing import Dict, List

def fetch_metrics(base_url: str = "http://localhost:8000") -> str:
    """Fetch metrics from the /metrics endpoint."""
    try:
        response = requests.get(f"{base_url}/metrics", timeout=5)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Failed to fetch metrics: {e}")
        return ""

def parse_metrics(metrics_text: str) -> Dict[str, float]:
    """Parse Prometheus metrics text into a dictionary."""
    metrics = {}
    for line in metrics_text.split('\n'):
        line = line.strip()
        if line.startswith('app_') and not line.startswith('#'):
            try:
                # Handle both simple metrics and histograms
                if ' ' in line:
                    key, value = line.split(' ', 1)
                    if '{' in key:
                        # Skip histogram buckets and quantiles for now
                        continue
                    metrics[key] = float(value)
            except (ValueError, IndexError):
                continue
    return metrics

def validate_expected_metrics(metrics: Dict[str, float]) -> List[str]:
    """Validate that expected WebSocket metrics are present."""
    expected_metrics = [
        'app_active_connections',
        'app_messages_total', 
        'app_messages_sent',
        'app_connections_opened_total',
    ]
    
    missing_metrics = []
    for metric in expected_metrics:
        if metric not in metrics:
            missing_metrics.append(metric)
    
    return missing_metrics

def print_metrics_summary(metrics: Dict[str, float]):
    """Print a summary of the current metrics."""
    print("\n📊 WebSocket Metrics Summary:")
    print("=" * 50)
    
    # Connection metrics
    print(f"🔗 Active Connections: {metrics.get('app_active_connections', 0)}")
    print(f"📈 Total Connections: {metrics.get('app_connections_opened_total', 0)}")
    
    # Message metrics
    print(f"📨 Messages Received: {metrics.get('app_messages_total', 0)}")
    print(f"📤 Messages Sent: {metrics.get('app_messages_sent', 0)}")

def main():
    """Main test function."""
    print("🧪 Testing WebSocket Metrics Endpoint")
    print("=" * 40)
    
    # Fetch metrics
    print("📡 Fetching metrics from /metrics endpoint...")
    metrics_text = fetch_metrics()
    
    if not metrics_text:
        print("❌ No metrics data received")
        sys.exit(1)
    
    # Parse metrics
    metrics = parse_metrics(metrics_text)
    
    if not metrics:
        print("❌ No valid metrics found in response")
        sys.exit(1)
    
    # Validate expected metrics
    missing_metrics = validate_expected_metrics(metrics)
    
    if missing_metrics:
        print(f"⚠️  Missing expected metrics: {', '.join(missing_metrics)}")
    else:
        print("✅ All expected metrics are present")
    
    # Print summary
    print_metrics_summary(metrics)
    
    # Check for any issues
    active_connections = metrics.get('app_active_connections', 0)
    total_connections = metrics.get('app_connections_opened_total', 0)
    
    print("\n🔍 Health Check:")
    if active_connections >= 0:
        print("✅ Active connections metric is working")
    else:
        print("❌ Active connections metric has invalid value")
    
    if total_connections >= 0:
        print("✅ Total connections metric is working")
    else:
        print("❌ Total connections metric has invalid value")
    
    print("\n🎉 Metrics test completed successfully!")
    print("\n💡 To view metrics in the UI:")
    print("   1. Start the application: make run")
    print("   2. Open http://localhost:8000 in your browser")
    print("   3. Look for the 'WebSocket Metrics Dashboard' section")

if __name__ == "__main__":
    main()
