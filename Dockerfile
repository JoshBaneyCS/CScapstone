# =============================================================================
# ALL-IN-ONE DOCKERFILE - Casino Capstone
# =============================================================================
# Bundles: Go backend, Blackjack API, Poker API, GUI (Pygame/noVNC), Nginx
# Uses supervisord to manage all processes.
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
# Stage 2: Final all-in-one image
# ---------------------------------------------------------------------------
FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV TEMPLATE_PATH=/app/backend/templates

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libsdl2-gfx-dev \
    fonts-dejavu-core \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies - Blackjack & Poker APIs
COPY dev-testing/blackjack-api/requirements.txt /tmp/blackjack-requirements.txt
RUN pip install --no-cache-dir -r /tmp/blackjack-requirements.txt

# Python dependencies - GUI
COPY dev-testing/gui/requirements.txt /tmp/gui-requirements.txt
RUN pip install --no-cache-dir -r /tmp/gui-requirements.txt

# Go backend binary + assets
COPY --from=go-builder /build/casino-backend /app/backend/casino-backend
COPY backend/templates /app/backend/templates
COPY backend/static /app/backend/static

# Blackjack API source
COPY blackjack-api/ /app/blackjack-api/

# Poker API source (lives in apps/ directory)
COPY apps/ /app/poker-api/

# GUI source + resources
COPY gui/ /app/gui/

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
