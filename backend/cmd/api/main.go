// =============================================================================
// FILE: backend/cmd/api/main.go
// =============================================================================
// Main entry point for the Casino Capstone REST API.
//
// Startup sequence:
//   1. Load configuration from environment variables
//   2. Connect to PostgreSQL database
//   3. Run database migrations
//   4. Initialize JWT service
//   5. Set up HTTP router with all routes
//   6. Start server with graceful shutdown
//
// Usage:
//   go run ./cmd/api/main.go
//
// Environment variables: See internal/config/config.go
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

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/config"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

func main() {
	// -------------------------------------------------------------------------
	// STEP 1: Load Configuration
	// -------------------------------------------------------------------------
	log.Println("🚀 Starting Casino Capstone API...")
	log.Println("📋 Loading configuration...")

	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("❌ Failed to load configuration: %v", err)
	}

	log.Printf("✅ Configuration loaded (Port: %s)", cfg.APIPort)

	// -------------------------------------------------------------------------
	// STEP 2: Connect to Database
	// -------------------------------------------------------------------------
	log.Println("🔌 Connecting to database...")

	database, err := db.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	defer database.Close()

	log.Println("✅ Database connected")

	// -------------------------------------------------------------------------
	// STEP 3: Run Migrations
	// -------------------------------------------------------------------------
	log.Println("📦 Running database migrations...")

	if err := db.RunMigrations(cfg.DatabaseURL); err != nil {
		log.Fatalf("❌ Failed to run migrations: %v", err)
	}

	log.Println("✅ Migrations complete")

	// -------------------------------------------------------------------------
	// STEP 4: Initialize Services
	// -------------------------------------------------------------------------
	jwtService := auth.NewJWTService(cfg.JWTSecret, cfg.CookieSecure)

	// -------------------------------------------------------------------------
	// STEP 5: Set Up Router
	// -------------------------------------------------------------------------
	log.Println("🛣️  Setting up routes...")

	router := web.NewRouter(web.RouterConfig{
		Database:    database,
		JWTService:  jwtService,
		FrontendURL: cfg.FrontendURL,
	})

	// -------------------------------------------------------------------------
	// STEP 6: Create HTTP Server
	// -------------------------------------------------------------------------
	serverAddr := fmt.Sprintf(":%s", cfg.APIPort)

	server := &http.Server{
		Addr:              serverAddr,
		Handler:           router,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
		ReadHeaderTimeout: 5 * time.Second,
	}

	// -------------------------------------------------------------------------
	// STEP 7: Start Server with Graceful Shutdown
	// -------------------------------------------------------------------------
	shutdownChan := make(chan os.Signal, 1)
	signal.Notify(shutdownChan, os.Interrupt, syscall.SIGTERM)

	// Start server in goroutine
	go func() {
		log.Printf("✅ Server started on http://localhost%s", serverAddr)
		log.Printf("🔍 Health check: http://localhost%s/health", serverAddr)
		log.Printf("📡 API base URL: http://localhost%s/api", serverAddr)
		log.Println("🎰 Casino Capstone API is ready!")
		log.Println("   Press Ctrl+C to stop")

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("❌ Server error: %v", err)
		}
	}()

	// Wait for shutdown signal
	sig := <-shutdownChan
	log.Printf("⚠️  Received signal %v, shutting down...", sig)

	// Graceful shutdown with 30 second timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("❌ Server forced to shutdown: %v", err)
	}

	log.Println("✅ Server stopped gracefully. Goodbye! 👋")
}
