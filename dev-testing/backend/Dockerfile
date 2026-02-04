FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY backend/go.mod ./
COPY backend/main.go ./
RUN go mod tidy
RUN CGO_ENABLED=0 go build -o backend .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates wget
WORKDIR /app
COPY --from=builder /build/backend .
COPY backend/templates ./templates
COPY backend/static ./static
ENV TEMPLATE_PATH=/app/templates
EXPOSE 8080
CMD ["./backend"]
