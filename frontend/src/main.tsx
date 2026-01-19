// =============================================================================
// MAIN.TSX - REACT APPLICATION ENTRY POINT
// =============================================================================
// This is where our React application starts. It:
//   1. Finds the #root element in index.html
//   2. Creates a React root for that element
//   3. Renders the App component inside it
//
// This file should stay small - it's just the bootstrap code.
// All application logic goes in App.tsx and other components.
//
// React 18 Rendering:
// -------------------
// React 18 introduced createRoot() which enables:
//   - Concurrent rendering (better performance for large apps)
//   - Automatic batching of state updates
//   - New features like startTransition
//
// StrictMode:
// -----------
// <React.StrictMode> is a development tool that:
//   - Warns about deprecated lifecycle methods
//   - Warns about legacy string refs
//   - Detects unexpected side effects (by double-invoking functions)
//   - Does NOT affect production builds
// =============================================================================

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

// Import the main App component
import App from './App';

// Import global styles
import './styles/index.css';

// =============================================================================
// FIND THE ROOT ELEMENT
// =============================================================================
// Get the #root element from index.html where we'll mount our React app.
// We use the non-null assertion (!) because we know the element exists.
// If it doesn't exist, we want the app to fail loudly (not silently).

const rootElement = document.getElementById('root');

// Safety check - if root element doesn't exist, throw a helpful error
if (!rootElement) {
  throw new Error(
    'Failed to find the root element. ' +
    'Make sure there is a <div id="root"></div> in your index.html file.'
  );
}

// =============================================================================
// CREATE REACT ROOT AND RENDER
// =============================================================================
// createRoot is the React 18 way to render an application.
// It replaces the old ReactDOM.render() method.

const root = ReactDOM.createRoot(rootElement);

// Render the application
root.render(
  // ---------------------------------------------------------------------------
  // REACT STRICT MODE
  // ---------------------------------------------------------------------------
  // StrictMode enables additional development checks:
  //   - Identifies components with unsafe lifecycles
  //   - Warns about legacy string ref API usage
  //   - Warns about deprecated findDOMNode usage
  //   - Detects unexpected side effects
  //   - Ensures reusable state (components unmount/remount in dev)
  //
  // Note: StrictMode causes components to render twice in development.
  // This is intentional - it helps find bugs. It does NOT happen in production.
  <React.StrictMode>
    {/* 
    -------------------------------------------------------------------------
    BROWSER ROUTER
    -------------------------------------------------------------------------
    BrowserRouter enables client-side routing using the HTML5 History API.
    
    How it works:
      - Listens for URL changes
      - Matches URL to route definitions
      - Renders the appropriate component
      - Updates URL without page reload (using pushState)
    
    This must wrap the entire app so all components can access routing.
    
    Alternative routers:
      - HashRouter: Uses URL hash (#) for routing (works without server config)
      - MemoryRouter: Keeps history in memory (useful for tests)
    */}
    <BrowserRouter>
      {/* 
      -------------------------------------------------------------------------
      APP COMPONENT
      -------------------------------------------------------------------------
      The root component of our application.
      All other components are rendered inside App.
      */}
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// =============================================================================
// OPTIONAL: PERFORMANCE MONITORING
// =============================================================================
// Uncomment to enable performance monitoring with React's Profiler API
// or integrate with services like Google Analytics, Sentry, etc.
//
// Example with web-vitals (would need to install the package):
//
// import { reportWebVitals } from './reportWebVitals';
// reportWebVitals(console.log);
//
// Or send to an analytics endpoint:
// reportWebVitals((metric) => {
//   fetch('/api/analytics', {
//     method: 'POST',
//     body: JSON.stringify(metric),
//   });
// });