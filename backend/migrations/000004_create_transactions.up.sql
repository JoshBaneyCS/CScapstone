-- =============================================================================
-- MIGRATION: 000004_create_transactions.up.sql
-- =============================================================================
-- This migration creates the 'transactions' table, which provides a complete
-- audit trail of all bankroll changes. Every bet, win, refund, or adjustment
-- is recorded here.
--
-- Design Decisions:
--   1. Immutable records - transactions are never updated, only inserted
--   2. Balance tracking - stores before/after balance for each transaction
--   3. Links to game sessions when applicable
--   4. Supports various transaction types for future features
--
-- Compliance Note:
-- In regulated gambling environments, a complete audit trail of all financial
-- transactions is often legally required. This table serves that purpose.
-- =============================================================================


-- =============================================================================
-- CREATE TRANSACTIONS TABLE
-- =============================================================================

CREATE TABLE transactions (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    -- Unique identifier for each transaction
    -- UUID v4 ensures globally unique IDs

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- =========================================================================
    -- FOREIGN KEYS
    -- =========================================================================

    -- user_id: The user whose balance is affected
    -- ON DELETE CASCADE: If user is deleted, their transaction history is also deleted
    -- Note: In a production system, you might want to keep audit records even
    -- after user deletion (use ON DELETE SET NULL or separate archive table)

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- game_session_id: Links to the game session (if transaction is from a game)
    -- NULL for non-game transactions (bonuses, adjustments, deposits)
    -- No CASCADE - we want to keep transaction records even if session is deleted

    game_session_id UUID REFERENCES game_sessions(id),

    -- =========================================================================
    -- TRANSACTION DETAILS
    -- =========================================================================

    -- transaction_type: The category of transaction
    -- Values:
    --   'bet'        - Money deducted for placing a bet
    --   'win'        - Money credited from winning a game
    --   'refund'     - Money returned (e.g., game cancelled, error)
    --   'bonus'      - Promotional credits added
    --   'adjustment' - Admin adjustment (corrections, etc.)

    transaction_type VARCHAR(30) NOT NULL,

    -- amount_cents: The transaction amount in cents
    -- Positive for credits (win, bonus, refund)
    -- Negative for debits (bet)
    -- This allows simple SUM() queries to calculate net change
    --
    -- Example:
    --   Bet $10:       amount_cents = -1000
    --   Win $20:       amount_cents = +2000
    --   Refund $10:    amount_cents = +1000

    amount_cents BIGINT NOT NULL,

    -- balance_before_cents: User's balance BEFORE this transaction
    -- Allows reconstruction of balance history

    balance_before_cents BIGINT NOT NULL,

    -- balance_after_cents: User's balance AFTER this transaction
    -- Must equal balance_before_cents + amount_cents
    -- Stored explicitly for easy querying and data integrity verification

    balance_after_cents BIGINT NOT NULL,

    -- description: Human-readable description of the transaction
    -- Examples:
    --   "Blackjack bet placed"
    --   "Won blackjack (3:2 payout)"
    --   "New user signup bonus"

    description VARCHAR(255),

    -- =========================================================================
    -- TIMESTAMPS
    -- =========================================================================

    -- created_at: When this transaction occurred
    -- Never updated (transactions are immutable)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================

    -- Ensure transaction_type is one of the allowed values
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('bet', 'win', 'refund', 'bonus', 'adjustment')
    ),

    -- Ensure balance math is correct
    -- balance_after should always equal balance_before + amount
    CONSTRAINT balance_math_check CHECK (
        balance_after_cents = balance_before_cents + amount_cents
    )
);


-- =============================================================================
-- CREATE INDEXES
-- =============================================================================

-- Index for finding transactions by user (most common query)
-- Used when displaying transaction history
CREATE INDEX idx_transactions_user_id ON transactions(user_id);

-- Index for ordering by time (for history with pagination)
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- Index for linking to game sessions
CREATE INDEX idx_transactions_game_session_id ON transactions(game_session_id);

-- Index for filtering by transaction type
CREATE INDEX idx_transactions_type ON transactions(transaction_type);

-- Composite index for user + time queries (very common pattern)
-- Supports queries like: "Get last 20 transactions for user X"
CREATE INDEX idx_transactions_user_time ON transactions(user_id, created_at DESC);


-- =============================================================================
-- ADD TABLE AND COLUMN COMMENTS
-- =============================================================================

COMMENT ON TABLE transactions IS 'Audit trail of all bankroll changes. Every bet, win, refund, and adjustment is recorded here.';

COMMENT ON COLUMN transactions.id IS 'Unique identifier for the transaction';
COMMENT ON COLUMN transactions.user_id IS 'References users.id - the user whose balance changed';
COMMENT ON COLUMN transactions.game_session_id IS 'References game_sessions.id if this is a game-related transaction (NULL for bonuses/adjustments)';
COMMENT ON COLUMN transactions.transaction_type IS 'Type: bet, win, refund, bonus, or adjustment';
COMMENT ON COLUMN transactions.amount_cents IS 'Transaction amount in cents. Positive = credit, Negative = debit';
COMMENT ON COLUMN transactions.balance_before_cents IS 'User balance before this transaction';
COMMENT ON COLUMN transactions.balance_after_cents IS 'User balance after this transaction (must equal before + amount)';
COMMENT ON COLUMN transactions.description IS 'Human-readable description of the transaction';
COMMENT ON COLUMN transactions.created_at IS 'When this transaction occurred';
