# Database Provisioning

This directory contains the PostgreSQL schema and migration scripts for the Casino Capstone project.

## Files
- `database/schema.sql`: Idempotent DDL for creating tables, extensions, and triggers.
- `database/migrations/001_init.sql`: One-shot initialization migration wrapped in a transaction.

## Provisioning (Dedicated Postgres Instance)
You can apply the schema using `psql` against your hosted PostgreSQL instance.

Example using `DATABASE_URL`:
```bash
export DATABASE_URL='postgres://USER:PASSWORD@HOST:5432/DBNAME?sslmode=disable'
psql "$DATABASE_URL" -f CScapstone/database/schema.sql
```

Example using discrete variables:
```bash
export DB_HOST="YOUR_DB_HOST"
export DB_PORT="5432"
export DB_NAME="YOUR_DB_NAME"
export DB_USER="YOUR_DB_USER"
export DB_PASSWORD="YOUR_DB_PASSWORD"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f CScapstone/database/schema.sql
```

## Kubernetes Secrets and Config
The application should read connection details from Kubernetes secrets or environment variables.

Recommended variables:
- `DATABASE_URL` (preferred)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

If you are using the existing Kubernetes manifests, `infra/k8s/base/postgres/secrets.yaml` and `infra/k8s/base/backend/configmap.yaml` show the expected shape for these values.

## Schema Behavior
- `bankroll_cents` starts at `250000` (represents $2,500.00).
- A trigger deletes the user automatically when `bankroll_cents <= 0`.
- `updated_at` is automatically updated on every row update.

If a user is deleted due to bankroll reaching zero, API calls that depend on that user should return a 404 or 401 and clear any active session.

## Endpoint Integration Guidance
The Blackjack API endpoints are documented in `blackjack-api/README.md`:
- `POST /blackjack/start`
- `POST /blackjack/hit`
- `POST /blackjack/stand`
- `GET /blackjack/state`

Recommended flow for blackjack:
- On `POST /blackjack/start` with a bet, verify the user and deduct the bet from `bankroll_cents`.
- When the round resolves, increment `blackjack_wins` or `blackjack_losses` based on the final status.
- If the user wins, credit winnings back to `bankroll_cents`.
- Always return the updated bankroll to the caller.

Poker should follow the same bankroll rules:
- Deduct bet on hand start.
- Increment `poker_wins` or `poker_losses` on resolution.
- Credit winnings on wins.

Bankroll persists across games by storing all updates in `bankroll_cents`.

## Password Storage
Store only hashed passwords in `password_hash` using bcrypt or Argon2. Never store plaintext passwords.
