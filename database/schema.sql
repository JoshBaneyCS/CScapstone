-- =============================================================================
-- schema.sql - Idempotent schema for Casino Capstone
-- =============================================================================
-- This file is safe to run multiple times.
-- It creates the users table, extensions, and triggers.
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bankroll_cents BIGINT NOT NULL DEFAULT 250000 CHECK (bankroll_cents >= 0),
    blackjack_wins INTEGER NOT NULL DEFAULT 0 CHECK (blackjack_wins >= 0),
    blackjack_losses INTEGER NOT NULL DEFAULT 0 CHECK (blackjack_losses >= 0),
    poker_wins INTEGER NOT NULL DEFAULT 0 CHECK (poker_wins >= 0),
    poker_losses INTEGER NOT NULL DEFAULT 0 CHECK (poker_losses >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger function to maintain updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Note: The CHECK constraint (bankroll_cents >= 0) already prevents negative balances.
-- The application layer should check bankroll > 0 before allowing new bets.
-- Previously this trigger deleted users on zero bankroll, which was too aggressive.
DROP TRIGGER IF EXISTS users_delete_on_zero_bankroll ON users;
DROP FUNCTION IF EXISTS delete_user_on_zero_bankroll();
