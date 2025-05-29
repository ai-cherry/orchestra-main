import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { TanStackRouterVite } from '@tanstack/router-vite-plugin'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    TanStackRouterVite(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  css: {
    // Ensure CSS is properly processed
    devSourcemap: true,
    // Disable CSS code splitting to ensure CSS is included in the main bundle
    codeSplit: false,
    // Ensure all CSS is extracted to a single file
    preprocessorOptions: {
      scss: {
        charset: false
      }
    }
  },
  build: {
    // Generate source maps for better debugging
    sourcemap: mode === 'development',
    // Ensure assets are properly hashed for cache busting
    assetsInlineLimit: 4096,
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Ensure CSS is properly extracted and not code-split
    cssCodeSplit: false,
    // Minify output for production
    minify: mode === 'production',
    // Rollup options for better optimization
    rollupOptions: {
      output: {
        // Ensure CSS is included in the main entry
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
        // Ensure main CSS is not code-split
        manualChunks: undefined
      }
    },
    // Ensure proper asset handling
    assetsDir: 'assets',
    // Ensure proper HTML handling
    emptyOutDir: true,
    // Ensure proper CSS handling
    cssTarget: 'es2015'
  },
  // Ensure proper HTML handling
  server: {
    // Ensure proper hot module replacement
    hmr: true
  },
  // Keep test configuration
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts', // Vitest setup file
    css: true, // If your components import CSS files
    // Optional: configure coverage
    // coverage: {
    //   provider: 'v8', // or 'istanbul'
    //   reporter: ['text', 'json', 'html'],
    // },
  },
}))
