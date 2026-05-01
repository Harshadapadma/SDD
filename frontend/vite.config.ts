import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: 'localhost',
    port: 5173,
    watch: {
      usePolling: true,
      interval: 100
    },
    hmr: {
      host: 'localhost',
      port: 5173,
    }
  }
})