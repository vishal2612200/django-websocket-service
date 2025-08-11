# Prometheus Query for Log Search

## Comprehensive Log Search Query

Here's a powerful Prometheus query that combines error metrics with log search capabilities for comprehensive application monitoring:

```promql
# Comprehensive Log Search Query
(
  # Error rate over time (logs errors as they occur)
  rate(app_errors_total[5m]) * 60
  
  # Connection errors (failed connections)
  + rate(app_connections_closed_total[5m]) * 60
  
  # Message processing errors (failed message handling)
  + (rate(app_messages_total[5m]) - rate(app_messages_sent[5m])) * 60
  
  # High error threshold alert
  + (app_errors_total > 100) * 10
  
  # Connection failure rate
  + (rate(app_connections_opened_total[5m]) - rate(app_connections_closed_total[5m])) * 60
  
  # Session tracking errors
  + (app_active_connections - app_sessions_tracked) * 0.1
  
  # Shutdown duration anomalies (long shutdowns indicate issues)
  + (histogram_quantile(0.95, rate(app_shutdown_duration_seconds_bucket[5m])) > 10) * 5
  
  # Message throughput anomalies (sudden drops indicate problems)
  + (rate(app_messages_total[1m]) < rate(app_messages_total[5m]) * 0.5) * 3
  
  # Active connection drops (connection loss)
  + (app_active_connections < avg_over_time(app_active_connections[10m]) * 0.8) * 2
) * 100
```

## Query Breakdown

### **1. Error Rate Monitoring**
```promql
rate(app_errors_total[5m]) * 60
```
- **Purpose**: Tracks application errors over time
- **Use case**: Identify when errors spike in logs
- **Log correlation**: Matches `logger.error()` calls in code

### **2. Connection Error Detection**
```promql
rate(app_connections_closed_total[5m]) * 60
```
- **Purpose**: Monitors connection failures
- **Use case**: Detect WebSocket connection issues
- **Log correlation**: Matches connection close events

### **3. Message Processing Errors**
```promql
(rate(app_messages_total[5m]) - rate(app_messages_sent[5m])) * 60
```
- **Purpose**: Identifies messages that were received but not sent back
- **Use case**: Detect message processing failures
- **Log correlation**: Matches message handling errors

### **4. High Error Threshold Alert**
```promql
(app_errors_total > 100) * 10
```
- **Purpose**: Triggers when total errors exceed threshold
- **Use case**: Critical error alerting
- **Log correlation**: Emergency error conditions

### **5. Connection Failure Rate**
```promql
(rate(app_connections_opened_total[5m]) - rate(app_connections_closed_total[5m])) * 60
```
- **Purpose**: Detects connections that opened but didn't close properly
- **Use case**: Identify connection leaks
- **Log correlation**: Matches connection lifecycle issues

### **6. Session Tracking Errors**
```promql
(app_active_connections - app_sessions_tracked) * 0.1
```
- **Purpose**: Detects mismatches between connections and sessions
- **Use case**: Identify session tracking issues
- **Log correlation**: Matches session management errors

### **7. Shutdown Duration Anomalies**
```promql
(histogram_quantile(0.95, rate(app_shutdown_duration_seconds_bucket[5m])) > 10) * 5
```
- **Purpose**: Detects unusually long shutdown times
- **Use case**: Identify graceful shutdown issues
- **Log correlation**: Matches shutdown-related logs

### **8. Message Throughput Anomalies**
```promql
(rate(app_messages_total[1m]) < rate(app_messages_total[5m]) * 0.5) * 3
```
- **Purpose**: Detects sudden drops in message processing
- **Use case**: Identify message handling bottlenecks
- **Log correlation**: Matches message processing errors

### **9. Active Connection Drops**
```promql
(app_active_connections < avg_over_time(app_active_connections[10m]) * 0.8) * 2
```
- **Purpose**: Detects unexpected connection losses
- **Use case**: Identify connection stability issues
- **Log correlation**: Matches connection drop events

## Usage Examples

### **1. Real-time Error Monitoring**
```bash
# Query current error rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(app_errors_total[5m])*60'

# Monitor error spikes
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=rate(app_errors_total[5m])*60" | jq ".data.result[0].value[1]"'
```

### **2. Log Search Dashboard**
```promql
# Grafana dashboard query for log search
{
  "targets": [
    {
      "expr": "rate(app_errors_total[5m]) * 60",
      "legendFormat": "Error Rate (errors/min)"
    },
    {
      "expr": "rate(app_connections_closed_total[5m]) * 60",
      "legendFormat": "Connection Failures (failures/min)"
    },
    {
      "expr": "(rate(app_messages_total[5m]) - rate(app_messages_sent[5m])) * 60",
      "legendFormat": "Message Processing Errors (errors/min)"
    }
  ]
}
```

### **3. Alerting Rules**
```yaml
# prometheus.yml alerting rules
groups:
  - name: log_search_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(app_errors_total[5m]) * 60 > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per minute"
          
      - alert: ConnectionFailures
        expr: rate(app_connections_closed_total[5m]) * 60 > 50
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High connection failure rate"
          description: "Connection failure rate is {{ $value }} failures per minute"
          
      - alert: MessageProcessingErrors
        expr: (rate(app_messages_total[5m]) - rate(app_messages_sent[5m])) * 60 > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Message processing errors detected"
          description: "{{ $value }} messages per minute are failing to process"
```

### **4. Log Correlation Script**
```python
#!/usr/bin/env python3
"""
Log Search Correlation Script
Correlates Prometheus metrics with application logs
"""

import requests
import json
import time
from datetime import datetime, timedelta

def get_error_metrics():
    """Get current error metrics from Prometheus."""
    try:
        response = requests.get("http://localhost:9090/api/v1/query", params={
            "query": "rate(app_errors_total[5m]) * 60"
        })
        data = response.json()
        
        if data["status"] == "success" and data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
        return 0.0
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return 0.0

def search_logs_for_errors():
    """Search application logs for error patterns."""
    # This would integrate with your logging system
    # For demonstration, we'll show the correlation logic
    
    error_patterns = [
        "ERROR",
        "Failed to",
        "Error getting",
        "Error storing",
        "Error retrieving",
        "Failed to send",
        "Failed to store",
        "Redis status check failed"
    ]
    
    print("Log Search Patterns:")
    for pattern in error_patterns:
        print(f"  - {pattern}")
    
    return error_patterns

def correlate_metrics_with_logs():
    """Correlate Prometheus metrics with log patterns."""
    
    print("=" * 60)
    print("LOG SEARCH CORRELATION")
    print("=" * 60)
    print()
    
    # Get current error rate
    error_rate = get_error_metrics()
    
    print(f"Current Error Rate: {error_rate:.2f} errors/minute")
    print()
    
    # Get error patterns to search for
    error_patterns = search_logs_for_errors()
    
    print("Correlation Analysis:")
    if error_rate > 10:
        print("  🔴 HIGH ERROR RATE - Check logs for:")
        for pattern in error_patterns:
            print(f"    - {pattern}")
    elif error_rate > 5:
        print("  🟡 MODERATE ERROR RATE - Monitor logs for:")
        for pattern in error_patterns[:5]:
            print(f"    - {pattern}")
    else:
        print("  🟢 LOW ERROR RATE - System appears healthy")
    
    print()
    print("Log Search Commands:")
    print("  # Search for errors in container logs")
    print("  docker logs docker-app_green-1 2>&1 | grep -i error")
    print()
    print("  # Search for specific error patterns")
    print("  docker logs docker-app_green-1 2>&1 | grep -E '(ERROR|Failed|Error)'")
    print()
    print("  # Real-time log monitoring")
    print("  docker logs -f docker-app_green-1 2>&1 | grep -i error")

if __name__ == "__main__":
    correlate_metrics_with_logs()
```

## Advanced Log Search Queries

### **1. Error Pattern Analysis**
```promql
# Error patterns by type
sum by (error_type) (
  rate(app_errors_total[5m])
)
```

### **2. Connection Lifecycle Monitoring**
```promql
# Connection lifecycle analysis
(
  rate(app_connections_opened_total[5m]) * 60,
  rate(app_connections_closed_total[5m]) * 60,
  app_active_connections
)
```

### **3. Message Processing Health**
```promql
# Message processing health score
(
  rate(app_messages_sent[5m]) / rate(app_messages_total[5m])
) * 100
```

### **4. Session Management Issues**
```promql
# Session tracking anomalies
abs(app_active_connections - app_sessions_tracked) / app_active_connections * 100
```

## Conclusion

This comprehensive Prometheus query for log search provides:

1. **Real-time error monitoring** with correlation to application logs
2. **Connection lifecycle tracking** to identify connection issues
3. **Message processing health** to detect message handling problems
4. **Session management monitoring** to identify session tracking issues
5. **Performance anomaly detection** for shutdown and throughput issues
6. **Alerting integration** for proactive issue detection

The query combines multiple metrics to create a comprehensive log search capability that can help identify and troubleshoot application issues in real-time.




