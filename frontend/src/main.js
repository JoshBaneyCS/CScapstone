/**
 * Capstone Casino — Minimal SPA Frontend
 *
 * Pages: Login → Register → Lobby → Game (WASM canvas)
 * Auth: JWT via httpOnly cookie (set by Go backend)
 */

const app = document.getElementById('app');

// --------------- API helpers ---------------
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // send JWT cookie
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`/api${path}`, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

// --------------- Router ---------------
function navigate(page, data) {
  switch (page) {
    case 'login': renderLogin(); break;
    case 'register': renderRegister(); break;
    case 'lobby': renderLobby(); break;
    case 'game': renderGame(data); break;
    default: renderLogin();
  }
}

// --------------- Login Page ---------------
function renderLogin() {
  app.innerHTML = `
    <div class="auth-container">
      <h1>Capstone Casino</h1>
      <h2>Welcome back</h2>
      <form class="auth-form" id="login-form">
        <input type="email" name="email" placeholder="Email" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit" class="btn btn-primary">Log In</button>
        <div class="error-msg" id="login-error"></div>
      </form>
      <p class="link-text">
        Don't have an account? <a id="go-register">Sign up</a>
      </p>
    </div>
  `;
  document.getElementById('go-register').onclick = () => navigate('register');
  document.getElementById('login-form').onsubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';
    try {
      await api('POST', '/auth/login', {
        email: form.email.value,
        password: form.password.value,
      });
      navigate('lobby');
    } catch (err) {
      errEl.textContent = err.message;
    }
  };
}

// --------------- Register Page ---------------
function renderRegister() {
  app.innerHTML = `
    <div class="auth-container">
      <h1>Capstone Casino</h1>
      <h2>Create an account</h2>
      <form class="auth-form" id="register-form">
        <input type="text" name="first_name" placeholder="First Name" required />
        <input type="text" name="last_name" placeholder="Last Name" required />
        <input type="email" name="email" placeholder="Email" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit" class="btn btn-primary">Sign Up</button>
        <div class="error-msg" id="register-error"></div>
      </form>
      <p class="link-text">
        Already have an account? <a id="go-login">Log in</a>
      </p>
    </div>
  `;
  document.getElementById('go-login').onclick = () => navigate('login');
  document.getElementById('register-form').onsubmit = async (e) => {
    e.preventDefault();
    const form = e.target;
    const errEl = document.getElementById('register-error');
    errEl.textContent = '';
    try {
      await api('POST', '/auth/register', {
        first_name: form.first_name.value,
        last_name: form.last_name.value,
        email: form.email.value,
        password: form.password.value,
      });
      navigate('lobby');
    } catch (err) {
      errEl.textContent = err.message;
    }
  };
}

// --------------- Lobby Page ---------------
async function renderLobby() {
  app.innerHTML = `
    <div class="lobby">
      <h1 class="lobby-title">Capstone Casino</h1>
      <div class="lobby-user-info">
        <div id="user-greeting"></div>
        <div><span class="bankroll" id="bankroll">Loading...</span></div>
      </div>
      <div class="lobby-buttons">
        <button class="lobby-btn" id="play-poker">Poker</button>
        <button class="lobby-btn" id="play-blackjack">Blackjack</button>
        <button class="lobby-btn" id="play-credits">Credits</button>
        <button class="lobby-btn logout" id="logout-btn">Logout</button>
      </div>
    </div>
  `;

  // Register click handlers immediately (before async calls)
  document.getElementById('play-blackjack').onclick = () => navigate('game', 'blackjack');
  document.getElementById('play-poker').onclick = () => navigate('game', 'poker');
  document.getElementById('play-credits').onclick = () => { /* TODO: credits page */ };
  document.getElementById('logout-btn').onclick = async () => {
    try { await api('POST', '/auth/logout'); } catch { /* ignore */ }
    navigate('login');
  };

  // Load user info and bankroll
  try {
    const user = await api('GET', '/auth/me');
    const greetingEl = document.getElementById('user-greeting');
    const bankrollEl = document.getElementById('bankroll');
    // Guard: user navigated away from lobby during the fetch
    if (!greetingEl || !bankrollEl) return;
    greetingEl.textContent = `Welcome, ${user.first_name}`;
    bankrollEl.textContent = `$${(user.bankroll_cents / 100).toFixed(2)}`;
  } catch {
    // Only redirect to login if we're still on the lobby page
    if (document.getElementById('user-greeting')) {
      navigate('login');
    }
  }
}

// --------------- Game Page (WASM) ---------------
function renderGame(gameType) {
  app.innerHTML = `
    <div class="game-page">
      <div class="game-header">
        <button class="btn btn-secondary" id="back-lobby">Back to Lobby</button>
        <span>${gameType === 'blackjack' ? 'Blackjack' : 'Texas Hold\'em'}</span>
        <span id="game-bankroll"></span>
      </div>
      <div class="game-canvas-container" id="game-container">
        <div class="loading">
          <div class="spinner"></div>
          <p>Loading game...</p>
        </div>
      </div>
    </div>
  `;

  document.getElementById('back-lobby').onclick = () => navigate('lobby');

  // Load the WASM game in an iframe from /game/ static files
  const container = document.getElementById('game-container');
  const iframe = document.createElement('iframe');
  iframe.src = '/game/index.html';
  iframe.style.width = '100%';
  iframe.style.height = '100%';
  iframe.style.border = 'none';
  iframe.onload = () => {
    // Remove loading spinner
    const loading = container.querySelector('.loading');
    if (loading) loading.remove();
  };
  iframe.onerror = () => {
    container.innerHTML = `
      <div class="loading">
        <p>Failed to load game. Make sure the WASM build is available.</p>
        <button class="btn btn-primary" onclick="location.reload()">Retry</button>
      </div>
    `;
  };
  container.appendChild(iframe);
}

// --------------- Init ---------------
// Prevent recursive loading when Vite serves this app inside the game iframe
if (window.self !== window.top) {
  app.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading game...</p></div>';
} else {
  // Try to check auth status, go to lobby if logged in
  (async () => {
    try {
      await api('GET', '/auth/me');
      navigate('lobby');
    } catch {
      navigate('login');
    }
  })();
}
