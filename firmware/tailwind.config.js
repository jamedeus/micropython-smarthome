/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './setup.html'
  ],
  theme: {
    extend: {
      height: {
        '250': '250vh',
      },
      transitionDuration: {
        '800': '800ms',
      },
      spacing: {
        '50': '50%',
      },
      zIndex: {
        '99': '99',
        '100': '100',
      },
    },
  },
  plugins: [],
}

