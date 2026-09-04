/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        base: '#FAF7F0',
        primary: '#1C3A56',
        surface: '#DCE9F2',
        accent: '#4C9A94',
        neutral: '#E7E3DA',
        rare: '#C7C0DE',
        textPrimary: '#1A1F26',
        textSecondary: '#5B6470',
      },
      fontFamily: {
        sans: ['"Hanken Grotesk"', 'sans-serif'],
        serif: ['"Fraunces"', 'serif'],
      },
    },
  },
  plugins: [],
}
