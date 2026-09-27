import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/ops/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/fanpage-care': 'http://127.0.0.1:7777',
      '/ops/auth': 'http://127.0.0.1:7777',
      '/ops/me': 'http://127.0.0.1:7777',
      '/ops/users': 'http://127.0.0.1:7777',
      '/kanban': 'http://127.0.0.1:7777',
      '/usage': 'http://127.0.0.1:7777',
      '/inbox': 'http://127.0.0.1:7777',
      '/auth': 'http://127.0.0.1:7777',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
