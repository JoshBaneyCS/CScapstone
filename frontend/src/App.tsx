// =============================================================================
// APP.TSX - MAIN APPLICATION COMPONENT
// =============================================================================
// This is the root component of our React application. It:
//   1. Defines all application routes
//   2. Manages global authentication state
//   3. Provides the overall page layout
//   4. Handles protected route logic
//
// Route Structure:
//   /           → Redirects to /games if logged in, /login if not
//   /register   → Registration page (public)
//   /login      → Login page (public)
//   /games      → Games dashboard (protected - requires authentication)
//
// Authentication Flow:
//   - On app load, we check if user is authenticated via GET /api/auth/me
//   - If authenticated, user data is stored in state
//   - Protected routes redirect to /login if not authenticated
//   - Login/Register pages redirect to /games if already authenticated
// =============================================================================

import { useState, useEffect, createContext, useContext } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

// Import page components
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import GamesPage from './pages/GamesPage';
import GamePlayPage from './pages/GamePlayPage';

// Import styles
import './styles/App.css';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================
// TypeScript interfaces define the shape of our data.
// This provides autocomplete and catches type errors at compile time.

/**
 * User represents the authenticated user's profile data.
 * This matches the UserResponse from the backend API.
 */
export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  dob: string;
  createdAt: string;
}

/**
 * AuthContextType defines what the authentication context provides.
 * Components can access these values using the useAuth() hook.
 */
interface AuthContextType {
  // The current user (null if not logged in)
  user: User | null;
  
  // The user's bankroll in cents (null if not logged in)
  bankrollCents: number | null;
  
  // Whether we're currently checking authentication status
  isLoading: boolean;
  
  // Whether the user is authenticated
  isAuthenticated: boolean;
  
  // Function to update user state after login/register
  setAuthData: (user: User | null, bankrollCents: number | null) => void;
  
  // Function to clear auth state (logout)
  clearAuth: () => void;
  
  // Function to refresh user data from the server
  refreshAuth: () => Promise<void>;
}

// =============================================================================
// AUTHENTICATION CONTEXT
// =============================================================================
// React Context allows us to pass authentication state through the component
// tree without manually passing props at every level ("prop drilling").
//
// How it works:
//   1. Create a context with createContext()
//   2. Wrap the app in a Provider that supplies the value
//   3. Any child component can access the value with useContext()
//
// We use a custom hook (useAuth) to make accessing the context easier.

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * useAuth hook - Access authentication state from any component.
 * 
 * Usage:
 *   const { user, isAuthenticated, setAuthData } = useAuth();
 * 
 * Throws an error if used outside of AuthProvider (catches bugs early).
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

// =============================================================================
// PROTECTED ROUTE COMPONENT
// =============================================================================
// A wrapper component that redirects to login if the user is not authenticated.
// Used to protect routes that require authentication.

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute - Wraps routes that require authentication.
 * 
 * Behavior:
 *   - If loading, shows a loading spinner
 *   - If not authenticated, redirects to /login
 *   - If authenticated, renders the children
 * 
 * Usage:
 *   <Route path="/games" element={
 *     <ProtectedRoute>
 *       <GamesPage />
 *     </ProtectedRoute>
 *   } />
 */
function ProtectedRoute({ children }: ProtectedRouteProps): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  // We save the attempted URL so we can redirect back after login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
}

// =============================================================================
// PUBLIC ROUTE COMPONENT
// =============================================================================
// A wrapper for routes that should redirect away if already logged in.
// Used for login and register pages.

interface PublicRouteProps {
  children: React.ReactNode;
}

/**
 * PublicRoute - Wraps routes that should redirect if already authenticated.
 * 
 * Behavior:
 *   - If loading, shows a loading spinner
 *   - If authenticated, redirects to /games
 *   - If not authenticated, renders the children
 */
function PublicRoute({ children }: PublicRouteProps): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If already authenticated, redirect to games
  if (isAuthenticated) {
    return <Navigate to="/games" replace />;
  }

  // User is not authenticated, render the public content
  return <>{children}</>;
}

// =============================================================================
// APP COMPONENT
// =============================================================================
// The main application component that provides context and defines routes.

function App(): JSX.Element {
  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  // State for the authenticated user
  const [user, setUser] = useState<User | null>(null);
  
  // State for the user's bankroll (in cents)
  const [bankrollCents, setBankrollCents] = useState<number | null>(null);
  
  // State for loading status (true while checking auth on initial load)
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // ---------------------------------------------------------------------------
  // DERIVED STATE
  // ---------------------------------------------------------------------------
  // User is authenticated if we have user data
  const isAuthenticated = user !== null;

  // ---------------------------------------------------------------------------
  // AUTH FUNCTIONS
  // ---------------------------------------------------------------------------
  
  /**
   * setAuthData - Update the authentication state after login/register.
   * Called by LoginPage and RegisterPage on successful authentication.
   */
  const setAuthData = (newUser: User | null, newBankroll: number | null): void => {
    setUser(newUser);
    setBankrollCents(newBankroll);
  };

  /**
   * clearAuth - Clear the authentication state (for logout).
   * Called by the logout functionality.
   */
  const clearAuth = (): void => {
    setUser(null);
    setBankrollCents(null);
  };

  /**
   * refreshAuth - Fetch current user data from the server.
   * Called on initial load and can be called to refresh data.
   */
  const refreshAuth = async (): Promise<void> => {
    try {
      // Call the /api/auth/me endpoint to check if we're authenticated
      // The cookie is sent automatically by the browser
      const response = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'include', // Important: Include cookies in the request
      });

      if (response.ok) {
        // User is authenticated - parse and store the data
        const data = await response.json();
        setUser(data.user);
        setBankrollCents(data.bankrollCents);
      } else {
        // Not authenticated or error - clear any existing state
        setUser(null);
        setBankrollCents(null);
      }
    } catch (error) {
      // Network error or server down - clear state
      console.error('Failed to check authentication:', error);
      setUser(null);
      setBankrollCents(null);
    }
  };

  // ---------------------------------------------------------------------------
  // EFFECTS
  // ---------------------------------------------------------------------------
  
  /**
   * Check authentication status on initial app load.
   * This runs once when the app mounts.
   */
  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      await refreshAuth();
      setIsLoading(false);
    };

    checkAuth();
  }, []); // Empty dependency array = run once on mount

  // ---------------------------------------------------------------------------
  // CONTEXT VALUE
  // ---------------------------------------------------------------------------
  // The value provided to all children via AuthContext
  const authContextValue: AuthContextType = {
    user,
    bankrollCents,
    isLoading,
    isAuthenticated,
    setAuthData,
    clearAuth,
    refreshAuth,
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------
  return (
    // Provide authentication context to all children
    <AuthContext.Provider value={authContextValue}>
      <div className="app">
        {/* 
        -------------------------------------------------------------------------
        ROUTES
        -------------------------------------------------------------------------
        Define all application routes here.
        
        Route matching:
          - Routes are matched in order
          - Use exact path matching (no wildcards by default in v6)
          - Navigate component handles redirects
        */}
        <Routes>
          {/* 
          Home route - Redirect based on auth status 
          If logged in, go to games. If not, go to login.
          */}
          <Route 
            path="/" 
            element={
              isLoading ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <p>Loading...</p>
                </div>
              ) : isAuthenticated ? (
                <Navigate to="/games" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            } 
          />
          
          {/* 
          Login route - Public (redirects to /games if already logged in) 
          */}
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } 
          />
          
          {/* 
          Register route - Public (redirects to /games if already logged in) 
          */}
          <Route 
            path="/register" 
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            } 
          />
          
          {/*
          Games route - Protected (redirects to /login if not authenticated)
          */}
          <Route
            path="/games"
            element={
              <ProtectedRoute>
                <GamesPage />
              </ProtectedRoute>
            }
          />

          {/*
          Game Play route - Protected (play a specific game)
          */}
          <Route
            path="/games/:gameId"
            element={
              <ProtectedRoute>
                <GamePlayPage />
              </ProtectedRoute>
            }
          />

          {/*
          Catch-all route - Redirect unknown paths to home 
          This handles 404s by redirecting to the appropriate page.
          You could also render a custom 404 page here.
          */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </AuthContext.Provider>
  );
}

export default App;