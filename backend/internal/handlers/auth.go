// =============================================================================
// AUTH.GO - AUTHENTICATION HANDLERS
// =============================================================================
// This file contains HTTP handlers for user authentication:
//   - POST /api/auth/register - Create a new user account
//   - POST /api/auth/login    - Authenticate and get a session
//   - POST /api/auth/logout   - End the current session
//   - GET  /api/auth/me       - Get the current user's profile
//
// Authentication Flow:
// --------------------
// 1. REGISTER: User submits registration form
//    → Validate input (email, password, DOB, etc.)
//    → Check age >= 21 (server-side enforcement)
//    → Hash password with bcrypt
//    → Create user record in database
//    → Create account with starting bankroll ($2,500)
//    → Generate JWT and set session cookie
//    → Return user profile and bankroll
//
// 2. LOGIN: User submits email/username and password
//    → Find user by email or username
//    → Verify password against stored hash
//    → Generate JWT and set session cookie
//    → Return user profile and bankroll
//
// 3. LOGOUT: User clicks logout
//    → Clear the session cookie
//    → Return success message
//
// 4. ME: Frontend checks if user is logged in
//    → Validate JWT from cookie (via middleware)
//    → Fetch user profile and bankroll from database
//    → Return user data
//
// Security Considerations:
// ------------------------
// - Passwords are NEVER stored in plain text (bcrypt hash only)
// - Age verification is done server-side (can't trust client)
// - Generic error messages for login (don't reveal if email exists)
// - JWT stored in HttpOnly cookie (not accessible to JavaScript)
// =============================================================================

package handlers

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"golang.org/x/crypto/bcrypt"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/middleware"
)

// =============================================================================
// CONSTANTS
// =============================================================================

const (
	// MinimumAge is the required age to register (legal gambling age)
	// This is enforced server-side - never trust client-side validation!
	MinimumAge = 21

	// StartingBankrollCents is the initial balance for new users
	// $2,500.00 = 250,000 cents
	StartingBankrollCents = 250000

	// BcryptCost is the work factor for password hashing
	// Higher = more secure but slower
	// 12 is a good balance (about 250ms on modern hardware)
	// Increase this as hardware gets faster
	BcryptCost = 12
)

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================
// These structs define the shape of JSON request bodies and responses.
// Using structs with json tags ensures consistent serialization.

// RegisterRequest represents the JSON body for registration
type RegisterRequest struct {
	Email     string `json:"email"`
	Username  string `json:"username"`
	Password  string `json:"password"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	DOB       string `json:"dob"` // Format: "YYYY-MM-DD"
}

// LoginRequest represents the JSON body for login
// Users can log in with either email or username
type LoginRequest struct {
	Email    string `json:"email"`    // Optional if username provided
	Username string `json:"username"` // Optional if email provided
	Password string `json:"password"` // Required
}

// UserResponse represents user data returned to the frontend
// Note: We NEVER include password_hash in responses!
type UserResponse struct {
	ID        string `json:"id"`
	Email     string `json:"email"`
	Username  string `json:"username"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	DOB       string `json:"dob"`
	CreatedAt string `json:"createdAt"`
}

// AuthResponse is returned after successful login or registration
// It includes the user profile and their current bankroll
type AuthResponse struct {
	User          UserResponse `json:"user"`
	BankrollCents int64        `json:"bankrollCents"`
}

// ErrorResponse represents a JSON error response
type ErrorResponse struct {
	Error string `json:"error"`
	Code  string `json:"code,omitempty"`
}

// MessageResponse represents a simple success message
type MessageResponse struct {
	Message string `json:"message"`
}

// =============================================================================
// AUTH HANDLER
// =============================================================================
// AuthHandler contains all authentication-related HTTP handlers.
// It holds references to dependencies (database, JWT service) that handlers need.

type AuthHandler struct {
	db         *db.Database     // Database connection for queries
	jwtService *auth.JWTService // JWT service for token operations
}

// NewAuthHandler creates a new AuthHandler with the given dependencies
// This is called once at startup and the handler is reused for all requests
//
// Parameters:
//   - database: The database connection
//   - jwtService: The JWT service for token operations
//
// Returns:
//   - *AuthHandler: The configured handler
func NewAuthHandler(database *db.Database, jwtService *auth.JWTService) *AuthHandler {
	return &AuthHandler{
		db:         database,
		jwtService: jwtService,
	}
}

// =============================================================================
// REGISTER HANDLER
// =============================================================================

// Register handles user registration
// POST /api/auth/register
//
// Request body:
//
//	{
//	    "email": "user@example.com",
//	    "username": "johndoe",
//	    "password": "securepassword123",
//	    "firstName": "John",
//	    "lastName": "Doe",
//	    "dob": "1990-05-15"
//	}
//
// Success response (201 Created):
//
//	{
//	    "user": { ... },
//	    "bankrollCents": 250000
//	}
//
// Error responses:
//   - 400 Bad Request: Invalid input or age < 21
//   - 409 Conflict: Email or username already exists
//   - 500 Internal Server Error: Database or server error
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	// -------------------------------------------------------------------------
	// STEP 1: Parse Request Body
	// -------------------------------------------------------------------------
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid JSON request body", "INVALID_JSON")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 2: Validate Input
	// -------------------------------------------------------------------------
	// Validate all required fields are present and properly formatted

	if err := validateRegistrationInput(req); err != nil {
		writeError(w, http.StatusBadRequest, err.Error(), "VALIDATION_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 3: Parse and Validate Date of Birth
	// -------------------------------------------------------------------------
	// Parse DOB string to time.Time for age calculation

	dob, err := time.Parse("2006-01-02", req.DOB)
	if err != nil {
		writeError(w, http.StatusBadRequest, "Invalid date format. Use YYYY-MM-DD", "INVALID_DOB")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 4: Check Age Requirement (21+)
	// -------------------------------------------------------------------------
	// This is a legal requirement for gambling - MUST be server-side!
	// Never trust client-side age validation

	if !isAtLeast21(dob) {
		writeError(w, http.StatusBadRequest, "You must be at least 21 years old to register", "AGE_REQUIREMENT")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 5: Hash Password
	// -------------------------------------------------------------------------
	// bcrypt automatically generates a salt and includes it in the hash
	// The cost factor (12) determines how slow the hash is to compute
	// This makes brute-force attacks very expensive

	passwordHash, err := bcrypt.GenerateFromPassword([]byte(req.Password), BcryptCost)
	if err != nil {
		log.Printf("ERROR: Failed to hash password: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to process registration", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 6: Normalize Input
	// -------------------------------------------------------------------------
	// Normalize email and username to lowercase for consistent matching
	// Trim whitespace from all fields

	email := strings.ToLower(strings.TrimSpace(req.Email))
	username := strings.ToLower(strings.TrimSpace(req.Username))
	firstName := strings.TrimSpace(req.FirstName)
	lastName := strings.TrimSpace(req.LastName)

	// -------------------------------------------------------------------------
	// STEP 7: Insert User into Database
	// -------------------------------------------------------------------------
	// We use a transaction to ensure both user and account are created together
	// If either fails, both are rolled back (atomic operation)

	ctx := r.Context()

	// Begin transaction
	tx, err := h.db.Pool.Begin(ctx)
	if err != nil {
		log.Printf("ERROR: Failed to begin transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to process registration", "INTERNAL_ERROR")
		return
	}
	// Defer rollback - it's a no-op if transaction is committed
	defer tx.Rollback(ctx)

	// Insert user record
	var userID uuid.UUID
	var createdAt time.Time

	err = tx.QueryRow(ctx, `
		INSERT INTO users (email, username, password_hash, first_name, last_name, dob)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at
	`, email, username, string(passwordHash), firstName, lastName, dob).Scan(&userID, &createdAt)

	if err != nil {
		// Check if it's a unique constraint violation (duplicate email/username)
		if strings.Contains(err.Error(), "unique constraint") {
			if strings.Contains(err.Error(), "email") {
				writeError(w, http.StatusConflict, "Email already registered", "EMAIL_EXISTS")
			} else {
				writeError(w, http.StatusConflict, "Username already taken", "USERNAME_EXISTS")
			}
			return
		}
		log.Printf("ERROR: Failed to insert user: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create account", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 8: Create Account with Starting Bankroll
	// -------------------------------------------------------------------------
	// Every user gets a casino account with $2,500 starting balance

	_, err = tx.Exec(ctx, `
		INSERT INTO accounts (user_id, bankroll_cents)
		VALUES ($1, $2)
	`, userID, StartingBankrollCents)

	if err != nil {
		log.Printf("ERROR: Failed to create account: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create account", "INTERNAL_ERROR")
		return
	}

	// Commit the transaction
	if err := tx.Commit(ctx); err != nil {
		log.Printf("ERROR: Failed to commit transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create account", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 9: Generate JWT and Set Cookie
	// -------------------------------------------------------------------------
	// User is now registered - log them in automatically

	token, err := h.jwtService.GenerateToken(userID)
	if err != nil {
		log.Printf("ERROR: Failed to generate token: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create session", "INTERNAL_ERROR")
		return
	}

	// Set the session cookie
	h.jwtService.SetSessionCookie(w, token)

	// -------------------------------------------------------------------------
	// STEP 10: Return Success Response
	// -------------------------------------------------------------------------
	response := AuthResponse{
		User: UserResponse{
			ID:        userID.String(),
			Email:     email,
			Username:  username,
			FirstName: firstName,
			LastName:  lastName,
			DOB:       req.DOB,
			CreatedAt: createdAt.Format(time.RFC3339),
		},
		BankrollCents: StartingBankrollCents,
	}

	writeJSON(w, http.StatusCreated, response)
	log.Printf("INFO: New user registered: %s (%s)", username, email)
}

// =============================================================================
// LOGIN HANDLER
// =============================================================================

// Login handles user authentication
// POST /api/auth/login
//
// Request body (with email):
//
//	{
//	    "email": "user@example.com",
//	    "password": "securepassword123"
//	}
//
// Request body (with username):
//
//	{
//	    "username": "johndoe",
//	    "password": "securepassword123"
//	}
//
// Success response (200 OK):
//
//	{
//	    "user": { ... },
//	    "bankrollCents": 250000
//	}
//
// Error responses:
//   - 400 Bad Request: Missing email/username or password
//   - 401 Unauthorized: Invalid credentials
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	// -------------------------------------------------------------------------
	// STEP 1: Parse Request Body
	// -------------------------------------------------------------------------
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid JSON request body", "INVALID_JSON")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 2: Validate Input
	// -------------------------------------------------------------------------
	// Need either email or username, and password is always required

	if req.Email == "" && req.Username == "" {
		writeError(w, http.StatusBadRequest, "Email or username is required", "VALIDATION_ERROR")
		return
	}
	if req.Password == "" {
		writeError(w, http.StatusBadRequest, "Password is required", "VALIDATION_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 3: Find User in Database
	// -------------------------------------------------------------------------
	// Query by email or username (case-insensitive)

	ctx := r.Context()
	var userID uuid.UUID
	var email, username, passwordHash, firstName, lastName string
	var dob, createdAt time.Time

	// Build query based on whether email or username was provided
	var query string
	var param string

	if req.Email != "" {
		query = `
			SELECT id, email, username, password_hash, first_name, last_name, dob, created_at
			FROM users
			WHERE LOWER(email) = LOWER($1)
		`
		param = strings.TrimSpace(req.Email)
	} else {
		query = `
			SELECT id, email, username, password_hash, first_name, last_name, dob, created_at
			FROM users
			WHERE LOWER(username) = LOWER($1)
		`
		param = strings.TrimSpace(req.Username)
	}

	err := h.db.Pool.QueryRow(ctx, query, param).Scan(
		&userID, &email, &username, &passwordHash,
		&firstName, &lastName, &dob, &createdAt,
	)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			// User not found - use generic error to not reveal if email exists
			// SECURITY: Don't say "email not found" as this reveals valid emails
			writeError(w, http.StatusUnauthorized, "Invalid email/username or password", "INVALID_CREDENTIALS")
			return
		}
		log.Printf("ERROR: Database error during login: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to process login", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 4: Verify Password
	// -------------------------------------------------------------------------
	// bcrypt.CompareHashAndPassword safely compares the password to the hash
	// It's designed to take constant time to prevent timing attacks

	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password)); err != nil {
		// Password doesn't match - use same error as "user not found"
		// SECURITY: Don't reveal whether email exists by using different errors
		writeError(w, http.StatusUnauthorized, "Invalid email/username or password", "INVALID_CREDENTIALS")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 5: Get User's Bankroll
	// -------------------------------------------------------------------------
	var bankrollCents int64
	err = h.db.Pool.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1
	`, userID).Scan(&bankrollCents)

	if err != nil {
		log.Printf("ERROR: Failed to get bankroll for user %s: %v", userID, err)
		writeError(w, http.StatusInternalServerError, "Failed to process login", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 6: Generate JWT and Set Cookie
	// -------------------------------------------------------------------------
	token, err := h.jwtService.GenerateToken(userID)
	if err != nil {
		log.Printf("ERROR: Failed to generate token: %v", err)
		writeError(w, http.StatusInternalServerError, "Failed to create session", "INTERNAL_ERROR")
		return
	}

	h.jwtService.SetSessionCookie(w, token)

	// -------------------------------------------------------------------------
	// STEP 7: Return Success Response
	// -------------------------------------------------------------------------
	response := AuthResponse{
		User: UserResponse{
			ID:        userID.String(),
			Email:     email,
			Username:  username,
			FirstName: firstName,
			LastName:  lastName,
			DOB:       dob.Format("2006-01-02"),
			CreatedAt: createdAt.Format(time.RFC3339),
		},
		BankrollCents: bankrollCents,
	}

	writeJSON(w, http.StatusOK, response)
	log.Printf("INFO: User logged in: %s", username)
}

// =============================================================================
// LOGOUT HANDLER
// =============================================================================

// Logout handles user logout by clearing the session cookie
// POST /api/auth/logout
//
// # No request body required
//
// Success response (200 OK):
//
//	{
//	    "message": "Logged out successfully"
//	}
func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	// Clear the session cookie
	h.jwtService.ClearSessionCookie(w)

	// Return success message
	writeJSON(w, http.StatusOK, MessageResponse{
		Message: "Logged out successfully",
	})
	log.Printf("INFO: User logged out")
}

// =============================================================================
// ME HANDLER (Get Current User)
// =============================================================================

// Me returns the current authenticated user's profile and bankroll
// GET /api/auth/me
//
// Requires: Valid session cookie (enforced by AuthMiddleware)
//
// Success response (200 OK):
//
//	{
//	    "user": { ... },
//	    "bankrollCents": 250000
//	}
//
// Error responses:
//   - 401 Unauthorized: No valid session (handled by middleware)
//   - 500 Internal Server Error: Database error
func (h *AuthHandler) Me(w http.ResponseWriter, r *http.Request) {
	// -------------------------------------------------------------------------
	// STEP 1: Get User ID from Context
	// -------------------------------------------------------------------------
	// The AuthMiddleware has already validated the JWT and added the user ID
	// to the request context. We just need to retrieve it.

	userID, ok := middleware.GetUserIDFromContext(r.Context())
	if !ok {
		// This shouldn't happen if AuthMiddleware is applied correctly
		writeError(w, http.StatusUnauthorized, "Authentication required", "AUTH_REQUIRED")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 2: Fetch User Profile from Database
	// -------------------------------------------------------------------------
	ctx := r.Context()
	var email, username, firstName, lastName string
	var dob, createdAt time.Time

	err := h.db.Pool.QueryRow(ctx, `
		SELECT email, username, first_name, last_name, dob, created_at
		FROM users
		WHERE id = $1
	`, userID).Scan(&email, &username, &firstName, &lastName, &dob, &createdAt)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			// User was deleted but still has valid token
			// Clear their cookie and return unauthorized
			h.jwtService.ClearSessionCookie(w)
			writeError(w, http.StatusUnauthorized, "User not found", "USER_NOT_FOUND")
			return
		}
		log.Printf("ERROR: Failed to fetch user %s: %v", userID, err)
		writeError(w, http.StatusInternalServerError, "Failed to fetch profile", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 3: Fetch User's Bankroll
	// -------------------------------------------------------------------------
	var bankrollCents int64
	err = h.db.Pool.QueryRow(ctx, `
		SELECT bankroll_cents FROM accounts WHERE user_id = $1
	`, userID).Scan(&bankrollCents)

	if err != nil {
		log.Printf("ERROR: Failed to fetch bankroll for user %s: %v", userID, err)
		writeError(w, http.StatusInternalServerError, "Failed to fetch profile", "INTERNAL_ERROR")
		return
	}

	// -------------------------------------------------------------------------
	// STEP 4: Return User Profile
	// -------------------------------------------------------------------------
	response := AuthResponse{
		User: UserResponse{
			ID:        userID.String(),
			Email:     email,
			Username:  username,
			FirstName: firstName,
			LastName:  lastName,
			DOB:       dob.Format("2006-01-02"),
			CreatedAt: createdAt.Format(time.RFC3339),
		},
		BankrollCents: bankrollCents,
	}

	writeJSON(w, http.StatusOK, response)
}

// =============================================================================
// VALIDATION HELPERS
// =============================================================================

// validateRegistrationInput validates all fields in the registration request
// Returns an error describing the first validation failure, or nil if valid
func validateRegistrationInput(req RegisterRequest) error {
	// Email validation
	if req.Email == "" {
		return errors.New("email is required")
	}
	if !strings.Contains(req.Email, "@") || !strings.Contains(req.Email, ".") {
		return errors.New("invalid email format")
	}
	if len(req.Email) > 255 {
		return errors.New("email must be 255 characters or less")
	}

	// Username validation
	if req.Username == "" {
		return errors.New("username is required")
	}
	if len(req.Username) < 3 {
		return errors.New("username must be at least 3 characters")
	}
	if len(req.Username) > 50 {
		return errors.New("username must be 50 characters or less")
	}
	// Only allow alphanumeric and underscores
	for _, char := range req.Username {
		if !isAlphanumericOrUnderscore(char) {
			return errors.New("username can only contain letters, numbers, and underscores")
		}
	}

	// Password validation
	if req.Password == "" {
		return errors.New("password is required")
	}
	if len(req.Password) < 8 {
		return errors.New("password must be at least 8 characters")
	}
	if len(req.Password) > 72 {
		// bcrypt has a max input length of 72 bytes
		return errors.New("password must be 72 characters or less")
	}

	// Name validation
	if req.FirstName == "" {
		return errors.New("first name is required")
	}
	if len(req.FirstName) > 100 {
		return errors.New("first name must be 100 characters or less")
	}
	if req.LastName == "" {
		return errors.New("last name is required")
	}
	if len(req.LastName) > 100 {
		return errors.New("last name must be 100 characters or less")
	}

	// DOB validation (format check - age check done separately)
	if req.DOB == "" {
		return errors.New("date of birth is required")
	}

	return nil
}

// isAlphanumericOrUnderscore checks if a character is a letter, number, or underscore
func isAlphanumericOrUnderscore(char rune) bool {
	return (char >= 'a' && char <= 'z') ||
		(char >= 'A' && char <= 'Z') ||
		(char >= '0' && char <= '9') ||
		char == '_'
}

// isAtLeast21 checks if a person with the given DOB is at least 21 years old
// This uses proper date comparison, not days/365 which has edge cases
func isAtLeast21(dob time.Time) bool {
	// Get today's date (without time component)
	now := time.Now()
	today := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)

	// Calculate the date 21 years ago from today
	// AddDate handles leap years and month-length variations correctly
	minimumDOB := today.AddDate(-MinimumAge, 0, 0)

	// User must be born ON or BEFORE this date to be 21+
	// Before() is true if dob < minimumDOB
	// Equal() is true if dob == minimumDOB
	return dob.Before(minimumDOB) || dob.Equal(minimumDOB)
}

// =============================================================================
// RESPONSE HELPERS
// =============================================================================

// writeJSON writes a JSON response with the given status code
func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// writeError writes a JSON error response
func writeError(w http.ResponseWriter, status int, message string, code string) {
	writeJSON(w, status, ErrorResponse{
		Error: message,
		Code:  code,
	})
}
