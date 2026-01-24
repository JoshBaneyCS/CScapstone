// =============================================================================
// FILE: backend/internal/web/handlers/games.go
// =============================================================================
// HTTP handlers for game-related endpoints:
//   - GET /api/games - List all available games (protected)
//
// Currently returns a static list of games. When teammates integrate their
// Python/C#/C++ games, this can be extended to query from database or
// communicate with game microservices.
// =============================================================================

package handlers

import (
	"net/http"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

// =============================================================================
// GAME TYPES
// =============================================================================

// Game represents a single casino game
type Game struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	MinBet      int64  `json:"minBet"`  // Minimum bet in cents
	MaxBet      int64  `json:"maxBet"`  // Maximum bet in cents
	Enabled     bool   `json:"enabled"` // Is game currently playable?
	ImageURL    string `json:"imageUrl,omitempty"`
}

// GamesResponse is returned by the ListGames endpoint
type GamesResponse struct {
	Games []Game `json:"games"`
	Count int    `json:"count"`
}

// =============================================================================
// STATIC GAME DATA
// =============================================================================
// This list will be replaced with database queries when games are integrated.

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
// HANDLER STRUCT
// =============================================================================

// GamesHandler handles game listing HTTP requests
type GamesHandler struct {
	// Future: add database connection for dynamic game list
	// db *db.Database
}

// NewGamesHandler creates a new GamesHandler
func NewGamesHandler() *GamesHandler {
	return &GamesHandler{}
}

// =============================================================================
// LIST GAMES HANDLER
// =============================================================================

// ListGames returns all available casino games
// GET /api/games
// Requires: Valid session cookie (enforced by auth middleware)
//
// Response (200 OK):
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
//	        }
//	    ],
//	    "count": 2
//	}
func (h *GamesHandler) ListGames(w http.ResponseWriter, r *http.Request) {
	response := GamesResponse{
		Games: availableGames,
		Count: len(availableGames),
	}

	web.WriteJSON(w, http.StatusOK, response)
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// GetGameByID finds a game by its ID
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
func GetEnabledGames() []Game {
	enabled := make([]Game, 0)
	for _, game := range availableGames {
		if game.Enabled {
			enabled = append(enabled, game)
		}
	}
	return enabled
}
