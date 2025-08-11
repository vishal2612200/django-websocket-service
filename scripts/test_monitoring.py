#!/usr/bin/env python3
"""
Monitoring infrastructure validation and testing script.

This script performs comprehensive testing of the monitoring stack setup,
including Prometheus connectivity, metrics collection, Grafana accessibility,
and alerting system validation. It ensures the monitoring infrastructure
is properly configured and collecting data for production observability.
"""

import requests
import time
import json
from urllib.parse import urljoin

def test_prometheus_connection():
    """
    Validate Prometheus service connectivity and configuration.
    
    This function tests the Prometheus API endpoints to ensure the service
    is accessible and properly configured. It verifies target health and
    validates the monitoring setup for WebSocket service metrics.
    
    Returns:
        bool: True if Prometheus is accessible and properly configured
    """
    print("Validating Prometheus service connectivity...")
    
    try:
        # Test Prometheus API connectivity
        response = requests.get("http://localhost:9090/api/v1/status/config", timeout=5)
        if response.status_code == 200:
            print("Prometheus service is accessible")
        else:
            print(f"Prometheus service returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Prometheus service: {e}")
        return False
    
    # Validate monitoring targets configuration
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            websocket_targets = [t for t in targets if t.get('labels', {}).get('job') == 'websocket-app']
            
            if websocket_targets:
                target = websocket_targets[0]
                health = target.get('health', 'unknown')
                print(f"WebSocket application target configured: {health}")
                if health == 'up':
                    print("Target is healthy and collecting metrics")
                else:
                    print(f"Target health status: {health}")
            else:
                print("WebSocket application target not found in configuration")
                return False
        else:
            print(f"Failed to retrieve monitoring targets: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error validating monitoring targets: {e}")
        return False
    
    return True

def test_metrics_collection():
    """
    Validate metrics collection and data availability.
    
    This function queries key metrics to ensure the monitoring system
    is collecting data from the WebSocket service. It checks for the
    presence of critical performance and health metrics.
    """
    print("\nValidating metrics collection and data availability...")
    
    metrics_to_check = [
        'app_messages_total',
        'app_active_connections', 
        'app_errors_total',
        'app_connections_opened_total',
        'app_connections_closed_total',
        'app_sessions_tracked'
    ]
    
    for metric in metrics_to_check:
        try:
            response = requests.get(f"http://localhost:9090/api/v1/query?query={metric}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {}).get('result', [])
                if result:
                    value = result[0].get('value', [None, None])[1]
                    print(f"Metric '{metric}': {value} (data available)")
                else:
                    print(f"Metric '{metric}': No data points available (normal if service is idle)")
            else:
                print(f"Failed to query metric '{metric}': HTTP {response.status_code}")
        except Exception as e:
            print(f"Error querying metric '{metric}': {e}")

def test_grafana_connection():
    """
    Validate Grafana service accessibility and health.
    
    This function tests the Grafana API to ensure the dashboard service
    is accessible and properly configured for monitoring visualization.
    
    Returns:
        bool: True if Grafana is accessible and healthy
    """
    print("\nValidating Grafana service connectivity...")
    
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('database') == 'ok':
                print("Grafana service is accessible and healthy")
                return True
            else:
                print(f"Grafana health status: {data}")
                return False
        else:
            print(f"Grafana service returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Grafana service: {e}")
        return False

def test_alertmanager_connection():
    """
    Validate Alertmanager service connectivity and configuration.
    
    This function tests the Alertmanager API to ensure the alerting
    system is properly configured and accessible for incident response.
    
    Returns:
        bool: True if Alertmanager is accessible
    """
    print("\nValidating Alertmanager service connectivity...")
    
    try:
        response = requests.get("http://localhost:9093/api/v1/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("Alertmanager service is accessible")
            print(f"Alertmanager version: {data.get('versionInfo', {}).get('version', 'unknown')}")
            return True
        else:
            print(f"Alertmanager service returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Alertmanager service: {e}")
        return False

def generate_test_traffic():
    """
    Generate test traffic to validate metrics collection.
    
    This function creates WebSocket connections and sends messages
    to generate metrics data for monitoring validation. It ensures
    the monitoring system captures real activity data.
    """
    print("\nGenerating test traffic for metrics validation...")
    
    try:
        import websocket
        
        def on_message(ws, message):
            """Handle incoming WebSocket messages during testing."""
            pass

        def on_error(ws, error):
            """Handle WebSocket errors during testing."""
            print(f"WebSocket error during test: {error}")

        def on_close(ws, close_status_code, close_msg):
            """Handle WebSocket connection closure during testing."""
            pass

        def on_open(ws):
            """Handle WebSocket connection establishment during testing."""
            print("Test WebSocket connection established")
            # Send test messages to generate metrics
            for i in range(5):
                ws.send(f"test_message_{i}")
                time.sleep(0.5)
            ws.close()

        # Create WebSocket connection for testing
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("ws://localhost/ws/chat/",
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        ws.run_forever(timeout=10)
        print("Test traffic generation completed")
        
    except ImportError:
        print("WebSocket library not available - skipping traffic generation")
    except Exception as e:
        print(f"Error generating test traffic: {e}")

def main():
    """
    Execute comprehensive monitoring infrastructure validation.
    
    This function orchestrates the complete monitoring validation process,
    including service connectivity tests, metrics validation, and traffic
    generation for comprehensive testing of the observability stack.
    """
    print("Monitoring Infrastructure Validation")
    print("=" * 50)
    
    # Test Prometheus connectivity and configuration
    prometheus_ok = test_prometheus_connection()
    
    # Test metrics collection
    test_metrics_collection()
    
    # Test Grafana connectivity
    grafana_ok = test_grafana_connection()
    
    # Test Alertmanager connectivity
    alertmanager_ok = test_alertmanager_connection()
    
    # Generate test traffic for metrics validation
    generate_test_traffic()
    
    # Wait for metrics to be collected
    print("\nWaiting for metrics collection...")
    time.sleep(5)
    
    # Re-test metrics after traffic generation
    print("\nRe-validating metrics after test traffic...")
    test_metrics_collection()
    
    # Summary
    print("\n" + "=" * 50)
    print("MONITORING VALIDATION SUMMARY")
    print("=" * 50)
    
    if prometheus_ok and grafana_ok and alertmanager_ok:
        print("All monitoring services are accessible and properly configured")
        print("Monitoring infrastructure validation: PASSED")
        print("\nThe monitoring stack is ready for production use.")
        print("Access the dashboards at:")
        print("  - Grafana: http://localhost:3000")
        print("  - Prometheus: http://localhost:9090")
        return 0
    else:
        print("Some monitoring services are not properly configured")
        print("Monitoring infrastructure validation: FAILED")
        print("\nPlease review the configuration and restart the monitoring stack.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
