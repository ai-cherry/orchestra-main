# Build stage
FROM node:18.20.1-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:1.25.5-alpine

RUN addgroup -S nginx && adduser -S -G nginx nginx

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set user for nginx
USER nginx

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


