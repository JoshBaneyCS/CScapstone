// =============================================================================
// FILE: backend/internal/web/handlers/auth.go
// =============================================================================
// HTTP handlers for user authentication endpoints:
//   - POST /api/auth/register - Create a new user account
//   - POST /api/auth/login    - Authenticate and get a session
//   - POST /api/auth/logout   - End the current session
//   - GET  /api/auth/me       - Get the current user's profile
// =============================================================================

package handlers

import (
	"errors"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"golang.org/x/crypto/bcrypt"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================

// RegisterRequest represents the registration form data
type RegisterRequest struct {
	Email     string `json:"email"`
	Username  string `json:"username"`
	Password  string `json:"password"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	DOB       string `json:"dob"` // Format: "YYYY-MM-DD"
}

// LoginRequest represents the login form data
type LoginRequest struct {
	Email    string `json:"email,omitempty"`
	Username string `json:"username,omitempty"`
	Password string `json:"password"`
}

// UserResponse represents user data returned to the client
type UserResponse struct {
	ID        string `json:"id"`
	Email     string `json:"email"`
	Username  string `json:"username"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	DOB       string `json:"dob"`
	CreatedAt string `json:"createdAt"`
}

// AuthResponse is returned on successful login/register
type AuthResponse struct {
	User          UserResponse `json:"user"`
	BankrollCents int64        `json:"bankrollCents"`
}

// =============================================================================
// HANDLER STRUCT
// =============================================================================

// AuthHandler handles all authentication HTTP requests
type AuthHandler struct {
	db         *db.Database
	jwtService *auth.JWTService
}

// NewAuthHandler creates a new AuthHandler with required dependencies
func NewAuthHandler(database *db.Database, jwtService *auth.JWTService) *AuthHandler {
	return &AuthHandler{
		db:         database,
		jwtService: jwtService,
	}
}

// =============================================================================
// REGISTER HANDLER
// =============================================================================

// Register creates a new user account
// POST /api/auth/register
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Parse request body
	var req RegisterRequest
	if err := web.DecodeJSON(r, &req); err != nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid request body", web.ErrCodeInvalidJSON)
		return
	}

	// Validate required fields
	if req.Email == "" || req.Username == "" || req.Password == "" ||
		req.FirstName == "" || req.LastName == "" || req.DOB == "" {
		web.WriteError(w, http.StatusBadRequest, "All fields are required", web.ErrCodeValidation)
		return
	}

	// Validate password length
	if len(req.Password) < 8 {
		web.WriteError(w, http.StatusBadRequest, "Password must be at least 8 characters", web.ErrCodeValidation)
		return
	}

	// Normalize email and username
	email := strings.ToLower(strings.TrimSpace(req.Email))
	username := strings.TrimSpace(req.Username)

	// Parse and validate DOB (must be 21+)
	dob, err := time.Parse("2006-01-02", req.DOB)
	if err != nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid date format. Use YYYY-MM-DD", web.ErrCodeValidation)
		return
	}

	if !isAtLeast21(dob) {
		web.WriteError(w, http.StatusBadRequest, "You must be at least 21 years old to register", web.ErrCodeAgeRestriction)
		return
	}

	// Hash password
	passwordHash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		log.Printf("Failed to hash password: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Insert user and create account in a transaction
	var userID string
	var createdAt time.Time

	// Start transaction
	tx, err := h.db.Pool.Begin(ctx)
	if err != nil {
		log.Printf("Failed to begin transaction: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}
	defer tx.Rollback(ctx)

	// Insert user
	err = tx.QueryRow(ctx, `
		INSERT INTO users (email, username, password_hash, first_name, last_name, dob)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at
	`, email, username, string(passwordHash), req.FirstName, req.LastName, dob).Scan(&userID, &createdAt)

	if err != nil {
		if strings.Contains(err.Error(), "users_email_key") {
			web.WriteError(w, http.StatusConflict, "Email already registered", web.ErrCodeEmailTaken)
			return
		}
		if strings.Contains(err.Error(), "users_username_key") {
			web.WriteError(w, http.StatusConflict, "Username already taken", web.ErrCodeUsernameTaken)
			return
		}
		log.Printf("Failed to insert user: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Create account with starting bankroll ($2,500 = 250000 cents)
	_, err = tx.Exec(ctx, `
		INSERT INTO accounts (user_id, bankroll_cents)
		VALUES ($1, 250000)
	`, userID)
	if err != nil {
		log.Printf("Failed to create account: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Commit transaction
	if err := tx.Commit(ctx); err != nil {
		log.Printf("Failed to commit transaction: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Set session cookie
	if err := h.jwtService.SetSessionCookie(w, userID); err != nil {
		log.Printf("Failed to set session cookie: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Return success response
	web.WriteJSON(w, http.StatusCreated, AuthResponse{
		User: UserResponse{
			ID:        userID,
			Email:     email,
			Username:  username,
			FirstName: req.FirstName,
			LastName:  req.LastName,
			DOB:       dob.Format("2006-01-02"),
			CreatedAt: createdAt.Format(time.RFC3339),
		},
		BankrollCents: 250000,
	})
}

// =============================================================================
// LOGIN HANDLER
// =============================================================================

// Login authenticates a user and creates a session
// POST /api/auth/login
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Parse request
	var req LoginRequest
	if err := web.DecodeJSON(r, &req); err != nil {
		web.WriteError(w, http.StatusBadRequest, "Invalid request body", web.ErrCodeInvalidJSON)
		return
	}

	// Validate - need email OR username, plus password
	if req.Email == "" && req.Username == "" {
		web.WriteError(w, http.StatusBadRequest, "Email or username is required", web.ErrCodeValidation)
		return
	}
	if req.Password == "" {
		web.WriteError(w, http.StatusBadRequest, "Password is required", web.ErrCodeValidation)
		return
	}

	// Find user by email or username
	var user struct {
		ID           string
		Email        string
		Username     string
		PasswordHash string
		FirstName    string
		LastName     string
		DOB          time.Time
		CreatedAt    time.Time
	}

	var query string
	var param string

	if req.Email != "" {
		query = `SELECT id, email, username, password_hash, first_name, last_name, dob, created_at 
		         FROM users WHERE LOWER(email) = LOWER($1)`
		param = req.Email
	} else {
		query = `SELECT id, email, username, password_hash, first_name, last_name, dob, created_at 
		         FROM users WHERE LOWER(username) = LOWER($1)`
		param = req.Username
	}

	err := h.db.Pool.QueryRow(ctx, query, param).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, &user.DOB, &user.CreatedAt,
	)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusUnauthorized, "Invalid credentials", web.ErrCodeInvalidCreds)
			return
		}
		log.Printf("Database error during login: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		web.WriteError(w, http.StatusUnauthorized, "Invalid credentials", web.ErrCodeInvalidCreds)
		return
	}

	// Get bankroll
	var bankrollCents int64
	err = h.db.Pool.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1
	`, user.ID).Scan(&bankrollCents)

	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		log.Printf("Failed to get bankroll: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Set session cookie
	if err := h.jwtService.SetSessionCookie(w, user.ID); err != nil {
		log.Printf("Failed to set session cookie: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Return success
	web.WriteJSON(w, http.StatusOK, AuthResponse{
		User: UserResponse{
			ID:        user.ID,
			Email:     user.Email,
			Username:  user.Username,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			DOB:       user.DOB.Format("2006-01-02"),
			CreatedAt: user.CreatedAt.Format(time.RFC3339),
		},
		BankrollCents: bankrollCents,
	})
}

// =============================================================================
// LOGOUT HANDLER
// =============================================================================

// Logout clears the session cookie
// POST /api/auth/logout
func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	h.jwtService.ClearSessionCookie(w)
	web.WriteJSON(w, http.StatusOK, map[string]string{
		"message": "Logged out successfully",
	})
}

// =============================================================================
// ME HANDLER (Protected)
// =============================================================================

// Me returns the current user's profile and bankroll
// GET /api/auth/me
// Requires: Valid session cookie (enforced by auth middleware)
func (h *AuthHandler) Me(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get user ID from context (set by auth middleware)
	userID, ok := auth.GetUserIDFromContext(ctx)
	if !ok {
		web.WriteError(w, http.StatusUnauthorized, "Authentication required", web.ErrCodeAuthRequired)
		return
	}

	// Fetch user data
	var user struct {
		Email     string
		Username  string
		FirstName string
		LastName  string
		DOB       time.Time
		CreatedAt time.Time
	}

	err := h.db.Pool.QueryRow(ctx, `
		SELECT email, username, first_name, last_name, dob, created_at
		FROM users WHERE id = $1
	`, userID).Scan(&user.Email, &user.Username, &user.FirstName, &user.LastName, &user.DOB, &user.CreatedAt)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			web.WriteError(w, http.StatusNotFound, "User not found", web.ErrCodeNotFound)
			return
		}
		log.Printf("Failed to fetch user: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Fetch bankroll
	var bankrollCents int64
	err = h.db.Pool.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1
	`, userID).Scan(&bankrollCents)

	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		log.Printf("Failed to fetch bankroll: %v", err)
		web.WriteError(w, http.StatusInternalServerError, "Internal server error", web.ErrCodeInternal)
		return
	}

	// Return user data
	web.WriteJSON(w, http.StatusOK, AuthResponse{
		User: UserResponse{
			ID:        userID,
			Email:     user.Email,
			Username:  user.Username,
			FirstName: user.FirstName,
			LastName:  user.LastName,
			DOB:       user.DOB.Format("2006-01-02"),
			CreatedAt: user.CreatedAt.Format(time.RFC3339),
		},
		BankrollCents: bankrollCents,
	})
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// isAtLeast21 checks if the person is at least 21 years old
func isAtLeast21(dob time.Time) bool {
	now := time.Now()
	age := now.Year() - dob.Year()

	// Adjust if birthday hasn't occurred this year
	if now.YearDay() < dob.YearDay() {
		age--
	}

	return age >= 21
}
