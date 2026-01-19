# Frontend Integration Guide

This guide explains how to integrate your game's UI with the Casino Capstone React frontend.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Getting Started](#getting-started)
3. [Authentication Context](#authentication-context)
4. [Creating a Game Page](#creating-a-game-page)
5. [Making API Calls](#making-api-calls)
6. [Bankroll Display](#bankroll-display)
7. [Styling Guidelines](#styling-guidelines)
8. [Component Examples](#component-examples)
9. [State Management](#state-management)
10. [Testing Your Game UI](#testing-your-game-ui)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND STRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  src/                                                                        │
│  ├── main.tsx          # Entry point                                        │
│  ├── App.tsx           # Routes + Auth context                              │
│  ├── pages/                                                                  │
│  │   ├── LoginPage.tsx                                                      │
│  │   ├── RegisterPage.tsx                                                   │
│  │   ├── GamesPage.tsx      # Games dashboard                               │
│  │   ├── BlackjackPage.tsx  # YOUR GAME PAGE                                │
│  │   └── PokerPage.tsx      # YOUR GAME PAGE                                │
│  ├── components/                                                             │
│  │   ├── GameCard.tsx                                                       │
│  │   ├── BankrollDisplay.tsx                                                │
│  │   └── your-game/         # YOUR GAME COMPONENTS                          │
│  │       ├── Card.tsx                                                       │
│  │       ├── Hand.tsx                                                       │
│  │       └── BetControls.tsx                                                │
│  ├── api/                                                                    │
│  │   └── casino.ts          # API client                                    │
│  └── styles/                                                                 │
│      ├── index.css          # Global styles + variables                     │
│      └── App.css            # Component styles                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- The backend API running (see root README)

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Project Structure

| Directory | Purpose |
|-----------|---------|
| `src/pages/` | Full page components (one per route) |
| `src/components/` | Reusable UI components |
| `src/api/` | API client functions |
| `src/styles/` | CSS files |
| `src/types/` | TypeScript type definitions |

---

## Authentication Context

The app uses React Context for authentication state. Access it from any component:

### Using the Auth Hook

```tsx
import { useAuth } from '../App';

function MyComponent() {
  const { 
    user,           // User object or null
    bankrollCents,  // Bankroll in cents or null
    isAuthenticated,// Boolean
    isLoading,      // Boolean (true during auth check)
    setAuthData,    // Function to update auth state
    clearAuth,      // Function to logout
    refreshAuth     // Function to refresh user data
  } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <p>Welcome, {user.firstName}!</p>
      <p>Balance: ${(bankrollCents / 100).toFixed(2)}</p>
    </div>
  );
}
```

### User Object Shape

```typescript
interface User {
  id: string;         // UUID
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  dob: string;        // "YYYY-MM-DD"
  createdAt: string;  // ISO timestamp
}
```

### Refreshing Bankroll

After a game round, refresh the bankroll from the server:

```tsx
const { refreshAuth } = useAuth();

async function handleGameComplete() {
  // Game logic...
  
  // Refresh user data (including bankroll) from server
  await refreshAuth();
}
```

---

## Creating a Game Page

### Step 1: Create the Page Component

Create `src/pages/BlackjackPage.tsx`:

```tsx
// =============================================================================
// BLACKJACKPAGE.TSX - BLACKJACK GAME PAGE
// =============================================================================
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

// Types
interface Card {
  rank: string;
  suit: string;
}

interface GameState {
  playerHand: Card[];
  dealerHand: Card[];
  playerValue: number;
  dealerValue: number;
  status: 'betting' | 'playing' | 'dealer_turn' | 'finished';
  result: 'win' | 'lose' | 'push' | null;
}

// Initial state
const initialGameState: GameState = {
  playerHand: [],
  dealerHand: [],
  playerValue: 0,
  dealerValue: 0,
  status: 'betting',
  result: null,
};

function BlackjackPage(): JSX.Element {
  const navigate = useNavigate();
  const { user, bankrollCents, refreshAuth } = useAuth();

  // Game state
  const [gameState, setGameState] = useState<GameState>(initialGameState);
  const [betCents, setBetCents] = useState<number>(100); // Default $1.00
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Bet limits
  const MIN_BET = 100;    // $1.00
  const MAX_BET = 10000;  // $100.00

  // Format cents as dollars
  const formatCurrency = (cents: number): string => {
    return `$${(cents / 100).toFixed(2)}`;
  };

  // Handle placing a bet and starting a new game
  const handlePlaceBet = async () => {
    if (betCents < MIN_BET || betCents > MAX_BET) {
      setError(`Bet must be between ${formatCurrency(MIN_BET)} and ${formatCurrency(MAX_BET)}`);
      return;
    }

    if (bankrollCents !== null && betCents > bankrollCents) {
      setError('Insufficient funds');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Call your game API
      const response = await fetch('/api/games/blackjack/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ betCents }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'Failed to start game');
        return;
      }

      // Update game state with response
      setGameState({
        playerHand: data.playerHand,
        dealerHand: data.dealerHand,
        playerValue: data.playerValue,
        dealerValue: data.dealerValue,
        status: data.status,
        result: data.result,
      });

      // Refresh bankroll from server
      await refreshAuth();

    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle hit action
  const handleHit = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/games/blackjack/hit', {
        method: 'POST',
        credentials: 'include',
      });
      const data = await response.json();
      
      setGameState(prev => ({
        ...prev,
        playerHand: data.playerHand,
        playerValue: data.playerValue,
        status: data.status,
        result: data.result,
      }));

      if (data.status === 'finished') {
        await refreshAuth();
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle stand action
  const handleStand = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/games/blackjack/stand', {
        method: 'POST',
        credentials: 'include',
      });
      const data = await response.json();
      
      setGameState({
        playerHand: data.playerHand,
        dealerHand: data.dealerHand,
        playerValue: data.playerValue,
        dealerValue: data.dealerValue,
        status: 'finished',
        result: data.result,
      });

      await refreshAuth();
    } catch (err) {
      setError('Network error');
    } finally {
      setIsLoading(false);
    }
  };

  // Reset game
  const handleNewGame = () => {
    setGameState(initialGameState);
    setError('');
  };

  return (
    <div className="game-page">
      {/* Header */}
      <header className="game-header">
        <button onClick={() => navigate('/games')} className="back-btn">
          ← Back to Games
        </button>
        <h1>🃏 Blackjack</h1>
        <div className="bankroll-display">
          Balance: {bankrollCents !== null ? formatCurrency(bankrollCents) : '...'}
        </div>
      </header>

      {/* Game Area */}
      <main className="game-area">
        {/* Error Display */}
        {error && (
          <div className="error-message">{error}</div>
        )}

        {/* Betting Phase */}
        {gameState.status === 'betting' && (
          <div className="betting-area">
            <h2>Place Your Bet</h2>
            
            <div className="bet-controls">
              <button 
                onClick={() => setBetCents(prev => Math.max(MIN_BET, prev - 100))}
                disabled={isLoading}
              >
                -$1
              </button>
              
              <span className="bet-amount">{formatCurrency(betCents)}</span>
              
              <button 
                onClick={() => setBetCents(prev => Math.min(MAX_BET, prev + 100))}
                disabled={isLoading}
              >
                +$1
              </button>
            </div>

            <div className="quick-bets">
              <button onClick={() => setBetCents(100)}>$1</button>
              <button onClick={() => setBetCents(500)}>$5</button>
              <button onClick={() => setBetCents(1000)}>$10</button>
              <button onClick={() => setBetCents(2500)}>$25</button>
            </div>

            <button 
              onClick={handlePlaceBet} 
              disabled={isLoading}
              className="deal-btn"
            >
              {isLoading ? 'Dealing...' : 'Deal'}
            </button>
          </div>
        )}

        {/* Playing Phase */}
        {(gameState.status === 'playing' || gameState.status === 'finished') && (
          <div className="play-area">
            {/* Dealer's Hand */}
            <div className="hand dealer-hand">
              <h3>Dealer ({gameState.dealerValue})</h3>
              <div className="cards">
                {gameState.dealerHand.map((card, index) => (
                  <div key={index} className="card">
                    {card.rank}{card.suit}
                  </div>
                ))}
              </div>
            </div>

            {/* Player's Hand */}
            <div className="hand player-hand">
              <h3>Your Hand ({gameState.playerValue})</h3>
              <div className="cards">
                {gameState.playerHand.map((card, index) => (
                  <div key={index} className="card">
                    {card.rank}{card.suit}
                  </div>
                ))}
              </div>
            </div>

            {/* Game Actions */}
            {gameState.status === 'playing' && (
              <div className="game-actions">
                <button onClick={handleHit} disabled={isLoading}>
                  Hit
                </button>
                <button onClick={handleStand} disabled={isLoading}>
                  Stand
                </button>
              </div>
            )}

            {/* Result */}
            {gameState.status === 'finished' && (
              <div className={`game-result ${gameState.result}`}>
                <h2>
                  {gameState.result === 'win' && '🎉 You Win!'}
                  {gameState.result === 'lose' && '😔 You Lose'}
                  {gameState.result === 'push' && '🤝 Push'}
                </h2>
                <button onClick={handleNewGame} className="new-game-btn">
                  Play Again
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default BlackjackPage;
```

### Step 2: Add Route in App.tsx

Add the route to `src/App.tsx`:

```tsx
import BlackjackPage from './pages/BlackjackPage';

// In the Routes section:
<Route 
  path="/games/blackjack" 
  element={
    <ProtectedRoute>
      <BlackjackPage />
    </ProtectedRoute>
  } 
/>
```

### Step 3: Update Games Page Links

Update `src/pages/GamesPage.tsx` to navigate to your game:

```tsx
const handleGameClick = (game: Game): void => {
  if (!game.enabled) {
    alert(`${game.name} is coming soon!`);
    return;
  }

  // Navigate to the game page
  navigate(`/games/${game.id}`);
};
```

---

## Making API Calls

### API Client Setup

Create `src/api/casino.ts`:

```typescript
// =============================================================================
// CASINO API CLIENT
// =============================================================================

const API_BASE = '/api';

/**
 * Generic API request function with error handling.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include', // Always include cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new APIError(data.error || 'Request failed', data.code, response.status);
  }

  return data;
}

/**
 * Custom error class for API errors.
 */
export class APIError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
    this.name = 'APIError';
  }
}

// =============================================================================
// AUTH API
// =============================================================================

export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  dob: string;
  createdAt: string;
}

export interface AuthResponse {
  user: User;
  bankrollCents: number;
}

export const authAPI = {
  async getMe(): Promise<AuthResponse> {
    return apiRequest<AuthResponse>('/auth/me');
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    return apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async logout(): Promise<void> {
    await apiRequest('/auth/logout', { method: 'POST' });
  },
};

// =============================================================================
// GAMES API
// =============================================================================

export interface Game {
  id: string;
  name: string;
  description: string;
  minBet: number;
  maxBet: number;
  enabled: boolean;
  imageUrl?: string;
}

export const gamesAPI = {
  async list(): Promise<{ games: Game[]; count: number }> {
    return apiRequest('/games');
  },
};

// =============================================================================
// BLACKJACK API (Example)
// =============================================================================

export interface BlackjackState {
  playerHand: Array<{ rank: string; suit: string }>;
  dealerHand: Array<{ rank: string; suit: string }>;
  playerValue: number;
  dealerValue: number;
  status: 'betting' | 'playing' | 'finished';
  result: 'win' | 'lose' | 'push' | null;
  bankrollCents: number;
}

export const blackjackAPI = {
  async play(betCents: number): Promise<BlackjackState> {
    return apiRequest<BlackjackState>('/games/blackjack/play', {
      method: 'POST',
      body: JSON.stringify({ betCents }),
    });
  },

  async hit(): Promise<BlackjackState> {
    return apiRequest<BlackjackState>('/games/blackjack/hit', {
      method: 'POST',
    });
  },

  async stand(): Promise<BlackjackState> {
    return apiRequest<BlackjackState>('/games/blackjack/stand', {
      method: 'POST',
    });
  },
};
```

### Using the API Client

```tsx
import { blackjackAPI, APIError } from '../api/casino';

// In your component:
const handlePlaceBet = async () => {
  try {
    const result = await blackjackAPI.play(betCents);
    setGameState(result);
    await refreshAuth();
  } catch (error) {
    if (error instanceof APIError) {
      if (error.code === 'INSUFFICIENT_FUNDS') {
        setError('Not enough money!');
      } else {
        setError(error.message);
      }
    } else {
      setError('Network error');
    }
  }
};
```

---

## Bankroll Display

### Reusable Bankroll Component

Create `src/components/BankrollDisplay.tsx`:

```tsx
import { useAuth } from '../App';

interface BankrollDisplayProps {
  className?: string;
  showLabel?: boolean;
}

/**
 * Displays the user's current bankroll.
 * Automatically updates when auth state changes.
 */
function BankrollDisplay({ 
  className = '', 
  showLabel = true 
}: BankrollDisplayProps): JSX.Element {
  const { bankrollCents, isLoading } = useAuth();

  const formatCurrency = (cents: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100);
  };

  if (isLoading) {
    return <span className={`bankroll-display ${className}`}>Loading...</span>;
  }

  return (
    <span className={`bankroll-display ${className}`}>
      {showLabel && 'Balance: '}
      <strong>{bankrollCents !== null ? formatCurrency(bankrollCents) : '$0.00'}</strong>
    </span>
  );
}

export default BankrollDisplay;
```

### Usage

```tsx
import BankrollDisplay from '../components/BankrollDisplay';

function GameHeader() {
  return (
    <header>
      <h1>Blackjack</h1>
      <BankrollDisplay />
    </header>
  );
}
```

---

## Styling Guidelines

### CSS Variables (from index.css)

Use these CSS variables for consistent styling:

```css
/* Colors */
--color-primary: #fbbf24;           /* Gold - primary actions */
--color-bg-primary: #0f0f1a;        /* Dark background */
--color-bg-secondary: #1a1a2e;      /* Card backgrounds */
--color-text-primary: #ffffff;      /* Main text */
--color-success: #22c55e;           /* Win/success */
--color-error: #ef4444;             /* Lose/error */

/* Spacing */
--spacing-2: 0.5rem;
--spacing-4: 1rem;
--spacing-6: 1.5rem;
--spacing-8: 2rem;

/* Border Radius */
--radius-md: 0.5rem;
--radius-lg: 0.75rem;
--radius-xl: 1rem;

/* Shadows */
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
```

### Game Page Styles

Add to `src/styles/App.css`:

```css
/* =============================================================================
   GAME PAGE STYLES
   ============================================================================= */

.game-page {
  min-height: 100vh;
  background-color: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.back-btn {
  padding: var(--spacing-2) var(--spacing-4);
  background-color: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.back-btn:hover {
  background-color: var(--color-bg-hover);
}

.game-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-8);
  gap: var(--spacing-6);
}

/* Betting Area */
.betting-area {
  text-align: center;
  padding: var(--spacing-8);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
}

.bet-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-4);
  margin: var(--spacing-6) 0;
}

.bet-amount {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  min-width: 120px;
}

.quick-bets {
  display: flex;
  gap: var(--spacing-2);
  justify-content: center;
  margin-bottom: var(--spacing-6);
}

.quick-bets button {
  padding: var(--spacing-2) var(--spacing-4);
  background-color: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
}

.deal-btn {
  padding: var(--spacing-3) var(--spacing-8);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.deal-btn:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

/* Cards */
.hand {
  text-align: center;
  margin: var(--spacing-4) 0;
}

.cards {
  display: flex;
  gap: var(--spacing-2);
  justify-content: center;
}

.card {
  width: 60px;
  height: 84px;
  background: white;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: #1a1a2e;
  box-shadow: var(--shadow-md);
}

/* Game Actions */
.game-actions {
  display: flex;
  gap: var(--spacing-4);
  margin-top: var(--spacing-6);
}

.game-actions button {
  padding: var(--spacing-3) var(--spacing-8);
  font-size: var(--font-size-lg);
  background-color: var(--color-bg-tertiary);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.game-actions button:hover:not(:disabled) {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

/* Game Result */
.game-result {
  text-align: center;
  padding: var(--spacing-6);
  border-radius: var(--radius-xl);
  margin-top: var(--spacing-6);
}

.game-result.win {
  background-color: rgba(34, 197, 94, 0.2);
  border: 2px solid var(--color-success);
}

.game-result.lose {
  background-color: rgba(239, 68, 68, 0.2);
  border: 2px solid var(--color-error);
}

.game-result.push {
  background-color: rgba(251, 191, 36, 0.2);
  border: 2px solid var(--color-primary);
}

.new-game-btn {
  margin-top: var(--spacing-4);
  padding: var(--spacing-3) var(--spacing-6);
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}
```

---

## State Management

### Local State (Simple Games)

For simple games, use React's `useState`:

```tsx
const [gameState, setGameState] = useState<GameState>(initialState);
const [betCents, setBetCents] = useState(100);
const [isLoading, setIsLoading] = useState(false);
```

### useReducer (Complex Games)

For complex games with multiple actions, use `useReducer`:

```tsx
type GameAction =
  | { type: 'PLACE_BET'; betCents: number }
  | { type: 'HIT'; card: Card }
  | { type: 'STAND' }
  | { type: 'GAME_OVER'; result: 'win' | 'lose' | 'push' }
  | { type: 'RESET' };

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'PLACE_BET':
      return { ...state, status: 'playing', betCents: action.betCents };
    
    case 'HIT':
      return {
        ...state,
        playerHand: [...state.playerHand, action.card],
        playerValue: calculateValue([...state.playerHand, action.card]),
      };
    
    case 'STAND':
      return { ...state, status: 'dealer_turn' };
    
    case 'GAME_OVER':
      return { ...state, status: 'finished', result: action.result };
    
    case 'RESET':
      return initialState;
    
    default:
      return state;
  }
}

// In component:
const [state, dispatch] = useReducer(gameReducer, initialState);

// Usage:
dispatch({ type: 'HIT', card: newCard });
dispatch({ type: 'GAME_OVER', result: 'win' });
```

---

## Testing Your Game UI

### 1. Run the Development Server

```bash
cd frontend
npm run dev
```

### 2. Create a Test User

Register via the UI or use curl:

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "uitest@example.com",
    "username": "uitest",
    "password": "testpassword123",
    "firstName": "UI",
    "lastName": "Tester",
    "dob": "1990-01-15"
  }'
```

### 3. Test Game Flow

1. Log in to the frontend
2. Navigate to your game
3. Test betting controls
4. Test game actions
5. Verify bankroll updates after each round

### 4. Test Error States

- Try betting more than bankroll
- Try betting below/above limits
- Test network errors (disable backend)
- Test invalid game states

---

## Questions?

- Check the root `/INTEGRATION.md` for backend API details
- Check `/backend/INTEGRATION.md` for API documentation
- Create a GitHub issue for help

Happy coding! 🎰