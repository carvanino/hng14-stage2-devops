# --- STAGE 1: Builder ---
FROM node:18-alpine3.21 AS builder
WORKDIR /app
# Copy only package files first to leverage Docker caching
COPY package*.json ./
# Use npm ci for a clean, exact installation
RUN npm ci

# --- STAGE 2: Runtime ---
FROM node:18-alpine3.21
WORKDIR /app

# Upgrade OS packages to pick up any security patches (e.g. libcrypto3, libssl3)
RUN apk upgrade --no-cache

COPY --from=builder /app/node_modules ./node_modules
# Copy the rest of the application code
COPY --chown=node:node . .

# Switch to the built-in non-root user for security
USER node

EXPOSE 3000

# Healthcheck to ensure the container is actually running properly
HEALTHCHECK CMD node -e "require('http').get('http://localhost:3000/', r => process.exit(r.statusCode < 400 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]
