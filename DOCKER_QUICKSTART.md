# Getting Started with Docker

Complete Docker setup has been configured for the Listing Bot project!

## 📋 Files Created

### Main Configuration Files
- **docker-compose.yml** - Orchestrates all 8 services with proper networking
- **Dockerfile** - Multi-stage build (main)
- **Dockerfile.parent** - Parent API service
- **.dockerignore** - Optimizes build context
- **.env.example** - Environment variables template

### Individual Service Dockerfiles
- **ai_api/Dockerfile** - AI API service
- **listing-bot/Dockerfile** - Discord bot
- **logger-site/Dockerfile** - Logger/logging service
- **listing-bot-dashboard/Dockerfile** - React dashboard
- **seller_dashboard/Dockerfile** - Seller dashboard
- **shop-sites/Dockerfile** - Shop/marketplace frontend

### Helper Scripts
- **docker-setup.sh** - Initial setup and prerequisite checker
- **docker-manage.sh** - Command-line tool for managing containers

### Documentation
- **DOCKER_SETUP.md** - Complete Docker guide with examples

## 🚀 Quick Start (5 minutes)

### Step 1: Initial Setup
```bash
cd /Users/lily/projects/Listing-Bot

# Run initial setup
./docker-setup.sh

# This will:
# - Check Docker prerequisites
# - Create .env file from template
# - Give you next steps
```

### Step 2: Configure Environment
```bash
# Edit the .env file with your configuration
nano .env  # or use your preferred editor

# At minimum, set:
# - API_KEY
# - DISCORD_CLIENT_ID
# - DISCORD_CLIENT_SECRET
# - GOOGLE_AI_API_KEY (if using AI features)
```

### Step 3: Build All Services
```bash
./docker-manage.sh build

# Or use docker-compose directly:
docker-compose build
```

### Step 4: Start All Services
```bash
./docker-manage.sh up

# Or use docker-compose directly:
docker-compose up -d

# View logs (keep running in terminal):
docker-compose logs -f
```

### Step 5: Access Your Services

| Service | URL | Purpose |
|---------|-----|---------|
| Parent API | http://localhost:8000 | Main gateway API |
| AI API | http://localhost:8001 | AI/ML endpoints |
| Bot | http://localhost:8002 | Discord bot |
| Logger | http://localhost:8003 | Logging/monitoring |
| Dashboard | http://localhost:3000 | Listing dashboard |
| Seller Dashboard | http://localhost:3001 | Seller dashboard |
| Shop Sites | http://localhost:7878 | Shop/marketplace |
| Redis | localhost:6379 | Cache/sessions |

## 📝 Useful Commands

### Using the Management Script
```bash
# Build all services
./docker-manage.sh build

# Build specific service
./docker-manage.sh build listing-bot

# Start all services
./docker-manage.sh up

# Start specific service
./docker-manage.sh up ai-api

# View logs for all
./docker-manage.sh logs

# View logs for specific service
./docker-manage.sh logs listing-bot

# Restart services
./docker-manage.sh restart

# Stop all services
./docker-manage.sh down

# Clean everything
./docker-manage.sh clean

# Show status
./docker-manage.sh status

# Help
./docker-manage.sh help
```

### Using Docker Compose Directly
```bash
# Build
docker-compose build

# Start (daemon)
docker-compose up -d

# Start (foreground with logs)
docker-compose up

# Stop
docker-compose down

# View logs
docker-compose logs -f

# View logs for one service
docker-compose logs -f listing-bot

# Restart
docker-compose restart

# Restart specific service
docker-compose restart parent-api

# Remove volumes (clean slate)
docker-compose down -v
```

## 🔧 Customizing Port Numbers

Edit `.env` file to change default ports:
```bash
PARENT_API_PORT=8000
AI_API_PORT=8001
BOT_PORT=8002
LOGGER_PORT=8003
DASHBOARD_PORT=3000
SELLER_DASHBOARD_PORT=3001
SHOP_PORT=7878
REDIS_PORT=6379
```

Or edit `docker-compose.yml` directly (ports section).

## 📦 Services Architecture

```
┌─────────────────────────────────────────────────┐
│          Listing Bot Platform                   │
├─────────────────────────────────────────────────┤
│  Frontends (React)                              │
│  ├─ Listing Bot Dashboard (port 3000)          │
│  ├─ Seller Dashboard (port 3001)               │
│  └─ Shop Sites (port 7878)                     │
├─────────────────────────────────────────────────┤
│  APIs (Python)                                  │
│  ├─ Parent API (port 8000) - Gateway           │
│  ├─ AI API (port 8001) - AI/ML                 │
│  └─ Logger (port 8003) - Monitoring            │
├─────────────────────────────────────────────────┤
│  Bot                                            │
│  ├─ Discord Bot (port 8002)                    │
├─────────────────────────────────────────────────┤
│  Infrastructure                                 │
│  └─ Redis (port 6379) - Cache/Sessions        │
└─────────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# List what's using a port (macOS)
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env or docker-compose.yml
```

### Service Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Full rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Docker Daemon Not Running
```bash
# On macOS, open Docker Desktop or run:
open /Applications/Docker.app
```

### Out of Disk Space
```bash
# Clean up Docker
docker system prune -a

# Remove dangling volumes
docker volume prune
```

## 📈 Performance Tips

1. **First Build Takes Longer** - Building all images may take 5-10 minutes
2. **Volume Mounts Affect Speed** - Remove unnecessary mounts in docker-compose.yml
3. **Keep Services Updated** - Rebuild periodically:
   ```bash
   docker-compose build --no-cache
   ```

## 🔐 Production Deployment

For production servers:

1. Use environment-specific .env files:
   ```bash
   cp .env.example .env.production
   # Edit with production values
   ```

2. Use docker-compose with specific file:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. Set resource limits in docker-compose.yml:
   ```yaml
   services:
     parent-api:
       deploy:
         resources:
           limits:
             cpus: '0.5'
             memory: 512M
   ```

4. Use health checks (already configured) to auto-restart failed services

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- Full guide: [DOCKER_SETUP.md](DOCKER_SETUP.md)

## ❓ Need Help?

1. Check logs: `./docker-manage.sh logs`
2. Check status: `./docker-manage.sh status`
3. Review DOCKER_SETUP.md for comprehensive guide
4. Run: `./docker-manage.sh help` for command help

---

**Ready to go!** Start with: `./docker-setup.sh`
