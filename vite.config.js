import { defineConfig } from 'vite';

// The frontend lives in web/ as plain static files. Vite serves it directly;
// web/index.html is the entry point. Dev server runs on 8001 to match the
// API's default CORS_ORIGINS (see api/main.py), and proxies the REST routes to
// the API on 8002 so the page can call same-origin paths in dev if desired.
const API_TARGET = process.env.VR_API_TARGET || 'http://localhost:8002';

export default defineConfig({
  root: 'web',
  server: {
    host: true,
    port: 8001,
    proxy: {
      '/queue': API_TARGET,
      '/tracks': API_TARGET,
      '/now-playing': API_TARGET,
    },
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
});
