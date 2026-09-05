/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#14213a',
        muted: '#61708a',
        line: '#dfe6ee',
        emerald: {
          DEFAULT: '#07875f',
          50: '#ecfdf5',
          100: '#d1fae5',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
        blue: {
          DEFAULT: '#0d67d5',
          50: '#eff6ff',
          100: '#dbeafe',
          300: '#93c5fd',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(20, 33, 58, 0.06), 0 8px 24px rgba(20, 33, 58, 0.025)',
      },
    },
  },
  plugins: [],
};
