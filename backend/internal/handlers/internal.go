// Package handlers contains HTTP handlers for the Casino API.
// This file contains internal API endpoints used by game services.
package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
)

// InternalHandler handles internal API requests from game services
type InternalHandler struct {
	db *db.Database
}

// NewInternalHandler creates a new InternalHandler
func NewInternalHandler(database *db.Database) *InternalHandler {
	return &InternalHandler{db: database}
}

// InternalAuthMiddleware validates internal service authentication
func InternalAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authKey := r.Header.Get("X-Internal-Auth")
		expectedKey := os.Getenv("INTERNAL_AUTH_KEY")

		if expectedKey == "" {
			log.Println("WARNING: INTERNAL_AUTH_KEY not set")
			writeError(w, http.StatusInternalServerError, "Internal auth not configured", "CONFIG_ERROR")
			return
		}

		if authKey == "" || authKey != expectedKey {
			writeError(w, http.StatusUnauthorized, "Unauthorized", "AUTH_FAILED")
			return
		}
		next.ServeHTTP(w, r)
	})
}

// SessionResponse is returned when getting session details
type SessionResponse struct {
	SessionID string `json:"session_id"`
	UserID    string `json:"user_id"`
	GameType  string `json:"game_type"`
	BetCents  int64  `json:"bet_cents"`
	Status    string `json:"status"`
}

// GetSession returns session details for game service validation
// GET /api/internal/sessions/{sessionId}
func (h *InternalHandler) GetSession(w http.ResponseWriter, r *http.Request) {
	sessionID := chi.URLParam(r, "sessionId")
	sessionUUID, err := uuid.Parse(sessionID)
	if err != nil {
		writeError(w, http.StatusBadRequest, "Invalid session ID", "INVALID_SESSION")
		return
	}

	ctx := r.Context()
	var userID uuid.UUID
	var gameType string
	var betCents int64
	var status string

	err = h.db.Pool.QueryRow(ctx, `
		SELECT user_id, game_type, bet_cents, status
		FROM game_sessions
		WHERE id = $1
	`, sessionUUID).Scan(&userID, &gameType, &betCents, &status)

	if err != nil {
		writeError(w, http.StatusNotFound, "Session not found", "SESSION_NOT_FOUND")
		return
	}

	if status != "active" {
		writeError(w, http.StatusBadRequest, "Session not active", "SESSION_INACTIVE")
		return
	}

	writeJSON(w, http.StatusOK, SessionResponse{
		SessionID: sessionID,
		UserID:    userID.String(),
		GameType:  gameType,
		BetCents:  betCents,
		Status:    status,
	})
}

// CompleteSessionRequest is the request body for completing a session
type CompleteSessionRequest struct {
	Result      string `json:"result"`
	PayoutCents int64  `json:"payout_cents"`
}

// CompleteSessionResponse is returned after completing a session
type CompleteSessionResponse struct {
	Success        bool  `json:"success"`
	NewBankroll    int64 `json:"new_bankroll"`
	AccountDeleted bool  `json:"account_deleted"`
}

// CompleteSession completes a game session, updates bankroll, and deletes account if $0
// POST /api/internal/sessions/{sessionId}/complete
func (h *InternalHandler) CompleteSession(w http.ResponseWriter, r *http.Request) {
	sessionID := chi.URLParam(r, "sessionId")
	sessionUUID, err := uuid.Parse(sessionID)
	if err != nil {
		writeError(w, http.StatusBadRequest, "Invalid session ID", "INVALID_SESSION")
		return
	}

	var req CompleteSessionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body", "INVALID_JSON")
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

	// Get session and user info
	var userID uuid.UUID
	var betCents int64
	err = tx.QueryRow(ctx, `
		SELECT user_id, bet_cents FROM game_sessions
		WHERE id = $1 AND status = 'active'
		FOR UPDATE
	`, sessionUUID).Scan(&userID, &betCents)

	if err != nil {
		writeError(w, http.StatusNotFound, "Session not found or inactive", "SESSION_ERROR")
		return
	}

	// Update session to completed
	_, err = tx.Exec(ctx, `
		UPDATE game_sessions
		SET status = 'completed', result = $1, payout_cents = $2, ended_at = NOW()
		WHERE id = $3
	`, req.Result, req.PayoutCents, sessionUUID)
	if err != nil {
		log.Printf("ERROR: Failed to update session: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to update session", "DB_ERROR")
		return
	}

	// Get current bankroll
	var currentBankroll int64
	err = tx.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1 FOR UPDATE
	`, userID).Scan(&currentBankroll)
	if err != nil {
		log.Printf("ERROR: Failed to get bankroll: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to get bankroll", "DB_ERROR")
		return
	}

	// Credit payout to bankroll
	newBankroll := currentBankroll + req.PayoutCents

	_, err = tx.Exec(ctx, `
		UPDATE accounts SET bankroll_cents = $1 WHERE user_id = $2
	`, newBankroll, userID)
	if err != nil {
		log.Printf("ERROR: Failed to update bankroll: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to update bankroll", "DB_ERROR")
		return
	}

	// Record transaction
	_, err = tx.Exec(ctx, `
		INSERT INTO transactions
		(user_id, game_session_id, transaction_type, amount_cents, balance_before_cents, balance_after_cents, description)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, userID, sessionUUID, "win", req.PayoutCents, currentBankroll, newBankroll,
		"Game completed: "+req.Result)
	if err != nil {
		log.Printf("ERROR: Failed to record transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to record transaction", "DB_ERROR")
		return
	}

	// CHECK FOR $0 BANKROLL - DELETE ACCOUNT
	accountDeleted := false
	if newBankroll <= 0 {
		log.Printf("INFO: User %s bankroll hit $0 - deleting account", userID)

		// Delete user (cascades to accounts, sessions, transactions via ON DELETE CASCADE)
		_, err = tx.Exec(ctx, `DELETE FROM users WHERE id = $1`, userID)
		if err != nil {
			log.Printf("ERROR: Failed to delete user %s: %v", userID, err)
			// Don't fail the transaction - the game result should still be saved
		} else {
			accountDeleted = true
			log.Printf("INFO: User %s account deleted due to $0 bankroll", userID)
		}
	}

	if err := tx.Commit(ctx); err != nil {
		log.Printf("ERROR: Failed to commit transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to commit", "DB_ERROR")
		return
	}

	writeJSON(w, http.StatusOK, CompleteSessionResponse{
		Success:        true,
		NewBankroll:    newBankroll,
		AccountDeleted: accountDeleted,
	})
}
