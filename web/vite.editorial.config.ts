import { defineConfig } from 'vite'
export default defineConfig({ base: './', build: { outDir: 'editorial-dist', rollupOptions: { input: 'editorial-preview.html' } } })
