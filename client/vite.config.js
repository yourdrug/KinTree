import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 3001,
    proxy: {
      // Проксируем все API-пути на бэкенд
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/account': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/families': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/persons': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/relations': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
