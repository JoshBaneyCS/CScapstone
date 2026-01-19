// =============================================================================
// REGISTERPAGE.TSX - USER REGISTRATION PAGE
// =============================================================================
// This component provides the registration form for new users.
// It handles:
//   - Form input and validation for all required fields
//   - Date of birth input for 21+ age verification
//   - Submitting registration data to the API
//   - Error display (including age restriction errors)
//   - Auto-login and redirect after successful registration
//
// Required fields:
//   - Email (must be valid format, unique)
//   - Username (3-50 chars, alphanumeric + underscore, unique)
//   - Password (8-72 chars)
//   - First Name
//   - Last Name
//   - Date of Birth (must be 21+ years old)
//
// After successful registration:
//   - User account is created with $2,500 starting bankroll
//   - User is automatically logged in (cookie is set)
//   - User is redirected to the games page
// =============================================================================

import { useState, FormEvent, ChangeEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * RegisterFormData represents all the form input values.
 * Matches the backend's RegisterRequest structure.
 */
interface RegisterFormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;  // Client-side only, not sent to server
  firstName: string;
  lastName: string;
  dob: string;  // Format: YYYY-MM-DD
}

/**
 * FormErrors tracks validation errors for each field.
 * Empty string means no error.
 */
interface FormErrors {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  dob: string;
  general: string;  // For server-side errors
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Calculate if a date of birth makes someone at least 21 years old.
 * Uses proper date comparison (not days/365) to handle edge cases.
 * 
 * @param dobString - Date of birth in YYYY-MM-DD format
 * @returns true if the person is 21 or older
 */
function isAtLeast21(dobString: string): boolean {
  const dob = new Date(dobString);
  const today = new Date();
  
  // Calculate the date 21 years ago
  const minimumDate = new Date(
    today.getFullYear() - 21,
    today.getMonth(),
    today.getDate()
  );
  
  // Person must be born ON or BEFORE this date to be 21+
  return dob <= minimumDate;
}

/**
 * Calculate the maximum allowed date of birth (21 years ago from today).
 * Used to set the max attribute on the date input for better UX.
 * 
 * @returns Date string in YYYY-MM-DD format
 */
function getMaxDOB(): string {
  const today = new Date();
  const maxDate = new Date(
    today.getFullYear() - 21,
    today.getMonth(),
    today.getDate()
  );
  return maxDate.toISOString().split('T')[0];
}

/**
 * Validate email format using a simple regex.
 * This is a basic check - the server does the real validation.
 * 
 * @param email - Email string to validate
 * @returns true if email format is valid
 */
function isValidEmail(email: string): boolean {
  // Basic email regex - checks for something@something.something
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate username format.
 * Must be 3-50 characters, alphanumeric and underscores only.
 * 
 * @param username - Username string to validate
 * @returns true if username format is valid
 */
function isValidUsername(username: string): boolean {
  const usernameRegex = /^[a-zA-Z0-9_]{3,50}$/;
  return usernameRegex.test(username);
}

// =============================================================================
// COMPONENT
// =============================================================================

/**
 * RegisterPage - The registration form component.
 * 
 * Features:
 *   - All required fields with validation
 *   - Password confirmation
 *   - Date picker for DOB with age restriction hint
 *   - Client-side validation before submission
 *   - Server error handling (duplicate email/username, age restriction)
 *   - Loading state during submission
 *   - Link to login page
 */
function RegisterPage(): JSX.Element {
  // ---------------------------------------------------------------------------
  // HOOKS
  // ---------------------------------------------------------------------------
  
  // Navigation hook for redirecting after registration
  const navigate = useNavigate();
  
  // Auth context for updating authentication state
  const { setAuthData } = useAuth();

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------
  
  // Form input values
  const [formData, setFormData] = useState<RegisterFormData>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    dob: '',
  });

  // Validation errors
  const [errors, setErrors] = useState<FormErrors>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    dob: '',
    general: '',
  });

  // Loading state (true while submitting)
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Password visibility toggles
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);

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
   * Validate all form inputs.
   * Returns true if valid, false if there are errors.
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      dob: '',
      general: '',
    };

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (formData.username.length > 50) {
      newErrors.username = 'Username must be 50 characters or less';
    } else if (!isValidUsername(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (formData.password.length > 72) {
      newErrors.password = 'Password must be 72 characters or less';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // First name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    } else if (formData.firstName.length > 100) {
      newErrors.firstName = 'First name must be 100 characters or less';
    }

    // Last name validation
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    } else if (formData.lastName.length > 100) {
      newErrors.lastName = 'Last name must be 100 characters or less';
    }

    // Date of birth validation
    if (!formData.dob) {
      newErrors.dob = 'Date of birth is required';
    } else if (!isAtLeast21(formData.dob)) {
      newErrors.dob = 'You must be at least 21 years old to register';
    }

    setErrors(newErrors);

    // Return true if no errors (all error strings are empty)
    return Object.values(newErrors).every(error => error === '');
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
      // Build request body (excluding confirmPassword)
      const requestBody = {
        email: formData.email.trim().toLowerCase(),
        username: formData.username.trim().toLowerCase(),
        password: formData.password,
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        dob: formData.dob,
      };

      // Call the register API
      const response = await fetch('/api/auth/register', {
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
        // Registration successful!
        // Update auth context with user data
        setAuthData(data.user, data.bankrollCents);

        // Redirect to games page
        navigate('/games', { replace: true });
      } else {
        // Registration failed - show error message
        // Handle specific error codes
        let errorMessage = data.error || 'Registration failed. Please try again.';
        
        // Map error codes to user-friendly messages
        if (data.code === 'EMAIL_EXISTS') {
          setErrors(prev => ({ ...prev, email: 'This email is already registered' }));
        } else if (data.code === 'USERNAME_EXISTS') {
          setErrors(prev => ({ ...prev, username: 'This username is already taken' }));
        } else if (data.code === 'AGE_REQUIREMENT') {
          setErrors(prev => ({ ...prev, dob: errorMessage }));
        } else {
          setErrors(prev => ({ ...prev, general: errorMessage }));
        }
      }
    } catch (error) {
      // Network error or server down
      console.error('Registration error:', error);
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
      <div className="auth-container auth-container-wide">
        {/* Header */}
        <div className="auth-header">
          <h1>🎰 Casino Capstone</h1>
          <h2>Create Your Account</h2>
          <p>Join now and get $2,500 in free chips to play!</p>
        </div>

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {/* General Error Message */}
          {errors.general && (
            <div className="error-banner" role="alert">
              <span className="error-icon">⚠️</span>
              {errors.general}
            </div>
          )}

          {/* Two-column layout for name fields */}
          <div className="form-row">
            {/* First Name Field */}
            <div className="form-group">
              <label htmlFor="firstName">First Name</label>
              <input
                type="text"
                id="firstName"
                name="firstName"
                value={formData.firstName}
                onChange={handleChange}
                placeholder="John"
                className={errors.firstName ? 'input-error' : ''}
                disabled={isLoading}
                autoComplete="given-name"
                autoFocus
              />
              {errors.firstName && (
                <span className="field-error">{errors.firstName}</span>
              )}
            </div>

            {/* Last Name Field */}
            <div className="form-group">
              <label htmlFor="lastName">Last Name</label>
              <input
                type="text"
                id="lastName"
                name="lastName"
                value={formData.lastName}
                onChange={handleChange}
                placeholder="Doe"
                className={errors.lastName ? 'input-error' : ''}
                disabled={isLoading}
                autoComplete="family-name"
              />
              {errors.lastName && (
                <span className="field-error">{errors.lastName}</span>
              )}
            </div>
          </div>

          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
              className={errors.email ? 'input-error' : ''}
              disabled={isLoading}
              autoComplete="email"
            />
            {errors.email && (
              <span className="field-error">{errors.email}</span>
            )}
          </div>

          {/* Username Field */}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="johndoe123"
              className={errors.username ? 'input-error' : ''}
              disabled={isLoading}
              autoComplete="username"
            />
            <span className="field-hint">
              3-50 characters, letters, numbers, and underscores only
            </span>
            {errors.username && (
              <span className="field-error">{errors.username}</span>
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
                placeholder="At least 8 characters"
                className={errors.password ? 'input-error' : ''}
                disabled={isLoading}
                autoComplete="new-password"
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

          {/* Confirm Password Field */}
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className="password-input-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Re-enter your password"
                className={errors.confirmPassword ? 'input-error' : ''}
                disabled={isLoading}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                tabIndex={-1}
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? '🙈' : '👁️'}
              </button>
            </div>
            {errors.confirmPassword && (
              <span className="field-error">{errors.confirmPassword}</span>
            )}
          </div>

          {/* Date of Birth Field */}
          <div className="form-group">
            <label htmlFor="dob">Date of Birth</label>
            <input
              type="date"
              id="dob"
              name="dob"
              value={formData.dob}
              onChange={handleChange}
              max={getMaxDOB()}  // Prevent selecting dates that would make user under 21
              className={errors.dob ? 'input-error' : ''}
              disabled={isLoading}
              autoComplete="bday"
            />
            <span className="field-hint">
              You must be at least 21 years old to register
            </span>
            {errors.dob && (
              <span className="field-error">{errors.dob}</span>
            )}
          </div>

          {/* Terms Notice */}
          <div className="terms-notice">
            <p>
              By creating an account, you confirm that you are at least 21 years
              old and agree to play responsibly.
            </p>
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
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Footer Links */}
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;