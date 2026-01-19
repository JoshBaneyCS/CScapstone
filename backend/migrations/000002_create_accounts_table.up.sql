-- =============================================================================
-- MIGRATION: 000002_create_accounts_table.up.sql
-- =============================================================================
-- This migration creates the 'accounts' table, which stores financial
-- information for each user, primarily their casino bankroll.
--
-- Design Decision: Separate accounts table vs. bankroll column in users table
--
-- We use a separate accounts table because:
--   1. Separation of concerns: User profile data vs. financial data
--   2. Different access patterns: Profile rarely changes, bankroll changes often
--   3. Future flexibility: Could add multiple account types (e.g., bonus balance)
--   4. Audit requirements: Financial data often has different compliance needs
--   5. Locking: Can lock account row without locking user profile
--
-- IMPORTANT: Money is stored as INTEGER CENTS, not floating-point dollars!
-- This prevents floating-point precision errors in financial calculations.
-- Example: $25.00 is stored as 2500 cents
--          $2500.00 is stored as 250000 cents
-- =============================================================================


-- =============================================================================
-- CREATE ACCOUNTS TABLE
-- =============================================================================
-- Each user has exactly one account (1:1 relationship with users table).
-- The account tracks their casino bankroll balance.

CREATE TABLE accounts (
    -- =========================================================================
    -- PRIMARY KEY / FOREIGN KEY
    -- =========================================================================
    -- user_id: Links this account to a user
    -- This is BOTH the primary key AND a foreign key to users.id
    --
    -- Why user_id as PK instead of separate account_id?
    --   - Enforces 1:1 relationship (each user has exactly one account)
    --   - Simplifies queries (no need to join on separate ID)
    --   - User ID already uniquely identifies the account
    --
    -- REFERENCES users(id): Foreign key constraint
    --   - Ensures user_id must exist in users table
    --   - Prevents orphan accounts
    --
    -- ON DELETE CASCADE: If user is deleted, their account is also deleted
    --   - Maintains referential integrity
    --   - Alternative: ON DELETE RESTRICT would prevent user deletion
    --     if they have an account (safer but more complex to manage)
    
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- =========================================================================
    -- FINANCIAL FIELDS
    -- =========================================================================
    
    -- bankroll_cents: User's current balance in CENTS (not dollars!)
    -- Type: BIGINT (8 bytes, range: -9.2 quintillion to +9.2 quintillion)
    --
    -- WHY CENTS (integers) instead of DOLLARS (decimals)?
    -- ------------------------------------------------
    -- Floating-point numbers (DECIMAL, FLOAT, DOUBLE) have precision issues:
    --   0.1 + 0.2 = 0.30000000000000004 (not 0.3!)
    --
    -- In financial applications, this can cause:
    --   - Rounding errors that accumulate over time
    --   - Balances that are off by fractions of a cent
    --   - Failed equality checks (0.30 != 0.30000000000000004)
    --
    -- Using integers (cents) eliminates these issues:
    --   10 + 20 = 30 (always exact!)
    --
    -- Conversion:
    --   To store: dollars * 100 = cents (e.g., $25.50 → 2550)
    --   To display: cents / 100 = dollars (e.g., 2550 → $25.50)
    --
    -- WHY BIGINT instead of INTEGER?
    -- ------------------------------------------------
    -- INTEGER max: 2,147,483,647 cents = $21,474,836.47
    -- BIGINT max: 9,223,372,036,854,775,807 cents = ~$92 quadrillion
    --
    -- While INTEGER is probably enough for a casino app, BIGINT:
    --   - Handles any realistic balance
    --   - Prevents overflow errors
    --   - Is standard practice for financial applications
    --   - Costs only 4 extra bytes per row
    --
    -- Default value: 250000 cents = $2,500.00 (starting bankroll)
    -- CHECK constraint: Balance cannot go negative
    --   - Prevents users from betting more than they have
    --   - Enforced at database level as a safety net
    --   - Application should also check before allowing bets
    
    bankroll_cents BIGINT NOT NULL DEFAULT 250000 CHECK (bankroll_cents >= 0),
    
    -- =========================================================================
    -- TIMESTAMP FIELDS
    -- =========================================================================
    
    -- updated_at: When the bankroll was last modified
    -- Type: TIMESTAMPTZ (timestamp with time zone)
    -- Default: Current time when row is inserted
    --
    -- This is updated whenever the bankroll changes:
    --   - After winning a game
    --   - After losing a game
    --   - After any balance adjustment
    --
    -- Useful for:
    --   - Audit trails
    --   - Detecting stale data
    --   - Analytics (when do users play most?)
    
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- CREATE TRIGGER FOR updated_at AUTO-UPDATE
-- =============================================================================
-- This trigger automatically updates the updated_at column whenever
-- the row is modified. This ensures updated_at is always accurate
-- without requiring the application to remember to set it.
--
-- How triggers work:
--   1. Define a function that performs the action
--   2. Create a trigger that calls the function on specified events
--
-- BEFORE UPDATE: The function runs before the UPDATE is applied
-- FOR EACH ROW: The function runs once per row being updated

-- Step 1: Create the trigger function
-- This function sets updated_at to the current timestamp
-- NEW refers to the row being updated (with new values)

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    -- Set the updated_at column to the current timestamp
    NEW.updated_at = NOW();
    -- Return the modified row (required for BEFORE triggers)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger that calls the function
-- This trigger fires BEFORE any UPDATE on the accounts table

CREATE TRIGGER trigger_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- CREATE INDEXES
-- =============================================================================
-- The primary key (user_id) already has an index.
-- We add an index on updated_at for time-based queries.

-- Index for finding recently active accounts
-- Useful for queries like "users who played in the last hour"

CREATE INDEX idx_accounts_updated_at ON accounts (updated_at);


-- =============================================================================
-- ADD TABLE AND COLUMN COMMENTS
-- =============================================================================
-- Documentation for developers and database tools

COMMENT ON TABLE accounts IS 'Stores user financial information, primarily casino bankroll. Balance is stored in cents (integer) to avoid floating-point precision errors.';

COMMENT ON COLUMN accounts.user_id IS 'References users.id - each user has exactly one account (1:1 relationship)';
COMMENT ON COLUMN accounts.bankroll_cents IS 'User balance in cents (not dollars). $25.00 = 2500 cents. Default starting balance is $2,500 (250000 cents).';
COMMENT ON COLUMN accounts.updated_at IS 'Last time the bankroll was modified (auto-updated by trigger)';

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function that automatically sets updated_at to NOW() on row update';
COMMENT ON TRIGGER trigger_accounts_updated_at ON accounts IS 'Automatically updates updated_at column when account is modified';