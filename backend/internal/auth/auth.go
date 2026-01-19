// =============================================================================
// AUTH.GO - AUTHENTICATION MIDDLEWARE
// =============================================================================
// This package provides HTTP middleware for authenticating requests.
// Middleware is code that runs before (or after) your route handlers.
//
// What is Middleware?
// -------------------
// Middleware wraps HTTP handlers to add functionality like:
//   - Authentication (this file)
//   - Logging
//   - Rate limiting
//   - Compression
//   - CORS handling
//
// Middleware forms a chain: Request → Middleware1 → Middleware2 → Handler
// Each middleware can:
//   - Modify the request (e.g., add data to context)
//   - Modify the response (e.g., add headers)
//   - Short-circuit the chain (e.g., return 401 Unauthorized)
//   - Pass control to the next handler
//
// How Auth Middleware Works:
// --------------------------
// 1. Extract JWT from cookie
// 2. Validate the JWT (signature + expiration)
// 3. Extract user ID from JWT
// 4. Add user ID to request context
// 5. Call the next handler (the actual route handler)
//
// If any step fails, we return 401 Unauthorized and don't call the next handler.
//
// Using Context for User ID:
// --------------------------
// Go's context.Context is used to pass request-scoped values through the
// handler chain. We store the user ID in context so handlers can access it.
//
// This is cleaner than:
//   - Global variables (not thread-safe, bad practice)
//   - Custom request structs (requires type assertions everywhere)
//   - Parsing the JWT again in every handler (wasteful)
//
// Example flow:
//   Request → AuthMiddleware (adds userID to ctx) → Handler (reads userID from ctx)
// =============================================================================

package middleware

import (
	"context"
	"encoding/json"
	"net/http"

	"github.com/google/uuid"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
)

// =============================================================================
// CONTEXT KEYS
// =============================================================================
// We use a custom type for context keys to avoid collisions with other packages.
// If two packages both use string("userID") as a key, they'd conflict.
// Using a custom type ensures our keys are unique.

// contextKey is a custom type for context keys to prevent collisions
type contextKey string

// UserIDKey is the context key for storing/retrieving the authenticated user ID
// Usage:
//
//	ctx.Value(middleware.UserIDKey).(uuid.UUID)
const UserIDKey contextKey = "userID"

// =============================================================================
// AUTH MIDDLEWARE
// =============================================================================

// AuthMiddleware creates middleware that validates JWT authentication.
// It returns a function that wraps handlers to require authentication.
//
// Parameters:
//   - jwtService: The JWT service for token validation
//
// Returns:
//   - func(http.Handler) http.Handler: Middleware function for chi router
//
// Usage with chi router:
//
//	// Protect a single route:
//	r.With(middleware.AuthMiddleware(jwtService)).Get("/protected", handler)
//
//	// Protect a group of routes:
//	r.Route("/api/games", func(r chi.Router) {
//	    r.Use(middleware.AuthMiddleware(jwtService))
//	    r.Get("/", listGamesHandler)
//	    r.Get("/{id}", getGameHandler)
//	})
//
// Example request flow:
//  1. Request arrives at /api/games
//  2. AuthMiddleware extracts JWT from cookie
//  3. AuthMiddleware validates JWT
//  4. If valid: user ID added to context, handler called
//  5. If invalid: 401 response, handler NOT called
func AuthMiddleware(jwtService *auth.JWTService) func(http.Handler) http.Handler {
	// Return the actual middleware function
	// This two-layer function pattern allows us to pass configuration (jwtService)
	// while still matching the standard middleware signature
	return func(next http.Handler) http.Handler {
		// Return an http.HandlerFunc that performs the authentication
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// -----------------------------------------------------------------
			// STEP 1: Extract and Validate Token
			// -----------------------------------------------------------------
			// GetUserIDFromRequest does both:
			//   1. Extracts JWT from the cookie
			//   2. Validates the JWT and extracts user ID

			userID, err := jwtService.GetUserIDFromRequest(r)
			if err != nil {
				// Authentication failed - return 401 Unauthorized
				// We use a generic error message to not reveal specifics to attackers
				// (Don't say "invalid signature" vs "expired" vs "no cookie")
				writeUnauthorized(w, "Authentication required")
				return // Don't call the next handler
			}

			// -----------------------------------------------------------------
			// STEP 2: Add User ID to Context
			// -----------------------------------------------------------------
			// Create a new context with the user ID added
			// context.WithValue creates a derived context with the new value
			// The original context is not modified (contexts are immutable)

			ctx := context.WithValue(r.Context(), UserIDKey, userID)

			// -----------------------------------------------------------------
			// STEP 3: Call Next Handler
			// -----------------------------------------------------------------
			// Create a new request with the updated context
			// r.WithContext returns a shallow copy of r with the new context
			// Then call the next handler in the chain

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// =============================================================================
// CONTEXT HELPERS
// =============================================================================
// These helper functions make it easy to get/set user ID in context.
// They handle type assertions and provide a clean API.

// GetUserIDFromContext extracts the authenticated user ID from the request context.
// This should only be called in handlers that are protected by AuthMiddleware.
//
// Parameters:
//   - ctx: The request context (usually r.Context())
//
// Returns:
//   - uuid.UUID: The authenticated user's ID
//   - bool: True if user ID was found, false otherwise
//
// Usage in handlers:
//
//	func MyHandler(w http.ResponseWriter, r *http.Request) {
//	    userID, ok := middleware.GetUserIDFromContext(r.Context())
//	    if !ok {
//	        // This shouldn't happen if AuthMiddleware is used correctly
//	        http.Error(w, "Internal error", http.StatusInternalServerError)
//	        return
//	    }
//	    // Use userID...
//	}
//
// Note: If the handler is properly protected by AuthMiddleware, the user ID
// will always be present. The bool return is a safety check.
func GetUserIDFromContext(ctx context.Context) (uuid.UUID, bool) {
	// Get the value from context
	// ctx.Value returns interface{}, so we need a type assertion
	userID, ok := ctx.Value(UserIDKey).(uuid.UUID)
	return userID, ok
}

// MustGetUserIDFromContext extracts the user ID from context or panics.
// Use this in handlers where AuthMiddleware is definitely applied.
//
// Parameters:
//   - ctx: The request context
//
// Returns:
//   - uuid.UUID: The authenticated user's ID
//
// Panics:
//   - If user ID is not in context (middleware not applied or bug)
//
// Usage:
//
//	userID := middleware.MustGetUserIDFromContext(r.Context())
//
// Note: Prefer GetUserIDFromContext for more defensive code.
// This is a convenience for cases where you're certain the middleware ran.
func MustGetUserIDFromContext(ctx context.Context) uuid.UUID {
	userID, ok := GetUserIDFromContext(ctx)
	if !ok {
		// This indicates a programming error - handler called without middleware
		panic("user ID not found in context - AuthMiddleware not applied?")
	}
	return userID
}

// =============================================================================
// RESPONSE HELPERS
// =============================================================================
// Helper functions for writing consistent JSON error responses.

// ErrorResponse represents a JSON error response structure
// This provides a consistent format for all API errors
type ErrorResponse struct {
	// Error contains the error message
	Error string `json:"error"`

	// Code is an optional error code for programmatic handling
	// (e.g., "AUTH_REQUIRED", "INVALID_TOKEN")
	Code string `json:"code,omitempty"`
}

// writeUnauthorized sends a 401 Unauthorized JSON response
//
// Parameters:
//   - w: The response writer
//   - message: The error message to include
//
// Response format:
//
//	{
//	    "error": "Authentication required",
//	    "code": "AUTH_REQUIRED"
//	}
func writeUnauthorized(w http.ResponseWriter, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)

	response := ErrorResponse{
		Error: message,
		Code:  "AUTH_REQUIRED",
	}

	// Encode and write the JSON response
	// We ignore the error because if we can't write the response,
	// there's nothing else we can do
	json.NewEncoder(w).Encode(response)
}

// =============================================================================
// OPTIONAL: ADDITIONAL MIDDLEWARE
// =============================================================================
// Here are some additional middleware patterns you might want to add later.
// They're commented out but provided as examples.

/*
// RequireRole creates middleware that checks if the user has a specific role.
// This would be used after AuthMiddleware to enforce role-based access control.
//
// Example:
//   r.With(AuthMiddleware(jwt), RequireRole("admin")).Get("/admin", adminHandler)
func RequireRole(role string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Get user from context
            userID, ok := GetUserIDFromContext(r.Context())
            if !ok {
                writeUnauthorized(w, "Authentication required")
                return
            }

            // TODO: Look up user's role from database
            // userRole := db.GetUserRole(userID)
            // if userRole != role {
            //     writeForbidden(w, "Insufficient permissions")
            //     return
            // }

            next.ServeHTTP(w, r)
        })
    }
}
*/

/*
// OptionalAuth creates middleware that validates JWT if present but doesn't require it.
// Useful for routes that behave differently for authenticated vs anonymous users.
//
// Example:
//   r.With(OptionalAuth(jwt)).Get("/posts", listPostsHandler)
//   // In handler: if userID exists, show personalized content
func OptionalAuth(jwtService *auth.JWTService) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Try to get user ID, but don't fail if not present
            userID, err := jwtService.GetUserIDFromRequest(r)
            if err == nil {
                // User is authenticated - add to context
                ctx := context.WithValue(r.Context(), UserIDKey, userID)
                r = r.WithContext(ctx)
            }
            // Always call next handler (authenticated or not)
            next.ServeHTTP(w, r)
        })
    }
}
*/
