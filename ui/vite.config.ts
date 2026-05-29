import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';

let targetUrl = 
  process.env.RAILWAY_SERVICE_BACKEND_V3_URL || 
  process.env.VITE_API_BASE_URL || 
  process.env.VITE_API_URL || 
  process.env.API_BASE_URL || 
  'http://localhost:8000';

// Ensure targetUrl starts with http:// or https:// to prevent proxy split TypeError
if (targetUrl && !targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
  targetUrl = `http://${targetUrl}`;
}

console.log('--- PROXY RUNTIME TARGET URL:', targetUrl);
console.log('--- ALL PROCESS ENV KEYS:', Object.keys(process.env).filter(k => k.includes('API') || k.includes('VITE') || k.includes('URL')));

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
  },
  preview: {
    allowedHosts: true,
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: targetUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
