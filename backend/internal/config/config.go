// =============================================================================
// FILE: backend/internal/config/config.go
// =============================================================================
// Configuration loader for the Casino Capstone API.
//
// Loads all configuration from environment variables with sensible defaults
// for development. In production, these should be set via Docker, Kubernetes,
// or a secrets manager.
//
// Required environment variables for production:
//   - DATABASE_URL: PostgreSQL connection string
//   - JWT_SECRET: Secret key for signing JWT tokens (min 32 chars)
//
// Optional environment variables:
//   - API_PORT: Port to listen on (default: 8080)
//   - FRONTEND_URL: Frontend URL for CORS (default: http://localhost:5173)
//   - COOKIE_SECURE: Set to "true" in production for HTTPS-only cookies
//   - INTERNAL_API_KEY: API key for internal game service calls
// =============================================================================

package config

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

// Config holds all application configuration
type Config struct {
	// Server settings
	APIPort string // Port to listen on (e.g., "8080")

	// Database
	DatabaseURL string // PostgreSQL connection string

	// Authentication
	JWTSecret    string // Secret key for JWT signing
	CookieSecure bool   // true = HTTPS only cookies (production)

	// CORS
	FrontendURL string // Frontend URL for CORS headers

	// Internal API
	InternalAPIKey string // API key for game services
}

// Load reads configuration from environment variables
//
// Returns an error if required variables are missing or invalid.
func Load() (*Config, error) {
	cfg := &Config{}

	// -------------------------------------------------------------------------
	// SERVER SETTINGS
	// -------------------------------------------------------------------------
	cfg.APIPort = getEnvOrDefault("API_PORT", "8080")

	// -------------------------------------------------------------------------
	// DATABASE
	// -------------------------------------------------------------------------
	cfg.DatabaseURL = os.Getenv("DATABASE_URL")
	if cfg.DatabaseURL == "" {
		// Default for local development with Docker Compose
		cfg.DatabaseURL = "postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db?sslmode=disable"
	}

	// -------------------------------------------------------------------------
	// AUTHENTICATION
	// -------------------------------------------------------------------------
	cfg.JWTSecret = os.Getenv("JWT_SECRET")
	if cfg.JWTSecret == "" {
		// Default for development only - CHANGE IN PRODUCTION!
		cfg.JWTSecret = "dev-jwt-secret-change-me-in-production-min-32-chars"
	}

	// Validate JWT secret length (should be at least 32 characters)
	if len(cfg.JWTSecret) < 32 {
		return nil, errors.New("JWT_SECRET must be at least 32 characters")
	}

	// Cookie secure flag (should be true in production for HTTPS)
	cookieSecure := strings.ToLower(getEnvOrDefault("COOKIE_SECURE", "false"))
	cfg.CookieSecure = cookieSecure == "true" || cookieSecure == "1"

	// -------------------------------------------------------------------------
	// CORS
	// -------------------------------------------------------------------------
	cfg.FrontendURL = getEnvOrDefault("FRONTEND_URL", "http://localhost:5173")

	// -------------------------------------------------------------------------
	// INTERNAL API
	// -------------------------------------------------------------------------
	cfg.InternalAPIKey = getEnvOrDefault("INTERNAL_API_KEY", "dev-internal-key-change-me")

	// -------------------------------------------------------------------------
	// VALIDATION
	// -------------------------------------------------------------------------
	if err := cfg.validate(); err != nil {
		return nil, err
	}

	return cfg, nil
}

// validate checks that the configuration is valid
func (c *Config) validate() error {
	if c.APIPort == "" {
		return errors.New("API_PORT cannot be empty")
	}

	if c.DatabaseURL == "" {
		return errors.New("DATABASE_URL is required")
	}

	if c.JWTSecret == "" {
		return errors.New("JWT_SECRET is required")
	}

	if c.FrontendURL == "" {
		return errors.New("FRONTEND_URL cannot be empty")
	}

	return nil
}

// IsDevelopment returns true if running in development mode
func (c *Config) IsDevelopment() bool {
	env := strings.ToLower(os.Getenv("APP_ENV"))
	return env == "" || env == "development" || env == "dev"
}

// IsProduction returns true if running in production mode
func (c *Config) IsProduction() bool {
	env := strings.ToLower(os.Getenv("APP_ENV"))
	return env == "production" || env == "prod"
}

// String returns a string representation (hides sensitive values)
func (c *Config) String() string {
	return fmt.Sprintf(
		"Config{APIPort: %s, DatabaseURL: [hidden], JWTSecret: [hidden], CookieSecure: %v, FrontendURL: %s}",
		c.APIPort,
		c.CookieSecure,
		c.FrontendURL,
	)
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// getEnvOrDefault returns the environment variable value or a default
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// MustGetEnv returns the environment variable or panics if not set
// Use this only for truly required variables with no sensible default
func MustGetEnv(key string) string {
	value := os.Getenv(key)
	if value == "" {
		panic(fmt.Sprintf("required environment variable %s is not set", key))
	}
	return value
}
