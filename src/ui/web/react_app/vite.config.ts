import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [
    react({
      fastRefresh: true,
      babel: {
        plugins: [
          // Add plugins for AI component hot reloading
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@ai': path.resolve(__dirname, './src/ai'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@types': path.resolve(__dirname, './src/types')
    },
  },
  server: {
    port: 3000,
    host: true,
    hmr: {
      overlay: false
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    target: 'esnext',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
          ui: ['@headlessui/react', '@heroicons/react', 'framer-motion'],
          'ai-core': ['@ai/react', '@vercel/ai'],
          'ui-components': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          'utils': ['clsx', 'tailwind-merge', 'date-fns']
        },
      },
    },
    chunkSizeWarningLimit: 1000
  },
  define: {
    __AI_DEVELOPMENT__: process.env.NODE_ENV === 'development',
    __AI_FEATURES_ENABLED__: true
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@ai/react',
      'date-fns',
      'clsx'
    ],
    exclude: ['@vercel/ai']
  }
});
