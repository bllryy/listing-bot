# Multi-stage build for Listing Bot project
# Stage 1: Base Python image for bot services
FROM python:3.11-slim as bot-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy all Python service requirements
COPY ai_api/requirements.txt ai_requirements.txt
COPY listing-bot/requirements.txt bot_requirements.txt
COPY logger-site/ logger_requirements.txt 2>/dev/null || true

# Install Python dependencies
RUN pip install --no-cache-dir -r ai_requirements.txt && \
    pip install --no-cache-dir -r bot_requirements.txt && \
    pip install --no-cache-dir quart

# Stage 2: Node builder for React apps
FROM node:18-alpine as node-builder

WORKDIR /app

# Copy package files for all dashboards
COPY listing-bot-dashboard/package.json ./listing-bot-dashboard/
COPY seller_dashboard/package.json ./seller_dashboard/
COPY shop-sites/package.json ./shop-sites/

# Install dependencies for each dashboard
RUN cd listing-bot-dashboard && npm ci && npm run build && \
    cd ../seller_dashboard && npm ci && npm run build && \
    cd ../shop-sites && npm ci && npm run build

# Stage 3: Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for running React/Express servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=bot-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy project files
COPY . .

# Copy built React apps
COPY --from=node-builder /app/listing-bot-dashboard/build ./listing-bot-dashboard/build
COPY --from=node-builder /app/seller_dashboard/build ./seller_dashboard/build
COPY --from=node-builder /app/shop-sites/build ./shop-sites/build

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Listing Bot services..."\n\
\n\
# Start parent API\n\
echo "Starting parent API..."\n\
cd /app/parent_api\n\
python -m uvicorn api:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Start AI API\n\
echo "Starting AI API..."\n\
cd /app/ai_api\n\
python -m uvicorn main:app --host 0.0.0.0 --port 8001 &\n\
\n\
# Start listing bot\n\
echo "Starting listing bot..."\n\
cd /app/listing-bot\n\
python main.py &\n\
\n\
# Start logger site\n\
echo "Starting logger site..."\n\
cd /app/logger-site\n\
python main.py &\n\
\n\
# Keep container running\n\
wait\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 3000 3001 3002 8000 8001 8002 8003

CMD ["/app/entrypoint.sh"]
