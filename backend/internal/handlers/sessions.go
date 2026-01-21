// Package handlers contains HTTP handlers for the Casino API.
// This file contains game session management endpoints.
package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/google/uuid"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/middleware"
)

// GameSessionHandler handles game session operations
type GameSessionHandler struct {
	db *db.Database
}

// NewGameSessionHandler creates a new GameSessionHandler
func NewGameSessionHandler(database *db.Database) *GameSessionHandler {
	return &GameSessionHandler{db: database}
}

// StartGameRequest is the request body for starting a game
type StartGameRequest struct {
	GameType string `json:"game_type"`
	BetCents int64  `json:"bet_cents"`
}

// StartGameResponse is returned after starting a game
type StartGameResponse struct {
	SessionID    string `json:"session_id"`
	WebSocketURL string `json:"websocket_url"`
	GameType     string `json:"game_type"`
	BetCents     int64  `json:"bet_cents"`
}

// StartGame creates a new game session and deducts the bet from bankroll
// POST /api/games/start
func (h *GameSessionHandler) StartGame(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserIDFromContext(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "Authentication required", "AUTH_REQUIRED")
		return
	}

	var req StartGameRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body", "INVALID_JSON")
		return
	}

	// Validate game type
	game := GetGameByID(req.GameType)
	if game == nil {
		writeError(w, http.StatusBadRequest, "Invalid game type", "INVALID_GAME")
		return
	}

	if !game.Enabled {
		writeError(w, http.StatusBadRequest, "Game is not currently available", "GAME_DISABLED")
		return
	}

	// Validate bet amount
	if req.BetCents < game.MinBet {
		writeError(w, http.StatusBadRequest, "Bet is below minimum", "BET_TOO_LOW")
		return
	}
	if req.BetCents > game.MaxBet {
		writeError(w, http.StatusBadRequest, "Bet exceeds maximum", "BET_TOO_HIGH")
		return
	}

	ctx := r.Context()
	tx, err := h.db.Pool.Begin(ctx)
	if err != nil {
		log.Printf("ERROR: Failed to begin transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Database error", "DB_ERROR")
		return
	}
	defer tx.Rollback(ctx)

	// Check bankroll and lock row
	var bankroll int64
	err = tx.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1 FOR UPDATE
	`, userID).Scan(&bankroll)
	if err != nil {
		log.Printf("ERROR: Failed to check bankroll: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to check bankroll", "DB_ERROR")
		return
	}

	if bankroll < req.BetCents {
		writeError(w, http.StatusBadRequest, "Insufficient funds", "INSUFFICIENT_FUNDS")
		return
	}

	// Check for existing active session (database has unique constraint but check anyway)
	var existingCount int
	err = tx.QueryRow(ctx, `
		SELECT COUNT(*) FROM game_sessions WHERE user_id = $1 AND status = 'active'
	`, userID).Scan(&existingCount)
	if err == nil && existingCount > 0 {
		writeError(w, http.StatusConflict, "You already have an active game session", "SESSION_EXISTS")
		return
	}

	// Deduct bet from bankroll
	newBankroll := bankroll - req.BetCents
	_, err = tx.Exec(ctx, `
		UPDATE accounts SET bankroll_cents = $1 WHERE user_id = $2
	`, newBankroll, userID)
	if err != nil {
		log.Printf("ERROR: Failed to deduct bet: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to place bet", "DB_ERROR")
		return
	}

	// Create game session
	var sessionID uuid.UUID
	err = tx.QueryRow(ctx, `
		INSERT INTO game_sessions (user_id, game_type, bet_cents, status)
		VALUES ($1, $2, $3, 'active')
		RETURNING id
	`, userID, req.GameType, req.BetCents).Scan(&sessionID)
	if err != nil {
		log.Printf("ERROR: Failed to create session: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create game session", "DB_ERROR")
		return
	}

	// Record bet transaction
	_, err = tx.Exec(ctx, `
		INSERT INTO transactions
		(user_id, game_session_id, transaction_type, amount_cents, balance_before_cents, balance_after_cents, description)
		VALUES ($1, $2, 'bet', $3, $4, $5, $6)
	`, userID, sessionID, -req.BetCents, bankroll, newBankroll, "Bet placed on "+req.GameType)
	if err != nil {
		log.Printf("ERROR: Failed to record transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to record bet", "DB_ERROR")
		return
	}

	if err := tx.Commit(ctx); err != nil {
		log.Printf("ERROR: Failed to commit transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to start game", "DB_ERROR")
		return
	}

	// Build WebSocket URL
	gameServiceURL := os.Getenv("GAME_SERVICE_URL")
	if gameServiceURL == "" {
		gameServiceURL = "/ws/game"
	}
	wsURL := gameServiceURL + "/" + sessionID.String()

	log.Printf("INFO: User %s started %s game session %s with bet %d cents", userID, req.GameType, sessionID, req.BetCents)

	writeJSON(w, http.StatusCreated, StartGameResponse{
		SessionID:    sessionID.String(),
		WebSocketURL: wsURL,
		GameType:     req.GameType,
		BetCents:     req.BetCents,
	})
}

// GetActiveSession returns the user's current active game session if any
// GET /api/games/session
func (h *GameSessionHandler) GetActiveSession(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserIDFromContext(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "Authentication required", "AUTH_REQUIRED")
		return
	}

	ctx := r.Context()
	var sessionID uuid.UUID
	var gameType string
	var betCents int64

	err := h.db.Pool.QueryRow(ctx, `
		SELECT id, game_type, bet_cents
		FROM game_sessions
		WHERE user_id = $1 AND status = 'active'
	`, userID).Scan(&sessionID, &gameType, &betCents)

	if err != nil {
		// No active session is not an error
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"has_active_session": false,
		})
		return
	}

	gameServiceURL := os.Getenv("GAME_SERVICE_URL")
	if gameServiceURL == "" {
		gameServiceURL = "/ws/game"
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"has_active_session": true,
		"session": StartGameResponse{
			SessionID:    sessionID.String(),
			WebSocketURL: gameServiceURL + "/" + sessionID.String(),
			GameType:     gameType,
			BetCents:     betCents,
		},
	})
}

// AbandonSession abandons the current active game session (forfeit bet)
// POST /api/games/session/abandon
func (h *GameSessionHandler) AbandonSession(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserIDFromContext(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "Authentication required", "AUTH_REQUIRED")
		return
	}

	ctx := r.Context()
	result, err := h.db.Pool.Exec(ctx, `
		UPDATE game_sessions
		SET status = 'abandoned', result = 'lose', payout_cents = 0, ended_at = NOW()
		WHERE user_id = $1 AND status = 'active'
	`, userID)

	if err != nil {
		log.Printf("ERROR: Failed to abandon session: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to abandon session", "DB_ERROR")
		return
	}

	if result.RowsAffected() == 0 {
		writeError(w, http.StatusNotFound, "No active session to abandon", "NO_SESSION")
		return
	}

	log.Printf("INFO: User %s abandoned their game session", userID)

	writeJSON(w, http.StatusOK, MessageResponse{
		Message: "Game session abandoned",
	})
}
