# Observability and Monitoring Guide

## Overview

This document outlines the comprehensive observability strategy for the Django WebSocket Service, following enterprise-grade monitoring practices and SRE principles. The observability framework provides complete visibility into system behavior, enabling proactive issue detection and rapid incident response.

## Monitoring Strategy

### The Three Pillars of Observability

**Problem Statement**: Production systems require comprehensive visibility to maintain reliability, performance, and user experience. Without proper observability, issues can go undetected until they significantly impact users.

**Solution**: Implement a monitoring strategy that provides real-time insights into system health, performance, and user experience through metrics, logging, and distributed tracing.

**Implementation Approach**:
- Implement metrics collection for all critical operations
- Add structured logging with correlation IDs
- Create distributed tracing for request flows
- Set up automated alerting and incident response
- Build dashboards for operational visibility

**Expected Outcomes**:
- 100% visibility into system health and performance
- Proactive issue detection with <5 minute alert time
- Historical performance analysis capabilities
- Reduced mean time to resolution (MTTR) by 80%

## Metrics Collection

### Key Performance Indicators (KPIs)

| Category | Metric | Type | Description | Alert Threshold |
|----------|--------|------|-------------|-----------------|
| **Availability** | `app_uptime_percentage` | Gauge | Service uptime percentage | < 99.9% |
| **Performance** | `app_response_time_p95` | Histogram | 95th percentile response time | > 500ms |
| **Throughput** | `app_messages_per_second` | Counter | Messages processed per second | < 1 msg/sec |
| **Errors** | `app_error_rate` | Counter | Error rate per minute | > 10 errors/min |
| **Resources** | `app_memory_usage_percent` | Gauge | Memory utilization | > 85% |
| **Connections** | `app_active_connections` | Gauge | Active WebSocket connections | < 1 for 60s |

### WebSocket-Specific Metrics

```python
# Example: Comprehensive WebSocket metrics
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Connection metrics
CONNECTIONS_ACTIVE = Gauge('app_active_connections', 'Active WebSocket connections')
CONNECTIONS_TOTAL = Counter('app_connections_total', 'Total connections opened')
CONNECTIONS_CLOSED = Counter('app_connections_closed_total', 'Total connections closed')
CONNECTION_DURATION = Histogram('app_connection_duration_seconds', 'Connection duration', 
                               buckets=[1, 5, 15, 30, 60, 300, 600, 1800, 3600])

# Message metrics
MESSAGES_TOTAL = Counter('app_messages_total', 'Total messages processed')
MESSAGE_SIZE = Histogram('app_message_size_bytes', 'Message size distribution',
                        buckets=[64, 256, 1024, 4096, 16384, 65536])
MESSAGE_PROCESSING_TIME = Histogram('app_message_processing_seconds', 'Message processing time',
                                   buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5])

# Session metrics
SESSIONS_TRACKED = Gauge('app_sessions_tracked', 'Number of tracked sessions')
SESSION_DURATION = Histogram('app_session_duration_seconds', 'Session duration',
                            buckets=[60, 300, 900, 1800, 3600, 7200, 14400])

# Error metrics
ERRORS_TOTAL = Counter('app_errors_total', 'Total errors', ['error_type', 'error_code'])
ERROR_RATE = Counter('app_error_rate', 'Error rate per minute')

# Performance metrics
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('app_cpu_usage_percent', 'CPU usage percentage')
```

### Prometheus Queries

#### Basic Queries

```promql
# Messages per second (rate)
rate(app_messages_total[1m])

# Active connections trend
app_active_connections

# Error rate
rate(app_errors_total[5m])

# 95th percentile response time
histogram_quantile(0.95, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))

# Connection success rate
rate(app_connections_total[5m]) / (rate(app_connections_total[5m]) + rate(app_connections_closed_total[5m])) * 100
```

#### Advanced Queries

```promql
# Top error types by frequency
topk(5, sum(rate(app_errors_total[5m])) by (error_type))

# Memory usage trend over time
app_memory_usage_bytes / app_memory_total_bytes * 100

# Connection churn rate
rate(app_connections_closed_total[5m]) / app_active_connections

# Message processing latency by percentile
histogram_quantile(0.50, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))

# Redis operation latency
histogram_quantile(0.95, sum(rate(redis_commands_duration_seconds_bucket[5m])) by (le))
```

### Metrics Implementation

#### Django Middleware for Metrics

```python
# middleware.py
import time
from prometheus_client import Counter, Histogram, Gauge
from django.http import JsonResponse

# Metrics definitions
REQUEST_COUNT = Counter('django_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('django_http_request_duration_seconds', 'HTTP request duration')
ACTIVE_REQUESTS = Gauge('django_http_requests_active', 'Active HTTP requests')

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        try:
            response = self.get_response(request)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.path,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.observe(time.time() - start_time)
            
            return response
        finally:
            ACTIVE_REQUESTS.dec()
```

#### WebSocket Consumer Metrics

```python
# consumers.py
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from prometheus_client import Counter, Histogram, Gauge

class MetricsChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_start_time = None

    async def connect(self):
        self.connection_start_time = time.time()
        CONNECTIONS_ACTIVE.inc()
        CONNECTIONS_TOTAL.inc()
        
        await super().connect()

    async def disconnect(self, close_code):
        if self.connection_start_time:
            CONNECTION_DURATION.observe(time.time() - self.connection_start_time)
        
        CONNECTIONS_ACTIVE.dec()
        CONNECTIONS_CLOSED.inc()
        
        await super().disconnect(close_code)

    async def receive(self, text_data):
        start_time = time.time()
        
        try:
            await super().receive(text_data)
            MESSAGES_TOTAL.inc()
            MESSAGE_SIZE.observe(len(text_data))
        except Exception as e:
            ERRORS_TOTAL.labels(error_type='message_processing', error_code=str(e)).inc()
            raise
        finally:
            MESSAGE_PROCESSING_TIME.observe(time.time() - start_time)
```

## Structured Logging

### Logging Configuration

```python
# settings.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': StructuredFormatter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/websocket/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
        },
    },
    'loggers': {
        'websocket': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

### Correlation IDs

```python
# middleware.py
import uuid
import logging

class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        
        # Add to logging context
        logger = logging.getLogger('websocket')
        logger = logger.bind(correlation_id=correlation_id)
        
        # Add to response headers
        response = self.get_response(request)
        response['X-Correlation-ID'] = correlation_id
        
        return response

# Usage in views
def some_view(request):
    logger = logging.getLogger('websocket')
    logger.info('Processing request', extra={
        'correlation_id': request.correlation_id,
        'user_id': request.user.id,
        'endpoint': request.path,
    })
```

### Log Analysis Queries

#### Error Analysis

```sql
-- Find most common errors
SELECT 
    message,
    COUNT(*) as error_count,
    AVG(CAST(JSON_EXTRACT(extra_fields, '$.response_time') AS FLOAT)) as avg_response_time
FROM logs 
WHERE level = 'ERROR' 
    AND timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY message 
ORDER BY error_count DESC 
LIMIT 10;

-- Error rate over time
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    COUNT(*) as error_count
FROM logs 
WHERE level = 'ERROR' 
    AND timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY minute 
ORDER BY minute;
```

#### Performance Analysis

```sql
-- Slow requests
SELECT 
    correlation_id,
    JSON_EXTRACT(extra_fields, '$.endpoint') as endpoint,
    JSON_EXTRACT(extra_fields, '$.response_time') as response_time,
    message
FROM logs 
WHERE JSON_EXTRACT(extra_fields, '$.response_time') > 1.0
    AND timestamp >= NOW() - INTERVAL 1 HOUR
ORDER BY CAST(JSON_EXTRACT(extra_fields, '$.response_time') AS FLOAT) DESC
LIMIT 20;

-- Request patterns
SELECT 
    JSON_EXTRACT(extra_fields, '$.endpoint') as endpoint,
    JSON_EXTRACT(extra_fields, '$.method') as method,
    COUNT(*) as request_count,
    AVG(CAST(JSON_EXTRACT(extra_fields, '$.response_time') AS FLOAT)) as avg_response_time
FROM logs 
WHERE timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY endpoint, method
ORDER BY request_count DESC;
```

## Distributed Tracing

### OpenTelemetry Integration

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

# Add span processor
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument Django and Redis
DjangoInstrumentor().instrument()
RedisInstrumentor().instrument()
```

### Custom Spans

```python
# consumers.py
from opentelemetry import trace

class TracedChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        with tracer.start_as_current_span("websocket.connect") as span:
            span.set_attribute("websocket.session_id", self.session_id)
            span.set_attribute("websocket.room_name", self.room_name)
            
            await super().connect()

    async def receive(self, text_data):
        with tracer.start_as_current_span("websocket.message.process") as span:
            span.set_attribute("websocket.message.size", len(text_data))
            span.set_attribute("websocket.message.type", "text")
            
            try:
                await super().receive(text_data)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
```

## Alerting and Incident Response

### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: websocket_critical_alerts
    rules:
      - alert: ServiceDown
        expr: up{job="websocket-app"} == 0
        for: 1m
        labels:
          severity: critical
          team: websocket
        annotations:
          summary: "WebSocket service is down"
          description: "Service {{ $labels.instance }} is not responding"
          runbook_url: "https://wiki.company.com/runbooks/service-down"

      - alert: HighErrorRate
        expr: rate(app_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
          team: websocket
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
          runbook_url: "https://wiki.company.com/runbooks/high-error-rate"

  - name: websocket_warning_alerts
    rules:
      - alert: HighMemoryUsage
        expr: app_memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
          team: websocket
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
          runbook_url: "https://wiki.company.com/runbooks/high-memory-usage"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(app_message_processing_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
          team: websocket
        annotations:
          summary: "Slow response time"
          description: "95th percentile response time is {{ $value }}s"
          runbook_url: "https://wiki.company.com/runbooks/slow-response-time"
```

### Incident Response Automation

```python
# incident_response.py
import requests
import json
from datetime import datetime

class IncidentResponse:
    def __init__(self, slack_webhook_url, pagerduty_api_key):
        self.slack_webhook_url = slack_webhook_url
        self.pagerduty_api_key = pagerduty_api_key

    def create_incident(self, alert_data):
        """Create incident in PagerDuty and notify Slack"""
        
        # Create PagerDuty incident
        incident_data = {
            "incident": {
                "type": "incident",
                "title": alert_data['summary'],
                "service": {
                    "id": "websocket-service-id",
                    "type": "service_reference"
                },
                "urgency": "high" if alert_data['severity'] == 'critical' else 'low',
                "body": {
                    "type": "incident_body",
                    "details": alert_data['description']
                }
            }
        }
        
        response = requests.post(
            "https://api.pagerduty.com/incidents",
            headers={
                "Authorization": f"Token token={self.pagerduty_api_key}",
                "Content-Type": "application/json"
            },
            json=incident_data
        )
        
        # Send Slack notification
        slack_data = {
            "text": f"🚨 *{alert_data['severity'].upper()} Alert*",
            "attachments": [
                {
                    "title": alert_data['summary'],
                    "text": alert_data['description'],
                    "color": "danger" if alert_data['severity'] == 'critical' else "warning",
                    "fields": [
                        {
                            "title": "Runbook",
                            "value": alert_data['runbook_url'],
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().isoformat(),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        requests.post(self.slack_webhook_url, json=slack_data)
```

## Dashboards and Visualization

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "WebSocket Service Overview",
    "panels": [
      {
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "app_active_connections",
            "legendFormat": "Connections"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "displayMode": "gradient"
            }
          }
        }
      },
      {
        "title": "Message Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(app_messages_total[1m])",
            "legendFormat": "Messages/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(app_errors_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "title": "Response Time Percentiles",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(app_message_processing_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99"
          }
        ]
      }
    ]
  }
}
```

### Custom Dashboard Panels

#### Connection Health Panel

```json
{
  "title": "Connection Health",
  "type": "stat",
  "targets": [
    {
      "expr": "app_active_connections",
      "legendFormat": "Active"
    },
    {
      "expr": "rate(app_connections_total[5m])",
      "legendFormat": "New/sec"
    },
    {
      "expr": "rate(app_connections_closed_total[5m])",
      "legendFormat": "Closed/sec"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 1000},
          {"color": "red", "value": 5000}
        ]
      }
    }
  }
}
```

#### Error Analysis Panel

```json
{
  "title": "Error Analysis",
  "type": "table",
  "targets": [
    {
      "expr": "topk(5, sum(rate(app_errors_total[5m])) by (error_type))",
      "format": "table",
      "instant": true
    }
  ],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "excludeByName": {
          "Time": true,
          "__name__": true,
          "job": true,
          "instance": true
        },
        "renameByName": {
          "error_type": "Error Type",
          "Value": "Rate (errors/sec)"
        }
      }
    }
  ]
}
```

## Performance Monitoring

### SLO/SLI Definition

**Service Level Objectives (SLOs)**:

1. **Availability SLO**: 99.9% uptime
   - SLI: `(total_requests - failed_requests) / total_requests`
   - Measurement: 30-day rolling window

2. **Latency SLO**: 95th percentile < 500ms
   - SLI: `histogram_quantile(0.95, response_time)`
   - Measurement: 5-minute rolling window

3. **Throughput SLO**: > 1000 messages/second
   - SLI: `rate(messages_total[1m])`
   - Measurement: 1-minute rolling window

**Error Budget Tracking**:

```python
# error_budget.py
from datetime import datetime, timedelta
import requests

class ErrorBudgetTracker:
    def __init__(self, prometheus_url):
        self.prometheus_url = prometheus_url

    def calculate_error_budget(self, slo_target, time_window='30d'):
        """Calculate remaining error budget"""
        
        # Query for success rate
        success_rate_query = f"""
        (
            sum(rate(app_requests_total[{time_window}])) - 
            sum(rate(app_errors_total[{time_window}]))
        ) / sum(rate(app_requests_total[{time_window}]))
        """
        
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query",
            params={'query': success_rate_query}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['data']['result']:
                actual_success_rate = float(result['data']['result'][0]['value'][1])
                error_budget = actual_success_rate - slo_target
                return error_budget
        
        return None

    def get_error_budget_consumption(self, time_window='30d'):
        """Get error budget consumption over time"""
        
        query = f"""
        (
            1 - (
                sum(rate(app_requests_total[{time_window}])) - 
                sum(rate(app_errors_total[{time_window}]))
            ) / sum(rate(app_requests_total[{time_window}]))
        ) * 100
        """
        
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={
                'query': query,
                'start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'end': datetime.utcnow().isoformat(),
                'step': '1h'
            }
        )
        
        return response.json() if response.status_code == 200 else None
```

### Capacity Planning

```python
# capacity_planning.py
import numpy as np
from datetime import datetime, timedelta

class CapacityPlanner:
    def __init__(self, prometheus_url):
        self.prometheus_url = prometheus_url

    def analyze_traffic_patterns(self, days=30):
        """Analyze traffic patterns for capacity planning"""
        
        # Query for traffic patterns
        query = "rate(app_messages_total[1h])"
        
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={
                'query': query,
                'start': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'end': datetime.utcnow().isoformat(),
                'step': '1h'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            values = [float(point[1]) for point in data['data']['result'][0]['values']]
            
            return {
                'mean': np.mean(values),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99),
                'max': np.max(values),
                'trend': self._calculate_trend(values)
            }
        
        return None

    def _calculate_trend(self, values):
        """Calculate trend using linear regression"""
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        return slope

    def recommend_capacity(self, target_load_factor=0.7):
        """Recommend capacity based on current usage and trends"""
        
        patterns = self.analyze_traffic_patterns()
        if not patterns:
            return None
        
        # Calculate recommended capacity
        current_peak = patterns['p99']
        trend_factor = 1 + (patterns['trend'] * 30)  # 30-day projection
        
        recommended_capacity = (current_peak * trend_factor) / target_load_factor
        
        return {
            'current_peak': current_peak,
            'trend_factor': trend_factor,
            'recommended_capacity': recommended_capacity,
            'target_load_factor': target_load_factor
        }
```

## Operational Intelligence

### Anomaly Detection

```python
# anomaly_detection.py
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self, prometheus_url):
        self.prometheus_url = prometheus_url

    def detect_anomalies(self, metric_name, time_window='1h', threshold=3):
        """Detect anomalies using statistical methods"""
        
        # Query historical data
        query = f"rate({metric_name}[5m])"
        
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={
                'query': query,
                'start': (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                'end': datetime.utcnow().isoformat(),
                'step': '5m'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            values = [float(point[1]) for point in data['data']['result'][0]['values']]
            
            # Calculate statistics
            mean = np.mean(values)
            std = np.std(values)
            
            # Find anomalies (values beyond threshold standard deviations)
            anomalies = []
            for i, value in enumerate(values):
                z_score = abs((value - mean) / std)
                if z_score > threshold:
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'z_score': z_score,
                        'timestamp': data['data']['result'][0]['values'][i][0]
                    })
            
            return anomalies
        
        return []

    def alert_on_anomaly(self, metric_name, anomaly_data):
        """Send alert when anomaly is detected"""
        
        if anomaly_data:
            alert_message = {
                'title': f'Anomaly detected in {metric_name}',
                'description': f'Value: {anomaly_data["value"]}, Z-score: {anomaly_data["z_score"]:.2f}',
                'severity': 'warning',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to alerting system
            self._send_alert(alert_message)
```

### Predictive Monitoring

```python
# predictive_monitoring.py
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd

class PredictiveMonitor:
    def __init__(self, prometheus_url):
        self.prometheus_url = prometheus_url
        self.model = LinearRegression()
        self.scaler = StandardScaler()

    def train_model(self, metric_name, days=30):
        """Train predictive model for a metric"""
        
        # Query historical data
        query = f"rate({metric_name}[5m])"
        
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={
                'query': query,
                'start': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'end': datetime.utcnow().isoformat(),
                'step': '5m'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            values = [float(point[1]) for point in data['data']['result'][0]['values']]
            
            # Create features (time-based)
            timestamps = [point[0] for point in data['data']['result'][0]['values']]
            df = pd.DataFrame({
                'timestamp': timestamps,
                'value': values
            })
            
            # Add time-based features
            df['hour'] = pd.to_datetime(df['timestamp'], unit='s').dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp'], unit='s').dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Prepare training data
            X = df[['hour', 'day_of_week', 'is_weekend']].values
            y = df['value'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            return True
        
        return False

    def predict_next_hour(self, metric_name):
        """Predict metric value for the next hour"""
        
        # Get current time features
        now = datetime.utcnow()
        next_hour = now + timedelta(hours=1)
        
        features = np.array([[
            next_hour.hour,
            next_hour.weekday(),
            1 if next_hour.weekday() in [5, 6] else 0
        ]])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Make prediction
        prediction = self.model.predict(features_scaled)[0]
        
        return {
            'metric': metric_name,
            'predicted_value': prediction,
            'prediction_time': next_hour.isoformat(),
            'confidence': self._calculate_confidence()
        }

    def _calculate_confidence(self):
        """Calculate prediction confidence (simplified)"""
        # In a real implementation, this would use model uncertainty
        return 0.85
```

This comprehensive observability guide provides the foundation for building a robust monitoring and alerting system. The combination of metrics, logging, and tracing enables complete visibility into system behavior, while automated alerting and incident response ensure rapid issue resolution and minimal user impact.
