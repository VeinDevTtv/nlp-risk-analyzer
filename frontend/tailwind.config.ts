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
      },
    },
  },
  plugins: [],
}
export default config
