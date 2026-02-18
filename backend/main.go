package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
)

var db *sql.DB
var jwtSecret []byte
var templates *template.Template

type User struct {
	ID              string `json:"id"`
	Email           string `json:"email"`
	FirstName       string `json:"first_name"`
	LastName        string `json:"last_name"`
	BankrollCents   int64  `json:"bankroll_cents"`
	BlackjackWins   int    `json:"blackjack_wins"`
	BlackjackLosses int    `json:"blackjack_losses"`
	PokerWins       int    `json:"poker_wins"`
	PokerLosses     int    `json:"poker_losses"`
}

type RegisterRequest struct {
	Email     string `json:"email"`
	Password  string `json:"password"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type BetRequest struct {
	Bet int `json:"bet"`
}

func main() {
	var err error
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://casino_admin:casino_secret_password_123@localhost:5432/casino_db?sslmode=disable"
	}
	db, err = sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	for i := 0; i < 30; i++ {
		if err = db.Ping(); err == nil {
			break
		}
		log.Println("Waiting for database...")
		time.Sleep(time.Second)
	}
	if err != nil {
		log.Fatal("Database not available:", err)
	}

	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "dev-secret-key-change-in-production"
	}
	jwtSecret = []byte(secret)

	// Load templates
	tmplPath := os.Getenv("TEMPLATE_PATH")
	if tmplPath == "" {
		tmplPath = "templates"
	}
	var err2 error
	templates, err2 = template.ParseGlob(filepath.Join(tmplPath, "*.html"))
	if err2 != nil {
		log.Printf("Warning: Could not load templates: %v", err2)
	}

	r := mux.NewRouter()

	// Static files
	staticPath := filepath.Join(filepath.Dir(tmplPath), "static")
	r.PathPrefix("/static/").Handler(http.StripPrefix("/static/", http.FileServer(http.Dir(staticPath))))

	// Page routes (HTML)
	r.HandleFunc("/", handleIndexPage).Methods("GET")
	r.HandleFunc("/login", handleLoginPage).Methods("GET")
	r.HandleFunc("/login", handleLoginForm).Methods("POST")
	r.HandleFunc("/register", handleRegisterPage).Methods("GET")
	r.HandleFunc("/register", handleRegisterForm).Methods("POST")
	r.HandleFunc("/game", handleGamePage).Methods("GET")
	r.HandleFunc("/logout", handleLogoutPage).Methods("GET")

	// Public API routes
	r.HandleFunc("/api/auth/register", handleRegister).Methods("POST")
	r.HandleFunc("/api/auth/login", handleLogin).Methods("POST")
	r.HandleFunc("/api/health", handleHealth).Methods("GET")

	// Protected routes
	api := r.PathPrefix("/api").Subrouter()
	api.Use(authMiddleware)
	api.HandleFunc("/auth/logout", handleLogout).Methods("POST")
	api.HandleFunc("/auth/me", handleMe).Methods("GET")
	api.HandleFunc("/bankroll", handleBankroll).Methods("GET")

	// Blackjack proxy
	api.HandleFunc("/blackjack/start", handleBlackjackStart).Methods("POST")
	api.HandleFunc("/blackjack/hit", proxyBlackjack("/blackjack/hit")).Methods("POST")
	api.HandleFunc("/blackjack/stand", handleBlackjackStand).Methods("POST")
	api.HandleFunc("/blackjack/state", proxyBlackjack("/blackjack/state")).Methods("GET")

	// Poker proxy
	api.HandleFunc("/poker/start", handlePokerStart).Methods("POST")
	api.HandleFunc("/poker/action", proxyPoker("/texas/single/action")).Methods("POST")
	api.HandleFunc("/poker/bet", proxyPoker("/texas/single/bet")).Methods("POST")
	api.HandleFunc("/poker/flop", proxyPoker("/texas/flop")).Methods("POST")
	api.HandleFunc("/poker/turn", proxyPoker("/texas/turn")).Methods("POST")
	api.HandleFunc("/poker/river", proxyPoker("/texas/river")).Methods("POST")
	api.HandleFunc("/poker/showdown", handlePokerShowdown).Methods("POST")
	api.HandleFunc("/poker/state", proxyPoker("/texas/state")).Methods("GET")

	// CORS for dev
	r.Use(corsMiddleware)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Backend listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", r.Header.Get("Origin"))
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		cookie, err := r.Cookie("casino_session")
		if err != nil {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		token, err := jwt.Parse(cookie.Value, func(t *jwt.Token) (interface{}, error) {
			return jwtSecret, nil
		})
		if err != nil || !token.Valid {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		claims := token.Claims.(jwt.MapClaims)
		r.Header.Set("X-User-ID", claims["user_id"].(string))
		next.ServeHTTP(w, r)
	})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	if err := json.NewEncoder(w).Encode(map[string]string{"status": "ok"}); err != nil {
		log.Printf("Failed to encode health response: %v", err)
	}
}

func handleRegister(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	if req.Email == "" || req.Password == "" || req.FirstName == "" || req.LastName == "" {
		http.Error(w, "All fields required", http.StatusBadRequest)
		return
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Server error", http.StatusInternalServerError)
		return
	}
	var user User
	err = db.QueryRow(`
		INSERT INTO users (email, password_hash, first_name, last_name)
		VALUES ($1, $2, $3, $4)
		RETURNING id, email, first_name, last_name, bankroll_cents, blackjack_wins, blackjack_losses, poker_wins, poker_losses
	`, req.Email, string(hash), req.FirstName, req.LastName).Scan(
		&user.ID, &user.Email, &user.FirstName, &user.LastName, &user.BankrollCents,
		&user.BlackjackWins, &user.BlackjackLosses, &user.PokerWins, &user.PokerLosses,
	)
	if err != nil {
		if strings.Contains(err.Error(), "unique") {
			http.Error(w, "Email already exists", http.StatusConflict)
			return
		}
		http.Error(w, "Server error", http.StatusInternalServerError)
		return
	}
	setSessionCookie(w, user.ID)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(user); err != nil {
		log.Printf("Failed to encode register response: %v", err)
	}
}

func handleLogin(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	var user User
	var hash string
	err := db.QueryRow(`
		SELECT id, email, password_hash, first_name, last_name, bankroll_cents, blackjack_wins, blackjack_losses, poker_wins, poker_losses
		FROM users WHERE email = $1
	`, req.Email).Scan(&user.ID, &user.Email, &hash, &user.FirstName, &user.LastName, &user.BankrollCents,
		&user.BlackjackWins, &user.BlackjackLosses, &user.PokerWins, &user.PokerLosses)
	if err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}
	if err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(req.Password)); err != nil {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}
	setSessionCookie(w, user.ID)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(user); err != nil {
		log.Printf("Failed to encode login response: %v", err)
	}
}

func handleLogout(w http.ResponseWriter, r *http.Request) {
	http.SetCookie(w, &http.Cookie{
		Name:     "casino_session",
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	w.WriteHeader(http.StatusOK)
}

func handleMe(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")
	user, err := getUserByID(userID)
	if err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(user); err != nil {
		log.Printf("Failed to encode user response: %v", err)
	}
}

func handleBankroll(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")
	var cents int64
	err := db.QueryRow("SELECT bankroll_cents FROM users WHERE id = $1", userID).Scan(&cents)
	if err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(map[string]int64{"bankroll_cents": cents}); err != nil {
		log.Printf("Failed to encode bankroll response: %v", err)
	}
}

func handleBlackjackStart(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")
	var req BetRequest
	body, _ := io.ReadAll(r.Body)
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if req.Bet <= 0 {
		http.Error(w, "Invalid bet", http.StatusBadRequest)
		return
	}

	// Deduct bet from bankroll
	res, err := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents - $1 WHERE id = $2 AND bankroll_cents >= $1", req.Bet, userID)
	if err != nil {
		http.Error(w, "Server error", http.StatusInternalServerError)
		return
	}
	rows, _ := res.RowsAffected()
	if rows == 0 {
		http.Error(w, "Insufficient funds", http.StatusBadRequest)
		return
	}

	// Proxy to blackjack API
	apiURL := getBlackjackURL() + "/blackjack/start"
	resp, err := http.Post(apiURL, "application/json", strings.NewReader(string(body)))
	if err != nil {
		// Refund on error
		if _, execErr := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents + $1 WHERE id = $2", req.Bet, userID); execErr != nil {
			log.Printf("Failed to refund bet: %v", execErr)
		}
		http.Error(w, "Game API error", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", "application/json")
	if _, err := io.Copy(w, resp.Body); err != nil {
		log.Printf("Failed to copy blackjack start response: %v", err)
	}
}

func handleBlackjackStand(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")

	// Proxy to blackjack API
	apiURL := getBlackjackURL() + "/blackjack/stand"
	resp, err := http.Post(apiURL, "application/json", nil)
	if err != nil {
		http.Error(w, "Game API error", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var state map[string]interface{}
	if err := json.Unmarshal(body, &state); err != nil {
		log.Printf("Failed to unmarshal blackjack stand response: %v", err)
	}

	// Update bankroll based on result
	status, _ := state["status"].(string)
	bet, _ := state["bet"].(float64)
	betInt := int64(bet)

	switch status {
	case "player_win", "dealer_bust":
		if _, err := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents + $1, blackjack_wins = blackjack_wins + 1 WHERE id = $2", betInt*2, userID); err != nil {
			log.Printf("Failed to update blackjack win: %v", err)
		}
	case "push":
		if _, err := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents + $1 WHERE id = $2", betInt, userID); err != nil {
			log.Printf("Failed to update blackjack push: %v", err)
		}
	case "dealer_win", "player_bust":
		if _, err := db.Exec("UPDATE users SET blackjack_losses = blackjack_losses + 1 WHERE id = $1", userID); err != nil {
			log.Printf("Failed to update blackjack loss: %v", err)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	if _, err := w.Write(body); err != nil {
		log.Printf("Failed to write blackjack stand response: %v", err)
	}
}

func proxyBlackjack(path string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		apiURL := getBlackjackURL() + path
		var resp *http.Response
		var err error
		if r.Method == "POST" {
			body, _ := io.ReadAll(r.Body)
			resp, err = http.Post(apiURL, "application/json", strings.NewReader(string(body)))
		} else {
			resp, err = http.Get(apiURL)
		}
		if err != nil {
			http.Error(w, "Game API error", http.StatusServiceUnavailable)
			return
		}
		defer resp.Body.Close()
		w.Header().Set("Content-Type", "application/json")
		if _, err := io.Copy(w, resp.Body); err != nil {
			log.Printf("Failed to copy blackjack proxy response: %v", err)
		}
	}
}

func handlePokerStart(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")

	body, _ := io.ReadAll(r.Body)
	var req map[string]interface{}
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	bet, _ := req["bet"].(float64)
	if bet <= 0 {
		http.Error(w, "Invalid bet", http.StatusBadRequest)
		return
	}
	betInt := int64(bet)

	// Deduct bet
	res, err := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents - $1 WHERE id = $2 AND bankroll_cents >= $1", betInt, userID)
	if err != nil {
		http.Error(w, "Server error", http.StatusInternalServerError)
		return
	}
	rows, _ := res.RowsAffected()
	if rows == 0 {
		http.Error(w, "Insufficient funds", http.StatusBadRequest)
		return
	}

	// Get user bankroll for poker API
	var bankroll int64
	if err := db.QueryRow("SELECT bankroll_cents FROM users WHERE id = $1", userID).Scan(&bankroll); err != nil {
		log.Printf("Failed to get bankroll for poker: %v", err)
	}

	// Build poker start request
	pokerReq := map[string]interface{}{
		"player_bankroll": bankroll / 100,
		"cpu_bankroll":    100,
		"bet":             int(bet) / 100,
	}
	reqBody, _ := json.Marshal(pokerReq)

	apiURL := getPokerURL() + "/texas/single/start"
	resp, err := http.Post(apiURL, "application/json", strings.NewReader(string(reqBody)))
	if err != nil {
		if _, execErr := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents + $1 WHERE id = $2", betInt, userID); execErr != nil {
			log.Printf("Failed to refund poker bet: %v", execErr)
		}
		http.Error(w, "Game API error", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", "application/json")
	if _, err := io.Copy(w, resp.Body); err != nil {
		log.Printf("Failed to copy poker start response: %v", err)
	}
}

func handlePokerShowdown(w http.ResponseWriter, r *http.Request) {
	userID := r.Header.Get("X-User-ID")

	apiURL := getPokerURL() + "/texas/showdown"
	resp, err := http.Post(apiURL, "application/json", nil)
	if err != nil {
		http.Error(w, "Game API error", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var state map[string]interface{}
	if err := json.Unmarshal(body, &state); err != nil {
		log.Printf("Failed to unmarshal poker showdown response: %v", err)
	}

	// Check winner
	winners, _ := state["winners"].([]interface{})
	pot, _ := state["pot"].(float64)
	potCents := int64(pot * 100)

	playerWon := false
	for _, w := range winners {
		if w == "player" {
			playerWon = true
			break
		}
	}

	if playerWon {
		if _, err := db.Exec("UPDATE users SET bankroll_cents = bankroll_cents + $1, poker_wins = poker_wins + 1 WHERE id = $2", potCents, userID); err != nil {
			log.Printf("Failed to update poker win: %v", err)
		}
	} else {
		if _, err := db.Exec("UPDATE users SET poker_losses = poker_losses + 1 WHERE id = $1", userID); err != nil {
			log.Printf("Failed to update poker loss: %v", err)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	if _, err := w.Write(body); err != nil {
		log.Printf("Failed to write poker showdown response: %v", err)
	}
}

func proxyPoker(path string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		apiURL := getPokerURL() + path
		var resp *http.Response
		var err error
		if r.Method == "POST" {
			body, _ := io.ReadAll(r.Body)
			resp, err = http.Post(apiURL, "application/json", strings.NewReader(string(body)))
		} else {
			resp, err = http.Get(apiURL)
		}
		if err != nil {
			http.Error(w, "Game API error", http.StatusServiceUnavailable)
			return
		}
		defer resp.Body.Close()
		w.Header().Set("Content-Type", "application/json")
		if _, err := io.Copy(w, resp.Body); err != nil {
			log.Printf("Failed to copy poker proxy response: %v", err)
		}
	}
}

func setSessionCookie(w http.ResponseWriter, userID string) {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": userID,
		"exp":     time.Now().Add(24 * time.Hour).Unix(),
	})
	tokenStr, _ := token.SignedString(jwtSecret)
	http.SetCookie(w, &http.Cookie{
		Name:     "casino_session",
		Value:    tokenStr,
		Path:     "/",
		MaxAge:   86400,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
}

func getUserByID(id string) (*User, error) {
	var user User
	err := db.QueryRow(`
		SELECT id, email, first_name, last_name, bankroll_cents, blackjack_wins, blackjack_losses, poker_wins, poker_losses
		FROM users WHERE id = $1
	`, id).Scan(&user.ID, &user.Email, &user.FirstName, &user.LastName, &user.BankrollCents,
		&user.BlackjackWins, &user.BlackjackLosses, &user.PokerWins, &user.PokerLosses)
	return &user, err
}

func getBlackjackURL() string {
	url := os.Getenv("BLACKJACK_API_URL")
	if url == "" {
		return "http://blackjack-api:8000"
	}
	return url
}

func getPokerURL() string {
	url := os.Getenv("POKER_API_URL")
	if url == "" {
		return "http://poker-api:8001"
	}
	return url
}

// Page handlers for HTML templates

type PageData struct {
	Error     string
	FirstName string
	Bankroll  string
}

func handleIndexPage(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/login", http.StatusFound)
}

func handleLoginPage(w http.ResponseWriter, r *http.Request) {
	// Check if already logged in
	if user := getLoggedInUser(r); user != nil {
		http.Redirect(w, r, "/game", http.StatusFound)
		return
	}
	if err := templates.ExecuteTemplate(w, "login.html", PageData{}); err != nil {
		log.Printf("Failed to render login page: %v", err)
	}
}

func handleLoginForm(w http.ResponseWriter, r *http.Request) {
	email := r.FormValue("email")
	password := r.FormValue("password")

	var user User
	var hash string
	err := db.QueryRow(`
		SELECT id, email, password_hash, first_name, last_name, bankroll_cents, blackjack_wins, blackjack_losses, poker_wins, poker_losses
		FROM users WHERE email = $1
	`, email).Scan(&user.ID, &user.Email, &hash, &user.FirstName, &user.LastName, &user.BankrollCents,
		&user.BlackjackWins, &user.BlackjackLosses, &user.PokerWins, &user.PokerLosses)
	if err != nil {
		if tmplErr := templates.ExecuteTemplate(w, "login.html", PageData{Error: "Invalid email or password"}); tmplErr != nil {
			log.Printf("Failed to render login page: %v", tmplErr)
		}
		return
	}
	if err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)); err != nil {
		if tmplErr := templates.ExecuteTemplate(w, "login.html", PageData{Error: "Invalid email or password"}); tmplErr != nil {
			log.Printf("Failed to render login page: %v", tmplErr)
		}
		return
	}
	setSessionCookie(w, user.ID)
	http.Redirect(w, r, "/game", http.StatusFound)
}

func handleRegisterPage(w http.ResponseWriter, r *http.Request) {
	// Check if already logged in
	if user := getLoggedInUser(r); user != nil {
		http.Redirect(w, r, "/game", http.StatusFound)
		return
	}
	if err := templates.ExecuteTemplate(w, "register.html", PageData{}); err != nil {
		log.Printf("Failed to render register page: %v", err)
	}
}

func handleRegisterForm(w http.ResponseWriter, r *http.Request) {
	firstName := r.FormValue("first_name")
	lastName := r.FormValue("last_name")
	email := r.FormValue("email")
	password := r.FormValue("password")

	if email == "" || password == "" || firstName == "" || lastName == "" {
		if tmplErr := templates.ExecuteTemplate(w, "register.html", PageData{Error: "All fields are required"}); tmplErr != nil {
			log.Printf("Failed to render register page: %v", tmplErr)
		}
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		if tmplErr := templates.ExecuteTemplate(w, "register.html", PageData{Error: "Server error"}); tmplErr != nil {
			log.Printf("Failed to render register page: %v", tmplErr)
		}
		return
	}

	var user User
	err = db.QueryRow(`
		INSERT INTO users (email, password_hash, first_name, last_name)
		VALUES ($1, $2, $3, $4)
		RETURNING id, email, first_name, last_name, bankroll_cents, blackjack_wins, blackjack_losses, poker_wins, poker_losses
	`, email, string(hash), firstName, lastName).Scan(
		&user.ID, &user.Email, &user.FirstName, &user.LastName, &user.BankrollCents,
		&user.BlackjackWins, &user.BlackjackLosses, &user.PokerWins, &user.PokerLosses,
	)
	if err != nil {
		if strings.Contains(err.Error(), "unique") {
			if tmplErr := templates.ExecuteTemplate(w, "register.html", PageData{Error: "Email already exists"}); tmplErr != nil {
				log.Printf("Failed to render register page: %v", tmplErr)
			}
			return
		}
		if tmplErr := templates.ExecuteTemplate(w, "register.html", PageData{Error: "Server error"}); tmplErr != nil {
			log.Printf("Failed to render register page: %v", tmplErr)
		}
		return
	}
	setSessionCookie(w, user.ID)
	http.Redirect(w, r, "/game", http.StatusFound)
}

func handleGamePage(w http.ResponseWriter, r *http.Request) {
	user := getLoggedInUser(r)
	if user == nil {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	bankroll := float64(user.BankrollCents) / 100
	if err := templates.ExecuteTemplate(w, "game.html", PageData{
		FirstName: user.FirstName,
		Bankroll:  formatMoney(bankroll),
	}); err != nil {
		log.Printf("Failed to render game page: %v", err)
	}
}

func handleLogoutPage(w http.ResponseWriter, r *http.Request) {
	http.SetCookie(w, &http.Cookie{
		Name:     "casino_session",
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	http.Redirect(w, r, "/login", http.StatusFound)
}

func getLoggedInUser(r *http.Request) *User {
	cookie, err := r.Cookie("casino_session")
	if err != nil {
		return nil
	}
	token, err := jwt.Parse(cookie.Value, func(t *jwt.Token) (interface{}, error) {
		return jwtSecret, nil
	})
	if err != nil || !token.Valid {
		return nil
	}
	claims := token.Claims.(jwt.MapClaims)
	userID := claims["user_id"].(string)
	user, err := getUserByID(userID)
	if err != nil {
		return nil
	}
	return user
}

func formatMoney(amount float64) string {
	if amount == float64(int64(amount)) {
		return fmt.Sprintf("%.0f", amount)
	}
	return fmt.Sprintf("%.2f", amount)
}
