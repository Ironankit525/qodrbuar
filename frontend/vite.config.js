import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In dev, /api is proxied to the Python backend (override with API_PROXY_TARGET).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' },
  },
})
