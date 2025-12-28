# Listing Bot Dashboard Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application
COPY . .

# Build React app
RUN npm run build

# Use lightweight Node server
EXPOSE 3000

CMD ["npm", "start"]
