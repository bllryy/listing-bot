# 🐳 Listing Bot - Docker Setup Complete!

Your project is now fully configured for Docker deployment on macOS and servers.

## ✅ What Was Created

### 🔧 Configuration Files (5)
- **docker-compose.yml** - Main orchestration (8 services, health checks, volume management)
- **docker-compose.prod.yml** - Production overrides with resource limits
- **Dockerfile** - Main multi-stage build
- **Dockerfile.parent** - Parent API service
- **.dockerignore** - Optimized build context

### 📦 Service Dockerfiles (6)
- ai_api/Dockerfile - AI/ML API
- listing-bot/Dockerfile - Discord bot
- logger-site/Dockerfile - Logging service
- listing-bot-dashboard/Dockerfile - Admin dashboard
- seller_dashboard/Dockerfile - Seller panel
- shop-sites/Dockerfile - Marketplace

### 🛠️ Helper Scripts (2)
- **docker-setup.sh** - Prerequisites checker and initial setup
- **docker-manage.sh** - CLI tool for managing containers

### 📖 Documentation (2)
- **DOCKER_QUICKSTART.md** - Quick reference guide
- **DOCKER_SETUP.md** - Comprehensive guide with examples

### 🔐 Environment
- **.env.example** - Template for configuration

---

## 🚀 Getting Started

### Option A: Using Setup Script (Recommended)
```bash
cd /Users/lily/projects/Listing-Bot
./docker-setup.sh      # Checks prerequisites and creates .env
nano .env              # Configure your settings
./docker-manage.sh build   # Build all images
./docker-manage.sh up      # Start all services
```

### Option B: Manual Docker Compose
```bash
cd /Users/lily/projects/Listing-Bot
cp .env.example .env
# Edit .env with your configuration
docker-compose build   # Build (takes 5-10 min first time)
docker-compose up -d   # Start in background
docker-compose logs -f # View logs
```

---

## 📋 Available Services

| Service | Port | Type | Purpose |
|---------|------|------|---------|
| Parent API | 8000 | Python (FastAPI) | Main gateway |
| AI API | 8001 | Python (FastAPI) | AI/ML endpoints |
| Discord Bot | 8002 | Python | Main bot service |
| Logger Site | 8003 | Python (Quart) | Logging & monitoring |
| Dashboard | 3000 | React | Admin dashboard |
| Seller Dashboard | 3001 | React | Seller panel |
| Shop Sites | 7878 | React | Marketplace |
| Redis | 6379 | Cache | Session/cache storage |

---

## 🎯 Common Commands

### Using docker-manage.sh Script
```bash
./docker-manage.sh build                    # Build all
./docker-manage.sh up                       # Start all
./docker-manage.sh down                     # Stop all
./docker-manage.sh logs [service]          # View logs
./docker-manage.sh restart [service]       # Restart
./docker-manage.sh status                  # Show status
./docker-manage.sh help                    # Help menu
```

### Using Docker Compose Directly
```bash
docker-compose build                        # Build all
docker-compose up -d                        # Start all (daemon)
docker-compose down                         # Stop all
docker-compose logs -f [service]           # View logs
docker-compose restart [service]           # Restart
docker-compose ps                          # List containers
```

### Production Deployment
```bash
docker-compose -f docker-compose.yml \
  -f docker-compose.prod.yml up -d
```

---

## 🔑 Configuration

Edit `.env` file to set:
- API keys and secrets
- Discord credentials
- Port numbers (optional)
- Environment mode (dev/prod)

Key environment variables:
```bash
API_KEY=your_api_key
INTERNAL_API_KEY=your_internal_key
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
GOOGLE_AI_API_KEY=your_ai_key (if using AI features)
```

---

## ⚙️ Customization

### Change Ports
Edit `.env` or `docker-compose.yml`:
```yaml
services:
  parent-api:
    ports:
      - "8000:8000"  # Change first number to use different port
```

### Add Environment Variables
```yaml
environment:
  - NEW_VAR=value
  - ANOTHER_VAR=value
```

### Mount Additional Volumes
```yaml
volumes:
  - ./your/path:/container/path
```

---

## 🐛 Troubleshooting

### Port Conflicts
```bash
lsof -i :8000           # Find process using port
kill -9 <PID>           # Kill the process
# OR change port in .env
```

### Service Won't Start
```bash
docker-compose logs <service>   # Check error logs
docker-compose restart <service>
```

### Clear Everything & Rebuild
```bash
docker-compose down -v          # Stop & remove volumes
docker system prune -a          # Clean up unused images
docker-compose build --no-cache # Rebuild
docker-compose up               # Start fresh
```

---

## 📚 Documentation

- **Quick Start**: DOCKER_QUICKSTART.md
- **Full Guide**: DOCKER_SETUP.md
- **Docker Docs**: https://docs.docker.com/

---

## 💡 Pro Tips

1. **Keep Docker Running** - Leave Docker Desktop open for best performance
2. **First Build Takes Time** - Multi-service builds can take 5-10 minutes
3. **Use Health Checks** - Services auto-restart if they fail
4. **Volume Mounts** - Keep code mounted for live development
5. **Resource Limits** - Use prod override file to prevent resource exhaustion

---

## 🔍 Verify Installation

```bash
# Test Docker
docker --version
docker-compose --version
docker ps

# Test setup script
./docker-setup.sh

# View project structure
ls -la Docker* docker-* .dockerignore .env.example
```

---

## ✨ Next Steps

1. ✅ Prerequisites installed? (Docker Desktop on Mac)
2. ✅ Run: `./docker-setup.sh`
3. ✅ Configure: Edit `.env`
4. ✅ Build: `./docker-manage.sh build`
5. ✅ Start: `./docker-manage.sh up`
6. ✅ Access: http://localhost:3000 (dashboard)

---

**Questions?** Check the documentation files or run `./docker-manage.sh help`
