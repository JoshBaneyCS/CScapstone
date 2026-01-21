-- =============================================================================
-- MIGRATION: 000003_create_game_sessions.down.sql
-- =============================================================================
-- Rollback migration: Drops the game_sessions table and all its indexes.
-- WARNING: This will delete all game session data!
-- =============================================================================

DROP TABLE IF EXISTS game_sessions;
