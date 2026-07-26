/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#070D19',
          900: '#0B1220',
          800: '#111A2C',
          700: '#18233A',
          600: '#1E2A44',
          500: '#2C3B5C',
        },
        bull: '#10B981',
        bear: '#F43F5E',
        brand: {
          400: '#38BDF8',
          500: '#0EA5E9',
          600: '#0284C7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.5)',
      },
    },
  },
  plugins: [],
};
