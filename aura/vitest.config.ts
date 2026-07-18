import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    // Playwright specs run via Playwright, not vitest — importing
    // @playwright/test under vitest fails the whole run.
    exclude: ['**/node_modules/**', 'tests/e2e/**'],
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
