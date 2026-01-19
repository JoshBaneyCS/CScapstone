-- =============================================================================
-- MIGRATION: 000001_create_users_table.down.sql
-- =============================================================================
-- This is the ROLLBACK migration for the users table.
-- It undoes everything done in 000001_create_users_table.up.sql
--
-- DOWN migrations are used when:
--   1. A migration has a bug and needs to be fixed
--   2. Rolling back a deployment to a previous version
--   3. Development: testing migrations repeatedly
--
-- IMPORTANT: Running this migration DELETES ALL USER DATA!
-- Only use in development or when you're certain you want to rollback.
--
-- To rollback this migration:
--   migrate -path ./migrations -database $DATABASE_URL down 1
--
-- The "down 1" means rollback exactly 1 migration.
-- You can also use "down" to rollback all migrations.
-- =============================================================================


-- =============================================================================
-- DROP INDEXES
-- =============================================================================
-- We drop indexes first because they depend on the table.
-- Actually, DROP TABLE CASCADE would handle this automatically,
-- but being explicit is better for documentation and safety.
--
-- IF EXISTS prevents errors if the index was already dropped or never created.

-- Drop the case-insensitive email lookup index
DROP INDEX IF EXISTS idx_users_email_lower;

-- Drop the case-insensitive username lookup index
DROP INDEX IF EXISTS idx_users_username_lower;

-- Drop the created_at index for time-based queries
DROP INDEX IF EXISTS idx_users_created_at;


-- =============================================================================
-- DROP USERS TABLE
-- =============================================================================
-- This removes the entire users table and ALL DATA in it.
--
-- CASCADE: Also drops objects that depend on this table:
--   - Foreign keys referencing this table
--   - Views that reference this table
--   - Any other dependent objects
--
-- Without CASCADE, the DROP would fail if other objects reference this table.
-- With CASCADE, dependent objects are also dropped (be careful!).
--
-- IF EXISTS: Prevents an error if the table doesn't exist.
-- This makes the migration idempotent (safe to run multiple times).

DROP TABLE IF EXISTS users CASCADE;


-- =============================================================================
-- NOTE: We do NOT drop the uuid-ossp extension
-- =============================================================================
-- We intentionally leave the uuid-ossp extension in place because:
--
--   1. Other tables may depend on it (accounts table uses UUIDs too)
--   2. It's a system extension that doesn't store data
--   3. Dropping it could break other parts of the application
--   4. It's harmless to have it installed even if unused
--
-- If you truly want to remove it, you can run manually:
--   DROP EXTENSION IF EXISTS "uuid-ossp";
--
-- But this is almost never necessary or desirable.
-- =============================================================================