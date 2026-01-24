# =============================================================================
# FILE: backend/Dockerfile
# =============================================================================
# Multi-stage Dockerfile for the Casino Capstone Go API.
#
# Stages:
#   1. builder - Compiles the Go binary
#   2. runtime - Minimal image with just the binary
#
# Build:
#   docker build -t casino-api .
#
# Run:
#   docker run -p 8080:8080 --env-file .env casino-api
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
FROM golang:1.22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Set working directory
WORKDIR /build

# Copy go.mod and go.sum first (for layer caching)
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the binary
# CGO_ENABLED=0 creates a static binary (no C dependencies)
# -ldflags="-s -w" strips debug info for smaller binary
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w" \
    -o casino-api \
    ./cmd/api

# -----------------------------------------------------------------------------
# STAGE 2: Runtime
# -----------------------------------------------------------------------------
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Create non-root user for security
RUN addgroup -g 1000 casino && \
    adduser -u 1000 -G casino -s /bin/sh -D casino

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/casino-api .

# Copy migrations
COPY --from=builder /build/migrations ./migrations

# Change ownership to non-root user
RUN chown -R casino:casino /app

# Switch to non-root user
USER casino

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the binary
CMD ["./casino-api"]