/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#effcf9',
          100: '#c9f7ee',
          200: '#96efe0',
          300: '#5ee0cd',
          400: '#2dc9b6',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        ai: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
        },
      },
      boxShadow: {
        soft: '0 1px 2px rgba(15,23,42,.05), 0 10px 30px rgba(15,23,42,.06)',
        lift: '0 8px 24px rgba(15,23,42,.10), 0 28px 60px rgba(15,23,42,.10)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
    },
  },
  plugins: [],
}
