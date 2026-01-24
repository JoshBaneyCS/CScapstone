// =============================================================================
// FILE: backend/internal/db/db.go
// =============================================================================
// Database connection and utilities for PostgreSQL.
//
// Features:
//   - Connection pool management with pgxpool
//   - Automatic migration running on startup
//   - Transaction helpers
//
// Usage:
//   database, err := db.Connect(databaseURL)
//   defer database.Close()
// =============================================================================

package db

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Database wraps the connection pool and provides helper methods
type Database struct {
	Pool *pgxpool.Pool
}

// Connect establishes a connection pool to PostgreSQL
//
// Parameters:
//   - databaseURL: PostgreSQL connection string
//     Example: "postgres://user:pass@localhost:5432/casino_db?sslmode=disable"
//
// Returns:
//   - *Database: Database wrapper with connection pool
//   - error: Connection error if failed
func Connect(databaseURL string) (*Database, error) {
	// Parse config from URL
	config, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	// Configure pool settings
	config.MaxConns = 25                      // Maximum connections in pool
	config.MinConns = 5                       // Minimum idle connections
	config.MaxConnLifetime = 1 * time.Hour    // Max time a connection can be reused
	config.MaxConnIdleTime = 30 * time.Minute // Max time a connection can be idle
	config.HealthCheckPeriod = 1 * time.Minute

	// Create context with timeout for initial connection
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Connect to database
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Verify connection
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Database{Pool: pool}, nil
}

// Close closes the database connection pool
func (d *Database) Close() {
	if d.Pool != nil {
		d.Pool.Close()
	}
}

// Ping checks if the database connection is alive
func (d *Database) Ping(ctx context.Context) error {
	return d.Pool.Ping(ctx)
}

// =============================================================================
// MIGRATIONS
// =============================================================================

// RunMigrations runs all pending database migrations
//
// Parameters:
//   - databaseURL: PostgreSQL connection string
//
// Migrations are loaded from the "migrations" directory relative to the
// working directory. In production, this is typically /app/migrations.
func RunMigrations(databaseURL string) error {
	// Try multiple migration paths (for different environments)
	migrationPaths := []string{
		"file://migrations",
		"file://./migrations",
		"file:///app/migrations",
		"file://backend/migrations",
	}

	var m *migrate.Migrate
	var err error

	for _, path := range migrationPaths {
		m, err = migrate.New(path, databaseURL)
		if err == nil {
			break
		}
	}

	if err != nil {
		return fmt.Errorf("failed to create migrator: %w", err)
	}
	defer m.Close()

	// Run migrations
	if err := m.Up(); err != nil && err != migrate.ErrNoChange {
		return fmt.Errorf("failed to run migrations: %w", err)
	}

	version, dirty, _ := m.Version()
	if dirty {
		log.Printf("⚠️  Warning: Migration state is dirty at version %d", version)
	} else {
		log.Printf("✅ Migrations at version %d", version)
	}

	return nil
}

// =============================================================================
// TRANSACTION HELPERS
// =============================================================================

// TxFunc is a function that runs within a transaction
type TxFunc func(ctx context.Context, tx pgxpool.Tx) error

// WithTransaction executes a function within a database transaction
//
// If the function returns an error, the transaction is rolled back.
// If the function succeeds, the transaction is committed.
//
// Usage:
//
//	err := db.WithTransaction(ctx, func(ctx context.Context, tx pgxpool.Tx) error {
//	    _, err := tx.Exec(ctx, "INSERT INTO ...")
//	    return err
//	})
func (d *Database) WithTransaction(ctx context.Context, fn TxFunc) error {
	tx, err := d.Pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}

	// Ensure rollback on panic
	defer func() {
		if p := recover(); p != nil {
			tx.Rollback(ctx)
			panic(p) // Re-throw panic after rollback
		}
	}()

	// Execute the function
	if err := fn(ctx, tx); err != nil {
		if rbErr := tx.Rollback(ctx); rbErr != nil {
			return fmt.Errorf("tx error: %v, rollback error: %w", err, rbErr)
		}
		return err
	}

	// Commit transaction
	if err := tx.Commit(ctx); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}
