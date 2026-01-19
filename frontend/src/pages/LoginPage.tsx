// =============================================================================
// LOGINPAGE.TSX - USER LOGIN PAGE
// =============================================================================
// This component provides the login form for existing users.
// It handles:
//   - Form input and validation
//   - Submitting credentials to the API
//   - Error display
//   - Redirect after successful login
//
// The login endpoint accepts either email OR username along with password.
// After successful login, the server sets an HttpOnly cookie with the JWT.
// =============================================================================

import { useState, FormEvent, ChangeEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * LoginFormData represents the form input values.
 * Users can log in with either email or username.
 */
interface LoginFormData {
  emailOrUsername: string;  // Can be either email or username
  password: string;
}

/**
 * FormErrors tracks validation errors for each field.
 * Empty string means no error.
 */
interface FormErrors {
  emailOrUsername: string;
  password: string;
  general: string;  // For server-side errors
}

// =============================================================================
// COMPONENT
// =============================================================================

/**
 * LoginPage - The login form component.
 * 
 * Features:
 *   - Email or username input
 *   - Password input with show/hide toggle
 *   - Client-side validation
 *   - Loading state during submission
 *   - Error handling and display
 *   - Link to registration page
 */
function LoginPage(): JSX.Element {
  // ---------------------------------------------------------------------------
  // HOOKS
  // ---------------------------------------------------------------------------
  
  // Navigation hook for redirecting after login
  const navigate = useNavigate();
  
  // Location hook to get the "from" state (where user was trying to go)
  const location = useLocation();
  
  // Auth context for updating authentication state
  const { setAuthData } = useAuth();

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  
  // Form input values
  const [formData, setFormData] = useState<LoginFormData>({
    emailOrUsername: '',
    password: '',
  });

  // Validation errors
  const [errors, setErrors] = useState<FormErrors>({
    emailOrUsername: '',
    password: '',
    general: '',
  });

  // Loading state (true while submitting)
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Password visibility toggle
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // ---------------------------------------------------------------------------
  // EVENT HANDLERS
  // ---------------------------------------------------------------------------

  /**
   * Handle input changes.
   * Updates form data and clears any existing error for that field.
   */
  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for this field when user starts typing
    setErrors(prev => ({
      ...prev,
      [name]: '',
      general: '', // Also clear general errors
    }));
  };

  /**
   * Validate form inputs.
   * Returns true if valid, false if there are errors.
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {
      emailOrUsername: '',
      password: '',
      general: '',
    };

    // Email/Username validation
    if (!formData.emailOrUsername.trim()) {
      newErrors.emailOrUsername = 'Email or username is required';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);

    // Return true if no errors
    return !newErrors.emailOrUsername && !newErrors.password;
  };

  /**
   * Handle form submission.
   * Validates inputs, calls the API, and handles the response.
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    // Prevent default form submission (page reload)
    e.preventDefault();

    // Validate form
    if (!validateForm()) {
      return;
    }

    // Start loading
    setIsLoading(true);
    setErrors(prev => ({ ...prev, general: '' }));

    try {
      // Determine if input is email or username
      // Simple check: if it contains @, treat as email
      const isEmail = formData.emailOrUsername.includes('@');
      
      // Build request body
      const requestBody = isEmail
        ? { email: formData.emailOrUsername, password: formData.password }
        : { username: formData.emailOrUsername, password: formData.password };

      // Call the login API
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important: Include cookies
        body: JSON.stringify(requestBody),
      });

      // Parse response
      const data = await response.json();

      if (response.ok) {
        // Login successful!
        // Update auth context with user data
        setAuthData(data.user, data.bankrollCents);

        // Redirect to the page they were trying to access, or /games
        const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/games';
        navigate(from, { replace: true });
      } else {
        // Login failed - show error message
        setErrors(prev => ({
          ...prev,
          general: data.error || 'Invalid email/username or password',
        }));
      }
    } catch (error) {
      // Network error or server down
      console.error('Login error:', error);
      setErrors(prev => ({
        ...prev,
        general: 'Unable to connect to server. Please try again.',
      }));
    } finally {
      // Stop loading
      setIsLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------------------------
  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Header */}
        <div className="auth-header">
          <h1>🎰 Casino Capstone</h1>
          <h2>Welcome Back!</h2>
          <p>Sign in to continue to your account</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {/* General Error Message */}
          {errors.general && (
            <div className="error-banner" role="alert">
              <span className="error-icon">⚠️</span>
              {errors.general}
            </div>
          )}

          {/* Email/Username Field */}
          <div className="form-group">
            <label htmlFor="emailOrUsername">Email or Username</label>
            <input
              type="text"
              id="emailOrUsername"
              name="emailOrUsername"
              value={formData.emailOrUsername}
              onChange={handleChange}
              placeholder="Enter your email or username"
              className={errors.emailOrUsername ? 'input-error' : ''}
              disabled={isLoading}
              autoComplete="username"
              autoFocus
            />
            {errors.emailOrUsername && (
              <span className="field-error">{errors.emailOrUsername}</span>
            )}
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                className={errors.password ? 'input-error' : ''}
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
            {errors.password && (
              <span className="field-error">{errors.password}</span>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="btn-spinner"></span>
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer Links */}
        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">
              Create one here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;ß