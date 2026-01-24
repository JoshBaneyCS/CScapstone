// =============================================================================
// FILE: backend/internal/web/handlers/internal.go
// =============================================================================
// Internal API handlers for game services (Python, C#, C++ games).
//
// These endpoints are NOT for end users - they are called by game services:
//   - GET  /api/internal/sessions/{sessionId}          - Get session details
//   - POST /api/internal/sessions/{sessionId}/complete - Complete a session
//
// Authentication: Uses API key or internal service token (not user JWT).
// This allows game services to update bankroll without user credentials.
// =============================================================================

package handlers

import (
	"errors"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

// =============================================================================
// INTERNAL AUTH MIDDLEWARE
// =============================================================================

// InternalAuthMiddleware validates internal API requests using API key
func InternalAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get API key from environment
		expectedKey := os.Getenv("INTERNAL_API_KEY")
		if expectedKey == "" {
			// Default key for development (change in production!)
			expectedKey = "dev-internal-key-change-me"
		}

		// Check Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			web.WriteError(w, http.StatusUnauthorized, "Missing API key", "AUTH_REQUIRED")
			return
		}

		// Expect format: "Bearer <key>"
		if len(authHeader) < 7 || authHeader[:7] != "Bearer " {
			web.WriteError(w, http.StatusUnauthorized, "Invalid authorization format", "AUTH_REQUIRED")
			return
		}

		apiKey := authHeader[7:]
		if apiKey != expectedKey {
			web.WriteError(w, http.StatusUnauthorized, "Invalid API key", "INVALID_CREDENTIALS")
			return
		}

		next.ServeHTTP(w, r)
	})
}

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================

// InternalSessionResponse is returned by GetSession
type InternalSessionResponse struct {
	ID        string `json:"id"`
	UserID    string `json:"userId"`
	GameID    string `json:"gameId"`
	BetCents  int64  `json:"betCents"`
	Status    string `json:"status"`
	StartedAt string `json:"startedAt"`
}

// CompleteSessionRequest is the request body for completing a session
type CompleteSessionRequest struct {
	WinningsCents int64  `json:"winningsCents"` // Total winnings (0 if lost)
	Result        string `json:"result"`        // "win", "lose", "push"
}

// CompleteSessionResponse is returned after completing a session
type CompleteSessionResponse struct {
	SessionID     string `json:"sessionId"`
	Result        string `json:"result"`
	BetCents      int64  `json:"betCents"`
	WinningsCents int64  `json:"winningsCents"`
	BankrollCents int64  `json:"bankrollCents"` // New bankroll balance
}

// =============================================================================
// HANDLER STRUCT
// =============================================================================

// InternalHandler handles internal API requests from game services
type InternalHandler struct {
	db *db.Database
}

// NewInternalHandler creates a new InternalHandler
func NewInternalHandler(database *db.Database) *InternalHandler {
	return &InternalHandler{
		db: database,
	}
}

// =============================================================================
// GET SESSION HANDLER
// =============================================================================

// GetSession returns session details for validation by game services
// GET /api/internal/sessions/{sessionId}
// Requires: Internal API key
//
// Response (200 OK):
//
//	{
//	    "id": "uuid",
//	    "userId": "uuid",
//	    "gameId": "blackjack",
//	    "betCents": 1000,
//	    "status": "active",
//	    "startedAt": "2024-01-15T10:30:00Z"
//	}
func (h *InternalHandler) GetSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	sessionID := chi.URLParam(r, "sessionId")

	if sessionID == "" {
		web.WriteError(w, http.StatusBadRequest, "Session ID is required", web.ErrCodeValidation)
		return
	}

	// Fetch session
	var session InternalSessionResponse
	var startedAt time.Time

	err := h.db.Pool.QueryRow(ctx, `
		SELECT id, user_id, game_id, bet_cents, status, started_at
		FROM game_sessions
		WHERE id = $1
	`, sessionID).Scan(
		&session.ID, &session.UserID, &session.GameID,
		&session.BetCents, &session.Status, &startedAt,
	)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusNotFound, "Session not found", web.ErrCodeNotFound)
			return
		}
		log.Printf("Failed to get session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	session.StartedAt = startedAt.Format(time.RFC3339)

	web.WriteJSON(w, http.StatusOK, session)
}

// =============================================================================
// COMPLETE SESSION HANDLER
// =============================================================================

// CompleteSession marks a session as complete and updates bankroll
// POST /api/internal/sessions/{sessionId}/complete
// Requires: Internal API key
//
// Request:
//
//	{
//	    "winningsCents": 2000,
//	    "result": "win"
//	}
//
// Response (200 OK):
//
//	{
//	    "sessionId": "uuid",
//	    "result": "win",
//	    "betCents": 1000,
//	    "winningsCents": 2000,
//	    "bankrollCents": 251000
//	}
func (h *InternalHandler) CompleteSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	sessionID := chi.URLParam(r, "sessionId")

	if sessionID == "" {
		web.WriteError(w, http.StatusBadRequest, "Session ID is required", web.ErrCodeValidation)
		return
	}

	// Parse request
	var req CompleteSessionRequest
	if err := web.DecodeJSON(r, &req); err != nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid request body", web.ErrCodeInvalidJSON)
		return
	}

	// Validate result
	if req.Result != "win" && req.Result != "lose" && req.Result != "push" {
		web.WriteError(w, http.StatusBadRequest, "Result must be 'win', 'lose', or 'push'", web.ErrCodeValidation)
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

	// Get and lock session
	var userID string
	var betCents int64
	var status string

	err = tx.QueryRow(ctx, `
		SELECT user_id, bet_cents, status
		FROM game_sessions
		WHERE id = $1
		FOR UPDATE
	`, sessionID).Scan(&userID, &betCents, &status)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusNotFound, "Session not found", web.ErrCodeNotFound)
			return
		}
		log.Printf("Failed to get session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Check session is active
	if status != "active" {
		web.WriteError(w, http.StatusConflict, "Session is not active", "SESSION_NOT_ACTIVE")
		return
	}

	// Update session
	_, err = tx.Exec(ctx, `
		UPDATE game_sessions
		SET status = 'completed', 
		    result = $1, 
		    winnings_cents = $2, 
		    completed_at = NOW()
		WHERE id = $3
	`, req.Result, req.WinningsCents, sessionID)

	if err != nil {
		log.Printf("Failed to update session: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Update bankroll (add winnings if any)
	var newBankroll int64
	if req.WinningsCents > 0 {
		err = tx.QueryRow(ctx, `
			UPDATE accounts
			SET bankroll_cents = bankroll_cents + $1, updated_at = NOW()
			WHERE user_id = $2
			RETURNING bankroll_cents
		`, req.WinningsCents, userID).Scan(&newBankroll)
	} else {
		// Just get current bankroll
		err = tx.QueryRow(ctx, `
			SELECT bankroll_cents FROM accounts WHERE user_id = $1
		`, userID).Scan(&newBankroll)
	}

	if err != nil {
		log.Printf("Failed to update bankroll: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Commit transaction
	if err := tx.Commit(ctx); err != nil {
		log.Printf("Failed to commit transaction: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Return response
	web.WriteJSON(w, http.StatusOK, CompleteSessionResponse{
		SessionID:     sessionID,
		Result:        req.Result,
		BetCents:      betCents,
		WinningsCents: req.WinningsCents,
		BankrollCents: newBankroll,
	})
}
