#!/bin/bash

# WebSocket Service Monitoring Infrastructure Setup Script
# This script initializes and configures the complete monitoring stack
# including Prometheus, Grafana, and Alertmanager for production-grade
# observability of the WebSocket service.

set -e

echo "Initializing WebSocket Service Monitoring Infrastructure..."

# Validate Docker runtime availability
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker runtime is not available or not running."
    echo "Please ensure Docker is installed and running before proceeding."
    exit 1
fi

# Create monitoring infrastructure directories
echo "Creating monitoring infrastructure directories..."
mkdir -p docker/grafana/provisioning/datasources
mkdir -p docker/grafana/provisioning/dashboards
mkdir -p docker/grafana/dashboards

# Initialize monitoring services
echo "Starting monitoring services..."
cd docker
docker compose -f monitoring-compose.yml up -d

# Allow services to initialize
echo "Waiting for monitoring services to initialize..."
sleep 10

# Validate service deployment status
echo "Validating monitoring service deployment status..."
docker compose -f monitoring-compose.yml ps

echo ""
echo "Monitoring infrastructure deployment completed successfully!"
echo ""
echo "Monitoring Service Access Information:"
echo "  • Grafana Dashboard:     http://localhost:3000 (admin/admin123)"
echo "  • Prometheus Metrics:    http://localhost:9090"
echo "  • Alertmanager Alerts:   http://localhost:9093"
echo ""
echo "Initial Setup Instructions:"
echo "1. Access Grafana at http://localhost:3000"
echo "2. Authenticate using admin/admin123"
echo "3. Verify Prometheus datasource is automatically configured"
echo "4. Navigate to the WebSocket service dashboard"
echo ""
echo "Configuration File Locations:"
echo "  • Prometheus Configuration: docker/prometheus.yml"
echo "  • Alert Rules Definition:   docker/alert_rules.yml"
echo "  • Alertmanager Config:      docker/alertmanager.yml"
echo "  • Grafana Dashboards:       docker/grafana/dashboards/"
echo ""
echo "Service Management Commands:"
echo "  Stop monitoring stack:     cd docker && docker compose -f monitoring-compose.yml down"
echo "  View service logs:         cd docker && docker compose -f monitoring-compose.yml logs -f"
echo "  Restart services:          cd docker && docker compose -f monitoring-compose.yml restart"
echo ""
echo "The monitoring infrastructure is now ready for production use."
echo "Review the dashboards to ensure proper metrics collection."
