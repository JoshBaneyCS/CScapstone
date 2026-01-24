// =============================================================================
// FILE: backend/internal/auth/jwt.go
// =============================================================================
// JWT (JSON Web Token) service for creating and validating authentication tokens.
//
// This service handles:
//   - Generating JWT tokens for authenticated users
//   - Validating tokens from incoming requests
//   - Setting and clearing session cookies
//
// Security Notes:
//   - Tokens are stored in HttpOnly cookies (not accessible to JavaScript)
//   - Tokens expire after 24 hours
//   - Cookie secure flag is configurable for dev/prod environments
// =============================================================================

package auth

import (
	"errors"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// Cookie and token configuration
const (
	CookieName      = "casino_session"
	TokenExpiration = 24 * time.Hour
)

// Custom errors
var (
	ErrInvalidToken = errors.New("invalid or expired token")
	ErrMissingToken = errors.New("missing authentication token")
)

// Claims represents the JWT claims structure
type Claims struct {
	UserID string `json:"user_id"`
	jwt.RegisteredClaims
}

// JWTService handles JWT token operations
type JWTService struct {
	secretKey    []byte
	cookieSecure bool // true in production (HTTPS), false in dev (HTTP)
}

// NewJWTService creates a new JWT service
//
// Parameters:
//   - secret: The secret key for signing tokens (keep this secure!)
//   - cookieSecure: Set to true in production to require HTTPS
func NewJWTService(secret string, cookieSecure bool) *JWTService {
	return &JWTService{
		secretKey:    []byte(secret),
		cookieSecure: cookieSecure,
	}
}

// GenerateToken creates a new JWT token for a user
//
// Parameters:
//   - userID: The UUID of the authenticated user
//
// Returns:
//   - Signed JWT token string
//   - Error if signing fails
func (s *JWTService) GenerateToken(userID string) (string, error) {
	now := time.Now()

	claims := Claims{
		UserID: userID,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(now.Add(TokenExpiration)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "casino-api",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.secretKey)
}

// ValidateToken validates a JWT token and returns the claims
//
// Parameters:
//   - tokenString: The JWT token to validate
//
// Returns:
//   - Claims containing user_id if valid
//   - Error if token is invalid, expired, or malformed
func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, ErrInvalidToken
		}
		return s.secretKey, nil
	})

	if err != nil {
		return nil, ErrInvalidToken
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, ErrInvalidToken
	}

	return claims, nil
}

// SetSessionCookie sets the JWT token as an HttpOnly cookie
//
// Parameters:
//   - w: HTTP response writer
//   - userID: User ID to encode in the token
func (s *JWTService) SetSessionCookie(w http.ResponseWriter, userID string) error {
	token, err := s.GenerateToken(userID)
	if err != nil {
		return err
	}

	http.SetCookie(w, &http.Cookie{
		Name:     CookieName,
		Value:    token,
		Path:     "/",
		HttpOnly: true,                 // Not accessible to JavaScript
		Secure:   s.cookieSecure,       // HTTPS only in production
		SameSite: http.SameSiteLaxMode, // CSRF protection
		MaxAge:   int(TokenExpiration.Seconds()),
	})

	return nil
}

// ClearSessionCookie removes the session cookie (logout)
func (s *JWTService) ClearSessionCookie(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieName,
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		Secure:   s.cookieSecure,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   -1, // Delete immediately
	})
}

// GetTokenFromRequest extracts the JWT token from the request cookie
//
// Returns:
//   - Token string if found
//   - Error if cookie is missing
func (s *JWTService) GetTokenFromRequest(r *http.Request) (string, error) {
	cookie, err := r.Cookie(CookieName)
	if err != nil {
		return "", ErrMissingToken
	}
	return cookie.Value, nil
}

// GetUserIDFromRequest validates the token and returns the user ID
//
// This is a convenience method that combines GetTokenFromRequest and ValidateToken
func (s *JWTService) GetUserIDFromRequest(r *http.Request) (string, error) {
	tokenString, err := s.GetTokenFromRequest(r)
	if err != nil {
		return "", err
	}

	claims, err := s.ValidateToken(tokenString)
	if err != nil {
		return "", err
	}

	return claims.UserID, nil
}
