# Shop Sites Dockerfile
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

EXPOSE 7878

ENV PORT=7878

CMD ["npm", "start"]
