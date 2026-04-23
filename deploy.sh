#!/bin/bash
# deploy.sh
SERVICE=$1

if [ -z "$SERVICE" ]; then
  echo "Usage: $0 <service_name>"
  exit 1
fi

echo "Starting deployment for $SERVICE..."

# 1. Find the currently running container for this service
OLD_CONTAINER=$(docker compose ps -q $SERVICE | head -n 1)

if [ -z "$OLD_CONTAINER" ]; then
  echo "No existing container found for $SERVICE. Starting normally."
  docker compose up -d $SERVICE
  exit 0
fi

echo "Old container ID: $OLD_CONTAINER"

# 2. Scale up to 2 containers so a new one starts alongside the old one
docker compose up -d --scale $SERVICE=2 --no-recreate $SERVICE

# 3. Find the ID of the new container
NEW_CONTAINER=$(docker compose ps -q $SERVICE | grep -v "$OLD_CONTAINER" | head -n 1)
echo "New container ID: $NEW_CONTAINER"

# 4. Wait up to 60 seconds for the new container to become healthy
TIMEOUT=60
while [ $TIMEOUT -gt 0 ]; do
  HEALTH=$(docker inspect --format='{{json .State.Health.Status}}' $NEW_CONTAINER)
  
  if [ "$HEALTH" == '"healthy"' ]; then
    echo "New container is healthy! Tearing down the old container."
    docker stop $OLD_CONTAINER
    docker rm $OLD_CONTAINER
    # Tell docker-compose we are back to 1 instance so it doesn't get confused later
    docker compose up -d --scale $SERVICE=1 --no-recreate $SERVICE
    exit 0
  fi
  
  echo "Waiting for healthcheck... ($TIMEOUT seconds left)"
  sleep 5
  TIMEOUT=$((TIMEOUT-5))
done

# 5. If we get here, it means we timed out!
echo "ERROR: New container failed to become healthy within 60 seconds."
echo "Aborting deployment. Tearing down the new container and leaving the old one untouched."
docker stop $NEW_CONTAINER
docker rm $NEW_CONTAINER
docker compose up -d --scale $SERVICE=1 --no-recreate $SERVICE
exit 1
