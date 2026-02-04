# Build Pygame to WASM using Pygbag
FROM python:3.11-slim AS builder
WORKDIR /build

# Install pygbag
RUN pip install pygbag

# Copy game source
COPY gui/ ./

# Build to WebAssembly (--build flag creates static output)
RUN pygbag --build .

# Serve with nginx
FROM nginx:alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
