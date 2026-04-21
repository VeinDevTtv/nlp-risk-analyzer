import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef6ff',
          100: '#d9eaff',
          200: '#b6d4ff',
          300: '#88b9ff',
          400: '#5a98ff',
          500: '#2f72ff',
          600: '#2159db',
          700: '#1b48b0',
          800: '#1a3d8f',
          900: '#193772',
        },
        glass: {
          border: 'rgba(255, 255, 255, 0.1)',
          fill: 'rgba(17, 25, 40, 0.75)',
          highlight: 'rgba(255, 255, 255, 0.05)',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
      },
      backdropBlur: {
        xs: '2px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      }
    },
  },
  plugins: [],
}
export default config
