// =============================================================================
// GAMES.GO - GAMES LISTING HANDLER
// =============================================================================
// This file contains the HTTP handler for listing available casino games.
// Currently returns a static list, but designed to be extended when teammates
// integrate their Python-based game implementations.
//
// Current endpoint:
//   - GET /api/games - List all available games (requires authentication)
//
// Future Integration Notes:
// -------------------------
// When your teammates' Python games are ready to integrate, there are several
// approaches you could take:
//
// 1. MICROSERVICES APPROACH:
//    - Each game runs as a separate Python service
//    - This Go API acts as a gateway, forwarding requests to game services
//    - Pros: Language flexibility, isolated failures, independent scaling
//    - Cons: More complex deployment, network overhead
//
// 2. DATABASE-DRIVEN APPROACH:
//    - Games are registered in a database table
//    - Python games write results to the database
//    - Go API reads game state and updates bankroll
//    - Pros: Simpler architecture, single source of truth
//    - Cons: Tighter coupling, potential for race conditions
//
// 3. MESSAGE QUEUE APPROACH:
//    - Use RabbitMQ or Redis for game events
//    - Python games publish bet results
//    - Go API subscribes and updates bankroll
//    - Pros: Decoupled, async processing, reliable delivery
//    - Cons: Additional infrastructure, eventual consistency
//
// For a capstone project, Option 2 (database-driven) is probably the simplest
// to implement while still demonstrating good architecture principles.
// =============================================================================

package handlers

import (
	"net/http"
)

// =============================================================================
// GAME TYPES
// =============================================================================
// These structs define the shape of game data.
// When integrating with actual games, you might expand these significantly.

// Game represents a single casino game
type Game struct {
	// ID is a unique identifier for the game (used in URLs/routing)
	// Example: "blackjack", "poker", "slots"
	ID string `json:"id"`

	// Name is the display name shown in the UI
	// Example: "Blackjack", "Texas Hold'em Poker", "Lucky Slots"
	Name string `json:"name"`

	// Description provides a brief explanation of the game
	// Shown on game cards in the UI
	Description string `json:"description"`

	// MinBet is the minimum bet amount in cents
	// Example: 100 = $1.00 minimum bet
	MinBet int64 `json:"minBet"`

	// MaxBet is the maximum bet amount in cents
	// Example: 100000 = $1,000.00 maximum bet
	MaxBet int64 `json:"maxBet"`

	// Enabled indicates if the game is currently playable
	// Disabled games are shown but greyed out in the UI
	Enabled bool `json:"enabled"`

	// ImageURL is the URL to the game's thumbnail image (optional)
	// Can be a relative path or full URL
	ImageURL string `json:"imageUrl,omitempty"`
}

// GamesResponse is the response returned by the ListGames endpoint
type GamesResponse struct {
	// Games is the array of available games
	Games []Game `json:"games"`

	// Count is the total number of games (for convenience)
	Count int `json:"count"`
}

// =============================================================================
// STATIC GAME DATA
// =============================================================================
// This is a static list of games for the initial implementation.
// When your teammates' games are ready, this could be replaced with
// database queries or service discovery.
//
// Each game represents a potential integration point for Python game code.
// The 'Enabled' field lets you show upcoming games without them being playable.

var availableGames = []Game{
	{
		ID:          "blackjack",
		Name:        "Blackjack",
		Description: "Classic card game. Get as close to 21 as possible without going over. Beat the dealer to win!",
		MinBet:      100,   // $1.00
		MaxBet:      10000, // $100.00
		Enabled:     true,
		ImageURL:    "/images/games/blackjack.png",
	},
	{
		ID:          "poker",
		Name:        "Texas Hold'em Poker",
		Description: "The world's most popular poker game. Make the best 5-card hand from your 2 hole cards and 5 community cards.",
		MinBet:      500,   // $5.00
		MaxBet:      50000, // $500.00
		Enabled:     true,
		ImageURL:    "/images/games/poker.png",
	},
}

// =============================================================================
// GAMES HANDLER
// =============================================================================
// GamesHandler contains all game-related HTTP handlers.
// Currently simple, but structured for future expansion.

type GamesHandler struct {
	// In the future, you might add:
	// - db *db.Database         // For fetching games from database
	// - gameService GameService // For communicating with game microservices
	// - cache *redis.Client     // For caching game data
}

// NewGamesHandler creates a new GamesHandler
// Currently takes no dependencies, but structured for future expansion
//
// Future signature might look like:
//
//	func NewGamesHandler(db *db.Database, gameService GameService) *GamesHandler
func NewGamesHandler() *GamesHandler {
	return &GamesHandler{}
}

// =============================================================================
// LIST GAMES HANDLER
// =============================================================================

// ListGames returns all available casino games
// GET /api/games
//
// Requires: Valid session cookie (enforced by AuthMiddleware)
//
// Success response (200 OK):
//
//	{
//	    "games": [
//	        {
//	            "id": "blackjack",
//	            "name": "Blackjack",
//	            "description": "Classic card game...",
//	            "minBet": 100,
//	            "maxBet": 10000,
//	            "enabled": true,
//	            "imageUrl": "/images/games/blackjack.png"
//	        },
//	        ...
//	    ],
//	    "count": 6
//	}
//
// The frontend uses this list to:
//   - Display game cards on the /games page
//   - Show enabled games as playable, disabled as "coming soon"
//   - Navigate to individual game pages (e.g., /games/blackjack)
func (h *GamesHandler) ListGames(w http.ResponseWriter, r *http.Request) {
	// -------------------------------------------------------------------------
	// For now, we return the static list of games
	// -------------------------------------------------------------------------
	// In a more complete implementation, you might:
	//
	// 1. Fetch games from database:
	//    games, err := h.db.Pool.Query(ctx, "SELECT * FROM games WHERE active = true")
	//
	// 2. Check which game services are online:
	//    for i, game := range games {
	//        games[i].Enabled = h.gameService.IsOnline(game.ID)
	//    }
	//
	// 3. Filter based on user permissions or VIP status:
	//    userID := middleware.MustGetUserIDFromContext(r.Context())
	//    games = filterGamesForUser(games, userID)
	//
	// 4. Apply any promotional or seasonal games:
	//    games = append(games, h.getPromotionalGames()...)

	response := GamesResponse{
		Games: availableGames,
		Count: len(availableGames),
	}

	writeJSON(w, http.StatusOK, response)
}

// =============================================================================
// FUTURE ENDPOINTS (Commented templates for when games are integrated)
// =============================================================================
// These are placeholder implementations for endpoints you might need
// when integrating actual game logic. Uncomment and implement as needed.

/*
// GetGame returns details for a specific game
// GET /api/games/{gameID}
func (h *GamesHandler) GetGame(w http.ResponseWriter, r *http.Request) {
    gameID := chi.URLParam(r, "gameID")

    // Find the game
    for _, game := range availableGames {
        if game.ID == gameID {
            writeJSON(w, http.StatusOK, game)
            return
        }
    }

    writeError(w, http.StatusNotFound, "Game not found", "GAME_NOT_FOUND")
}
*/

/*
// PlaceBet handles a bet placement for a game
// POST /api/games/{gameID}/bet
//
// Request body:
//   {
//       "amount": 1000,  // Bet amount in cents ($10.00)
//       "data": { ... }  // Game-specific bet data
//   }
//
// This would:
// 1. Validate the bet amount against user's bankroll
// 2. Validate bet is within game's min/max limits
// 3. Deduct the bet from user's bankroll
// 4. Forward the bet to the game service
// 5. Return the result and update bankroll accordingly
func (h *GamesHandler) PlaceBet(w http.ResponseWriter, r *http.Request) {
    gameID := chi.URLParam(r, "gameID")
    userID := middleware.MustGetUserIDFromContext(r.Context())

    // Parse bet request
    var betRequest struct {
        Amount int64                  `json:"amount"`
        Data   map[string]interface{} `json:"data"`
    }
    if err := json.NewDecoder(r.Body).Decode(&betRequest); err != nil {
        writeError(w, http.StatusBadRequest, "Invalid request", "INVALID_JSON")
        return
    }

    // TODO: Implement bet logic
    // 1. Check bankroll >= bet amount
    // 2. Check bet amount within game limits
    // 3. Begin transaction
    // 4. Deduct bet from bankroll
    // 5. Call game service with bet
    // 6. Process result (win/lose)
    // 7. Update bankroll if won
    // 8. Commit transaction
    // 9. Return result

    writeError(w, http.StatusNotImplemented, "Betting not yet implemented", "NOT_IMPLEMENTED")
}
*/

/*
// GetGameHistory returns the user's play history for a game
// GET /api/games/{gameID}/history
func (h *GamesHandler) GetGameHistory(w http.ResponseWriter, r *http.Request) {
    gameID := chi.URLParam(r, "gameID")
    userID := middleware.MustGetUserIDFromContext(r.Context())

    // TODO: Query game history from database
    // SELECT * FROM game_history
    // WHERE user_id = $1 AND game_id = $2
    // ORDER BY played_at DESC
    // LIMIT 50

    writeError(w, http.StatusNotImplemented, "History not yet implemented", "NOT_IMPLEMENTED")
}
*/

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// GetGameByID finds a game by its ID (helper for other handlers)
// Returns nil if game not found
func GetGameByID(gameID string) *Game {
	for _, game := range availableGames {
		if game.ID == gameID {
			return &game
		}
	}
	return nil
}

// GetEnabledGames returns only games that are currently enabled
// Useful for showing only playable games in some views
func GetEnabledGames() []Game {
	enabled := make([]Game, 0)
	for _, game := range availableGames {
		if game.Enabled {
			enabled = append(enabled, game)
		}
	}
	return enabled
}

// =============================================================================
// NOTES FOR TEAMMATES INTEGRATING PYTHON GAMES
// =============================================================================
//
// When you're ready to integrate your Python game, here's a suggested approach:
//
// 1. CREATE A GAME SERVICE INTERFACE
//    Define what operations each game must support:
//
//    type GameService interface {
//        StartGame(userID string) (*GameSession, error)
//        PlaceBet(sessionID string, bet BetRequest) (*BetResult, error)
//        GetState(sessionID string) (*GameState, error)
//        EndGame(sessionID string) (*GameResult, error)
//    }
//
// 2. IMPLEMENT AN HTTP CLIENT FOR YOUR PYTHON SERVICE
//    Your Python game should expose a REST API that this Go code calls:
//
//    type BlackjackService struct {
//        baseURL string
//        client  *http.Client
//    }
//
//    func (s *BlackjackService) PlaceBet(sessionID string, bet BetRequest) (*BetResult, error) {
//        resp, err := s.client.Post(s.baseURL+"/bet", "application/json", betJSON)
//        // ... handle response
//    }
//
// 3. ADD A DATABASE TABLE FOR GAME SESSIONS
//    Track active games and their state:
//
//    CREATE TABLE game_sessions (
//        id UUID PRIMARY KEY,
//        user_id UUID REFERENCES users(id),
//        game_id VARCHAR(50),
//        state JSONB,
//        bet_cents BIGINT,
//        started_at TIMESTAMPTZ,
//        ended_at TIMESTAMPTZ
//    );
//
// 4. ADD AN AUDIT LOG FOR BANKROLL CHANGES
//    Track every change to user bankroll for compliance and debugging:
//
//    CREATE TABLE bankroll_audit (
//        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
//        user_id UUID REFERENCES users(id),
//        game_id VARCHAR(50),
//        session_id UUID,
//        change_cents BIGINT,
//        balance_before BIGINT,
//        balance_after BIGINT,
//        reason VARCHAR(100),
//        created_at TIMESTAMPTZ DEFAULT NOW()
//    );
//
// Feel free to reach out if you need help with the integration!
// =============================================================================
