import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // FE-002: Bundle optimization settings
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Core React libraries - rarely change
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // UI utilities
          'vendor-ui': ['lucide-react', 'clsx'],
          // Data handling
          'vendor-data': ['date-fns', 'axios'],
        },
      },
    },
    // Target modern browsers for smaller bundles
    target: 'es2020',
    // Generate source maps for debugging (can disable in prod if needed)
    sourcemap: false,
    // Chunk size warning threshold (500KB)
    chunkSizeWarningLimit: 500,
  },
})
