# --- STAGE 1: Builder ---
FROM node:18-alpine AS builder
WORKDIR /app
# Copy only package files first to leverage Docker caching
COPY package*.json ./
# Use npm ci for a clean, exact installation
RUN npm ci

# --- STAGE 2: Runtime ---
FROM node:18-alpine
WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /app/node_modules ./node_modules
# Copy the rest of the application code
COPY --chown=node:node . .

# Switch to the built-in non-root user for security
USER node

EXPOSE 3000

# Healthcheck to ensure the container is actually running properly
HEALTHCHECK CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "app.js"]
