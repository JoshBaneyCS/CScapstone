# 🎰 Casino Capstone - Integration Guide

Welcome, teammates! This guide explains how to integrate your games (Blackjack, Poker, etc.) with the Casino Capstone platform. Whether you're building in **Python**, **C#**, or **C++**, this document has everything you need.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Authentication Flow](#authentication-flow)
5. [Bankroll Management](#bankroll-management)
6. [Integration Patterns](#integration-patterns)
7. [Python Integration](#python-integration)
8. [C# Integration](#c-integration)
9. [C++ Integration](#c-integration-1)
10. [Database Access](#database-access)
11. [Environment Variables](#environment-variables)
12. [Testing Your Integration](#testing-your-integration)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CASINO CAPSTONE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐ │
│  │   Frontend   │────▶│   Backend    │────▶│        PostgreSQL            │ │
│  │   (React)    │◀────│   (Go API)   │◀────│        Database              │ │
│  │  Port: 5173  │     │  Port: 8080  │     │        Port: 5432            │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────────┘ │
│         │                    │                         │                     │
│         │                    │                         │                     │
│         │              ┌─────▼─────┐                   │                     │
│         │              │   YOUR    │                   │                     │
│         └─────────────▶│   GAME    │◀──────────────────┘                     │
│                        │ (Py/C#/C++)│                                        │
│                        └───────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| Frontend | React/TypeScript | 5173 | User interface |
| Backend | Go REST API | 8080 | Auth, bankroll, game registry |
| Database | PostgreSQL 16 | 5432 | User data, accounts, game history |
| Your Game | Python/C#/C++ | Varies | Game logic implementation |

---

## Quick Start

### 1. Clone and Run the Platform

```bash
# Clone the repository
git clone https://github.com/JoshBaneyCS/CScapstone.git
cd CScapstone

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

### 2. Verify Services Are Running

```bash
# Check API health
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","service":"casino-api"}
```

### 3. Create a Test User

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testplayer@example.com",
    "username": "testplayer",
    "password": "testpassword123",
    "firstName": "Test",
    "lastName": "Player",
    "dob": "1990-01-15"
  }'
```

---

## API Reference

### Base URL

```
http://localhost:8080/api
```

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new user | No |
| POST | `/auth/login` | Login user | No |
| POST | `/auth/logout` | Logout user | Yes |
| GET | `/auth/me` | Get current user + bankroll | Yes |

### Game Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/games` | List all games | Yes |

### Bankroll Endpoints (For Your Games)

These endpoints need to be added for game integration:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/bankroll/bet` | Deduct bet from bankroll | Yes |
| POST | `/bankroll/win` | Add winnings to bankroll | Yes |
| GET | `/bankroll/balance` | Get current balance | Yes |

---

## Authentication Flow

### How Auth Works

1. User logs in via frontend → Backend validates → JWT cookie set
2. All subsequent requests include the cookie automatically
3. For game servers, you'll need to validate the session

### Session Cookie

```
Name: casino_session
Type: HttpOnly (JavaScript cannot access)
Contains: JWT with user_id
Expires: 24 hours
```

### Validating a User Session (For Your Game Server)

Your game needs to verify the user is authenticated. Two approaches:

#### Option A: Proxy Through Backend (Recommended)

Your game calls the backend API which handles auth:

```
User → Frontend → Backend API → Your Game
                      ↓
                 (validates JWT)
```

#### Option B: Direct JWT Validation

If your game needs to validate JWTs directly:

```python
# JWT Secret (from .env)
JWT_SECRET = "your-super-secret-jwt-key-change-in-production-abc123"

# JWT contains:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "exp": 1705312800,  # Expiration timestamp
    "iat": 1705226400,  # Issued at timestamp
    "iss": "casino-api"
}
```

---

## Bankroll Management

### Key Concept: Money is Stored in CENTS

```
$25.00  = 2500 cents
$100.50 = 10050 cents
$2,500  = 250000 cents (starting bankroll)
```

### Why Cents?

Floating-point math has precision issues:
```
0.1 + 0.2 = 0.30000000000000004  ❌
10 + 20 = 30                      ✅
```

### Bankroll Operations

When a player places a bet:

```
1. CHECK: Does user have enough bankroll?
2. DEDUCT: Subtract bet amount from bankroll
3. PLAY: Run the game logic
4. RESULT: Win or lose
5. UPDATE: Add winnings (if any) to bankroll
6. RECORD: Log the transaction for audit
```

### Database Tables

```sql
-- Users table
users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(50) UNIQUE,
    password_hash CHAR(60),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    created_at TIMESTAMPTZ
)

-- Accounts table (bankroll)
accounts (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    bankroll_cents BIGINT DEFAULT 250000,
    updated_at TIMESTAMPTZ
)
```

---

## Integration Patterns

### Pattern 1: HTTP API Integration (Simplest)

Your game exposes an HTTP API that the backend calls:

```
Frontend → Backend → Your Game API
              ↓
           Database
```

**Best for:** Simple games, stateless interactions

### Pattern 2: Shared Database (Recommended for Capstone)

Your game reads/writes directly to the PostgreSQL database:

```
Frontend → Backend ←→ Database ←→ Your Game
```

**Best for:** Real-time balance updates, simpler architecture

### Pattern 3: Message Queue (Advanced)

Use Redis or RabbitMQ for async communication:

```
Frontend → Backend → Message Queue → Your Game
                           ↓
                       Database
```

**Best for:** High-throughput, decoupled systems

---

## Python Integration

### Installation

```bash
# Required packages
pip install psycopg2-binary  # PostgreSQL driver
pip install requests         # HTTP client (if using API pattern)
pip install python-dotenv    # Environment variables
pip install pyjwt            # JWT validation (if needed)
```

### Database Connection

```python
"""
casino_db.py - Database connection for Python games
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection string
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db'
)

def get_connection():
    """
    Get a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Example:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
    """
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_user_bankroll(user_id: str) -> int:
    """
    Get user's current bankroll in cents.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        int: Bankroll in cents (e.g., 250000 = $2,500.00)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bankroll_cents FROM accounts WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        return result['bankroll_cents'] if result else 0
    finally:
        conn.close()


def update_bankroll(user_id: str, amount_cents: int) -> int:
    """
    Update user's bankroll (add or subtract).
    
    Args:
        user_id: UUID of the user
        amount_cents: Amount to add (positive) or subtract (negative)
        
    Returns:
        int: New bankroll balance in cents
        
    Example:
        # Player bets $10
        update_bankroll(user_id, -1000)
        
        # Player wins $25
        update_bankroll(user_id, 2500)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE accounts 
            SET bankroll_cents = bankroll_cents + %s,
                updated_at = NOW()
            WHERE user_id = %s
            RETURNING bankroll_cents
            """,
            (amount_cents, user_id)
        )
        result = cursor.fetchone()
        conn.commit()
        return result['bankroll_cents'] if result else 0
    finally:
        conn.close()


def place_bet(user_id: str, bet_amount_cents: int) -> bool:
    """
    Attempt to place a bet (deduct from bankroll).
    
    Args:
        user_id: UUID of the user
        bet_amount_cents: Bet amount in cents
        
    Returns:
        bool: True if bet was placed, False if insufficient funds
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Check current balance
        cursor.execute(
            "SELECT bankroll_cents FROM accounts WHERE user_id = %s FOR UPDATE",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result or result['bankroll_cents'] < bet_amount_cents:
            return False  # Insufficient funds
        
        # Deduct bet
        cursor.execute(
            """
            UPDATE accounts 
            SET bankroll_cents = bankroll_cents - %s,
                updated_at = NOW()
            WHERE user_id = %s
            """,
            (bet_amount_cents, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()
```

### Example: Blackjack Game Integration

```python
"""
blackjack_game.py - Example Blackjack game with bankroll integration
"""
import random
from casino_db import get_user_bankroll, place_bet, update_bankroll

# Card values
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
}


def calculate_hand(cards: list) -> int:
    """Calculate the value of a blackjack hand."""
    value = sum(CARD_VALUES[card] for card in cards)
    aces = cards.count('A')
    
    # Adjust for aces (count as 1 instead of 11 if over 21)
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    
    return value


def play_blackjack(user_id: str, bet_cents: int) -> dict:
    """
    Play a hand of Blackjack.
    
    Args:
        user_id: UUID of the player
        bet_cents: Bet amount in cents
        
    Returns:
        dict: Game result with outcome and new balance
    """
    # Step 1: Check and deduct bet
    if not place_bet(user_id, bet_cents):
        return {
            'success': False,
            'error': 'Insufficient funds',
            'bankroll_cents': get_user_bankroll(user_id)
        }
    
    # Step 2: Deal cards
    deck = list(CARD_VALUES.keys()) * 4
    random.shuffle(deck)
    
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    player_value = calculate_hand(player_hand)
    dealer_value = calculate_hand(dealer_hand)
    
    # Step 3: Simple game logic (player stands, dealer draws to 17)
    while dealer_value < 17:
        dealer_hand.append(deck.pop())
        dealer_value = calculate_hand(dealer_hand)
    
    # Step 4: Determine winner
    if player_value > 21:
        outcome = 'lose'
        winnings = 0
    elif dealer_value > 21:
        outcome = 'win'
        winnings = bet_cents * 2  # Return bet + winnings
    elif player_value > dealer_value:
        outcome = 'win'
        winnings = bet_cents * 2
    elif player_value < dealer_value:
        outcome = 'lose'
        winnings = 0
    else:
        outcome = 'push'
        winnings = bet_cents  # Return original bet
    
    # Step 5: Update bankroll with winnings
    if winnings > 0:
        update_bankroll(user_id, winnings)
    
    new_balance = get_user_bankroll(user_id)
    
    return {
        'success': True,
        'outcome': outcome,
        'player_hand': player_hand,
        'player_value': player_value,
        'dealer_hand': dealer_hand,
        'dealer_value': dealer_value,
        'bet_cents': bet_cents,
        'winnings_cents': winnings,
        'bankroll_cents': new_balance
    }


# Example usage
if __name__ == '__main__':
    # Test with a user ID (replace with actual UUID)
    test_user_id = '550e8400-e29b-41d4-a716-446655440000'
    
    result = play_blackjack(test_user_id, 1000)  # $10 bet
    print(f"Result: {result}")
```

### Python HTTP API Server (Flask Example)

```python
"""
game_server.py - Flask server for your game
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from casino_db import get_user_bankroll, place_bet, update_bankroll

app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'game': 'blackjack'})


@app.route('/play', methods=['POST'])
def play():
    """
    Play a round of the game.
    
    Expected JSON body:
    {
        "user_id": "uuid-here",
        "bet_cents": 1000
    }
    """
    data = request.json
    user_id = data.get('user_id')
    bet_cents = data.get('bet_cents', 0)
    
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    if bet_cents < 100:  # Minimum $1 bet
        return jsonify({'error': 'Minimum bet is $1.00 (100 cents)'}), 400
    
    # Your game logic here
    result = play_blackjack(user_id, bet_cents)
    
    return jsonify(result)


@app.route('/balance/<user_id>', methods=['GET'])
def balance(user_id):
    """Get user's current balance."""
    bankroll = get_user_bankroll(user_id)
    return jsonify({
        'user_id': user_id,
        'bankroll_cents': bankroll,
        'bankroll_dollars': bankroll / 100
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

## C# Integration

### Required Packages

```xml
<!-- Add to your .csproj file -->
<PackageReference Include="Npgsql" Version="8.0.1" />
<PackageReference Include="Dapper" Version="2.1.24" />
<PackageReference Include="DotNetEnv" Version="3.0.0" />
```

### Database Connection

```csharp
// CasinoDb.cs - Database access for C# games
using System;
using System.Threading.Tasks;
using Npgsql;
using Dapper;
using DotNetEnv;

namespace CasinoGame
{
    /// <summary>
    /// Database access layer for casino operations.
    /// Handles bankroll queries and updates.
    /// </summary>
    public class CasinoDb
    {
        private readonly string _connectionString;

        public CasinoDb()
        {
            // Load environment variables from .env file
            Env.Load();
            
            _connectionString = Environment.GetEnvironmentVariable("DATABASE_URL") 
                ?? "Host=localhost;Port=5432;Database=casino_db;Username=casino_admin;Password=casino_secret_password_123";
        }

        /// <summary>
        /// Get a user's current bankroll in cents.
        /// </summary>
        /// <param name="userId">The user's UUID</param>
        /// <returns>Bankroll in cents (e.g., 250000 = $2,500.00)</returns>
        public async Task<long> GetBankrollAsync(Guid userId)
        {
            using var conn = new NpgsqlConnection(_connectionString);
            
            var result = await conn.QueryFirstOrDefaultAsync<long?>(
                "SELECT bankroll_cents FROM accounts WHERE user_id = @UserId",
                new { UserId = userId }
            );
            
            return result ?? 0;
        }

        /// <summary>
        /// Attempt to place a bet (deduct from bankroll).
        /// Uses a transaction to ensure atomicity.
        /// </summary>
        /// <param name="userId">The user's UUID</param>
        /// <param name="betCents">Bet amount in cents</param>
        /// <returns>True if bet was placed, false if insufficient funds</returns>
        public async Task<bool> PlaceBetAsync(Guid userId, long betCents)
        {
            using var conn = new NpgsqlConnection(_connectionString);
            await conn.OpenAsync();
            
            using var transaction = await conn.BeginTransactionAsync();
            
            try
            {
                // Check current balance (with row lock)
                var balance = await conn.QueryFirstOrDefaultAsync<long?>(
                    "SELECT bankroll_cents FROM accounts WHERE user_id = @UserId FOR UPDATE",
                    new { UserId = userId },
                    transaction
                );

                if (balance == null || balance < betCents)
                {
                    await transaction.RollbackAsync();
                    return false;
                }

                // Deduct bet
                await conn.ExecuteAsync(
                    @"UPDATE accounts 
                      SET bankroll_cents = bankroll_cents - @BetCents,
                          updated_at = NOW()
                      WHERE user_id = @UserId",
                    new { UserId = userId, BetCents = betCents },
                    transaction
                );

                await transaction.CommitAsync();
                return true;
            }
            catch
            {
                await transaction.RollbackAsync();
                throw;
            }
        }

        /// <summary>
        /// Add winnings to user's bankroll.
        /// </summary>
        /// <param name="userId">The user's UUID</param>
        /// <param name="amountCents">Amount to add in cents</param>
        /// <returns>New bankroll balance</returns>
        public async Task<long> AddWinningsAsync(Guid userId, long amountCents)
        {
            using var conn = new NpgsqlConnection(_connectionString);
            
            var newBalance = await conn.QueryFirstAsync<long>(
                @"UPDATE accounts 
                  SET bankroll_cents = bankroll_cents + @Amount,
                      updated_at = NOW()
                  WHERE user_id = @UserId
                  RETURNING bankroll_cents",
                new { UserId = userId, Amount = amountCents }
            );
            
            return newBalance;
        }
    }
}
```

### Example: Poker Game Integration

```csharp
// PokerGame.cs - Example poker game with bankroll integration
using System;
using System.Threading.Tasks;

namespace CasinoGame
{
    /// <summary>
    /// Result of a poker hand.
    /// </summary>
    public class PokerResult
    {
        public bool Success { get; set; }
        public string? Error { get; set; }
        public string Outcome { get; set; } = "";
        public long BetCents { get; set; }
        public long WinningsCents { get; set; }
        public long BankrollCents { get; set; }
        public string[] PlayerCards { get; set; } = Array.Empty<string>();
        public string HandRank { get; set; } = "";
    }

    /// <summary>
    /// Simple poker game implementation.
    /// </summary>
    public class PokerGame
    {
        private readonly CasinoDb _db;
        private readonly Random _random = new();

        public PokerGame()
        {
            _db = new CasinoDb();
        }

        /// <summary>
        /// Play a hand of video poker.
        /// </summary>
        /// <param name="userId">Player's UUID</param>
        /// <param name="betCents">Bet amount in cents</param>
        /// <returns>Game result</returns>
        public async Task<PokerResult> PlayHandAsync(Guid userId, long betCents)
        {
            // Step 1: Place bet
            if (!await _db.PlaceBetAsync(userId, betCents))
            {
                return new PokerResult
                {
                    Success = false,
                    Error = "Insufficient funds",
                    BankrollCents = await _db.GetBankrollAsync(userId)
                };
            }

            // Step 2: Deal cards and evaluate hand
            var cards = DealCards(5);
            var handRank = EvaluateHand(cards);
            var multiplier = GetPayoutMultiplier(handRank);
            
            // Step 3: Calculate winnings
            long winnings = (long)(betCents * multiplier);
            
            // Step 4: Add winnings to bankroll
            if (winnings > 0)
            {
                await _db.AddWinningsAsync(userId, winnings);
            }

            var newBalance = await _db.GetBankrollAsync(userId);

            return new PokerResult
            {
                Success = true,
                Outcome = winnings > betCents ? "win" : (winnings > 0 ? "push" : "lose"),
                BetCents = betCents,
                WinningsCents = winnings,
                BankrollCents = newBalance,
                PlayerCards = cards,
                HandRank = handRank
            };
        }

        private string[] DealCards(int count)
        {
            string[] suits = { "♠", "♥", "♦", "♣" };
            string[] ranks = { "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A" };
            
            var cards = new string[count];
            for (int i = 0; i < count; i++)
            {
                cards[i] = ranks[_random.Next(ranks.Length)] + suits[_random.Next(suits.Length)];
            }
            return cards;
        }

        private string EvaluateHand(string[] cards)
        {
            // Simplified hand evaluation
            // In a real game, you'd implement full poker hand ranking
            return _random.Next(10) switch
            {
                0 => "Royal Flush",
                1 => "Straight Flush",
                2 => "Four of a Kind",
                3 => "Full House",
                4 => "Flush",
                5 => "Straight",
                6 => "Three of a Kind",
                7 => "Two Pair",
                8 => "Pair",
                _ => "High Card"
            };
        }

        private double GetPayoutMultiplier(string handRank)
        {
            return handRank switch
            {
                "Royal Flush" => 800,
                "Straight Flush" => 50,
                "Four of a Kind" => 25,
                "Full House" => 9,
                "Flush" => 6,
                "Straight" => 4,
                "Three of a Kind" => 3,
                "Two Pair" => 2,
                "Pair" => 1,  // Jacks or better
                _ => 0
            };
        }
    }
}
```

---

## C++ Integration

### Required Libraries

```bash
# Install libpq (PostgreSQL C library)
# Ubuntu/Debian:
sudo apt-get install libpq-dev

# macOS:
brew install libpq

# Or use vcpkg:
vcpkg install libpqxx
```

### Database Connection

```cpp
// casino_db.hpp - Database access for C++ games
#ifndef CASINO_DB_HPP
#define CASINO_DB_HPP

#include <string>
#include <optional>
#include <pqxx/pqxx>

namespace casino {

/**
 * Database access class for casino operations.
 * Handles bankroll queries and updates.
 */
class CasinoDb {
public:
    /**
     * Constructor - initializes database connection.
     * @param connection_string PostgreSQL connection string
     */
    explicit CasinoDb(const std::string& connection_string = 
        "host=localhost port=5432 dbname=casino_db user=casino_admin password=casino_secret_password_123");

    /**
     * Get user's current bankroll in cents.
     * @param user_id UUID of the user
     * @return Bankroll in cents, or 0 if user not found
     */
    int64_t get_bankroll(const std::string& user_id);

    /**
     * Attempt to place a bet (deduct from bankroll).
     * @param user_id UUID of the user
     * @param bet_cents Bet amount in cents
     * @return true if bet was placed, false if insufficient funds
     */
    bool place_bet(const std::string& user_id, int64_t bet_cents);

    /**
     * Add winnings to user's bankroll.
     * @param user_id UUID of the user
     * @param amount_cents Amount to add in cents
     * @return New bankroll balance
     */
    int64_t add_winnings(const std::string& user_id, int64_t amount_cents);

private:
    std::string connection_string_;
};

} // namespace casino

#endif // CASINO_DB_HPP
```

```cpp
// casino_db.cpp - Implementation
#include "casino_db.hpp"
#include <iostream>

namespace casino {

CasinoDb::CasinoDb(const std::string& connection_string)
    : connection_string_(connection_string) {}

int64_t CasinoDb::get_bankroll(const std::string& user_id) {
    try {
        pqxx::connection conn(connection_string_);
        pqxx::work txn(conn);
        
        pqxx::result result = txn.exec_params(
            "SELECT bankroll_cents FROM accounts WHERE user_id = $1",
            user_id
        );
        
        if (result.empty()) {
            return 0;
        }
        
        return result[0][0].as<int64_t>();
    } catch (const std::exception& e) {
        std::cerr << "Database error: " << e.what() << std::endl;
        return 0;
    }
}

bool CasinoDb::place_bet(const std::string& user_id, int64_t bet_cents) {
    try {
        pqxx::connection conn(connection_string_);
        pqxx::work txn(conn);
        
        // Check current balance with row lock
        pqxx::result result = txn.exec_params(
            "SELECT bankroll_cents FROM accounts WHERE user_id = $1 FOR UPDATE",
            user_id
        );
        
        if (result.empty()) {
            return false;
        }
        
        int64_t balance = result[0][0].as<int64_t>();
        
        if (balance < bet_cents) {
            return false;  // Insufficient funds
        }
        
        // Deduct bet
        txn.exec_params(
            "UPDATE accounts SET bankroll_cents = bankroll_cents - $1, "
            "updated_at = NOW() WHERE user_id = $2",
            bet_cents, user_id
        );
        
        txn.commit();
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Database error: " << e.what() << std::endl;
        return false;
    }
}

int64_t CasinoDb::add_winnings(const std::string& user_id, int64_t amount_cents) {
    try {
        pqxx::connection conn(connection_string_);
        pqxx::work txn(conn);
        
        pqxx::result result = txn.exec_params(
            "UPDATE accounts SET bankroll_cents = bankroll_cents + $1, "
            "updated_at = NOW() WHERE user_id = $2 RETURNING bankroll_cents",
            amount_cents, user_id
        );
        
        txn.commit();
        
        if (result.empty()) {
            return 0;
        }
        
        return result[0][0].as<int64_t>();
    } catch (const std::exception& e) {
        std::cerr << "Database error: " << e.what() << std::endl;
        return 0;
    }
}

} // namespace casino
```

### Example: Blackjack in C++

```cpp
// blackjack.cpp - Example blackjack game
#include "casino_db.hpp"
#include <iostream>
#include <vector>
#include <random>
#include <algorithm>

namespace casino {

struct BlackjackResult {
    bool success;
    std::string error;
    std::string outcome;
    std::vector<std::string> player_hand;
    std::vector<std::string> dealer_hand;
    int player_value;
    int dealer_value;
    int64_t bet_cents;
    int64_t winnings_cents;
    int64_t bankroll_cents;
};

class Blackjack {
public:
    Blackjack() : db_() {}

    BlackjackResult play(const std::string& user_id, int64_t bet_cents) {
        BlackjackResult result;
        result.bet_cents = bet_cents;
        
        // Step 1: Place bet
        if (!db_.place_bet(user_id, bet_cents)) {
            result.success = false;
            result.error = "Insufficient funds";
            result.bankroll_cents = db_.get_bankroll(user_id);
            return result;
        }
        
        // Step 2: Initialize deck and deal
        init_deck();
        shuffle_deck();
        
        result.player_hand = {draw_card(), draw_card()};
        result.dealer_hand = {draw_card(), draw_card()};
        
        result.player_value = calculate_hand(result.player_hand);
        result.dealer_value = calculate_hand(result.dealer_hand);
        
        // Step 3: Dealer draws to 17
        while (result.dealer_value < 17) {
            result.dealer_hand.push_back(draw_card());
            result.dealer_value = calculate_hand(result.dealer_hand);
        }
        
        // Step 4: Determine outcome
        if (result.player_value > 21) {
            result.outcome = "lose";
            result.winnings_cents = 0;
        } else if (result.dealer_value > 21 || result.player_value > result.dealer_value) {
            result.outcome = "win";
            result.winnings_cents = bet_cents * 2;
        } else if (result.player_value < result.dealer_value) {
            result.outcome = "lose";
            result.winnings_cents = 0;
        } else {
            result.outcome = "push";
            result.winnings_cents = bet_cents;
        }
        
        // Step 5: Add winnings
        if (result.winnings_cents > 0) {
            db_.add_winnings(user_id, result.winnings_cents);
        }
        
        result.success = true;
        result.bankroll_cents = db_.get_bankroll(user_id);
        return result;
    }

private:
    CasinoDb db_;
    std::vector<std::string> deck_;
    std::mt19937 rng_{std::random_device{}()};
    
    void init_deck() {
        deck_.clear();
        const std::vector<std::string> ranks = 
            {"2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"};
        const std::vector<std::string> suits = {"♠", "♥", "♦", "♣"};
        
        for (const auto& suit : suits) {
            for (const auto& rank : ranks) {
                deck_.push_back(rank + suit);
            }
        }
    }
    
    void shuffle_deck() {
        std::shuffle(deck_.begin(), deck_.end(), rng_);
    }
    
    std::string draw_card() {
        std::string card = deck_.back();
        deck_.pop_back();
        return card;
    }
    
    int card_value(const std::string& card) {
        char rank = card[0];
        if (rank == '1') return 10;  // "10"
        if (rank == 'J' || rank == 'Q' || rank == 'K') return 10;
        if (rank == 'A') return 11;
        return rank - '0';
    }
    
    int calculate_hand(const std::vector<std::string>& hand) {
        int value = 0;
        int aces = 0;
        
        for (const auto& card : hand) {
            int v = card_value(card);
            value += v;
            if (card[0] == 'A') aces++;
        }
        
        while (value > 21 && aces > 0) {
            value -= 10;
            aces--;
        }
        
        return value;
    }
};

} // namespace casino
```

---

## Database Access

### Connection String Format

```
postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=disable
```

### Default Development Credentials

| Variable | Value |
|----------|-------|
| Host | `localhost` (or `db` in Docker) |
| Port | `5432` |
| Database | `casino_db` |
| Username | `casino_admin` |
| Password | `casino_secret_password_123` |

### Connection String Examples

```bash
# Local development
postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db?sslmode=disable

# Inside Docker network
postgres://casino_admin:casino_secret_password_123@db:5432/casino_db?sslmode=disable
```

---

## Environment Variables

Create a `.env` file in your game's directory:

```bash
# Database connection
DATABASE_URL=postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db?sslmode=disable

# JWT Secret (if validating tokens directly)
JWT_SECRET=your-super-secret-jwt-key-change-in-production-abc123

# Your game's port (if running as a server)
GAME_PORT=5000

# Debug mode
DEBUG=true
```

---

## Testing Your Integration

### 1. Start the Platform

```bash
cd CScapstone
docker compose up --build
```

### 2. Create a Test User

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gametest@example.com",
    "username": "gametest",
    "password": "testpassword123",
    "firstName": "Game",
    "lastName": "Tester",
    "dob": "1990-01-15"
  }'
```

Save the `user.id` from the response.

### 3. Test Your Database Connection

```python
# test_connection.py
from casino_db import get_user_bankroll

user_id = "paste-uuid-here"
balance = get_user_bankroll(user_id)
print(f"Balance: ${balance / 100:.2f}")
```

### 4. Test Bankroll Operations

```python
# test_bankroll.py
from casino_db import place_bet, update_bankroll, get_user_bankroll

user_id = "paste-uuid-here"

# Check initial balance
print(f"Initial: ${get_user_bankroll(user_id) / 100:.2f}")

# Place a $10 bet
if place_bet(user_id, 1000):
    print("Bet placed!")
    print(f"After bet: ${get_user_bankroll(user_id) / 100:.2f}")
    
    # Simulate winning $25
    update_bankroll(user_id, 2500)
    print(f"After win: ${get_user_bankroll(user_id) / 100:.2f}")
else:
    print("Insufficient funds!")
```

---

## Need Help?

- **Backend API issues**: See `/backend/INTEGRATION.md`
- **Frontend integration**: See `/frontend/INTEGRATION.md`
- **Questions**: Create an issue on GitHub or message the team

Happy coding! 🎰