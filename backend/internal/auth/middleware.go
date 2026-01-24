// =============================================================================
// FILE: backend/internal/auth/middleware.go
// =============================================================================
// Authentication middleware for protecting routes that require a valid session.
//
// Usage in router:
//   authMiddleware := auth.NewAuthMiddleware(jwtService)
//   r.With(authMiddleware.RequireAuth).Get("/protected", handler)
//
// The middleware:
//   1. Extracts JWT token from cookie
//   2. Validates the token
//   3. Adds user ID to request context
//   4. Passes request to next handler (or returns 401)
// =============================================================================

package auth

import (
	"context"
	"net/http"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/web"
)

// Context key type for storing user ID
type contextKey string

const (
	// UserIDContextKey is the key used to store user ID in request context
	UserIDContextKey contextKey = "userID"
)

// AuthMiddleware provides authentication middleware functions
type AuthMiddleware struct {
	jwtService *JWTService
}

// NewAuthMiddleware creates a new auth middleware instance
func NewAuthMiddleware(jwtService *JWTService) *AuthMiddleware {
	return &AuthMiddleware{
		jwtService: jwtService,
	}
}

// RequireAuth is middleware that requires a valid session cookie
//
// If valid: adds user ID to context and calls next handler
// If invalid: returns 401 Unauthorized
func (m *AuthMiddleware) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract and validate token
		userID, err := m.jwtService.GetUserIDFromRequest(r)
		if err != nil {
			web.WriteError(w, http.StatusUnauthorized, "Authentication required", web.ErrCodeAuthRequired)
			return
		}

		// Add user ID to context for downstream handlers
		ctx := context.WithValue(r.Context(), UserIDContextKey, userID)

		// Call next handler with updated context
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// OptionalAuth is middleware that validates auth if present but doesn't require it
//
// Useful for routes that behave differently for authenticated vs anonymous users
func (m *AuthMiddleware) OptionalAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try to extract and validate token
		userID, err := m.jwtService.GetUserIDFromRequest(r)
		if err == nil && userID != "" {
			// Valid token - add user ID to context
			ctx := context.WithValue(r.Context(), UserIDContextKey, userID)
			r = r.WithContext(ctx)
		}
		// Continue regardless of auth status
		next.ServeHTTP(w, r)
	})
}

// =============================================================================
// CONTEXT HELPERS
// =============================================================================
// These functions help handlers access the user ID from the request context

// GetUserIDFromContext retrieves the user ID from the request context
//
// Returns:
//   - userID: The authenticated user's ID (empty string if not found)
//   - ok: true if user ID was found in context
func GetUserIDFromContext(ctx context.Context) (string, bool) {
	userID, ok := ctx.Value(UserIDContextKey).(string)
	return userID, ok
}

// MustGetUserIDFromContext retrieves the user ID or panics if not found
//
// Use this only in handlers that are behind RequireAuth middleware,
// where you're certain the user ID will be present
func MustGetUserIDFromContext(ctx context.Context) string {
	userID, ok := GetUserIDFromContext(ctx)
	if !ok {
		panic("MustGetUserIDFromContext called without auth middleware")
	}
	return userID
}
