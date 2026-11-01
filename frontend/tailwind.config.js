/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f1f5f9',
          100: '#e2e8f0',
          600: '#1e4a72',
          700: '#16395a',
          800: '#102a44',
          900: '#0b1f33',
        },
        green: {
          50: '#ecfdf5',
          100: '#d1fae5',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 42, 68, 0.06), 0 8px 24px rgba(15, 42, 68, 0.06)',
      },
    },
  },
  plugins: [],
}
