-- =============================================================================
-- FILE: backend/migrations/000001_create_users.down.sql
-- =============================================================================

DROP TRIGGER IF EXISTS users_updated_at ON users;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP TABLE IF EXISTS users;