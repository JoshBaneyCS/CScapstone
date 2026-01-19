// =============================================================================
// VITE CONFIGURATION FOR CASINO CAPSTONE FRONTEND
// =============================================================================
// Vite is a modern build tool that provides:
//   - Lightning-fast dev server with Hot Module Replacement (HMR)
//   - Optimized production builds with code splitting
//   - Native ES modules support (no bundling during development)
//   - Built-in TypeScript support
//
// Why Vite over Create React App (CRA)?
//   - Much faster startup (no bundling in dev mode)
//   - Faster hot updates (only updates what changed)
//   - Smaller production bundles
//   - More flexible configuration
//   - Active development (CRA is in maintenance mode)
//
// Configuration documentation: https://vitejs.dev/config/
// =============================================================================

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  // ===========================================================================
  // PLUGINS
  // ===========================================================================
  // Plugins extend Vite's functionality
  
  plugins: [
    // React plugin provides:
    //   - Fast Refresh (HMR that preserves component state)
    //   - JSX transformation
    //   - React-specific optimizations
    react(),
  ],

  // ===========================================================================
  // PATH RESOLUTION
  // ===========================================================================
  // Configure how imports are resolved
  
  resolve: {
    // Alias: Create shortcuts for import paths
    // This allows using '@/components/Button' instead of '../../components/Button'
    // Must match the paths configured in tsconfig.json
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  // ===========================================================================
  // DEVELOPMENT SERVER
  // ===========================================================================
  // Configuration for the dev server (npm run dev)
  
  server: {
    // Port: Which port to run the dev server on
    // Default is 5173, but can be changed if that port is in use
    port: 5173,
    
    // StrictPort: If true, exit if port is already in use
    // If false, try the next available port
    strictPort: true,
    
    // Host: Which network interfaces to listen on
    // '0.0.0.0' makes it accessible from other devices on the network
    // Useful for testing on mobile devices or in Docker
    host: '0.0.0.0',

    // ---------------------------------------------------------------------------
    // PROXY CONFIGURATION
    // ---------------------------------------------------------------------------
    // Proxy API requests to the backend server during development.
    // This solves CORS issues by making API calls appear to come from
    // the same origin as the frontend.
    //
    // How it works:
    //   1. Frontend makes request to /api/auth/login
    //   2. Vite dev server intercepts requests starting with /api
    //   3. Vite forwards the request to http://localhost:8080/api/auth/login
    //   4. Response is returned to the frontend
    //
    // Note: In production, the reverse proxy (nginx/ingress) handles this.
    // This proxy is only used during local development.
    
    proxy: {
      '/api': {
        // Target: The backend server URL
        target: 'http://localhost:8080',
        
        // ChangeOrigin: Changes the origin header to match the target
        // Required for some backend servers that check the origin
        changeOrigin: true,
        
        // Secure: Whether to verify SSL certificates
        // Set to false for local development with self-signed certs
        secure: false,
        
        // Configure proxy to handle WebSocket connections (if needed later)
        // ws: true,
      },
    },
  },

  // ===========================================================================
  // PREVIEW SERVER
  // ===========================================================================
  // Configuration for the preview server (npm run preview)
  // Preview serves the production build locally for testing
  
  preview: {
    port: 5173,
    strictPort: true,
    host: '0.0.0.0',
  },

  // ===========================================================================
  // BUILD CONFIGURATION
  // ===========================================================================
  // Configuration for production builds (npm run build)
  
  build: {
    // OutDir: Output directory for the build
    outDir: 'dist',
    
    // SourceMap: Generate source maps for debugging
    // 'hidden' creates source maps but doesn't reference them in the bundle
    // This allows error tracking services to use them without exposing to users
    sourcemap: true,
    
    // Target: Which browsers to support
    // esnext assumes modern browsers that support native ES modules
    target: 'esnext',
    
    // MinifyL Minification method
    // 'esbuild' is faster, 'terser' produces slightly smaller bundles
    minify: 'esbuild',

    // Rollup options for advanced bundling configuration
    rollupOptions: {
      output: {
        // Manual chunks: Split code into separate files for better caching
        // When you update one part of your app, users only re-download that chunk
        manualChunks: {
          // Vendor chunk: Third-party libraries that rarely change
          vendor: ['react', 'react-dom'],
          // Router chunk: React Router (separate because it's a distinct feature)
          router: ['react-router-dom'],
        },
      },
    },
  },

  // ===========================================================================
  // ENVIRONMENT VARIABLES
  // ===========================================================================
  // Configuration for environment variables
  //
  // Vite exposes env variables on import.meta.env
  // Only variables prefixed with VITE_ are exposed to the client
  // This prevents accidentally leaking sensitive server-side variables
  //
  // Example:
  //   VITE_API_URL=http://localhost:8080  → Exposed
  //   DATABASE_URL=postgres://...         → NOT exposed (no VITE_ prefix)
  //
  // Access in code:
  //   const apiUrl = import.meta.env.VITE_API_URL;
  
  envPrefix: 'VITE_',

  // ===========================================================================
  // CSS CONFIGURATION
  // ===========================================================================
  // Configuration for CSS processing
  
  css: {
    // DevSourcemap: Enable CSS source maps in development
    // Makes it easier to debug styles in browser dev tools
    devSourcemap: true,
  },

  // ===========================================================================
  // DEPENDENCY OPTIMIZATION
  // ===========================================================================
  // Vite pre-bundles dependencies for faster page loads
  
  optimizeDeps: {
    // Include: Dependencies to pre-bundle
    // Add packages here if you see slow loading or "optimizing dependencies" messages
    include: ['react', 'react-dom', 'react-router-dom'],
  },
});