/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Anthropic warm editorial system (Refero DESIGN.md, Claude).
        // Token swap, not a rename: the class names below keep their old
        // names so the 170+ usages across pages flip with the tokens.
        // ink now holds warm light surfaces, slate holds warm ink text.
        paper: '#f8f8f6',
        ivory: '#f0eee6',
        manilla: '#f5e3c7',
        ink: {
          950: '#f8f8f6', // page canvas (bone parchment)
          900: '#ffffff', // card surface (paper white)
          800: '#f0eee6', // ivory, secondary surface
          700: '#e3dacc', // sand, hairlines and fills
          600: '#cccbc8', // stone
          500: '#b0aea5', // pebble
        },
        slate: {
          100: '#141413', // slate dark, primary text
          200: '#3d3d3a', // graphite, secondary text
          300: '#6b6a66', // mid warm gray
          400: '#87867f', // ash, muted text
          500: '#b0aea5', // pebble, more muted
          600: '#cccbc8',
          700: '#e3dacc',
          800: '#f0eee6',
          900: '#faf9f5',
          950: '#f8f8f6',
        },
        clay: {
          DEFAULT: '#d97757', // the one chromatic accent
          deep: '#c6613f', // clay hover
        },
        bull: '#02a745', // semantic success green
        bear: '#a10214', // semantic error red
        brand: {
          400: '#d97757',
          500: '#c6613f',
          600: '#a84e2e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['"Source Serif 4"', 'Charter', 'Georgia', 'serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(18,18,18,0.05), 0 12px 32px -16px rgba(18,18,18,0.18)',
      },
    },
  },
  plugins: [],
};
