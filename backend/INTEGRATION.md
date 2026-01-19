# Backend Integration Guide

This guide explains how to integrate your game with the Casino Capstone Go backend API.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Making API Requests](#making-api-requests)
4. [Bankroll Operations](#bankroll-operations)
5. [Adding New Endpoints](#adding-new-endpoints)
6. [Database Operations](#database-operations)
7. [Error Handling](#error-handling)
8. [Example Integrations](#example-integrations)

---

## API Overview

### Base URL

```
Development: http://localhost:8080/api
Production:  https://umgcgroupe.com/api
```

### Content Type

All requests and responses use JSON:

```
Content-Type: application/json
```

### Authentication

The API uses JWT tokens stored in HttpOnly cookies. Include credentials in all requests:

```python
# Python
requests.get(url, cookies=cookies)  # or
requests.get(url, credentials='include')  # fetch API

# JavaScript
fetch(url, { credentials: 'include' })
```

---

## Authentication

### Endpoints

#### Register User

```http
POST /api/auth/register
```

**Request:**
```json
{
    "email": "player@example.com",
    "username": "player123",
    "password": "securepassword",
    "firstName": "John",
    "lastName": "Doe",
    "dob": "1990-05-15"
}
```

**Response (201 Created):**
```json
{
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "player@example.com",
        "username": "player123",
        "firstName": "John",
        "lastName": "Doe",
        "dob": "1990-05-15",
        "createdAt": "2024-01-15T10:30:00Z"
    },
    "bankrollCents": 250000
}
```

**Errors:**
| Code | Message |
|------|---------|
| 400 | Validation error (missing fields, invalid format) |
| 400 | You must be at least 21 years old to register |
| 409 | Email already registered |
| 409 | Username already taken |

---

#### Login

```http
POST /api/auth/login
```

**Request (with email):**
```json
{
    "email": "player@example.com",
    "password": "securepassword"
}
```

**Request (with username):**
```json
{
    "username": "player123",
    "password": "securepassword"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "player@example.com",
        "username": "player123",
        "firstName": "John",
        "lastName": "Doe",
        "dob": "1990-05-15",
        "createdAt": "2024-01-15T10:30:00Z"
    },
    "bankrollCents": 248500
}
```

**Note:** Sets `casino_session` HttpOnly cookie on success.

---

#### Get Current User

```http
GET /api/auth/me
```

**Requires:** Valid session cookie

**Response (200 OK):**
```json
{
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "player@example.com",
        "username": "player123",
        "firstName": "John",
        "lastName": "Doe",
        "dob": "1990-05-15",
        "createdAt": "2024-01-15T10:30:00Z"
    },
    "bankrollCents": 248500
}
```

---

#### Logout

```http
POST /api/auth/logout
```

**Response (200 OK):**
```json
{
    "message": "Logged out successfully"
}
```

**Note:** Clears the session cookie.

---

### Games Endpoints

#### List Games

```http
GET /api/games
```

**Requires:** Valid session cookie

**Response (200 OK):**
```json
{
    "games": [
        {
            "id": "blackjack",
            "name": "Blackjack",
            "description": "Classic card game...",
            "minBet": 100,
            "maxBet": 10000,
            "enabled": true,
            "imageUrl": "/images/games/blackjack.png"
        },
        {
            "id": "poker",
            "name": "Texas Hold'em Poker",
            "description": "The world's most popular poker game...",
            "minBet": 500,
            "maxBet": 50000,
            "enabled": true,
            "imageUrl": "/images/games/poker.png"
        }
    ],
    "count": 2
}
```

---

## Making API Requests

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8080/api"

class CasinoAPI:
    def __init__(self):
        # Session maintains cookies across requests
        self.session = requests.Session()
    
    def register(self, email, username, password, first_name, last_name, dob):
        """Register a new user."""
        response = self.session.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
            "dob": dob  # Format: "YYYY-MM-DD"
        })
        return response.json()
    
    def login(self, email=None, username=None, password=None):
        """Login with email or username."""
        payload = {"password": password}
        if email:
            payload["email"] = email
        else:
            payload["username"] = username
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=payload)
        return response.json()
    
    def get_me(self):
        """Get current user and bankroll."""
        response = self.session.get(f"{BASE_URL}/auth/me")
        return response.json()
    
    def get_games(self):
        """Get list of available games."""
        response = self.session.get(f"{BASE_URL}/games")
        return response.json()
    
    def logout(self):
        """Logout current user."""
        response = self.session.post(f"{BASE_URL}/auth/logout")
        return response.json()


# Usage example
api = CasinoAPI()

# Register
result = api.register(
    email="test@example.com",
    username="testuser",
    password="password123",
    first_name="Test",
    last_name="User",
    dob="1990-01-15"
)
print(f"Registered! User ID: {result['user']['id']}")
print(f"Starting bankroll: ${result['bankrollCents'] / 100:.2f}")

# Get current user (uses cookie from register)
me = api.get_me()
print(f"Current bankroll: ${me['bankrollCents'] / 100:.2f}")

# Get games
games = api.get_games()
for game in games['games']:
    print(f"- {game['name']}: ${game['minBet']/100:.2f} - ${game['maxBet']/100:.2f}")
```

### cURL Examples

```bash
# Store cookies in a file
COOKIE_FILE="cookies.txt"

# Register
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -c $COOKIE_FILE \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "firstName": "Test",
    "lastName": "User",
    "dob": "1990-01-15"
  }'

# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -c $COOKIE_FILE \
  -d '{"email": "test@example.com", "password": "password123"}'

# Get current user
curl http://localhost:8080/api/auth/me -b $COOKIE_FILE

# Get games
curl http://localhost:8080/api/games -b $COOKIE_FILE

# Logout
curl -X POST http://localhost:8080/api/auth/logout -b $COOKIE_FILE -c $COOKIE_FILE
```

---

## Bankroll Operations

### Understanding Money Storage

**IMPORTANT:** All money is stored in **CENTS** (integers), not dollars.

```
$1.00    = 100 cents
$25.50   = 2550 cents
$2,500   = 250000 cents (starting bankroll)
```

### Why Cents?

Floating-point arithmetic has precision issues:
```python
>>> 0.1 + 0.2
0.30000000000000004  # Wrong!

>>> 10 + 20
30  # Always correct!
```

### Converting Between Cents and Dollars

```python
# Cents to dollars (for display)
def cents_to_dollars(cents: int) -> float:
    return cents / 100

# Dollars to cents (for storage)
def dollars_to_cents(dollars: float) -> int:
    return int(dollars * 100)

# Format for display
def format_currency(cents: int) -> str:
    return f"${cents / 100:,.2f}"

# Examples
print(format_currency(250000))  # $2,500.00
print(format_currency(1550))    # $15.50
```

### Bankroll Database Operations

For direct database access in your game:

```python
import psycopg2
from contextlib import contextmanager

DATABASE_URL = "postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db"

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def get_bankroll(user_id: str) -> int:
    """
    Get user's bankroll in cents.
    
    Args:
        user_id: UUID string of the user
        
    Returns:
        Bankroll in cents
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT bankroll_cents FROM accounts WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            return result[0] if result else 0


def deduct_bet(user_id: str, bet_cents: int) -> bool:
    """
    Deduct bet from bankroll. Returns False if insufficient funds.
    
    Args:
        user_id: UUID string of the user
        bet_cents: Amount to deduct in cents
        
    Returns:
        True if successful, False if insufficient funds
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Use FOR UPDATE to lock the row during transaction
            cur.execute(
                "SELECT bankroll_cents FROM accounts WHERE user_id = %s FOR UPDATE",
                (user_id,)
            )
            result = cur.fetchone()
            
            if not result or result[0] < bet_cents:
                return False
            
            cur.execute(
                """
                UPDATE accounts 
                SET bankroll_cents = bankroll_cents - %s,
                    updated_at = NOW()
                WHERE user_id = %s
                """,
                (bet_cents, user_id)
            )
            conn.commit()
            return True


def add_winnings(user_id: str, amount_cents: int) -> int:
    """
    Add winnings to bankroll.
    
    Args:
        user_id: UUID string of the user
        amount_cents: Amount to add in cents
        
    Returns:
        New bankroll balance in cents
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE accounts 
                SET bankroll_cents = bankroll_cents + %s,
                    updated_at = NOW()
                WHERE user_id = %s
                RETURNING bankroll_cents
                """,
                (amount_cents, user_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else 0
```

### Game Flow with Bankroll

```python
def play_game(user_id: str, bet_dollars: float) -> dict:
    """
    Complete game flow with bankroll management.
    
    Args:
        user_id: Player's UUID
        bet_dollars: Bet amount in dollars
        
    Returns:
        Game result dictionary
    """
    bet_cents = int(bet_dollars * 100)
    
    # Step 1: Validate bet amount
    if bet_cents < 100:  # $1.00 minimum
        return {"error": "Minimum bet is $1.00"}
    
    if bet_cents > 10000:  # $100.00 maximum
        return {"error": "Maximum bet is $100.00"}
    
    # Step 2: Check and deduct bankroll
    if not deduct_bet(user_id, bet_cents):
        return {"error": "Insufficient funds"}
    
    # Step 3: Run your game logic
    # ... your game code here ...
    won = run_game_logic()  # Returns True/False
    
    # Step 4: Calculate and pay winnings
    if won:
        winnings_cents = bet_cents * 2  # 1:1 payout
        new_balance = add_winnings(user_id, winnings_cents)
        return {
            "outcome": "win",
            "bet_cents": bet_cents,
            "winnings_cents": winnings_cents,
            "bankroll_cents": new_balance
        }
    else:
        return {
            "outcome": "lose",
            "bet_cents": bet_cents,
            "winnings_cents": 0,
            "bankroll_cents": get_bankroll(user_id)
        }
```

---

## Adding New Endpoints

If you need to add game-specific endpoints to the backend:

### Step 1: Create Handler

Create a new file `backend/internal/handlers/your_game.go`:

```go
package handlers

import (
    "encoding/json"
    "net/http"
    
    "github.com/JoshBaneyCS/CScapstone/backend/internal/db"
    "github.com/JoshBaneyCS/CScapstone/backend/internal/middleware"
)

type YourGameHandler struct {
    db *db.Database
}

func NewYourGameHandler(database *db.Database) *YourGameHandler {
    return &YourGameHandler{db: database}
}

// PlayRequest represents the request body for playing the game
type PlayRequest struct {
    BetCents int64 `json:"betCents"`
    // Add game-specific fields
}

// PlayResponse represents the game result
type PlayResponse struct {
    Success       bool   `json:"success"`
    Outcome       string `json:"outcome"`
    BetCents      int64  `json:"betCents"`
    WinningsCents int64  `json:"winningsCents"`
    BankrollCents int64  `json:"bankrollCents"`
    // Add game-specific fields
}

func (h *YourGameHandler) Play(w http.ResponseWriter, r *http.Request) {
    // Get user ID from context (set by auth middleware)
    userID, ok := middleware.GetUserIDFromContext(r.Context())
    if !ok {
        writeError(w, http.StatusUnauthorized, "Unauthorized", "AUTH_REQUIRED")
        return
    }
    
    // Parse request
    var req PlayRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        writeError(w, http.StatusBadRequest, "Invalid request", "INVALID_JSON")
        return
    }
    
    // Validate bet
    if req.BetCents < 100 {
        writeError(w, http.StatusBadRequest, "Minimum bet is $1.00", "BET_TOO_LOW")
        return
    }
    
    // Deduct bet from bankroll
    // ... implement bankroll deduction ...
    
    // Run game logic
    // ... your game logic ...
    
    // Return result
    response := PlayResponse{
        Success:       true,
        Outcome:       "win",
        BetCents:      req.BetCents,
        WinningsCents: req.BetCents * 2,
        BankrollCents: newBalance,
    }
    
    writeJSON(w, http.StatusOK, response)
}
```

### Step 2: Register Route

Add to `backend/cmd/api/main.go`:

```go
// In the route setup section:
yourGameHandler := handlers.NewYourGameHandler(database)

r.Route("/api/games/yourgame", func(r chi.Router) {
    r.Use(middleware.AuthMiddleware(jwtService))
    r.Post("/play", yourGameHandler.Play)
    r.Get("/state", yourGameHandler.GetState)  // If needed
})
```

---

## Database Operations

### Direct Database Access

Your game can access the database directly using the same connection string:

```
postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db
```

When running in Docker, use `db` as the host:

```
postgres://casino_admin:casino_secret_password_123@db:5432/casino_db
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Accounts table (bankroll)
CREATE TABLE accounts (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bankroll_cents BIGINT NOT NULL DEFAULT 250000 CHECK (bankroll_cents >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Adding Game-Specific Tables

If you need to store game state or history:

```sql
-- Example: Game sessions table
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    bet_cents BIGINT NOT NULL,
    result VARCHAR(20),  -- 'win', 'lose', 'push'
    winnings_cents BIGINT DEFAULT 0,
    game_data JSONB,  -- Store game-specific state
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Index for querying user's game history
CREATE INDEX idx_game_sessions_user ON game_sessions(user_id, created_at DESC);
```

Create a migration file `backend/migrations/000003_create_game_sessions.up.sql`.

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_CODE"
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_JSON` | 400 | Request body is not valid JSON |
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `BET_TOO_LOW` | 400 | Bet below minimum |
| `BET_TOO_HIGH` | 400 | Bet above maximum |
| `INSUFFICIENT_FUNDS` | 400 | Not enough bankroll |
| `AUTH_REQUIRED` | 401 | Authentication required |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Server error |

### Handling Errors in Python

```python
import requests

def safe_api_call(func):
    """Decorator for handling API errors."""
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            data = response.json()
            
            if not response.ok:
                error_code = data.get('code', 'UNKNOWN')
                error_msg = data.get('error', 'Unknown error')
                raise APIError(error_code, error_msg, response.status_code)
            
            return data
        except requests.RequestException as e:
            raise APIError('NETWORK_ERROR', str(e), 0)
    return wrapper


class APIError(Exception):
    def __init__(self, code, message, status_code):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")


# Usage
try:
    result = api.play_game(bet_cents=5000)
except APIError as e:
    if e.code == 'INSUFFICIENT_FUNDS':
        print("Not enough money!")
    elif e.code == 'AUTH_REQUIRED':
        print("Please log in first")
    else:
        print(f"Error: {e.message}")
```

---

## Example Integrations

### Complete Blackjack Integration

See `/INTEGRATION.md` for a complete Python Blackjack example.

### Complete Poker Integration

See `/INTEGRATION.md` for a complete C# Poker example.

---

## Questions?

- Check the root `/INTEGRATION.md` for language-specific examples
- Check `/frontend/INTEGRATION.md` for frontend integration
- Create a GitHub issue for help

Happy coding! 🎰