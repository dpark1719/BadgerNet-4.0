import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// For GitHub Pages (or any subpath), set base, e.g.:
//   base: '/BadgerNet-4.0/'
// Data fetches use `publicPath()` in src so /data/*.json resolve correctly.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
  },
})
