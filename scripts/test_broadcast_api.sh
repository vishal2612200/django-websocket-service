#!/bin/bash

# Test script for broadcast message API
echo "🧪 Testing Broadcast Message API"
echo "================================="

# Test deployment start message
echo -e "\n📡 Sending deployment start message..."
curl -X POST http://localhost:8000/chat/api/broadcast/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Deployment in progress: Switching from blue to green environment",
    "title": "Deployment Started",
    "level": "warning"
  }'

echo -e "\n\n📡 Sending deployment complete message..."
curl -X POST http://localhost:8000/chat/api/broadcast/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Traffic switched to green environment. New deployment is now active!",
    "title": "Deployment Complete",
    "level": "success"
  }'

echo -e "\n\n📡 Sending system alert message..."
curl -X POST http://localhost:8000/chat/api/broadcast/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "High error rate detected. Investigating...",
    "title": "System Alert",
    "level": "error"
  }'

echo -e "\n\n📡 Sending maintenance notice..."
curl -X POST http://localhost:8000/chat/api/broadcast/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "System maintenance scheduled for tonight at 2 AM UTC",
    "title": "Maintenance Notice",
    "level": "info"
  }'

echo -e "\n\n🎉 Broadcast API test completed!"
echo "Check your WebSocket UI to see the broadcast messages appear."
