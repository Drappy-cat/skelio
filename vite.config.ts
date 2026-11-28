import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// Vite config — https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  optimizeDeps: {
    entries: ['index.html'],
  },
  server: {
    port: 5173,
    watch: {
      ignored: [
        '**/dataset/**',
        '**/models/**',
        '**/runs/**',
        '**/yolo11*/**',
        '**/assets_sempro/**',
        '**/docs/**',
        '**/notebooks/**',
        '**/apps/**',
        '**/core/**',
      ],
    },
    proxy: {
      '/video_feed': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
