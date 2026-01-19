-- =============================================================================
-- MIGRATION: 000002_create_accounts_table.down.sql
-- =============================================================================
-- This is the ROLLBACK migration for the accounts table.
-- It undoes everything done in 000002_create_accounts_table.up.sql
--
-- This migration will:
--   1. Drop the trigger (must be done before dropping the table)
--   2. Drop the trigger function
--   3. Drop the accounts table
--
-- WARNING: Running this migration DELETES ALL ACCOUNT/BANKROLL DATA!
-- Only use in development or when you're certain you want to rollback.
--
-- To rollback this migration:
--   migrate -path ./migrations -database $DATABASE_URL down 1
-- =============================================================================


-- =============================================================================
-- DROP TRIGGER
-- =============================================================================
-- We drop the trigger first because it depends on both the table and function.
-- The trigger automatically fires on UPDATE, so we remove it before the table.
--
-- IF EXISTS: Prevents errors if the trigger was already dropped or never created.
-- ON accounts: Specifies which table the trigger is attached to.

DROP TRIGGER IF EXISTS trigger_accounts_updated_at ON accounts;


-- =============================================================================
-- DROP TRIGGER FUNCTION
-- =============================================================================
-- Now we can drop the trigger function since no triggers reference it.
--
-- IF EXISTS: Prevents errors if the function doesn't exist.
-- CASCADE: Drops objects that depend on this function (should be none now).
--
-- Note: We need to specify the function signature () even though it takes
-- no explicit parameters. Trigger functions receive parameters implicitly.

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;


-- =============================================================================
-- DROP INDEX
-- =============================================================================
-- Drop the index we created for updated_at queries.
-- IF EXISTS prevents errors if it was already dropped.

DROP INDEX IF EXISTS idx_accounts_updated_at;


-- =============================================================================
-- DROP ACCOUNTS TABLE
-- =============================================================================
-- Finally, drop the accounts table itself.
--
-- CASCADE: Also drops any objects that depend on this table.
-- In this case, that's mainly the foreign key relationship.
--
-- IF EXISTS: Prevents errors if the table doesn't exist.
--
-- Note: Because accounts has ON DELETE CASCADE referencing users,
-- dropping the accounts table does NOT affect the users table.
-- (CASCADE in DROP TABLE is different from ON DELETE CASCADE)

DROP TABLE IF EXISTS accounts CASCADE;


-- =============================================================================
-- NOTES ON ROLLBACK ORDER
-- =============================================================================
-- When rolling back multiple migrations, they are applied in REVERSE order:
--   - If you run "migrate down 2", it will:
--     1. First run 000002_create_accounts_table.down.sql (this file)
--     2. Then run 000001_create_users_table.down.sql
--
-- This is important because:
--   - accounts references users (foreign key)
--   - accounts must be dropped before users
--   - The migration system handles this automatically by reversing order
--
-- If you try to drop users before accounts without CASCADE, you'd get:
--   ERROR: cannot drop table users because other objects depend on it
--   DETAIL: constraint accounts_user_id_fkey on table accounts depends on table users
--
-- The CASCADE keyword handles this, but proper ordering is cleaner.
-- =============================================================================