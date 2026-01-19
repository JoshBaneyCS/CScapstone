-- =============================================================================
-- MIGRATION: 000001_create_users_table.up.sql
-- =============================================================================
-- This migration creates the 'users' table, which stores all user account
-- information for the Casino Capstone application.
--
-- Migration naming convention:
--   NNNNNN_description.up.sql   - Apply the migration (create/alter)
--   NNNNNN_description.down.sql - Rollback the migration (drop/revert)
--
-- The NNNNNN prefix (000001) determines the order migrations are applied.
-- Always use sequential numbers and never reuse or change existing numbers.
--
-- To apply this migration:
--   The application runs migrations automatically on startup.
--   Or manually: migrate -path ./migrations -database $DATABASE_URL up
--
-- To rollback this migration:
--   migrate -path ./migrations -database $DATABASE_URL down 1
-- =============================================================================


-- =============================================================================
-- ENABLE UUID EXTENSION
-- =============================================================================
-- PostgreSQL doesn't have built-in UUID generation, so we need an extension.
-- uuid-ossp provides functions for generating UUIDs (Universally Unique IDs).
--
-- We use UUIDs as primary keys instead of auto-incrementing integers because:
--   1. Security: Sequential IDs reveal information (e.g., user count, order)
--   2. Distributed systems: UUIDs can be generated without a central authority
--   3. Merging data: No conflicts when combining data from multiple sources
--   4. Privacy: Can't guess other users' IDs by incrementing
--
-- CREATE EXTENSION IF NOT EXISTS is idempotent - safe to run multiple times.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- =============================================================================
-- CREATE USERS TABLE
-- =============================================================================
-- This table stores core user account information.
-- Passwords are NEVER stored directly - only bcrypt hashes.

CREATE TABLE users (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    -- id: Unique identifier for each user
    -- Type: UUID (128-bit universally unique identifier)
    -- Default: Auto-generated using uuid_generate_v4() (random UUID)
    --
    -- UUID v4 is randomly generated, making it:
    --   - Extremely unlikely to have collisions (1 in 5.3×10^36)
    --   - Impossible to predict or enumerate
    --   - Safe to expose in URLs and APIs
    
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- =========================================================================
    -- AUTHENTICATION FIELDS
    -- =========================================================================
    
    -- email: User's email address for login and communication
    -- Constraints:
    --   - NOT NULL: Required field
    --   - UNIQUE: No two users can have the same email
    --   - Max 255 characters (standard email length limit)
    --
    -- Note: We store emails in lowercase for consistent matching.
    -- The application normalizes emails before storing/querying.
    
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- username: User's chosen display name and login identifier
    -- Constraints:
    --   - NOT NULL: Required field
    --   - UNIQUE: No two users can have the same username
    --   - Max 50 characters (reasonable for display purposes)
    --
    -- Usernames provide an alternative to email for login and are
    -- displayed in the UI (e.g., "Welcome, JohnDoe!")
    
    username VARCHAR(50) NOT NULL UNIQUE,
    
    -- password_hash: Bcrypt hash of the user's password
    -- Constraints:
    --   - NOT NULL: Required field
    --   - Exactly 60 characters (bcrypt hash length)
    --
    -- SECURITY: We NEVER store plain-text passwords!
    -- Bcrypt is a one-way hash function that:
    --   - Includes a random salt (stored in the hash)
    --   - Is intentionally slow to resist brute-force attacks
    --   - Can be made slower as hardware improves (work factor)
    --
    -- Example bcrypt hash:
    --   $2a$10$N9qo8uLOickgx2ZMRZoMye.IjqQBrkHx9EXNlJZmN8DPmHKemR52W
    --   $2a = algorithm (bcrypt)
    --   $10 = cost factor (2^10 iterations)
    --   Remaining = salt + hash
    
    password_hash CHAR(60) NOT NULL,
    
    -- =========================================================================
    -- PROFILE FIELDS
    -- =========================================================================
    
    -- first_name: User's first/given name
    -- Constraints:
    --   - NOT NULL: Required for personalization
    --   - Max 100 characters (handles long names)
    
    first_name VARCHAR(100) NOT NULL,
    
    -- last_name: User's last/family name
    -- Constraints:
    --   - NOT NULL: Required field
    --   - Max 100 characters (handles long names)
    
    last_name VARCHAR(100) NOT NULL,
    
    -- dob: Date of birth for age verification
    -- Type: DATE (year-month-day, no time component)
    -- Constraints:
    --   - NOT NULL: Required for 21+ age gate
    --
    -- IMPORTANT: This is used for legal compliance (21+ gambling age).
    -- Age verification happens server-side at registration:
    --   - Calculate age from DOB
    --   - If under 21, reject registration
    --
    -- We store the full DOB (not just "is 21+") because:
    --   - Users who register at 20 will eventually turn 21
    --   - Compliance audits may require verification
    --   - Some features might need exact age
    
    dob DATE NOT NULL,
    
    -- =========================================================================
    -- TIMESTAMP FIELDS
    -- =========================================================================
    
    -- created_at: When the user account was created
    -- Type: TIMESTAMPTZ (timestamp with time zone)
    -- Default: Current time when row is inserted
    --
    -- TIMESTAMPTZ stores the time in UTC internally but displays
    -- in the client's timezone. This prevents timezone-related bugs.
    --
    -- NOW() returns the current timestamp at the start of the transaction.
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- CREATE INDEXES
-- =============================================================================
-- Indexes speed up queries by creating a sorted data structure.
-- Without indexes, the database must scan every row (slow for large tables).
--
-- We create indexes on columns we frequently search by.
-- The UNIQUE constraints already create indexes on email and username.

-- Index on email (lowercase) for case-insensitive login lookups
-- This allows efficient queries like: WHERE LOWER(email) = LOWER($1)
-- The UNIQUE constraint creates an index, but this one is for lowercase matching

CREATE INDEX idx_users_email_lower ON users (LOWER(email));

-- Index on username (lowercase) for case-insensitive login lookups
-- Allows users to log in with "JohnDoe" even if stored as "johndoe"

CREATE INDEX idx_users_username_lower ON users (LOWER(username));

-- Index on created_at for time-based queries (e.g., "users who signed up this week")
-- Useful for analytics and admin features

CREATE INDEX idx_users_created_at ON users (created_at);


-- =============================================================================
-- ADD TABLE COMMENT
-- =============================================================================
-- Comments help developers understand the table's purpose.
-- Visible in database tools like pgAdmin, DBeaver, etc.

COMMENT ON TABLE users IS 'Stores user account information for the Casino Capstone application. Passwords are stored as bcrypt hashes. DOB is used for 21+ age verification.';

COMMENT ON COLUMN users.id IS 'Unique identifier (UUID v4) for the user';
COMMENT ON COLUMN users.email IS 'User email address for login and notifications (unique, case-insensitive)';
COMMENT ON COLUMN users.username IS 'User display name and alternative login identifier (unique, case-insensitive)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hash of user password (60 characters)';
COMMENT ON COLUMN users.first_name IS 'User first/given name';
COMMENT ON COLUMN users.last_name IS 'User last/family name';
COMMENT ON COLUMN users.dob IS 'Date of birth for 21+ age verification';
COMMENT ON COLUMN users.created_at IS 'Timestamp when the account was created';