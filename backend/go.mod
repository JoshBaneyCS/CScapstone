// =============================================================================
// GO MODULE DEFINITION FOR CASINO CAPSTONE BACKEND
// =============================================================================
// This file defines the Go module and its dependencies. It's automatically
// managed by Go's module system but we've added comments for clarity.
//
// To add a new dependency:
//   $ go get github.com/some/package
//
// To update all dependencies:
//   $ go get -u ./...
//
// To tidy up unused dependencies:
//   $ go mod tidy
// =============================================================================

// Module path - this is the import path for this module
// It matches our GitHub repository structure
module github.com/JoshBaneyCS/CScapstone/backend

// Go version - we're using Go 1.21 for modern features and stability
// This ensures anyone building the project uses a compatible Go version
go 1.21

// =============================================================================
// DEPENDENCIES
// =============================================================================
// Each dependency is listed with its version, pinned for reproducible builds

require (
	// -------------------------------------------------------------------------
	// DATABASE DEPENDENCIES
	// -------------------------------------------------------------------------
	
	// pgx - PostgreSQL driver for Go
	// This is the most performant and feature-rich PostgreSQL driver available
	// We use v5 which has improved connection pooling and context support
	// Docs: https://github.com/jackc/pgx
	github.com/jackc/pgx/v5 v5.5.1

	// golang-migrate - Database migration tool
	// Handles creating and versioning database schema changes
	// Supports up/down migrations for easy rollbacks
	// Docs: https://github.com/golang-migrate/migrate
	github.com/golang-migrate/migrate/v4 v4.17.0

	// -------------------------------------------------------------------------
	// AUTHENTICATION DEPENDENCIES
	// -------------------------------------------------------------------------
	
	// bcrypt - Password hashing library
	// Industry standard for securely hashing passwords
	// Uses adaptive hashing that can be made slower as hardware improves
	// Docs: https://pkg.go.dev/golang.org/x/crypto/bcrypt
	golang.org/x/crypto v0.18.0

	// golang-jwt - JSON Web Token implementation
	// Used for creating and validating session tokens
	// Tokens are stored in HttpOnly cookies for security
	// Docs: https://github.com/golang-jwt/jwt
	github.com/golang-jwt/jwt/v5 v5.2.0

	// -------------------------------------------------------------------------
	// HTTP DEPENDENCIES
	// -------------------------------------------------------------------------
	
	// chi - Lightweight HTTP router
	// Chosen for its simplicity, stdlib compatibility, and middleware support
	// Much lighter than frameworks like Gin while still being powerful
	// Docs: https://github.com/go-chi/chi
	github.com/go-chi/chi/v5 v5.0.11

	// cors - CORS middleware for chi
	// Handles Cross-Origin Resource Sharing headers
	// Required for the frontend to make authenticated requests to the API
	// Docs: https://github.com/go-chi/cors
	github.com/go-chi/cors v1.2.1

	// -------------------------------------------------------------------------
	// UTILITY DEPENDENCIES
	// -------------------------------------------------------------------------
	
	// uuid - UUID generation library
	// Used for generating unique user IDs
	// We use v4 (random) UUIDs for primary keys
	// Docs: https://github.com/google/uuid
	github.com/google/uuid v1.5.0

	// godotenv - .env file loader
	// Loads environment variables from .env file during development
	// In production, use actual environment variables instead
	// Docs: https://github.com/joho/godotenv
	github.com/joho/godotenv v1.5.1
)

// =============================================================================
// INDIRECT DEPENDENCIES
// =============================================================================
// These are dependencies of our direct dependencies (transitive dependencies)
// Go manages these automatically, but they're listed here for completeness

require (
	// pgx sub-packages for connection handling and type support
	github.com/jackc/pgpassfile v1.0.0 // indirect
	github.com/jackc/pgservicefile v0.0.0-20231201235250-de7065d80cb9 // indirect
	github.com/jackc/puddle/v2 v2.2.1 // indirect
	
	// migrate dependencies for PostgreSQL support
	github.com/hashicorp/errwrap v1.1.0 // indirect
	github.com/hashicorp/go-multierror v1.1.1 // indirect
	github.com/lib/pq v1.10.9 // indirect
	go.uber.org/atomic v1.11.0 // indirect
	
	// Crypto and text processing utilities
	golang.org/x/sync v0.6.0 // indirect
	golang.org/x/text v0.14.0 // indirect
)