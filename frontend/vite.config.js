import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => ({
  base: '/ui/',
  plugins: [tailwindcss()],
  define: { __DEMO__: JSON.stringify(mode === 'demo') },
  server: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { port: 4173, strictPort: true },
}));
