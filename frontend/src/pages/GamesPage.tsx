// =============================================================================
// GAMESPAGE.TSX - GAMES DASHBOARD (PROTECTED)
// =============================================================================
// This is the main dashboard for authenticated users. It displays:
//   - User's profile information
//   - Current bankroll balance
//   - List of available casino games
//   - Logout functionality
//
// This page is protected by the ProtectedRoute component in App.tsx.
// Users who are not authenticated will be redirected to /login.
//
// The games list is fetched from GET /api/games endpoint.
// Currently shows Blackjack and Poker as available games.
// =============================================================================

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, User } from '../App';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Game represents a single casino game from the API.
 * Matches the Game struct from the backend.
 */
interface Game {
  id: string;
  name: string;
  description: string;
  minBet: number;      // In cents
  maxBet: number;      // In cents
  enabled: boolean;
  imageUrl?: string;
}

/**
 * GamesResponse represents the API response from GET /api/games.
 */
interface GamesResponse {
  games: Game[];
  count: number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Format cents as a dollar amount string.
 * Example: 250000 -> "$2,500.00"
 * 
 * @param cents - Amount in cents
 * @returns Formatted dollar string
 */
function formatCurrency(cents: number): string {
  const dollars = cents / 100;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(dollars);
}

/**
 * Get a greeting based on the time of day.
 * 
 * @returns Greeting string (Good morning/afternoon/evening)
 */
function getGreeting(): string {
  const hour = new Date().getHours();
  
  if (hour < 12) {
    return 'Good morning';
  } else if (hour < 18) {
    return 'Good afternoon';
  } else {
    return 'Good evening';
  }
}

// =============================================================================
// COMPONENT
// =============================================================================

/**
 * GamesPage - The main games dashboard component.
 * 
 * Features:
 *   - Displays user greeting and profile info
 *   - Shows current bankroll prominently
 *   - Lists all available games with descriptions
 *   - Provides logout functionality
 *   - Responsive design for mobile and desktop
 */
function GamesPage(): JSX.Element {
  // ---------------------------------------------------------------------------
  // HOOKS
  // ---------------------------------------------------------------------------
  
  // Navigation hook for redirecting after logout
  const navigate = useNavigate();
  
  // Auth context for user data and logout
  const { user, bankrollCents, clearAuth, refreshAuth } = useAuth();

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  
  // List of games from the API
  const [games, setGames] = useState<Game[]>([]);
  
  // Loading state for games fetch
  const [isLoadingGames, setIsLoadingGames] = useState<boolean>(true);
  
  // Error state for games fetch
  const [gamesError, setGamesError] = useState<string>('');
  
  // Logout loading state
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);

  // ---------------------------------------------------------------------------
  // EFFECTS
  // ---------------------------------------------------------------------------

  /**
   * Fetch the list of games when the component mounts.
   */
  useEffect(() => {
    const fetchGames = async () => {
      try {
        setIsLoadingGames(true);
        setGamesError('');

        const response = await fetch('/api/games', {
          method: 'GET',
          credentials: 'include', // Include session cookie
        });

        if (response.ok) {
          const data: GamesResponse = await response.json();
          setGames(data.games);
        } else if (response.status === 401) {
          // Session expired - redirect to login
          clearAuth();
          navigate('/login', { replace: true });
        } else {
          setGamesError('Failed to load games. Please try again.');
        }
      } catch (error) {
        console.error('Failed to fetch games:', error);
        setGamesError('Unable to connect to server. Please try again.');
      } finally {
        setIsLoadingGames(false);
      }
    };

    fetchGames();
  }, [clearAuth, navigate]);

  // ---------------------------------------------------------------------------
  // EVENT HANDLERS
  // ---------------------------------------------------------------------------

  /**
   * Handle logout button click.
   * Calls the logout API and clears local auth state.
   */
  const handleLogout = async (): Promise<void> => {
    setIsLoggingOut(true);

    try {
      // Call logout API to clear the cookie on the server
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      // Even if the API call fails, we still clear local state
      console.error('Logout API error:', error);
    }

    // Clear local auth state
    clearAuth();
    
    // Redirect to login page
    navigate('/login', { replace: true });
  };

  /**
   * Handle clicking on a game card.
   * For now, shows an alert. Later, this would navigate to the game.
   */
  const handleGameClick = (game: Game): void => {
    if (!game.enabled) {
      alert(`${game.name} is coming soon!`);
      return;
    }

    // TODO: Navigate to the actual game page
    // navigate(`/games/${game.id}`);
    alert(`${game.name} will be available soon! Your teammates are building it.`);
  };

  /**
   * Handle refresh bankroll button click.
   * Fetches the latest user data from the server.
   */
  const handleRefreshBankroll = async (): Promise<void> => {
    await refreshAuth();
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------
  
  // Type guard - user should always exist on this protected page
  if (!user) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="games-page">
      {/* ===================================================================
          HEADER / NAVBAR
          =================================================================== */}
      <header className="games-header">
        <div className="header-content">
          {/* Logo/Brand */}
          <div className="header-brand">
            <span className="brand-icon">🎰</span>
            <span className="brand-text">Casino Capstone</span>
          </div>

          {/* User Info & Logout */}
          <div className="header-user">
            <span className="user-greeting">
              {getGreeting()}, <strong>{user.firstName}</strong>!
            </span>
            <button
              className="logout-btn"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              {isLoggingOut ? 'Logging out...' : 'Logout'}
            </button>
          </div>
        </div>
      </header>

      {/* ===================================================================
          MAIN CONTENT
          =================================================================== */}
      <main className="games-main">
        {/* -----------------------------------------------------------------
            BANKROLL CARD
            ----------------------------------------------------------------- */}
        <section className="bankroll-section">
          <div className="bankroll-card">
            <div className="bankroll-header">
              <h2>Your Bankroll</h2>
              <button
                className="refresh-btn"
                onClick={handleRefreshBankroll}
                title="Refresh balance"
              >
                🔄
              </button>
            </div>
            <div className="bankroll-amount">
              {bankrollCents !== null ? formatCurrency(bankrollCents) : '$0.00'}
            </div>
            <div className="bankroll-hint">
              Available to play
            </div>
          </div>

          {/* User Profile Summary */}
          <div className="profile-card">
            <h3>Profile</h3>
            <div className="profile-info">
              <div className="profile-row">
                <span className="profile-label">Username:</span>
                <span className="profile-value">@{user.username}</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Email:</span>
                <span className="profile-value">{user.email}</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Member since:</span>
                <span className="profile-value">
                  {new Date(user.createdAt).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* -----------------------------------------------------------------
            GAMES SECTION
            ----------------------------------------------------------------- */}
        <section className="games-section">
          <h2>Available Games</h2>
          <p className="section-subtitle">
            Choose a game to start playing with your bankroll
          </p>

          {/* Loading State */}
          {isLoadingGames && (
            <div className="games-loading">
              <div className="loading-spinner"></div>
              <p>Loading games...</p>
            </div>
          )}

          {/* Error State */}
          {gamesError && (
            <div className="games-error">
              <p>⚠️ {gamesError}</p>
              <button onClick={() => window.location.reload()}>
                Try Again
              </button>
            </div>
          )}

          {/* Games Grid */}
          {!isLoadingGames && !gamesError && (
            <div className="games-grid">
              {games.map((game) => (
                <div
                  key={game.id}
                  className={`game-card ${!game.enabled ? 'game-disabled' : ''}`}
                  onClick={() => handleGameClick(game)}
                  role="button"
                  tabIndex={0}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleGameClick(game);
                    }
                  }}
                >
                  {/* Game Icon/Image */}
                  <div className="game-icon">
                    {game.id === 'blackjack' && '🃏'}
                    {game.id === 'poker' && '♠️'}
                    {!['blackjack', 'poker'].includes(game.id) && '🎮'}
                  </div>

                  {/* Game Info */}
                  <div className="game-info">
                    <h3 className="game-name">{game.name}</h3>
                    <p className="game-description">{game.description}</p>
                    
                    {/* Bet Limits */}
                    <div className="game-limits">
                      <span className="limit-label">Bet Range:</span>
                      <span className="limit-value">
                        {formatCurrency(game.minBet)} - {formatCurrency(game.maxBet)}
                      </span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="game-status">
                    {game.enabled ? (
                      <span className="status-badge status-available">
                        Available
                      </span>
                    ) : (
                      <span className="status-badge status-coming-soon">
                        Coming Soon
                      </span>
                    )}
                  </div>

                  {/* Play Button */}
                  <button
                    className={`play-btn ${!game.enabled ? 'play-btn-disabled' : ''}`}
                    disabled={!game.enabled}
                  >
                    {game.enabled ? 'Play Now' : 'Coming Soon'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Empty State (no games) */}
          {!isLoadingGames && !gamesError && games.length === 0 && (
            <div className="games-empty">
              <p>🎲 No games available yet. Check back soon!</p>
            </div>
          )}
        </section>

        {/* -----------------------------------------------------------------
            INFO SECTION
            ----------------------------------------------------------------- */}
        <section className="info-section">
          <div className="info-card">
            <h3>🎓 CS Capstone Project</h3>
            <p>
              This casino application is a capstone project demonstrating
              full-stack development with React, Go, and PostgreSQL.
              The games are being developed by team members and will be
              integrated soon!
            </p>
          </div>
          <div className="info-card">
            <h3>💰 Play Money Only</h3>
            <p>
              All chips are virtual and have no real monetary value.
              This is an educational project for demonstrating software
              development skills. Have fun and play responsibly!
            </p>
          </div>
        </section>
      </main>

      {/* ===================================================================
          FOOTER
          =================================================================== */}
      <footer className="games-footer">
        <p>
          Casino Capstone &copy; {new Date().getFullYear()} | 
          Built with React, Go, and PostgreSQL |
          For educational purposes only
        </p>
      </footer>
    </div>
  );
}

export default GamesPage;