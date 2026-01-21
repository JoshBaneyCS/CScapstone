-- =============================================================================
-- MIGRATION: 000003_create_game_sessions.up.sql
-- =============================================================================
-- This migration creates the 'game_sessions' table, which tracks all active
-- and completed game sessions for users. Each time a user starts a game
-- (Blackjack, Poker, etc.), a new session is created.
--
-- Design Decisions:
--   1. Game state stored as JSONB - flexible schema for different game types
--   2. One active session per user - prevents abuse/exploits
--   3. Result and payout tracked for history and analytics
--   4. Timestamps for session duration tracking
-- =============================================================================


-- =============================================================================
-- CREATE GAME_SESSIONS TABLE
-- =============================================================================

CREATE TABLE game_sessions (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    -- Unique identifier for each game session
    -- UUID v4 ensures globally unique IDs without coordination

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- =========================================================================
    -- FOREIGN KEY TO USER
    -- =========================================================================
    -- Links this session to the user who is playing
    -- ON DELETE CASCADE: If user is deleted, their game sessions are also deleted

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- =========================================================================
    -- GAME METADATA
    -- =========================================================================

    -- game_type: The type of game being played
    -- Values: 'blackjack', 'poker'
    -- VARCHAR(50) allows for future game types

    game_type VARCHAR(50) NOT NULL,

    -- status: Current state of the game session
    -- Values:
    --   'active'    - Game is in progress
    --   'completed' - Game finished normally
    --   'abandoned' - Game was abandoned (e.g., user logout, timeout)
    -- Default: 'active' for new sessions

    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- =========================================================================
    -- BETTING INFORMATION
    -- =========================================================================

    -- bet_cents: The initial bet amount in cents
    -- Must be positive (CHECK constraint)
    -- Example: $10.00 bet = 1000 cents

    bet_cents BIGINT NOT NULL CHECK (bet_cents > 0),

    -- =========================================================================
    -- GAME STATE (JSONB)
    -- =========================================================================
    -- Stores the complete game state as JSON
    -- This is flexible and allows different structures per game type
    --
    -- Blackjack state example:
    -- {
    --   "playerHand": [{"suit": "hearts", "rank": "A"}, {"suit": "spades", "rank": "K"}],
    --   "dealerHand": [{"suit": "clubs", "rank": "7"}, {"suit": "diamonds", "rank": "5"}],
    --   "deck": [...],
    --   "playerScore": 21,
    --   "dealerScore": 12,
    --   "doubled": false
    -- }
    --
    -- Poker state example:
    -- {
    --   "playerHand": [...],
    --   "dealerHand": [...],
    --   "communityCards": [...],
    --   "deck": [...],
    --   "stage": "flop",
    --   "pot": 2000
    -- }
    --
    -- JSONB vs JSON:
    --   - JSONB is stored in binary format (slightly slower insert)
    --   - JSONB has faster reads and supports indexing
    --   - JSONB removes whitespace and duplicate keys

    state JSONB NOT NULL DEFAULT '{}',

    -- =========================================================================
    -- RESULT INFORMATION
    -- =========================================================================

    -- result: The outcome of the game
    -- NULL while game is active
    -- Values: 'win', 'lose', 'push', 'blackjack', 'fold', 'dealer_bust'

    result VARCHAR(20),

    -- payout_cents: Amount paid out to user (0 for losses)
    -- For wins: includes original bet + winnings
    -- Example: $10 bet, 1:1 win = 2000 cents payout (bet + winnings)
    -- Example: $10 bet, blackjack (3:2) = 2500 cents payout

    payout_cents BIGINT DEFAULT 0,

    -- =========================================================================
    -- TIMESTAMPS
    -- =========================================================================

    -- started_at: When the game session began
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ended_at: When the game session ended (NULL while active)
    ended_at TIMESTAMPTZ,

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================

    -- Ensure status is one of the allowed values
    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'abandoned')),

    -- Ensure result is one of the allowed values (or NULL for active games)
    CONSTRAINT valid_result CHECK (
        result IS NULL OR
        result IN ('win', 'lose', 'push', 'blackjack', 'fold', 'dealer_bust')
    )
);


-- =============================================================================
-- CREATE INDEXES
-- =============================================================================

-- Index for finding sessions by user (most common query)
CREATE INDEX idx_game_sessions_user_id ON game_sessions(user_id);

-- Index for filtering by game status
CREATE INDEX idx_game_sessions_status ON game_sessions(status);

-- Index for filtering by game type
CREATE INDEX idx_game_sessions_game_type ON game_sessions(game_type);

-- Index for ordering by start time (for history queries)
CREATE INDEX idx_game_sessions_started_at ON game_sessions(started_at DESC);

-- Unique partial index: Only one active session per user
-- This prevents users from having multiple games open simultaneously
-- which could be exploited or cause inconsistent state
-- A partial index only indexes rows that match the WHERE clause
CREATE UNIQUE INDEX idx_one_active_session_per_user
    ON game_sessions(user_id)
    WHERE status = 'active';


-- =============================================================================
-- ADD TABLE AND COLUMN COMMENTS
-- =============================================================================

COMMENT ON TABLE game_sessions IS 'Tracks all game sessions (active and completed) for casino games like Blackjack and Poker';

COMMENT ON COLUMN game_sessions.id IS 'Unique identifier for the game session';
COMMENT ON COLUMN game_sessions.user_id IS 'References users.id - the player';
COMMENT ON COLUMN game_sessions.game_type IS 'Type of game: blackjack, poker, etc.';
COMMENT ON COLUMN game_sessions.status IS 'Session status: active, completed, or abandoned';
COMMENT ON COLUMN game_sessions.bet_cents IS 'Initial bet amount in cents';
COMMENT ON COLUMN game_sessions.state IS 'JSONB containing complete game state (cards, scores, etc.)';
COMMENT ON COLUMN game_sessions.result IS 'Game outcome: win, lose, push, blackjack, fold, dealer_bust';
COMMENT ON COLUMN game_sessions.payout_cents IS 'Total amount paid out to user (0 for losses)';
COMMENT ON COLUMN game_sessions.started_at IS 'When the game session started';
COMMENT ON COLUMN game_sessions.ended_at IS 'When the game session ended (NULL if active)';
