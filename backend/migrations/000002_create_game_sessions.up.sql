-- =============================================================================
-- FILE: backend/migrations/000002_create_game_sessions.up.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS game_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id         VARCHAR(50) NOT NULL,           -- e.g., 'blackjack', 'slots', 'roulette'
    status          VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, completed, abandoned
    bet_cents       INTEGER NOT NULL DEFAULT 0,     -- Initial bet amount
    result          VARCHAR(20),                    -- win, lose, push (null while active)
    winnings_cents  INTEGER NOT NULL DEFAULT 0,     -- Net change (positive=won, negative=lost)
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ                     -- Null while active
);

-- Index for finding active sessions by user
CREATE INDEX idx_game_sessions_user_active ON game_sessions(user_id, status) 
    WHERE status = 'active';

-- Index for game analytics
CREATE INDEX idx_game_sessions_game_id ON game_sessions(game_id);

-- Constraint: result required when completed
ALTER TABLE game_sessions ADD CONSTRAINT chk_completed_has_result
    CHECK (status != 'completed' OR result IS NOT NULL);