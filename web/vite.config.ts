import { defineConfig } from 'vite'
import osydHmr from 'vite-plugin-osyd'

// https://vitejs.dev/config/
export default defineConfig({
  // Deployed as a GitHub Pages project page under /point-share-rating/
  base: '/point-share-rating/',
  // The Python pipeline writes ratings.json to ../data; serve and ship it as-is.
  publicDir: '../data',
  plugins: [osydHmr()],
})
