/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FDFBF7',
          100: '#F9F5EC',
          200: '#F4EFE2',
          300: '#EBE2CD',
          400: '#DECFA9',
        },
        nixtio: {
          bg: '#F5F1EA',
          card: '#FBF9F5',
          dark: '#1E1E24',
          darkCard: '#272730',
          accent: '#F5C842',
          accentHover: '#E5B932',
          subtle: '#8C8C9A',
          border: '#E8E2D6',
        },
        palette: {
          midnight: '#2C1320',   // Midnight Violet
          grape: '#5F4B66',      // Vintage Grape
          lavender: '#A7ADC6',   // Lavender Grey
          slateLav: '#8797AF',   // Lavender Grey slate
          blueSlate: '#56667A',  // Blue Slate
          darkCard: '#1C0D15',
          border: 'rgba(167, 173, 198, 0.25)',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'nixtio': '0 10px 30px -5px rgba(30, 30, 36, 0.05), 0 4px 12px -2px rgba(30, 30, 36, 0.03)',
        'nixtio-lg': '0 20px 40px -10px rgba(30, 30, 36, 0.1)',
        'nixtio-dark': '0 12px 30px rgba(0, 0, 0, 0.25)',
      },
      borderRadius: {
        '3xl': '1.75rem',
        '4xl': '2.25rem',
      }
    },
  },
  plugins: [],
};
