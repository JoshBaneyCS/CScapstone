// =============================================================================
// SETUP-TESTS.TS - TEST CONFIGURATION FOR REACT TESTING
// =============================================================================
// This file sets up the testing environment for React components.
// It runs before each test file and configures:
//   - Jest DOM matchers (toBeInTheDocument, toHaveClass, etc.)
//   - Mock implementations for browser APIs
//   - Global test utilities
//
// This file is referenced in vite.config.ts or vitest.config.ts
// as the setupFiles option.
//
// Running tests:
//   npm test              # Run all tests
//   npm test -- --watch   # Watch mode
//   npm run test:coverage # With coverage report
// =============================================================================

import '@testing-library/jest-dom';
import { vi } from 'vitest';

// =============================================================================
// MOCK: FETCH API
// =============================================================================
// Mock the global fetch function for testing API calls.
// Individual tests can override this with specific mock implementations.

global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    status: 200,
    statusText: 'OK',
  } as Response)
);

// =============================================================================
// MOCK: WINDOW.MATCHMEDIA
// =============================================================================
// Some components use media queries. Mock matchMedia for consistent tests.

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// =============================================================================
// MOCK: LOCALSTORAGE / SESSIONSTORAGE
// =============================================================================
// Mock browser storage APIs.

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string): string | null => store[key] || null,
    setItem: (key: string, value: string): void => {
      store[key] = value;
    },
    removeItem: (key: string): void => {
      delete store[key];
    },
    clear: (): void => {
      store = {};
    },
    get length(): number {
      return Object.keys(store).length;
    },
    key: (index: number): string | null => {
      const keys = Object.keys(store);
      return keys[index] || null;
    },
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(window, 'sessionStorage', { value: localStorageMock });

// =============================================================================
// MOCK: INTERSECTION OBSERVER
// =============================================================================
// Mock IntersectionObserver for components that use lazy loading.

class MockIntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];
  
  constructor() {
    // Constructor
  }
  
  disconnect(): void {
    // Disconnect
  }
  
  observe(): void {
    // Observe
  }
  
  unobserve(): void {
    // Unobserve
  }
  
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});

// =============================================================================
// MOCK: RESIZE OBSERVER
// =============================================================================
// Mock ResizeObserver for components that respond to size changes.

class MockResizeObserver {
  constructor() {
    // Constructor
  }
  
  disconnect(): void {
    // Disconnect
  }
  
  observe(): void {
    // Observe
  }
  
  unobserve(): void {
    // Unobserve
  }
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: MockResizeObserver,
});

// =============================================================================
// MOCK: SCROLL FUNCTIONS
// =============================================================================
// Mock scroll functions that aren't implemented in JSDOM.

window.scrollTo = vi.fn();
Element.prototype.scrollIntoView = vi.fn();

// =============================================================================
// CLEANUP AFTER EACH TEST
// =============================================================================
// Reset mocks and clear storage after each test.

afterEach(() => {
  // Clear all mocks
  vi.clearAllMocks();

  // Clear storage
  localStorage.clear();
  sessionStorage.clear();

  // Reset fetch mock
  (global.fetch as ReturnType<typeof vi.fn>).mockClear();
});

// =============================================================================
// CONSOLE ERROR SUPPRESSION (Optional)
// =============================================================================
// Suppress specific console errors during tests.
// Useful for expected errors that would clutter test output.

const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Suppress React act() warnings if they become noisy
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An update to')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// =============================================================================
// TEST UTILITIES
// =============================================================================
// Export common test utilities for use in test files.

/**
 * Helper to wait for async updates in tests.
 * Use when you need to wait for state updates or effects.
 */
export const waitForAsync = (): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Mock API response helper.
 * Creates a mock fetch response for testing.
 */
export const mockApiResponse = <T>(data: T, status = 200): Response =>
  ({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
    redirected: false,
    type: 'basic',
    url: '',
    clone: function() { return this; },
  } as Response);

/**
 * Mock authenticated user for testing protected components.
 */
export const mockUser = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  email: 'test@example.com',
  username: 'testuser',
  firstName: 'Test',
  lastName: 'User',
  dob: '1990-01-15',
  createdAt: '2024-01-01T00:00:00Z',
};

/**
 * Mock bankroll in cents.
 */
export const mockBankrollCents = 250000; // $2,500.00