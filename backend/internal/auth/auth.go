// Package auth provides JWT authentication services for the Casino API.
package auth

import (
	"errors"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

const (
	// CookieName is the name of the session cookie
	CookieName = "session"
	// TokenExpiry is how long tokens are valid
	TokenExpiry = 24 * time.Hour
)

// JWTService handles JWT token operations
type JWTService struct {
	secret       []byte
	cookieSecure bool
}

// Claims represents the JWT claims
type Claims struct {
	UserID string `json:"user_id"`
	jwt.RegisteredClaims
}

// NewJWTService creates a new JWT service
func NewJWTService(secret string, cookieSecure bool) *JWTService {
	return &JWTService{
		secret:       []byte(secret),
		cookieSecure: cookieSecure,
	}
}

// GenerateToken creates a new JWT for the given user ID
func (s *JWTService) GenerateToken(userID uuid.UUID) (string, error) {
	claims := Claims{
		UserID: userID.String(),
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(TokenExpiry)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.secret)
}

// ValidateToken validates a JWT and returns the claims
func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return s.secret, nil
	})

	if err != nil {
		return nil, err
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New("invalid token")
	}

	return claims, nil
}

// GetUserIDFromRequest extracts and validates the user ID from the session cookie
func (s *JWTService) GetUserIDFromRequest(r *http.Request) (uuid.UUID, error) {
	cookie, err := r.Cookie(CookieName)
	if err != nil {
		return uuid.Nil, errors.New("no session cookie")
	}

	claims, err := s.ValidateToken(cookie.Value)
	if err != nil {
		return uuid.Nil, err
	}

	userID, err := uuid.Parse(claims.UserID)
	if err != nil {
		return uuid.Nil, errors.New("invalid user ID in token")
	}

	return userID, nil
}

// SetSessionCookie sets the JWT in an HttpOnly cookie
func (s *JWTService) SetSessionCookie(w http.ResponseWriter, token string) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieName,
		Value:    token,
		Path:     "/",
		HttpOnly: true,
		Secure:   s.cookieSecure,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   int(TokenExpiry.Seconds()),
	})
}

// ClearSessionCookie removes the session cookie
func (s *JWTService) ClearSessionCookie(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieName,
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		Secure:   s.cookieSecure,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   -1,
	})
}
