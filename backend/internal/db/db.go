// =============================================================================
// DB.GO - DATABASE CONNECTION AND MANAGEMENT
// =============================================================================
// This package handles PostgreSQL database connections using pgx, a pure Go
// driver for PostgreSQL. pgx provides better performance than the standard
// database/sql with the pq driver and has native support for PostgreSQL types.
//
// The Database struct wraps a connection pool (pgxpool.Pool) which:
//   - Manages multiple connections efficiently
//   - Handles connection reuse and health checking
//   - Provides thread-safe concurrent access
//
// Usage:
//   db, err := db.Connect(cfg.DatabaseURL)
//   if err != nil {
//       log.Fatal(err)
//   }
//   defer db.Close()
//
//   // Run migrations
//   if err := db.RunMigrations(cfg.DatabaseURL); err != nil {
//       log.Fatal(err)
//   }
// =============================================================================

package db

import (
	"context"
	"fmt"
	"time"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
	"github.com/jackc/pgx/v5/pgxpool"
)

// =============================================================================
// DATABASE STRUCT
// =============================================================================
// Database wraps a pgxpool.Pool to provide database operations.
// The pool manages connections automatically and is safe for concurrent use.

type Database struct {
	// Pool is the connection pool for PostgreSQL
	// It's exported so handlers can access it directly for complex queries
	Pool *pgxpool.Pool
}

// =============================================================================
// CONNECT FUNCTION
// =============================================================================
// Connect establishes a connection pool to the PostgreSQL database.
// It validates the connection by pinging the database before returning.
//
// Parameters:
//   - databaseURL: PostgreSQL connection string
//     Format: postgres://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=disable
//
// Returns:
//   - *Database: Database wrapper with active connection pool
//   - error: Connection error if unable to connect

func Connect(databaseURL string) (*Database, error) {
	// Create a context with timeout for the connection attempt
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Parse the connection string and create pool configuration
	config, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	// Configure the connection pool
	// These settings balance resource usage with availability
	config.MaxConns = 25                      // Maximum connections in the pool
	config.MinConns = 5                       // Minimum connections kept open
	config.MaxConnLifetime = 1 * time.Hour    // Maximum lifetime of a connection
	config.MaxConnIdleTime = 30 * time.Minute // Close idle connections after this
	config.HealthCheckPeriod = 1 * time.Minute

	// Create the connection pool
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Verify the connection by pinging the database
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Database{Pool: pool}, nil
}

// =============================================================================
// RUN MIGRATIONS
// =============================================================================
// RunMigrations applies all pending database migrations from the migrations
// directory. Migrations are versioned SQL files that evolve the database schema.
//
// Migration files should be in: backend/migrations/
//   - XXXXXX_description.up.sql   (apply migration)
//   - XXXXXX_description.down.sql (rollback migration)
//
// Parameters:
//   - databaseURL: PostgreSQL connection string
//
// Returns:
//   - error: Migration error if migrations fail

func RunMigrations(databaseURL string) error {
	// Create a new migrate instance
	// Source: file path to migrations directory
	// Database: PostgreSQL connection string
	m, err := migrate.New(
		"file://migrations",
		databaseURL,
	)
	if err != nil {
		return fmt.Errorf("failed to create migrate instance: %w", err)
	}
	defer m.Close()

	// Apply all pending migrations
	// Up() applies all available migrations that haven't been run yet
	if err := m.Up(); err != nil && err != migrate.ErrNoChange {
		return fmt.Errorf("failed to run migrations: %w", err)
	}

	return nil
}

// =============================================================================
// CLOSE METHOD
// =============================================================================
// Close gracefully shuts down the database connection pool.
// Should be called when the application shuts down (typically via defer).
//
// This releases all database connections back to the PostgreSQL server.

func (d *Database) Close() {
	if d.Pool != nil {
		d.Pool.Close()
	}
}

// =============================================================================
// HELPER METHODS
// =============================================================================

// Ping checks if the database connection is still alive.
// Useful for health check endpoints.
func (d *Database) Ping(ctx context.Context) error {
	return d.Pool.Ping(ctx)
}

// Stats returns connection pool statistics.
// Useful for monitoring and debugging.
func (d *Database) Stats() *pgxpool.Stat {
	return d.Pool.Stat()
}
