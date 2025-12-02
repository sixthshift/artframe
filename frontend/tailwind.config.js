/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#667eea',
          600: '#5a6fd6',
          700: '#4f46e5',
          800: '#4338ca',
          900: '#3730a3',
        },
        accent: {
          500: '#764ba2',
        }
      },
      fontFamily: {
        mono: ['SF Mono', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
