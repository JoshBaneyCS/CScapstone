# =============================================================================
# ALL-IN-ONE DOCKERFILE - Casino Capstone
# =============================================================================
# Bundles: Go backend, Blackjack API, Poker API, Frontend (static), Nginx
# Uses supervisord to manage all processes.
# No NoVNC — game runs as WASM in the browser.
#
# Build:  docker build -t capstone .
# Run:    docker run -p 80:80 -e DATABASE_URL=... -e JWT_SECRET=... capstone
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build Go backend
# ---------------------------------------------------------------------------
FROM golang:1.21-alpine AS go-builder

WORKDIR /build
COPY backend/go.mod backend/go.sum ./
RUN go mod download
COPY backend/main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o casino-backend .

# ---------------------------------------------------------------------------
# Stage 2: Build frontend
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 3: Final all-in-one image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TEMPLATE_PATH=/app/backend/templates

# System packages (no VNC, no X11)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies - Blackjack & Poker APIs
COPY dev-testing/blackjack-api/requirements.txt /tmp/blackjack-requirements.txt
RUN pip install --no-cache-dir -r /tmp/blackjack-requirements.txt

# Go backend binary + assets
COPY --from=go-builder /build/casino-backend /app/backend/casino-backend
COPY backend/templates /app/backend/templates
COPY backend/static /app/backend/static

# Blackjack API source
COPY blackjack-api/ /app/blackjack-api/

# Poker API source (lives in apps/ directory)
COPY apps/ /app/poker-api/

# Frontend static build + WASM game assets
COPY --from=frontend-builder /app/dist /app/frontend/dist

# Nginx config - remove default site, add ours
RUN rm -f /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory
RUN mkdir -p /var/log/supervisor

# Health check through nginx -> Go backend
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
