import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/search': 'http://localhost:5000',
      '/chats': 'http://localhost:5000',
      '/templates': 'http://localhost:5000',
    }
  }
})

