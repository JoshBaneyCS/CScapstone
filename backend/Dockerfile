# =============================================================================
# DOCKERFILE FOR CASINO CAPSTONE GO BACKEND
# =============================================================================
# This Dockerfile uses a multi-stage build pattern to create a small, secure
# production image. Multi-stage builds work by:
#
# 1. BUILDER STAGE: Uses a full Go image with all build tools to compile the app
# 2. FINAL STAGE: Uses a minimal base image and copies only the compiled binary
#
# Benefits of this approach:
#   - Final image is ~20MB instead of ~1GB (no Go toolchain included)
#   - Smaller attack surface (fewer packages = fewer vulnerabilities)
#   - Faster deployments (smaller images transfer faster)
#   - Build tools aren't available in production (more secure)
#
# To build manually:
#   $ docker build -t casino-api .
#
# To run manually:
#   $ docker run -p 8080:8080 --env-file ../.env casino-api
# =============================================================================


# =============================================================================
# STAGE 1: BUILDER
# =============================================================================
# This stage compiles the Go application into a static binary

# Use the official Go 1.21 image based on Alpine Linux
# Alpine is a minimal Linux distribution (~5MB) that keeps the builder small
FROM golang:1.21-alpine AS builder

# Install build dependencies
# - git: Required for fetching Go modules from repositories
# - ca-certificates: Required for HTTPS connections
# - tzdata: Timezone data for proper time handling
RUN apk add --no-cache git ca-certificates tzdata

# Set the working directory inside the container
# All subsequent commands will run from this directory
WORKDIR /build

# Copy go.mod and go.sum first (dependency definition files)
# This is a Docker optimization: these files change less often than source code
# Docker caches each layer, so if these files haven't changed, the next RUN
# command (go mod download) will use the cached layer instead of re-downloading
COPY go.mod go.sum ./

# Download all dependencies
# This step is cached separately from the source code compilation
# If dependencies haven't changed, Docker reuses the cached layer
RUN go mod download

# Verify dependencies haven't been tampered with
# This checks the downloaded modules against the checksums in go.sum
RUN go mod verify

# Now copy the rest of the source code
# This is done after downloading dependencies so that code changes
# don't invalidate the dependency cache
COPY . .

# Build the Go application
# Flags explained:
#   -ldflags="-w -s": Strip debug information to reduce binary size
#     -w: Omit DWARF symbol table (debugging info)
#     -s: Omit symbol table and debug information
#   -o /build/api: Output the binary to /build/api
#   ./cmd/api: Build the main package in cmd/api directory
#
# CGO_ENABLED=0: Disable CGO (C bindings) for a fully static binary
#   This is important because it allows the binary to run on scratch/distroless
#   images that don't have C libraries
#
# GOOS=linux GOARCH=amd64: Cross-compile for Linux AMD64
#   Ensures the binary works regardless of the build machine's OS
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o /build/api \
    ./cmd/api


# =============================================================================
# STAGE 2: FINAL (Production Image)
# =============================================================================
# This stage creates the final, minimal production image

# Use Alpine Linux as the base image
# Alpine is chosen because:
#   - Very small (~5MB base image)
#   - Includes a shell for debugging if needed
#   - Has a package manager if we need to add tools later
#
# Alternative: "FROM scratch" for an even smaller image (~0MB base)
# but scratch has no shell, no debugging tools, and is harder to troubleshoot
FROM alpine:3.19

# Add labels for image metadata
# These help identify the image in registries and tooling
LABEL maintainer="CS Capstone Team"
LABEL description="Casino Capstone Go REST API"
LABEL version="1.0"

# Install runtime dependencies
# - ca-certificates: Required for making HTTPS requests (e.g., to external APIs)
# - tzdata: Timezone data for proper time handling in logs and timestamps
RUN apk add --no-cache ca-certificates tzdata

# Create a non-root user for security
# Running as root inside containers is a security risk because:
#   - If an attacker escapes the container, they have root access to the host
#   - Principle of least privilege: apps shouldn't have more permissions than needed
#
# We create a system user (no login shell, no home directory) called 'appuser'
RUN adduser -D -g '' -u 1000 appuser

# Set the working directory for the application
WORKDIR /app

# Copy the compiled binary from the builder stage
# The --from=builder flag tells Docker to copy from the builder stage
# We only copy the binary, not the source code or Go toolchain
COPY --from=builder /build/api .

# Copy migration files
# These SQL files define our database schema
# They're needed at runtime so the API can run migrations on startup
COPY --from=builder /build/migrations ./migrations

# Change ownership of the app directory to our non-root user
# This ensures the application can read its files when running as appuser
RUN chown -R appuser:appuser /app

# Switch to the non-root user
# All subsequent commands (and the final CMD) will run as this user
USER appuser

# Document which port the application listens on
# This is informational only - it doesn't actually publish the port
# The port is published in docker-compose.yml or with 'docker run -p'
EXPOSE 8080

# Health check to verify the API is responding
# Docker will periodically run this command to check container health
# If the health check fails, Docker can automatically restart the container
#
# We check the /health endpoint (which we'll implement in the API)
# --fail: Return exit code 22 if HTTP response is 4xx or 5xx
# --silent: Don't show progress meter
# --show-error: Show error message if curl fails
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Define the command to run when the container starts
# This runs our compiled Go binary
CMD ["./api"]