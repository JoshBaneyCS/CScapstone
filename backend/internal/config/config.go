// =============================================================================
// CONFIG.GO - APPLICATION CONFIGURATION
// =============================================================================
// This package handles loading and validating configuration from environment
// variables. Using environment variables for configuration follows the
// 12-factor app methodology (https://12factor.net/config) and allows the
// same code to run in different environments (dev, staging, production)
// without code changes.
//
// Configuration is loaded once at startup and passed to components that need it.
// This is better than reading env vars throughout the code because:
//   1. All config is validated upfront - fail fast if something is missing
//   2. Easy to see all configuration in one place
//   3. Easy to test by passing mock config
//   4. Type safety - convert strings to proper types once
//
// Usage:
//   cfg, err := config.Load()
//   if err != nil {
//       log.Fatal(err)
//   }
//   // Use cfg.DatabaseURL, cfg.JWTSecret, etc.
// =============================================================================

package config

import (
	"errors"
	"fmt"
	"os"
	"strings"

	// godotenv loads .env files into environment variables
	// This is only used for local development - in production,
	// environment variables are set by the deployment platform
	"github.com/joho/godotenv"
)

// =============================================================================
// CONFIG STRUCT
// =============================================================================
// Config holds all configuration values for the application.
// Each field is documented with its purpose and expected format.

type Config struct {
	// -------------------------------------------------------------------------
	// Database Configuration
	// -------------------------------------------------------------------------

	// DatabaseURL is the PostgreSQL connection string
	// Format: postgres://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=disable
	// Example: postgres://casino_admin:secret@localhost:5432/casino_db?sslmode=disable
	//
	// Components:
	//   - USER: Database username
	//   - PASSWORD: Database password (URL-encoded if it contains special chars)
	//   - HOST: Database server hostname (use "db" in Docker, "localhost" otherwise)
	//   - PORT: PostgreSQL port (default 5432)
	//   - DATABASE: Name of the database
	//   - sslmode: SSL mode (disable for local dev, require for production)
	DatabaseURL string

	// -------------------------------------------------------------------------
	// Authentication Configuration
	// -------------------------------------------------------------------------

	// JWTSecret is the secret key used to sign and verify JWT tokens
	// SECURITY: This must be kept secret! Anyone with this key can forge tokens.
	//
	// Requirements:
	//   - At least 32 characters for security
	//   - Random, unpredictable value
	//   - Different for each environment (dev, staging, prod)
	//
	// Generate a secure secret with: openssl rand -base64 32
	JWTSecret string

	// CookieSecure determines if cookies should only be sent over HTTPS
	// - false: Cookies work over HTTP (required for local development)
	// - true: Cookies only sent over HTTPS (required for production)
	//
	// SECURITY: Always set to true in production! Setting to false in production
	// allows cookies to be intercepted over unencrypted connections.
	CookieSecure bool

	// -------------------------------------------------------------------------
	// Server Configuration
	// -------------------------------------------------------------------------

	// APIPort is the port the HTTP server listens on
	// Default: 8080
	// This should match the port exposed in Docker and docker-compose
	APIPort string

	// FrontendURL is the URL of the frontend application
	// Used for CORS configuration to allow the frontend to make requests
	// Example: http://localhost:5173 (Vite default) or https://casino.example.com
	//
	// IMPORTANT: This must be set correctly for cookies to work!
	// The browser will only send cookies to the API if CORS is configured
	// to allow the frontend origin with credentials.
	FrontendURL string
}

// =============================================================================
// LOAD FUNCTION
// =============================================================================
// Load reads configuration from environment variables and returns a Config struct.
// It attempts to load a .env file first (for local development), then reads
// from actual environment variables.
//
// Returns an error if any required configuration is missing or invalid.

func Load() (*Config, error) {
	// -------------------------------------------------------------------------
	// Load .env file (optional, for local development)
	// -------------------------------------------------------------------------
	// godotenv.Load() reads a .env file and sets environment variables.
	// We ignore the error because:
	//   1. In production, there's no .env file - env vars are set directly
	//   2. In development, if .env is missing, we'll catch it when checking required vars
	//
	// The .env file should be in the working directory (project root or backend/)

	// Try to load .env from current directory
	_ = godotenv.Load()

	// Also try to load from parent directory (when running from backend/)
	_ = godotenv.Load("../.env")

	// -------------------------------------------------------------------------
	// Read Environment Variables
	// -------------------------------------------------------------------------
	// getEnv is a helper that reads an env var with a default fallback
	// getEnvRequired is for vars that must be set (no default)

	// Database URL - REQUIRED, no sensible default
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		return nil, errors.New("DATABASE_URL environment variable is required")
	}

	// JWT Secret - REQUIRED, no sensible default (security critical)
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		return nil, errors.New("JWT_SECRET environment variable is required")
	}

	// Validate JWT secret length for security
	// Short secrets are vulnerable to brute-force attacks
	if len(jwtSecret) < 16 {
		return nil, errors.New("JWT_SECRET must be at least 16 characters for security")
	}

	// API Port - Optional, defaults to 8080
	apiPort := getEnvWithDefault("API_PORT", "8080")

	// Cookie Secure flag - Optional, defaults to false for local dev
	// Accepts: "true", "false", "1", "0", "yes", "no"
	cookieSecure := parseEnvBool("COOKIE_SECURE", false)

	// Frontend URL - Optional, defaults to Vite's default dev URL
	frontendURL := getEnvWithDefault("FRONTEND_URL", "http://localhost:5173")

	// Validate frontend URL format
	if !strings.HasPrefix(frontendURL, "http://") && !strings.HasPrefix(frontendURL, "https://") {
		return nil, fmt.Errorf("FRONTEND_URL must start with http:// or https://, got: %s", frontendURL)
	}

	// -------------------------------------------------------------------------
	// Create and Return Config
	// -------------------------------------------------------------------------

	config := &Config{
		DatabaseURL:  databaseURL,
		JWTSecret:    jwtSecret,
		CookieSecure: cookieSecure,
		APIPort:      apiPort,
		FrontendURL:  frontendURL,
	}

	return config, nil
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// getEnvWithDefault reads an environment variable and returns a default value
// if the variable is not set or is empty.
//
// Parameters:
//   - key: The name of the environment variable
//   - defaultValue: The value to return if the env var is not set
//
// Returns:
//   - The environment variable value, or defaultValue if not set
//
// Example:
//
//	port := getEnvWithDefault("API_PORT", "8080")
func getEnvWithDefault(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// parseEnvBool reads an environment variable and parses it as a boolean.
// Handles various common boolean representations.
//
// Truthy values (case-insensitive): "true", "1", "yes", "on"
// Falsy values (case-insensitive): "false", "0", "no", "off", ""
//
// Parameters:
//   - key: The name of the environment variable
//   - defaultValue: The value to return if the env var is not set or unrecognized
//
// Returns:
//   - The parsed boolean value, or defaultValue if not set/unrecognized
//
// Example:
//
//	secure := parseEnvBool("COOKIE_SECURE", false)
func parseEnvBool(key string, defaultValue bool) bool {
	value := os.Getenv(key)

	// If not set, return default
	if value == "" {
		return defaultValue
	}

	// Normalize to lowercase for comparison
	value = strings.ToLower(strings.TrimSpace(value))

	// Check for truthy values
	switch value {
	case "true", "1", "yes", "on":
		return true
	case "false", "0", "no", "off":
		return false
	default:
		// Unrecognized value, return default
		return defaultValue
	}
}

// =============================================================================
// VALIDATION HELPERS (for future use)
// =============================================================================

// ValidateProductionConfig performs additional validation for production deployments.
// Call this when deploying to staging or production to catch common misconfigurations.
//
// This is not called automatically - it's available for production deployment scripts
// to use as an additional safety check.
func (c *Config) ValidateProductionConfig() error {
	var errs []string

	// In production, cookies MUST be secure (HTTPS only)
	if !c.CookieSecure {
		errs = append(errs, "COOKIE_SECURE should be true in production")
	}

	// In production, frontend URL should use HTTPS
	if !strings.HasPrefix(c.FrontendURL, "https://") {
		errs = append(errs, "FRONTEND_URL should use HTTPS in production")
	}

	// JWT secret should be longer in production
	if len(c.JWTSecret) < 32 {
		errs = append(errs, "JWT_SECRET should be at least 32 characters in production")
	}

	// Database should use SSL in production
	if !strings.Contains(c.DatabaseURL, "sslmode=require") &&
		!strings.Contains(c.DatabaseURL, "sslmode=verify") {
		errs = append(errs, "DATABASE_URL should use sslmode=require or sslmode=verify-full in production")
	}

	if len(errs) > 0 {
		return fmt.Errorf("production configuration warnings:\n  - %s", strings.Join(errs, "\n  - "))
	}

	return nil
}
