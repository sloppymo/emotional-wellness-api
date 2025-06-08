import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/core': resolve(__dirname, './src/core'),
      '@/game': resolve(__dirname, './src/game'),
      '@/ui': resolve(__dirname, './src/ui'),
      '@/api': resolve(__dirname, './src/api'),
      '@/utils': resolve(__dirname, './src/utils'),
      '@/types': resolve(__dirname, './src/types'),
      '@/assets': resolve(__dirname, './assets'),
      '@/config': resolve(__dirname, './config'),
    },
  },
  server: {
    port: 3000,
    host: true,
    watch: {
      usePolling: true,
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'phaser', 'pixi.js', 'three'],
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
}) 