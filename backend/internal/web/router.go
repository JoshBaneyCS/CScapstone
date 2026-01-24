// =============================================================================
// FILE: backend/internal/web/router.go
// =============================================================================
// HTTP router setup - defines all API routes and wires up handlers.
//
// Route Groups:
//   /health              - Health check (public)
//   /api/auth/*          - Authentication endpoints
//   /api/games/*         - Game listing and sessions (protected)
//   /api/internal/*      - Internal API for game services
// =============================================================================

package web

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"github.com/JoshBaneyCS/CScapstone/backend/internal/auth"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/db"
	"github.com/JoshBaneyCS/CScapstone/backend/internal/web/handlers"
)

// RouterConfig holds dependencies needed to set up routes
type RouterConfig struct {
	Database    *db.Database
	JWTService  *auth.JWTService
	FrontendURL string
}

// NewRouter creates and configures the main HTTP router
func NewRouter(cfg RouterConfig) chi.Router {
	r := chi.NewRouter()

	// -------------------------------------------------------------------------
	// GLOBAL MIDDLEWARE
	// -------------------------------------------------------------------------
	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(chimiddleware.Logger)
	r.Use(chimiddleware.Recoverer)
	r.Use(chimiddleware.Timeout(60 * time.Second))

	// -------------------------------------------------------------------------
	// CORS CONFIGURATION
	// -------------------------------------------------------------------------
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{cfg.FrontendURL},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token", "X-Requested-With"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// -------------------------------------------------------------------------
	// INITIALIZE HANDLERS
	// -------------------------------------------------------------------------
	authHandler := handlers.NewAuthHandler(cfg.Database, cfg.JWTService)
	gamesHandler := handlers.NewGamesHandler()
	sessionHandler := handlers.NewGameSessionHandler(cfg.Database)
	internalHandler := handlers.NewInternalHandler(cfg.Database)

	// Create auth middleware
	authMiddleware := auth.NewAuthMiddleware(cfg.JWTService)

	// -------------------------------------------------------------------------
	// HEALTH CHECK (Public)
	// -------------------------------------------------------------------------
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		WriteJSON(w, http.StatusOK, map[string]string{
			"status":  "healthy",
			"service": "casino-api",
		})
	})

	// -------------------------------------------------------------------------
	// API ROUTES
	// -------------------------------------------------------------------------
	r.Route("/api", func(r chi.Router) {

		// ---------------------------------------------------------------------
		// AUTH ROUTES (/api/auth/*)
		// ---------------------------------------------------------------------
		r.Route("/auth", func(r chi.Router) {
			r.Post("/register", authHandler.Register)
			r.Post("/login", authHandler.Login)
			r.Post("/logout", authHandler.Logout)
			r.With(authMiddleware.RequireAuth).Get("/me", authHandler.Me)
		})

		// ---------------------------------------------------------------------
		// GAMES ROUTES (/api/games/*) - Protected
		// ---------------------------------------------------------------------
		r.Route("/games", func(r chi.Router) {
			r.Use(authMiddleware.RequireAuth)
			r.Get("/", gamesHandler.ListGames)
			r.Post("/start", sessionHandler.StartGame)
			r.Get("/session", sessionHandler.GetActiveSession)
			r.Post("/session/abandon", sessionHandler.AbandonSession)
		})

		// ---------------------------------------------------------------------
		// INTERNAL API ROUTES (/api/internal/*) - For game services
		// ---------------------------------------------------------------------
		r.Route("/internal", func(r chi.Router) {
			r.Use(handlers.InternalAuthMiddleware)
			r.Get("/sessions/{sessionId}", internalHandler.GetSession)
			r.Post("/sessions/{sessionId}/complete", internalHandler.CompleteSession)
		})
	})

	return r
}
