-- =============================================================================
-- MIGRATION: 000004_create_transactions.down.sql
-- =============================================================================
-- Rollback migration: Drops the transactions table and all its indexes.
-- WARNING: This will delete all transaction history!
-- =============================================================================

DROP TABLE IF EXISTS transactions;
