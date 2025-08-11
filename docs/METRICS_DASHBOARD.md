# WebSocket Metrics Dashboard

## Overview

The WebSocket Metrics Dashboard provides real-time visibility into the core performance metrics of your WebSocket application. It displays four essential metrics directly in the UI, making it easy to monitor system activity at a glance.

## Features

### 🎯 Real-Time Metrics Display
- **Live Updates**: Metrics refresh automatically every 30 seconds for stability
- **Manual Refresh**: Click the refresh button for immediate updates
- **Simple Layout**: Clean, focused display of essential metrics

### 📊 Essential Metrics Coverage

#### Connection Metrics
- **Total Connections**: Total connections opened since server restart
- **Active Connections**: Current number of active WebSocket connections

#### Message Metrics
- **Messages Received**: Total messages received from clients
- **Messages Sent**: Total messages sent by server to clients

### 🎨 Visual Design

#### Metric Cards
Each metric is displayed in an individual card with:
- **Icon**: Visual representation of the metric type
- **Value**: Formatted number with appropriate units
- **Tooltip**: Detailed description on hover

#### Color Coding
- **Blue**: Primary connection metrics
- **Green**: Active connections
- **Purple**: Message sent metrics
- **Orange**: Message received metrics

## Usage

### Accessing the Dashboard

1. **Start the Application**:
   ```bash
   make run
   ```

2. **Open the UI**:
   Navigate to `http://localhost:8000` in your browser

3. **Locate the Dashboard**:
   The WebSocket Metrics Dashboard appears in the sidebar on the right side of the interface

### Interacting with the Dashboard

#### Basic View
- **View Metrics**: All key metrics are displayed in a grid layout
- **Status Overview**: Quick health indicators at the top
- **Real-time Updates**: Metrics update automatically every 5 seconds



#### Manual Refresh
- **Refresh Button**: Click the refresh icon for immediate updates
- **Force Update**: Useful when you want to see the latest metrics immediately

## Technical Implementation

### Metrics Source
The dashboard fetches metrics from the `/metrics` endpoint, which provides Prometheus-formatted metrics:

```bash
# Example metrics endpoint response
app_active_connections 5
app_messages_total 1234
app_messages_sent 1234
app_errors_total 0
app_connections_opened_total 10
app_connections_closed_total 5
app_sessions_tracked 3
```

### Component Architecture

#### MetricsDashboard Component
- **Location**: `ui/src/components/MetricsDashboard.tsx`
- **Props**: 
  - `metrics`: Raw metrics data from server
  - `derived`: Calculated metrics (averages, rates)
  - `expanded`: Whether to show detailed view
  - `onRefresh`: Manual refresh callback
  - `onToggleExpanded`: Toggle detailed view callback

#### MetricCard Component
- **Reusable**: Individual metric display component
- **Features**: Icons, trends, progress bars, tooltips
- **Responsive**: Adapts to different screen sizes

### Data Flow

1. **Polling**: `useMetrics` hook polls `/metrics` endpoint every 5 seconds
2. **Parsing**: Raw Prometheus text is parsed into structured data
3. **Calculation**: Derived metrics are calculated (rates, averages)
4. **Display**: Metrics are rendered in the dashboard component
5. **Updates**: UI updates automatically as new data arrives

## Configuration

### Polling Interval
The metrics refresh interval can be configured in `ui/src/config/api.ts`:

```typescript
export function getMetricsPollingInterval(): number {
  return 30000; // 30 seconds for stable metrics
}
```

## Testing

### Manual Testing
1. **Start the application**: `make run`
2. **Open the UI**: Navigate to `http://localhost:8000`
3. **Verify metrics**: Check that metrics are displaying and updating
4. **Test interactions**: Try refresh and expand/collapse buttons

### Automated Testing
Run the metrics test script:

```bash
python scripts/test_metrics_ui.py
```

This script will:
- Fetch metrics from the `/metrics` endpoint
- Validate that all expected metrics are present
- Display a summary of current values
- Check for any issues with metric collection

## Troubleshooting

### Common Issues

#### Metrics Not Updating
- **Check Network**: Ensure the application is running and accessible
- **Verify Endpoint**: Confirm `/metrics` endpoint returns data
- **Browser Console**: Check for JavaScript errors in browser dev tools

#### Missing Metrics
- **Server Logs**: Check Django application logs for errors
- **Prometheus Client**: Verify Prometheus client is properly configured
- **Metric Names**: Ensure metric names match expected format

#### Performance Issues
- **Polling Interval**: Consider increasing polling interval for high-traffic systems
- **Browser Performance**: Monitor browser memory usage with many metrics
- **Network Load**: Reduce polling frequency if network bandwidth is limited

### Debug Mode
Enable debug logging in the browser console:

```javascript
// In browser console
localStorage.setItem('debug', 'metrics:*')
```

## Integration with Monitoring

### Prometheus Integration
The metrics endpoint is compatible with Prometheus scraping:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'websocket-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards
Use the metrics in Grafana dashboards for advanced visualization and alerting.

### Alerting
Set up alerts based on metric thresholds:
- High error rates
- Low connection success rates
- High connection utilization
- Missing metrics

## Future Enhancements

### Planned Features
- **Historical Data**: Show metric trends over time
- **Custom Thresholds**: User-configurable warning/error levels
- **Metric Filtering**: Show/hide specific metrics
- **Export Functionality**: Export metrics data
- **Alert Integration**: Display active alerts in the dashboard

### Performance Optimizations
- **WebSocket Metrics**: Use WebSocket for real-time metric updates
- **Metric Aggregation**: Server-side metric aggregation
- **Caching**: Client-side metric caching
- **Compression**: Compress metric data for faster transmission
