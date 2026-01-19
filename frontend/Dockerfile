# =============================================================================
# DOCKERFILE FOR CASINO CAPSTONE FRONTEND
# =============================================================================
# This Dockerfile uses a multi-stage build to create an optimized production
# image for the React frontend application.
#
# Stages:
#   1. BUILD: Install dependencies and build the production bundle
#   2. PRODUCTION: Serve the static files with nginx
#
# Why multi-stage?
#   - Build stage has Node.js and all dev dependencies (~1GB)
#   - Production stage only has nginx and static files (~25MB)
#   - Smaller images = faster deployments and less attack surface
#
# Why nginx?
#   - Industry standard for serving static files
#   - Extremely fast and low resource usage
#   - Built-in gzip compression
#   - Easy configuration for SPA routing
#
# To build manually:
#   $ docker build -t casino-frontend .
#
# To run manually:
#   $ docker run -p 5173:80 casino-frontend
# =============================================================================


# =============================================================================
# STAGE 1: BUILD
# =============================================================================
# This stage installs dependencies and builds the production bundle.

# Use Node.js 20 LTS on Alpine Linux (small base image)
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install dependencies first (for better Docker caching)
# Copy only package files first - these change less often than source code
# If package.json hasn't changed, Docker will use cached node_modules
COPY package.json package-lock.json* ./

# Install dependencies
# --frozen-lockfile: Fail if package-lock.json is out of sync (reproducible builds)
# Using npm ci instead of npm install for faster, more reliable installs
RUN npm ci

# Copy the rest of the source code
# This is done after npm ci so code changes don't invalidate the dependency cache
COPY . .

# Set build-time environment variables
# These are embedded into the built JavaScript bundle
# ARG allows passing values at build time: docker build --build-arg VITE_API_URL=...
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

# Build the production bundle
# This runs: tsc && vite build
# Output goes to /app/dist directory
RUN npm run build


# =============================================================================
# STAGE 2: PRODUCTION
# =============================================================================
# This stage creates the final production image with nginx.

# Use nginx on Alpine Linux (very small: ~25MB)
FROM nginx:alpine AS production

# Add labels for image metadata
LABEL maintainer="CS Capstone Team"
LABEL description="Casino Capstone React Frontend"
LABEL version="1.0"

# Remove default nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy our custom nginx configuration
# This configures SPA routing and security headers
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files from the builder stage
# This is the only thing we need from the build - no Node.js runtime required!
COPY --from=builder /app/dist /usr/share/nginx/html

# Create a non-root user for security (optional but recommended)
# nginx runs as 'nginx' user by default in the official image

# Expose port 80 (standard HTTP port)
# nginx listens on this port inside the container
EXPOSE 80

# Health check to verify nginx is serving content
# Checks if the index.html is accessible
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx in the foreground
# -g 'daemon off;' keeps nginx in the foreground so Docker can track the process
CMD ["nginx", "-g", "daemon off;"]