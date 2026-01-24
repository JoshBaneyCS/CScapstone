// =============================================================================
// FILE: backend/internal/web/responses.go
// =============================================================================
// HTTP response helpers for standardized JSON responses across all handlers.
//
// Usage:
//   WriteJSON(w, http.StatusOK, data)
//   WriteError(w, http.StatusBadRequest, "Invalid input", "VALIDATION_ERROR")
// =============================================================================

package web

import (
	"encoding/json"
	"log"
	"net/http"
)

// ErrorResponse represents a standardized error response
type ErrorResponse struct {
	Error string `json:"error"`
	Code  string `json:"code"`
}

// WriteJSON writes a JSON response with the given status code
func WriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if data != nil {
		if err := json.NewEncoder(w).Encode(data); err != nil {
			log.Printf("Error encoding JSON response: %v", err)
		}
	}
}

// WriteError writes a standardized error response
func WriteError(w http.ResponseWriter, status int, message, code string) {
	WriteJSON(w, status, ErrorResponse{
		Error: message,
		Code:  code,
	})
}

// DecodeJSON decodes a JSON request body into the provided struct
func DecodeJSON(r *http.Request, v interface{}) error {
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	return decoder.Decode(v)
}

// Standard error codes
const (
	ErrCodeInvalidJSON       = "INVALID_JSON"
	ErrCodeValidation        = "VALIDATION_ERROR"
	ErrCodeAuthRequired      = "AUTH_REQUIRED"
	ErrCodeInvalidCreds      = "INVALID_CREDENTIALS"
	ErrCodeNotFound          = "NOT_FOUND"
	ErrCodeEmailTaken        = "EMAIL_TAKEN"
	ErrCodeUsernameTaken     = "USERNAME_TAKEN"
	ErrCodeInsufficientFunds = "INSUFFICIENT_FUNDS"
	ErrCodeAgeRestriction    = "AGE_RESTRICTION"
	ErrCodeInternal          = "INTERNAL_ERROR"
)
