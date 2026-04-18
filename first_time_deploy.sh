#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/root/Ayush_Project"
REPO_URL="https://github.com/neerajdangii/Ayush_Project.git"

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
else
  echo "Error: neither docker-compose nor docker compose is available."
  exit 1
fi

echo "Starting first-time deployment..."

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "Cloning repository into $PROJECT_DIR..."
  git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

if [ ! -f .env.prod ]; then
  echo "Error: $PROJECT_DIR/.env.prod not found."
  exit 1
fi

if [ ! -f .env ]; then
  echo "Creating .env from .env.prod for Docker Compose variable substitution..."
  cp .env.prod .env
fi

echo "Ensuring .env matches .env.prod..."
cp .env.prod .env

echo "Stopping any existing containers without removing volumes..."
$COMPOSE_CMD down || true

echo "Building and starting containers..."
$COMPOSE_CMD up -d --build

echo "Container status:"
$COMPOSE_CMD ps

echo "Recent web logs:"
$COMPOSE_CMD logs --tail=50 web

echo
echo "First-time deployment complete."
echo "Next steps:"
echo "1. Create admin user: $COMPOSE_CMD exec web python manage.py createsuperuser"
echo "2. Open: http://your-vps-ip:8000/accounts/login/"
