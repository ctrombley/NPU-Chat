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
        'chat-bg': 'rgb(var(--color-chat-bg) / <alpha-value>)',
        'sidebar-bg': 'rgb(var(--color-sidebar-bg) / <alpha-value>)',
        'message-sent': 'rgb(var(--color-message-sent) / <alpha-value>)',
        'message-received': 'rgb(var(--color-message-received) / <alpha-value>)',
        'accent': 'rgb(var(--color-accent) / <alpha-value>)',
        'accent-hover': 'rgb(var(--color-accent-hover) / <alpha-value>)',
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

