// =============================================================================
// FILE: backend/internal/web/handlers/sessions.go
// =============================================================================
// HTTP handlers for game session management:
//   - POST /api/games/start           - Start a new game session
//   - GET  /api/games/session         - Get current active session
//   - POST /api/games/session/abandon - Abandon current session
//
// Game sessions track active gameplay and manage bankroll deductions/payouts.
// When a user starts a game, a session is created. The session tracks the bet
// amount and game state until the game completes or is abandoned.
// =============================================================================

package handlers

import (
	"errors"
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================

// StartGameRequest represents the request to start a new game
type StartGameRequest struct {
	GameID   string `json:"gameId"`
	BetCents int64  `json:"betCents"`
}

// GameSession represents an active or completed game session
type GameSession struct {
	ID            string  `json:"id"`
	UserID        string  `json:"userId"`
	GameID        string  `json:"gameId"`
	BetCents      int64   `json:"betCents"`
	Status        string  `json:"status"` // "active", "completed", "abandoned"
	WinningsCents int64   `json:"winningsCents,omitempty"`
	StartedAt     string  `json:"startedAt"`
	CompletedAt   *string `json:"completedAt,omitempty"`
}

// StartGameResponse is returned when a game session is created
type StartGameResponse struct {
	Session       GameSession `json:"session"`
	BankrollCents int64       `json:"bankrollCents"` // Updated bankroll after bet
}

// =============================================================================
// HANDLER STRUCT
// =============================================================================

// GameSessionHandler handles game session HTTP requests
type GameSessionHandler struct {
	db *db.Database
}

// NewGameSessionHandler creates a new GameSessionHandler
func NewGameSessionHandler(database *db.Database) *GameSessionHandler {
	return &GameSessionHandler{
		db: database,
	}
}

// =============================================================================
// START GAME HANDLER
// =============================================================================

// StartGame creates a new game session and deducts the bet from bankroll
// POST /api/games/start
// Requires: Valid session cookie
//
// Request:
//
//	{
//	    "gameId": "blackjack",
//	    "betCents": 1000
//	}
//
// Response (201 Created):
//
//	{
//	    "session": { ... },
//	    "bankrollCents": 249000
//	}
func (h *GameSessionHandler) StartGame(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get user ID from context
	userID, ok := auth.GetUserIDFromContext(ctx)
	if !ok {
		web.WriteError(w, http.StatusUnauthorized, "Authentication required", web.ErrCodeAuthRequired)
		return
	}

	// Parse request
	var req StartGameRequest
	if err := web.DecodeJSON(r, &req); err != nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid request body", web.ErrCodeInvalidJSON)
		return
	}

	// Validate game exists
	game := GetGameByID(req.GameID)
	if game == nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid game ID", web.ErrCodeValidation)
		return
	}

	if !game.Enabled {
		web.WriteError(w, http.StatusBadRequest, "Game is not currently available", web.ErrCodeValidation)
		return
	}

	// Validate bet amount
	if req.BetCents < game.MinBet {
		web.WriteError(w, http.StatusBadRequest, "Bet is below minimum", "BET_TOO_LOW")
		return
	}
	if req.BetCents > game.MaxBet {
		web.WriteError(w, http.StatusBadRequest, "Bet exceeds maximum", "BET_TOO_HIGH")
		return
	}

	// Check for existing active session
	var existingSessionID string
	err := h.db.Pool.QueryRow(ctx, `
		SELECT id FROM game_sessions 
		WHERE user_id = $1 AND status = 'active'
		LIMIT 1
	`, userID).Scan(&existingSessionID)

	if err == nil {
		web.WriteError(w, http.StatusConflict, "You already have an active game session", "SESSION_EXISTS")
		return
	} else if !errors.Is(err, pgx.ErrNoRows) {
		log.Printf("Failed to check existing session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Start transaction
	tx, err := h.db.Pool.Begin(ctx)
	if err != nil {
		log.Printf("Failed to begin transaction: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}
	defer tx.Rollback(ctx)

	// Check and deduct bankroll
	var newBankroll int64
	err = tx.QueryRow(ctx, `
		UPDATE accounts 
		SET bankroll_cents = bankroll_cents - $1, updated_at = NOW()
		WHERE user_id = $2 AND bankroll_cents >= $1
		RETURNING bankroll_cents
	`, req.BetCents, userID).Scan(&newBankroll)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusBadRequest, "Insufficient funds", web.ErrCodeInsufficientFunds)
			return
		}
		log.Printf("Failed to deduct bankroll: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Create game session
	sessionID := uuid.New().String()
	startedAt := time.Now()

	_, err = tx.Exec(ctx, `
		INSERT INTO game_sessions (id, user_id, game_id, bet_cents, status, started_at)
		VALUES ($1, $2, $3, $4, 'active', $5)
	`, sessionID, userID, req.GameID, req.BetCents, startedAt)

	if err != nil {
		log.Printf("Failed to create session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Commit transaction
	if err := tx.Commit(ctx); err != nil {
		log.Printf("Failed to commit transaction: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Return success
	web.WriteJSON(w, http.StatusCreated, StartGameResponse{
		Session: GameSession{
			ID:        sessionID,
			UserID:    userID,
			GameID:    req.GameID,
			BetCents:  req.BetCents,
			Status:    "active",
			StartedAt: startedAt.Format(time.RFC3339),
		},
		BankrollCents: newBankroll,
	})
}

// =============================================================================
// GET ACTIVE SESSION HANDLER
// =============================================================================

// GetActiveSession returns the user's current active game session
// GET /api/games/session
// Requires: Valid session cookie
//
// Response (200 OK): { "session": { ... } }
// Response (404): No active session
func (h *GameSessionHandler) GetActiveSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get user ID from context
	userID, ok := auth.GetUserIDFromContext(ctx)
	if !ok {
		web.WriteError(w, http.StatusUnauthorized, "Authentication required", web.ErrCodeAuthRequired)
		return
	}

	// Find active session
	var session GameSession
	var startedAt time.Time

	err := h.db.Pool.QueryRow(ctx, `
		SELECT id, user_id, game_id, bet_cents, status, started_at
		FROM game_sessions
		WHERE user_id = $1 AND status = 'active'
		LIMIT 1
	`, userID).Scan(&session.ID, &session.UserID, &session.GameID, &session.BetCents, &session.Status, &startedAt)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusNotFound, "No active session", web.ErrCodeNotFound)
			return
		}
		log.Printf("Failed to get session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	session.StartedAt = startedAt.Format(time.RFC3339)

	web.WriteJSON(w, http.StatusOK, map[string]GameSession{
		"session": session,
	})
}

// =============================================================================
// ABANDON SESSION HANDLER
// =============================================================================

// AbandonSession abandons the current active session (forfeits bet)
// POST /api/games/session/abandon
// Requires: Valid session cookie
//
// Response (200 OK): { "message": "Session abandoned" }
func (h *GameSessionHandler) AbandonSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get user ID from context
	userID, ok := auth.GetUserIDFromContext(ctx)
	if !ok {
		web.WriteError(w, http.StatusUnauthorized, "Authentication required", web.ErrCodeAuthRequired)
		return
	}

	// Update session status to abandoned
	result, err := h.db.Pool.Exec(ctx, `
		UPDATE game_sessions
		SET status = 'abandoned', completed_at = NOW()
		WHERE user_id = $1 AND status = 'active'
	`, userID)

	if err != nil {
		log.Printf("Failed to abandon session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	if result.RowsAffected() == 0 {
		web.WriteError(w, http.StatusNotFound, "No active session to abandon", web.ErrCodeNotFound)
		return
	}

	web.WriteJSON(w, http.StatusOK, map[string]string{
		"message": "Session abandoned",
	})
}
