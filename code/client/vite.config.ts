import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import ports from '../ports.json'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'API_TARGET')
  const proxy = {
    '/api': { target: env.API_TARGET || `http://127.0.0.1:${ports.backend}`, changeOrigin: true },
  }
  return {
    base: './',
    plugins: [react()],
    server: { port: ports.frontend, strictPort: true, proxy },
    preview: { proxy },
    build: { rollupOptions: { input: 'frontend.html' } },
  }
})
