# Multi-stage Dockerfile for Pulumi Migration Framework
# Optimized for performance and minimal image size

# Stage 1: Builder
FROM node:18-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git \
    curl

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY src/ ./src/
COPY index.ts ./

# Build TypeScript
RUN npm run build

# Remove dev dependencies and source files
RUN rm -rf src/ *.ts tsconfig.json

# Stage 2: Runtime
FROM node:18-alpine AS runtime

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# Install Pulumi CLI
RUN curl -fsSL https://get.pulumi.com | sh
ENV PATH="/root/.pulumi/bin:${PATH}"

# Create non-root user for security
RUN addgroup -g 1001 -S pulumi && \
    adduser -u 1001 -S pulumi -G pulumi

# Set working directory
WORKDIR /app

# Copy built application from builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist

# Copy configuration files
COPY Pulumi*.yaml ./

# Create necessary directories
RUN mkdir -p /app/.pulumi-migration/reports && \
    chown -R pulumi:pulumi /app

# Switch to non-root user
USER pulumi

# Set environment variables
ENV NODE_ENV=production \
    PULUMI_SKIP_UPDATE_CHECK=true \
    PULUMI_DISABLE_AUTOMATIC_PLUGIN_ACQUISITION=false \
    NODE_OPTIONS="--max-old-space-size=2048"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "console.log('OK')" || exit 1

# Default command
ENTRYPOINT ["node", "dist/index.js"]
CMD ["--help"]

# Labels for metadata
LABEL maintainer="Pulumi Migration Framework" \
      version="1.0.0" \
      description="Infrastructure migration framework for Pulumi" \
      org.opencontainers.image.source="https://github.com/your-org/pulumi-migration"