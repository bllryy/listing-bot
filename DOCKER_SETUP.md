# Docker Setup Guide for Listing Bot Project

This project has been configured to run in Docker containers for easy deployment on macOS and servers.

## Prerequisites

- Docker Desktop (Mac): https://www.docker.com/products/docker-desktop
- For Linux servers: `sudo apt-get install docker.io docker-compose`

## Quick Start

### Build and run all services with Docker Compose

```bash
# Navigate to project root
cd /path/to/Listing-Bot

# Build all Docker images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Services

The docker-compose configuration includes:

- **parent-api** (port 8000): Main gateway/coordination API
- **ai-api** (port 8001): AI/ML API service
- **listing-bot** (port 8002): Main Discord bot
- **logger-site** (port 8003): Logging/dashboard service
- **listing-bot-dashboard** (port 3000): React dashboard frontend
- **seller-dashboard** (port 3001): Seller dashboard frontend
- **shop-sites** (port 7878): Shop/marketplace frontend
- **redis** (port 6379): Cache/session storage

## Individual Service Commands

### Build a specific service

```bash
docker-compose build listing-bot
docker-compose build ai-api
docker-compose build parent-api
```

### Run a specific service

```bash
docker-compose up -d listing-bot
docker-compose up -d ai-api
```

### View logs for a service

```bash
docker-compose logs -f listing-bot
docker-compose logs -f parent-api
```

## Environment Variables

Create a `.env` file in the project root for environment-specific configuration:

```bash
# Example .env
API_KEY=your_api_key_here
INTERNAL_API_KEY=your_internal_key_here
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
```

Each service will inherit these variables. You can also add service-specific env vars in `docker-compose.yml`.

## Building Individual Dockerfiles

If you want more control, you can build individual services:

```bash
# Build specific services
docker build -t listing-bot:latest -f listing-bot/Dockerfile listing-bot/
docker build -t ai-api:latest -f ai_api/Dockerfile ai_api/
docker build -t listing-bot-dashboard:latest -f listing-bot-dashboard/Dockerfile listing-bot-dashboard/

# Run them individually
docker run -p 8002:8002 listing-bot:latest
docker run -p 8001:8001 ai-api:latest
docker run -p 3000:3000 listing-bot-dashboard:latest
```

## Troubleshooting

### Port conflicts

If you get "port already in use" errors, either:
1. Stop the conflicting service
2. Change the port mapping in `docker-compose.yml` (e.g., `"8001:8001"` → `"8011:8001"`)

### Service won't start

```bash
# Check logs
docker-compose logs service-name

# Restart a service
docker-compose restart service-name
```

### Clean rebuild

```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild everything
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Permission issues on Linux

```bash
# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

## Development Mode

For development, you can modify docker-compose.yml to mount source directories:

```yaml
services:
  listing-bot:
    volumes:
      - ./listing-bot:/app  # This allows live code updates
```

Then restart the service:
```bash
docker-compose restart listing-bot
```

## Production Deployment

For production on a server:

1. Ensure Docker and Docker Compose are installed
2. Clone the repository
3. Create a `.env` file with production values
4. Run: `docker-compose up -d`
5. Services will restart automatically if they crash (due to `restart: unless-stopped`)

## Monitoring

View real-time resource usage:
```bash
docker stats
```

View all running containers:
```bash
docker ps
```

## Cleanup

Remove stopped containers and unused images:
```bash
docker system prune -a
```

---

For more information, see the main [README.md](README.md)
