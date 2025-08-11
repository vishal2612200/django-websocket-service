#!/bin/bash

# Script to manually import Grafana dashboard
# This is a fallback method if automatic provisioning doesn't work

set -e

echo " Importing Grafana dashboard..."

# Check if Grafana is running
if ! curl -s http://localhost:3000/api/health > /dev/null; then
    echo " Grafana is not running. Please start the monitoring stack first:"
    echo "   ./scripts/monitoring.sh start"
    exit 1
fi

# Import the comprehensive dashboard
echo " Importing WebSocket Comprehensive Dashboard..."
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d @docker/simple-grafana-provisioning/dashboards/websocket-comprehensive-dashboard.json \
  http://admin:admin123@localhost:3000/api/dashboards/db

echo ""
echo " Dashboard import completed!"
echo ""
echo " Access your dashboard at:"
echo "   http://localhost:3000"
echo ""
echo " Login credentials: admin/admin123"
echo ""
echo " The dashboard should now be available in your Grafana instance."
