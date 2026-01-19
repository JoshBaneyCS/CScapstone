// =============================================================================
// MAIN.GO - CASINO CAPSTONE API ENTRY POINT
// =============================================================================
// This is the main entry point for the Casino Capstone REST API.
// It orchestrates the startup of all components:
//
//   1. Load configuration from environment variables
//   2. Connect to PostgreSQL database
//   3. Run database migrations to ensure schema is up to date
//   4. Set up HTTP router with middleware (CORS, logging, auth)
//   5. Register API route handlers
//   6. Start the HTTP server with graceful shutdown support
//
// The application follows a layered architecture:
//   - cmd/api/main.go: Entry point and server setup (this file)
//   - internal/config: Configuration loading
//   - internal/db: Database connection and queries
//   - internal/auth: JWT token generation and validation
//   - internal/handlers: HTTP request handlers
//   - internal/middleware: HTTP middleware (auth, logging)
// =============================================================================

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	// Chi router - lightweight HTTP router with middleware support
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	// Internal packages - our application code
	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/config"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/handlers"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/middleware"
)

// =============================================================================
// MAIN FUNCTION
// =============================================================================
// The main function is the entry point of our application.
// It sets up everything and starts the server.

func main() {
	// -------------------------------------------------------------------------
	// STEP 1: Load Configuration
	// -------------------------------------------------------------------------
	// Load all configuration from environment variables.
	// This includes database URL, JWT secret, ports, etc.
	// See internal/config/config.go for all available settings.

	log.Println("🚀 Starting Casino Capstone API...")
	log.Println("📋 Loading configuration...")

	cfg, err := config.Load()
	if err != nil {
		// If we can't load config, we can't run. Exit with error.
		log.Fatalf("❌ Failed to load configuration: %v", err)
	}

	log.Printf("✅ Configuration loaded (API Port: %s)", cfg.APIPort)

	// -------------------------------------------------------------------------
	// STEP 2: Connect to Database
	// -------------------------------------------------------------------------
	// Establish a connection pool to PostgreSQL.
	// The pool manages multiple connections for concurrent requests.

	log.Println("🔌 Connecting to database...")

	database, err := db.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	// Ensure database connection is closed when the application exits
	defer database.Close()

	log.Println("✅ Database connected successfully")

	// -------------------------------------------------------------------------
	// STEP 3: Run Database Migrations
	// -------------------------------------------------------------------------
	// Migrations ensure the database schema is up to date.
	// They create tables, indexes, and other database objects.
	// See migrations/ directory for SQL migration files.

	log.Println("📦 Running database migrations...")

	if err := db.RunMigrations(cfg.DatabaseURL); err != nil {
		log.Fatalf("❌ Failed to run migrations: %v", err)
	}

	log.Println("✅ Migrations completed successfully")

	// -------------------------------------------------------------------------
	// STEP 4: Initialize Services
	// -------------------------------------------------------------------------
	// Create instances of our service components.
	// These are injected into handlers for dependency injection.

	// JWT service handles token creation and validation
	jwtService := auth.NewJWTService(cfg.JWTSecret, cfg.CookieSecure)

	// Create the handlers with all dependencies
	authHandler := handlers.NewAuthHandler(database, jwtService)
	gamesHandler := handlers.NewGamesHandler()

	// -------------------------------------------------------------------------
	// STEP 5: Set Up Router and Middleware
	// -------------------------------------------------------------------------
	// Chi is our HTTP router. We configure it with middleware that runs
	// on every request (logging, recovery, CORS, etc.)

	log.Println("🛣️  Setting up routes and middleware...")

	// Create a new Chi router
	r := chi.NewRouter()

	// ----- Global Middleware (runs on EVERY request) -----

	// RequestID: Adds a unique ID to each request for tracing in logs
	r.Use(chimiddleware.RequestID)

	// RealIP: Gets the real client IP even behind proxies/load balancers
	r.Use(chimiddleware.RealIP)

	// Logger: Logs every request with method, path, and duration
	r.Use(chimiddleware.Logger)

	// Recoverer: Catches panics and returns 500 instead of crashing
	r.Use(chimiddleware.Recoverer)

	// Timeout: Cancels requests that take longer than 60 seconds
	r.Use(chimiddleware.Timeout(60 * time.Second))

	// ----- CORS Configuration -----
	// CORS (Cross-Origin Resource Sharing) controls which websites can
	// make requests to our API. This is crucial for security.
	//
	// Without proper CORS:
	//   - Browsers block requests from the frontend to the API
	//   - Cookies won't be sent with requests
	//
	// Key settings:
	//   - AllowedOrigins: Only our frontend can make requests
	//   - AllowCredentials: Allows cookies to be sent
	//   - AllowedMethods: Which HTTP methods are permitted

	r.Use(cors.Handler(cors.Options{
		// Only allow requests from our frontend URL
		// IMPORTANT: Cannot use "*" wildcard when AllowCredentials is true
		AllowedOrigins: []string{cfg.FrontendURL},

		// HTTP methods the frontend can use
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},

		// Headers the frontend can send
		AllowedHeaders: []string{
			"Accept",
			"Authorization",
			"Content-Type",
			"X-CSRF-Token",
			"X-Requested-With",
		},

		// Headers the frontend can read from responses
		ExposedHeaders: []string{"Link"},

		// CRITICAL: Must be true for cookies to work cross-origin
		AllowCredentials: true,

		// How long browsers cache CORS preflight responses (5 minutes)
		MaxAge: 300,
	}))

	// -------------------------------------------------------------------------
	// STEP 6: Register Routes
	// -------------------------------------------------------------------------
	// Define all API endpoints and their handlers.
	// Routes are grouped by functionality.

	// ----- Health Check (Public) -----
	// Used by Docker health checks and load balancers to verify the API is running
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"casino-api"}`))
	})

	// ----- API Routes -----
	// All API routes are grouped under /api prefix
	r.Route("/api", func(r chi.Router) {

		// ----- Authentication Routes (Public) -----
		// These endpoints don't require authentication
		r.Route("/auth", func(r chi.Router) {
			// Register a new user account
			// POST /api/auth/register
			// Body: {email, username, password, firstName, lastName, dob}
			r.Post("/register", authHandler.Register)

			// Log in to an existing account
			// POST /api/auth/login
			// Body: {email, password} or {username, password}
			r.Post("/login", authHandler.Login)

			// Log out (clear session cookie)
			// POST /api/auth/logout
			r.Post("/logout", authHandler.Logout)

			// Get current user info (requires auth)
			// GET /api/auth/me
			// This route requires authentication, so we wrap it with middleware
			r.With(middleware.AuthMiddleware(jwtService)).Get("/me", authHandler.Me)
		})

		// ----- Games Routes (Protected) -----
		// These endpoints require authentication
		r.Route("/games", func(r chi.Router) {
			// Apply auth middleware to all routes in this group
			r.Use(middleware.AuthMiddleware(jwtService))

			// Get list of available games
			// GET /api/games
			r.Get("/", gamesHandler.ListGames)
		})
	})

	// -------------------------------------------------------------------------
	// STEP 7: Create and Configure HTTP Server
	// -------------------------------------------------------------------------
	// Create the HTTP server with sensible timeouts to prevent resource exhaustion

	serverAddr := fmt.Sprintf(":%s", cfg.APIPort)

	server := &http.Server{
		Addr:    serverAddr,
		Handler: r,

		// ReadTimeout: Max time to read the entire request (headers + body)
		// Prevents slow-loris attacks where clients send data very slowly
		ReadTimeout: 15 * time.Second,

		// WriteTimeout: Max time to write the response
		// Prevents the server from hanging on slow clients
		WriteTimeout: 15 * time.Second,

		// IdleTimeout: Max time to keep idle keep-alive connections open
		// Frees up resources from inactive connections
		IdleTimeout: 60 * time.Second,

		// ReadHeaderTimeout: Max time to read request headers
		// Additional protection against slow-loris attacks
		ReadHeaderTimeout: 5 * time.Second,
	}

	// -------------------------------------------------------------------------
	// STEP 8: Start Server with Graceful Shutdown
	// -------------------------------------------------------------------------
	// Graceful shutdown allows the server to finish handling current requests
	// before shutting down, preventing data corruption and errors.
	//
	// How it works:
	//   1. Server starts listening for requests in a goroutine
	//   2. Main goroutine waits for shutdown signal (Ctrl+C or kill)
	//   3. On signal, server stops accepting new requests
	//   4. Server waits for current requests to finish (up to timeout)
	//   5. Server shuts down cleanly

	// Channel to receive shutdown signals
	// We buffer it to prevent missing the signal
	shutdownChan := make(chan os.Signal, 1)

	// Register for SIGINT (Ctrl+C) and SIGTERM (docker stop, kill)
	signal.Notify(shutdownChan, os.Interrupt, syscall.SIGTERM)

	// Start the server in a goroutine so it doesn't block
	go func() {
		log.Printf("✅ Server started on http://localhost%s", serverAddr)
		log.Printf("📍 Health check: http://localhost%s/health", serverAddr)
		log.Printf("📍 API base URL: http://localhost%s/api", serverAddr)
		log.Println("🎰 Casino Capstone API is ready to accept connections!")
		log.Println("   Press Ctrl+C to stop the server")

		// ListenAndServe blocks until the server is shut down
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("❌ Server error: %v", err)
		}
	}()

	// Wait for shutdown signal
	// This blocks until we receive SIGINT or SIGTERM
	sig := <-shutdownChan
	log.Printf("⚠️  Received signal %v, initiating graceful shutdown...", sig)

	// Create a deadline for the shutdown
	// Give existing requests 30 seconds to complete
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Attempt graceful shutdown
	// This stops accepting new connections and waits for existing ones to finish
	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("❌ Server forced to shutdown: %v", err)
	}

	log.Println("✅ Server stopped gracefully. Goodbye! 👋")
}
