/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'bauhaus': ['Bauhaus', 'sans-serif'],
      },
      colors: {
        'chat-bg': '#232323',
        'sidebar-bg': '#1a1a1a',
        'message-sent': '#383838',
        'message-received': '#111111',
        'accent': '#9805b5',
        'accent-hover': '#b025d1',
      },
      animation: {
        'pulse': 'pulse 1s',
        'load': 'load 1s steps(10) infinite',
        'pupil': 'pupilAnimation 2s infinite alternate',
      },
    },
  },
  plugins: [],
}

