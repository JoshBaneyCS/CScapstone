// Package middleware provides HTTP middleware for the Casino API.
package middleware

import (
	"context"
	"encoding/json"
	"net/http"

	"github.com/google/uuid"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
)

// contextKey is a custom type for context keys to prevent collisions
type contextKey string

// UserIDKey is the context key for storing/retrieving the authenticated user ID
const UserIDKey contextKey = "userID"

// AuthMiddleware creates middleware that validates JWT authentication.
func AuthMiddleware(jwtService *auth.JWTService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			userID, err := jwtService.GetUserIDFromRequest(r)
			if err != nil {
				writeUnauthorized(w, "Authentication required")
				return
			}

			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserIDFromContext extracts the authenticated user ID from the request context.
func GetUserIDFromContext(ctx context.Context) (uuid.UUID, bool) {
	userID, ok := ctx.Value(UserIDKey).(uuid.UUID)
	return userID, ok
}

// MustGetUserIDFromContext extracts the user ID from context or panics.
func MustGetUserIDFromContext(ctx context.Context) uuid.UUID {
	userID, ok := GetUserIDFromContext(ctx)
	if !ok {
		panic("user ID not found in context - AuthMiddleware not applied?")
	}
	return userID
}

// ErrorResponse represents a JSON error response structure
type ErrorResponse struct {
	Error string `json:"error"`
	Code  string `json:"code,omitempty"`
}

// writeUnauthorized sends a 401 Unauthorized JSON response
func writeUnauthorized(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error: message,
		Code:  "AUTH_REQUIRED",
	})
}
