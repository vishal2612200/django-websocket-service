#!/usr/bin/env bash
set -euo pipefail

# Blue/Green Deployment Promotion Script
# This script performs automated blue/green deployment promotion
# by building and deploying the next environment, validating readiness,
# and switching traffic with zero-downtime deployment.

COLOR_FILE=docker/traefik/dynamic/active.yml
CURRENT=$(grep -q 'django-blue' "$COLOR_FILE" && echo blue || echo green)
NEXT=$([ "$CURRENT" = blue ] && echo green || echo blue)

echo "Deployment Promotion: Current=$CURRENT, Target=$NEXT"

# Build and deploy the next environment
echo "Building and deploying $NEXT environment..."

# Send deployment start notification to all active sessions
echo "Sending deployment start notification..."
docker compose -f docker/compose.yml exec -T app_$CURRENT python manage.py broadcast_message \
  "Deployment in progress: Switching from $CURRENT to $NEXT environment" \
  --title "Deployment Started" \
  --level warning

docker compose -f docker/compose.yml build app_$NEXT
docker compose -f docker/compose.yml up -d app_$NEXT redis_$NEXT

# Validate readiness of the new environment
echo "Validating $NEXT environment readiness..."
docker compose -f docker/compose.yml exec -T app_$NEXT sh -lc '
  for i in $(seq 1 30); do
    if curl -fsS http://localhost:8000/readyz >/dev/null; then exit 0; fi
    sleep 1
  done
  exit 1
'

# Execute smoke test against the new environment
# Target localhost:8000 to validate the specific container instance
echo "Executing smoke test against $NEXT environment..."
docker compose -f docker/compose.yml exec -T app_$NEXT python3 /app/scripts/smoke_ws.py --host localhost:8000 --path /ws/chat/ --expect 1 || {
  echo "Smoke test validation failed for $NEXT environment" >&2
  exit 1
}

# Switch traffic to the new environment
echo "Switching traffic to $NEXT environment..."

# Send traffic switch notification
echo "Sending traffic switch notification..."
docker compose -f docker/compose.yml exec -T app_$NEXT python manage.py broadcast_message \
  "Traffic switched to $NEXT environment. New deployment is now active!" \
  --title "Deployment Complete" \
  --level success

cp "docker/traefik/dynamic/$NEXT.yml" "$COLOR_FILE"
# Allow Traefik to detect configuration change
sleep 1

# Gracefully terminate the previous environment
echo "Gracefully terminating $CURRENT environment..."

# Send final notification
echo "Sending deployment completion notification..."
docker compose -f docker/compose.yml exec -T app_$NEXT python manage.py broadcast_message \
  "Deployment completed successfully! $NEXT environment is now active and $CURRENT environment has been terminated." \
  --title "Deployment Finalized" \
  --level success

docker compose -f docker/compose.yml stop app_$CURRENT

echo "Deployment promotion completed successfully: $NEXT environment is now active."
