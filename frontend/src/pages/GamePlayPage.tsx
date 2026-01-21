// =============================================================================
// GAMEPLAYPAGE.TSX - GAME PLAY PAGE (PROTECTED)
// =============================================================================
// This page handles:
//   1. Bet selection before starting a game
//   2. Rendering the game via WebSocket streaming
//   3. Displaying game results
//   4. Handling account deletion on $0 bankroll
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { GameCanvas, GameResult } from '../components/GameCanvas';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface Game {
  id: string;
  name: string;
  description: string;
  minBet: number;
  maxBet: number;
  enabled: boolean;
}

interface StartGameResponse {
  session_id: string;
  websocket_url: string;
  game_type: string;
  bet_cents: number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(cents / 100);
}

// =============================================================================
// COMPONENT
// =============================================================================

function GamePlayPage(): JSX.Element {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { user, bankrollCents, refreshAuth, clearAuth } = useAuth();

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  // Game info
  const [game, setGame] = useState<Game | null>(null);
  const [isLoadingGame, setIsLoadingGame] = useState(true);

  // Bet selection
  const [betAmount, setBetAmount] = useState<number>(0);
  const [betError, setBetError] = useState<string>('');

  // Game session
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStartingGame, setIsStartingGame] = useState(false);

  // Game result
  const [gameResult, setGameResult] = useState<GameResult | null>(null);

  // Error state
  const [error, setError] = useState<string>('');

  // ---------------------------------------------------------------------------
  // EFFECTS
  // ---------------------------------------------------------------------------

  // Fetch game info on mount
  useEffect(() => {
    const fetchGame = async () => {
      try {
        setIsLoadingGame(true);
        const response = await fetch('/api/games', {
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          const foundGame = data.games.find((g: Game) => g.id === gameId);

          if (foundGame) {
            setGame(foundGame);
            // Set default bet to minimum
            setBetAmount(foundGame.minBet);
          } else {
            setError('Game not found');
          }
        } else if (response.status === 401) {
          clearAuth();
          navigate('/login', { replace: true });
        } else {
          setError('Failed to load game info');
        }
      } catch (err) {
        setError('Unable to connect to server');
      } finally {
        setIsLoadingGame(false);
      }
    };

    if (gameId) {
      fetchGame();
    }
  }, [gameId, navigate, clearAuth]);

  // Check for existing active session
  useEffect(() => {
    const checkActiveSession = async () => {
      try {
        const response = await fetch('/api/games/session', {
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          if (data.has_active_session && data.session.game_type === gameId) {
            // Resume existing session
            setSessionId(data.session.session_id);
            setBetAmount(data.session.bet_cents);
          }
        }
      } catch (err) {
        console.error('Failed to check active session:', err);
      }
    };

    checkActiveSession();
  }, [gameId]);

  // ---------------------------------------------------------------------------
  // HANDLERS
  // ---------------------------------------------------------------------------

  const handleBetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10) || 0;
    setBetAmount(value);
    setBetError('');
  };

  const handleQuickBet = (amount: number) => {
    setBetAmount(amount);
    setBetError('');
  };

  const validateBet = (): boolean => {
    if (!game) {
      setBetError('Game not loaded');
      return false;
    }

    if (betAmount < game.minBet) {
      setBetError(`Minimum bet is ${formatCurrency(game.minBet)}`);
      return false;
    }

    if (betAmount > game.maxBet) {
      setBetError(`Maximum bet is ${formatCurrency(game.maxBet)}`);
      return false;
    }

    if (bankrollCents !== null && betAmount > bankrollCents) {
      setBetError('Insufficient funds');
      return false;
    }

    return true;
  };

  const startGame = async () => {
    if (!validateBet() || !gameId) return;

    setIsStartingGame(true);
    setBetError('');
    setError('');

    try {
      const response = await fetch('/api/games/start', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_type: gameId,
          bet_cents: betAmount,
        }),
      });

      if (response.ok) {
        const data: StartGameResponse = await response.json();
        setSessionId(data.session_id);
        // Refresh auth to update bankroll display
        await refreshAuth();
      } else {
        const errorData = await response.json();
        setBetError(errorData.error || 'Failed to start game');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setIsStartingGame(false);
    }
  };

  const handleGameEnd = async (result: GameResult) => {
    setGameResult(result);
    setSessionId(null);

    // Check if account was deleted
    if (result.account_deleted) {
      alert('Your bankroll has reached $0. Your account has been deleted.');
      clearAuth();
      navigate('/login', { replace: true });
      return;
    }

    // Refresh auth to update bankroll
    await refreshAuth();
  };

  const handleGameError = (errorMsg: string) => {
    setError(errorMsg);
    setSessionId(null);
  };

  const handlePlayAgain = () => {
    setGameResult(null);
    setError('');
  };

  const handleBackToGames = () => {
    navigate('/games');
  };

  const handleAbandonGame = async () => {
    if (!confirm('Are you sure you want to abandon this game? You will lose your bet.')) {
      return;
    }

    try {
      await fetch('/api/games/session/abandon', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Failed to abandon session:', err);
    }

    setSessionId(null);
    await refreshAuth();
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------

  if (isLoadingGame) {
    return (
      <div className="game-play-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading game...</p>
        </div>
      </div>
    );
  }

  if (error && !sessionId) {
    return (
      <div className="game-play-page">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={handleBackToGames} className="back-btn">
            Back to Games
          </button>
        </div>
      </div>
    );
  }

  if (!game) {
    return (
      <div className="game-play-page">
        <div className="error-container">
          <h2>Game Not Found</h2>
          <p>The requested game could not be found.</p>
          <button onClick={handleBackToGames} className="back-btn">
            Back to Games
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="game-play-page">
      {/* Header */}
      <header className="game-header">
        <button onClick={handleBackToGames} className="back-btn">
          ← Back to Games
        </button>
        <div className="game-title">
          <h1>{game.name}</h1>
        </div>
        <div className="bankroll-display">
          Balance: {bankrollCents !== null ? formatCurrency(bankrollCents) : '$0.00'}
        </div>
      </header>

      {/* Main content */}
      <main className="game-main">
        {/* Bet Selection (before game starts) */}
        {!sessionId && !gameResult && (
          <div className="bet-selection">
            <h2>Place Your Bet</h2>
            <p className="bet-description">{game.description}</p>

            <div className="bet-input-container">
              <label htmlFor="bet-amount">Bet Amount:</label>
              <div className="bet-input-wrapper">
                <span className="currency-symbol">$</span>
                <input
                  id="bet-amount"
                  type="number"
                  min={game.minBet / 100}
                  max={Math.min(game.maxBet, bankrollCents || 0) / 100}
                  step={0.5}
                  value={(betAmount / 100).toFixed(2)}
                  onChange={(e) => setBetAmount(Math.round(parseFloat(e.target.value) * 100) || 0)}
                  className="bet-input"
                />
              </div>
              <span className="bet-display">{formatCurrency(betAmount)}</span>
            </div>

            {/* Quick bet buttons */}
            <div className="quick-bets">
              {[game.minBet, 500, 1000, 2500, 5000].map((amount) => (
                <button
                  key={amount}
                  onClick={() => handleQuickBet(amount)}
                  disabled={(bankrollCents || 0) < amount || amount > game.maxBet}
                  className={`quick-bet-btn ${betAmount === amount ? 'active' : ''}`}
                >
                  {formatCurrency(amount)}
                </button>
              ))}
            </div>

            {/* Bet limits info */}
            <div className="bet-limits">
              <span>Min: {formatCurrency(game.minBet)}</span>
              <span>Max: {formatCurrency(game.maxBet)}</span>
            </div>

            {/* Error message */}
            {betError && <p className="bet-error">{betError}</p>}

            {/* Start game button */}
            <button
              className="start-game-btn"
              onClick={startGame}
              disabled={isStartingGame || betAmount <= 0}
            >
              {isStartingGame ? 'Starting...' : `Start Game - ${formatCurrency(betAmount)}`}
            </button>
          </div>
        )}

        {/* Game Canvas (during game) */}
        {sessionId && (
          <div className="game-container">
            <GameCanvas
              sessionId={sessionId}
              onGameEnd={handleGameEnd}
              onError={handleGameError}
              gameType={gameId || ''}
            />
            <button onClick={handleAbandonGame} className="abandon-btn">
              Abandon Game
            </button>
          </div>
        )}

        {/* Game Result (after game ends) */}
        {gameResult && (
          <div className="game-result">
            <h2>Game Over</h2>
            <div className={`result-badge result-${gameResult.result.toLowerCase()}`}>
              {gameResult.result.toUpperCase()}
            </div>
            <div className="result-details">
              <p className="payout-amount">
                {gameResult.payout_cents > 0 ? '+' : ''}
                {formatCurrency(gameResult.payout_cents)}
              </p>
              <p className="new-balance">
                New Balance: {formatCurrency(gameResult.new_bankroll)}
              </p>
            </div>
            <div className="result-actions">
              <button onClick={handlePlayAgain} className="play-again-btn">
                Play Again
              </button>
              <button onClick={handleBackToGames} className="back-btn">
                Back to Games
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default GamePlayPage;
