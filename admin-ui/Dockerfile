# Dockerfile for Admin UI (React + Vite + MUI)
# Supports both development (hot reload) and production (static build)

FROM node:18-slim

# Set working directory
WORKDIR /app

# Install dependencies first for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Expose port for Vite dev server or production server
EXPOSE 3000

# Default command: start dev server (can override with 'npm run build' for prod)
CMD ["npm", "start"]
