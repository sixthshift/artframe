/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import preact from '@preact/preset-vite'
import path from 'path'

export default defineConfig({
  plugins: [preact()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Preact compat for libraries expecting React
      'react': 'preact/compat',
      'react-dom': 'preact/compat',
      'react-dom/test-utils': 'preact/test-utils',
      'react/jsx-runtime': 'preact/jsx-runtime'
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/api/generated.ts', // Auto-generated file
        'src/pages/**', // Pages require full hook integration (React/Preact compat)
      ],
      thresholds: {
        // Lower thresholds due to React/Preact compatibility issues with hooks
        // Focus on testing utilities, API client, and simple components
        statements: 30,
        branches: 50,
        functions: 30,
        lines: 30,
      },
    },
    // CSS modules mocking
    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },
  },
})
